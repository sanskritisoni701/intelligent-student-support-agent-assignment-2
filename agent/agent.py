
import os
import json
import time
import re
from datetime import datetime
from tools.support_tools import (
    create_support_request,
    get_student_support_requests
)
from dotenv import load_dotenv
from groq import Groq

from tools.student_tools import get_student_fee_status
from tools.policy_tools import search_policy
from tools.approval_tools import create_due_date_change_request

from memory.memory_manager import (
    save_memory,
    get_memories
)

from agent.context_manager import build_context


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL")

if not API_KEY:
    raise ValueError("Groq API key not found in .env file.")

if not MODEL:
    raise ValueError("Groq model not configured in .env file.")

client = Groq(api_key=API_KEY)


def is_complete_due_date_change_request(question):
    """
    Detect a due-date change request that already includes:
    - a requested date
    - a reason for the change

    When both are present, the agent will be required to call the
    approval-request tool instead of replying with another question.
    """
    text = str(question or "").lower()

    due_date_intent = bool(re.search(
        r"(due[\s-]*date|fee[\s-]*payment deadline)",
        text
    )) and bool(re.search(
        r"(change|extend|extension|postpone|reschedule|new due date|"
        r"additional time|more time)",
        text
    ))

    date_present = bool(re.search(
        r"\b\d{4}-\d{2}-\d{2}\b|"
        r"\b\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|"
        r"apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        r"sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+\d{4}\b",
        text
    ))

    reason_present = bool(re.search(
        r"\b(because|since|as i|my reason|reason is|need additional time|"
        r"need more time|arrange the payment|financial|salary|"
        r"funds|payment difficulty)\b",
        text
    ))

    return due_date_intent and date_present and reason_present


def extract_due_date_and_reason(question):
    """Extract a natural-language date and reason from a complete request."""
    text = str(question or "")

    date_match = re.search(
        r"\b(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+(\d{4})\b",
        text,
        flags=re.IGNORECASE,
    )

    if date_match:
        parsed_date = datetime.strptime(
            date_match.group(0), "%d %B %Y"
        ).date()
    else:
        iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        if not iso_match:
            raise ValueError("Please provide the requested due date.")
        parsed_date = datetime.strptime(
            iso_match.group(0), "%Y-%m-%d"
        ).date()

    # First look for an explicit reason marker such as "because".
    reason_match = re.search(
        r"\b(?:because|since|my reason is|the reason is)\b\s*(.+)$",
        text,
        flags=re.IGNORECASE,
    )

    reason = ""
    if reason_match:
        reason = reason_match.group(1).strip()
    else:
        date_end = date_match.end() if date_match else iso_match.end()
        reason = text[date_end:].strip(" \t\r\n.,;:-")

    reason = re.sub(r"^(?:because|since)\s+", "", reason, flags=re.IGNORECASE)
    reason = reason.strip().rstrip(" .")
    if not reason:
        raise ValueError(
            "Please provide a reason, for example: 'I need additional time to arrange the payment.'"
        )

    return parsed_date.isoformat(), reason


# ==========================================
# 2. DEFINE AVAILABLE AI TOOLS
# ==========================================

TOOLS = [

    # TOOL 1: Student fee status
    {
        "type": "function",
        "function": {
            "name": "get_student_fee_status",
            "description": (
                "Retrieve the fee status of a student "
                "using their student ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The student's ID."
                    }
                },
                "required": ["student_id"]
            }
        }
    },

    # TOOL 2: Create support request
    {
        "type": "function",
        "function": {
            "name": "create_support_request",
            "description": (
                "Create a support ticket when a student "
                "requests help with an issue."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string"
                    },
                    "issue_description": {
                        "type": "string"
                    },
                    "category": {
                        "type": "string"
                    }
                },
                "required": [
                    "student_id",
                    "issue_description"
                ]
            }
        }
    },
    # TOOL 2.1: Retrieve support requests
    {
        "type": "function",
        "function": {
            "name": "get_student_support_requests",
            "description": (
                "Retrieve the logged-in student's existing "
                "support tickets. Use this whenever a student "
                "asks to view, check, list or track their "
                "existing support requests or ticket status."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    # TOOL 3: Search student handbook
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": (
                "Search the student handbook for policy "
                "information about fees, scholarships, "
                "course changes, attendance and support."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Policy-related question."
                    }
                },
                "required": ["question"]
            }
        }
    },

    # TOOL 4: Save student memory
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": (
                "Save useful long-term student information "
                "when the student explicitly asks you to "
                "remember it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string"
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "programme",
                            "preferred_language",
                            "response_preference",
                            "learning_preference"
                        ]
                    },
                    "value": {
                        "type": "string"
                    }
                },
                "required": [
                    "student_id",
                    "category",
                    "value"
                ]
            }
        }
    },

    # TOOL 5: Retrieve student memory
    {
        "type": "function",
        "function": {
            "name": "get_memories",
            "description": (
                "Retrieve previously saved student "
                "preferences and programme information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string"
                    }
                },
                "required": ["student_id"]
            }
        }
    }
,

    # TOOL 6: Request a fee due-date change (requires admin approval)
    {
        "type": "function",
        "function": {
            "name": "create_due_date_change_request",
            "description": (
                "Submit a student's request to change their fee payment due date. "
                "This only creates a PENDING approval request; it never changes "
                "the fee record. Use when the logged-in student asks to change "
                "or extend their fee due date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The active student's ID."
                    },
                    "requested_due_date": {
                        "type": "string",
                        "description": "Requested new due date in YYYY-MM-DD format."
                    },
                    "reason": {
                        "type": "string",
                        "description": "The student's reason for requesting the change."
                    }
                },
                "required": ["student_id", "requested_due_date", "reason"]
            }
        }
    }
]


# ==========================================
# 3. MAP TOOLS TO PYTHON FUNCTIONS
# ==========================================

AVAILABLE_FUNCTIONS = {
    "get_student_fee_status": get_student_fee_status,
    "create_support_request": create_support_request,
    "get_student_support_requests": get_student_support_requests,
    "search_policy": search_policy,
    "save_memory": save_memory,
    "get_memories": get_memories,
    "create_due_date_change_request": create_due_date_change_request
}


# ==========================================
# 4. MAIN AGENT FUNCTION
# ==========================================

def run_agent(user_question, student_id=None):

    # STEP 0: INITIALIZE MEASUREMENTS

    start_time = time.perf_counter()

    total_input_tokens = 0
    total_output_tokens = 0

    execution_trace = []
    tools_used = []

    # STEP 0.1: TRACE RECORDING FUNCTION

    def add_trace(event, **details):

        execution_trace.append({
            "event": event,
            "elapsed_seconds": round(
                time.perf_counter() - start_time, 3
            ),
            **details
        })

    add_trace(
        "user_query_received",
        question=user_question
    )

    # STEP 1: BUILD RELEVANT STUDENT CONTEXT

    context = "No student-specific context provided."

    if student_id:

        context = build_context(
            student_id,
            user_question
        )

    add_trace(
        "context_selected",
        student_id_provided=bool(student_id),
        context_available=(
            context != "No student-specific context provided."
        ),
        context_length=len(context)
    )

    # STEP 2: DEFINE AGENT INSTRUCTIONS

    system_prompt = """
    You are an Intelligent Student Support Agent.

    Help students with academic, administrative,
    financial and technical queries.

    TOOL SELECTION RULES:

    1. Use get_student_fee_status for personal fee
       balance, payment history and fee status.

    2. Use search_policy for general college policies,
       deadlines, scholarships, course changes,
       attendance and payment-related problems.

    3. A student ID is not required for general
       policy retrieval.

    4. Use create_support_request when a student
       explicitly asks to create a support ticket.

    RESPONSE RULES:

    5. Never invent student records or fee information.

    6. Ask for a student ID if a personal fee query
       requires one and it is missing.

    7. Answer policy questions only using retrieved
       handbook evidence.

    8. Never invent policy rules, deadlines or percentages.

    9. Never claim that a support ticket was created
       unless the tool confirms success.

    10. Answer clearly and in simple language.

    MEMORY RULES:

    11. When a student explicitly asks you to remember
        useful long-term information, use save_memory.

    12. Only save approved memory categories.

    13. Never store passwords, OTPs, sensitive personal
        information or temporary issues.

    14. When a student asks what you remember about
        them, use get_memories.

    15. Never guess or invent remembered information.

    16. If no relevant memory exists, say so.

    17. Never retrieve or disclose another student's memory.

    18. If the student ID is missing, ask for it before
        saving or retrieving personal memory.

    HUMAN APPROVAL RULES:

    19. When a student asks to change or extend their fee due date,
        use create_due_date_change_request.
    20. This tool only submits a request for administrator approval.
        It does not change the student fee record.
    21. Never tell the student that the due date has changed merely
        because a request was submitted.
    22. Clearly state that the request is PENDING until an admin
        approves it. Do not claim approval yourself.
    23. Ask for the requested date and reason if either is missing.

    CONTEXT RULES:

    24. Use the selected student context when relevant.

    25. Do not invent information that is absent
        from the selected context.
    26. Use get_student_support_requests whenever a student
   asks to view, list, check or track their existing
   support tickets.

27. Never invent ticket details. Only report tickets
   returned by the retrieval tool.
    """

    # STEP 3: ADD SELECTED CONTEXT TO SYSTEM PROMPT

    system_prompt += (
        "\n\nSELECTED STUDENT CONTEXT:\n" + context
    )

    # Provide active student ID to the agent

    if student_id:

        system_prompt += (
            f"\n\nACTIVE STUDENT ID: {student_id}\n"
            "Use this student ID for personal student "
            "queries. Do not ask the student to provide "
            "it again when it is already available."
        )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_question
        }
    ]

    # ==========================================
    # STEP 3.5: DETERMINISTIC HUMAN-APPROVAL ROUTING
    # ==========================================

    # For a complete authenticated fee due-date request, call the
    # approval tool directly. This avoids depending on the LLM to
    # decide whether to invoke a sensitive workflow.
    if student_id and is_complete_due_date_change_request(user_question):
        add_trace(
            "approval_request_detected",
            student_id_provided=True,
        )

        try:
            requested_date, request_reason = extract_due_date_and_reason(
                user_question
            )

            add_trace(
                "tool_call",
                tool_name="create_due_date_change_request",
            )

            result = create_due_date_change_request(
                student_id=student_id,
                requested_due_date=requested_date,
                reason=request_reason or str(user_question or "").strip(),
                authenticated_student_id=student_id,
            )

            tools_used.append("create_due_date_change_request")

            add_trace(
                "tool_result",
                tool_name="create_due_date_change_request",
                success=bool(result.get("success")),
                result_preview=json.dumps(result, default=str)[:1200],
            )

            if result.get("success"):
                answer = (
                    f"Your fee due-date change request has been submitted "
                    f"successfully. Request ID: {result.get('request_id')}. "
                    f"Status: PENDING APPROVAL. Your current fee due date "
                    f"has not been changed. An administrator must review "
                    f"and approve the request."
                )
            else:
                answer = (
                    "I couldn't submit your fee due-date change request. "
                    + str(result.get("message") or result.get("error") or
                          "Please check the details and try again.")
                )

        except Exception as error:
            add_trace(
                "tool_error",
                tool_name="create_due_date_change_request",
                error=str(error),
            )
            answer = (
                "I encountered a problem while submitting your request. "
                "Your fee due date has not been changed. Please try again."
            )

        add_trace(
            "final_answer_generated",
            answer_generated=True,
        )

        latency = time.perf_counter() - start_time
        return {
            "answer": answer,
            "tools_used": tools_used,
            "steps": 0,  # Deterministic approval path makes no LLM calls.
            "trace_events": len(execution_trace),
            "latency_seconds": round(latency, 3),
            "token_usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
            },
            "trace": execution_trace,
        }

    # ==========================================
    # STEP 4: START AGENT LOOP
    # ==========================================

    for step in range(5):

        # STEP 4.1: SEND REQUEST TO GROQ

        add_trace(
            "llm_request",
            iteration=step + 1,
            message_count=len(messages)
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0
        )

        # STEP 4.2: RECORD TOKEN USAGE

        usage = response.usage

        if usage:

            total_input_tokens += usage.prompt_tokens or 0
            total_output_tokens += usage.completion_tokens or 0

        assistant_message = response.choices[0].message

        # STEP 4.3: RECORD MODEL DECISION

        add_trace(
            "llm_response",
            iteration=step + 1,
            tool_requested=bool(assistant_message.tool_calls),
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0
        )

        # ==========================================
        # STEP 5: CHECK FOR FINAL ANSWER
        # ==========================================

        if not assistant_message.tool_calls:

            add_trace(
                "final_answer_generated",
                answer_generated=bool(assistant_message.content)
            )

            latency = time.perf_counter() - start_time

            return {
                "answer": assistant_message.content,
                "tools_used": tools_used,
                "steps": step + 1,  # Number of LLM iterations.
                "trace_events": len(execution_trace),

                "latency_seconds": round(latency, 3),

                "token_usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "total_tokens": (
                        total_input_tokens + total_output_tokens
                    )
                },

                "trace": execution_trace
            }

        # ==========================================
        # STEP 6: ADD TOOL REQUEST TO CONVERSATION
        # ==========================================

        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        # ==========================================
        # STEP 7: EXECUTE REQUESTED TOOLS
        # ==========================================

        for tool_call in assistant_message.tool_calls:

            function_name = tool_call.function.name

            add_trace(
                "tool_call",
                tool_name=function_name
            )

            try:

                arguments = json.loads(
                    tool_call.function.arguments
                )

                # STEP 7.1: CHECK TOOL AVAILABILITY
                if function_name not in AVAILABLE_FUNCTIONS:
                    result = {
                        "success": False,
                        "message": "Tool is not available."
                    }
                else:
                    function_to_call = AVAILABLE_FUNCTIONS[function_name]

                    # Record every registered tool invocation for evaluation.
                    tools_used.append(function_name)

                    # STEP 7.2: IDENTIFY PERSONAL TOOLS
                    personal_tools = [
                        "get_student_fee_status",
                        "create_support_request",
                        "save_memory",
                        "get_memories"
                    ]

                    # Each tool follows exactly one authorization/execution path.
                    if function_name == "create_due_date_change_request":
                        # Authenticated identity comes only from the active session.
                        if not student_id:
                            result = {
                                "success": False,
                                "error": "AUTHENTICATION_REQUIRED",
                                "message": "Please log in to submit a fee due-date change request."
                            }
                        else:
                            arguments.pop("authenticated_student_id", None)
                            arguments["student_id"] = student_id

                            supplied_reason = str(arguments.get("reason") or "").strip()
                            if not supplied_reason:
                                arguments["reason"] = str(user_question or "").strip()

                            result = function_to_call(
                                **arguments,
                                authenticated_student_id=student_id
                            )

                    elif function_name == "get_student_support_requests":
                        if not student_id:
                            result = {
                                "success": False,
                                "error": "AUTHENTICATION_REQUIRED",
                                "message": "Please log in to view your support tickets."
                            }
                        else:
                            result = function_to_call(
                                authenticated_student_id=student_id
                            )

                    elif function_name in personal_tools:
                        if not student_id:
                            result = {
                                "success": False,
                                "error": "AUTHENTICATION_REQUIRED",
                                "message": "Please log in to access personal student services."
                            }
                        else:
                            # Never accept authenticated identity from the LLM.
                            arguments.pop("authenticated_student_id", None)

                            # Preserve the requested ID for ownership verification.
                            arguments.setdefault("student_id", student_id)

                            # Pass verified identity separately.
                            result = function_to_call(
                                **arguments,
                                authenticated_student_id=student_id
                            )

                    else:
                        # General tools such as policy search.
                        result = function_to_call(**arguments)

                # STEP 7.4: RECORD TOOL RESULT
                tool_success = (
                    result.get("success")
                    if isinstance(result, dict)
                    else None
                )

                result_preview = json.dumps(
                    result,
                    default=str
                )[:1200]

                add_trace(
                    "tool_result",
                    tool_name=function_name,
                    success=tool_success,
                    result_keys=(
                        list(result.keys())
                        if isinstance(result, dict)
                        else []
                    ),
                    result_preview=result_preview
                )

            except Exception as error:

                result = {
                    "success": False,
                    "message": f"Tool execution failed: {str(error)}"
                }

                add_trace(
                    "tool_error",
                    tool_name=function_name,
                    error=str(error)
                )

            # ==========================================
            # STEP 8: RETURN TOOL OUTPUT TO LLM
            # ==========================================

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(
                    result,
                    default=str
                )
            })

    # ==========================================
    # STEP 9: MAXIMUM ITERATIONS REACHED
    # ==========================================

    latency = time.perf_counter() - start_time

    add_trace(
        "maximum_iterations_reached",
        max_iterations=5
    )

    return {
        "answer": (
            "I could not complete your request "
            "within the allowed steps."
        ),

        "tools_used": tools_used,
        "steps": 5,  # Maximum number of LLM iterations reached.
        "trace_events": len(execution_trace),

        "latency_seconds": round(latency, 3),

        "token_usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": (
                total_input_tokens + total_output_tokens
            )
        },

        "trace": execution_trace
    }
