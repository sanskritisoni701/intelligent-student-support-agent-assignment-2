import html
import json
import streamlit as st

from agent.agent import run_agent
from auth.auth_manager import (
    initialize_auth_db,
    authenticate_student,
    authenticate_admin,
)
from tools.approval_tools import (
    initialize_approval_db,
    list_pending_due_date_requests,
    review_due_date_request,
    get_audit_log,
)

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Student Support Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. DESIGN SYSTEM
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --navy: #173B67;
        --blue: #2663EB;
        --blue-dark: #174A91;
        --ink: #142B50;
        --muted: #71829B;
        --border: #E3EAF3;
        --page: #F5F8FC;
        --white: #FFFFFF;
    }

    .stApp {
        background: var(--page);
        color: var(--ink);
        font-family: Inter, "Segoe UI", sans-serif;
    }

    .block-container {
        max-width: 1580px;
        padding: 1.2rem 1.5rem 2.2rem;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    
/* ---------- SIDEBAR DESIGN ---------- */

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #174A91 0%,
        #103B78 55%,
        #0C3268 100%
    );
    min-width: 260px;
}

section[data-testid="stSidebar"] > div {
    padding: 1.2rem 1rem 1.5rem;
}

/* Brand */
.sidebar-brand {
    padding: 5px 2px 14px;
}

.sidebar-brand h2 {
    color: #FFFFFF;
    font-size: 21px;
    font-weight: 750;
    margin: 0;
}

.sidebar-brand p {
    color: #DCEBFF;
    font-size: 13px;
    margin: 5px 0 0 36px;
}

/* Section headings */
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    margin: 0 0 12px !important;
}

/* Dividers */
.sidebar-divider {
    border-top: 1px solid rgba(255,255,255,.22);
    margin: 15px 0;
}

/* Student ID label */
section[data-testid="stSidebar"] label {
    color: #FFFFFF !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}

/* Student ID input */
section[data-testid="stSidebar"] [data-testid="stTextInput"] {
    margin-bottom: 4px;
}

section[data-testid="stSidebar"] [data-testid="stTextInput"] input {
    background: #FFFFFF !important;
    color: #173B67 !important;
    border: 1px solid #D7E3F2 !important;
    border-radius: 9px !important;
    min-height: 43px;
    font-size: 14px;
}

/* Navigation buttons */
section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin-bottom: 5px;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: transparent !important;
    color: #FFFFFF !important;
    border: 1px solid transparent !important;
    border-radius: 9px !important;
    min-height: 43px;
    padding: 8px 12px !important;
    text-align: left !important;
    font-size: 13px !important;
    font-weight: 550 !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button p,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button span {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,.14) !important;
    border-color: rgba(255,255,255,.18) !important;
}

/* Help card */
.sidebar-note {
    background: rgba(255,255,255,.13);
    border: 1px solid rgba(255,255,255,.22);
    border-radius: 13px;
    padding: 15px;
    margin-top: 12px;
}

.sidebar-note h4 {
    color: #FFFFFF;
    margin: 0 0 8px;
    font-size: 15px;
}

.sidebar-note p {
    color: #DCEBFF;
    font-size: 12px;
    line-height: 1.55;
    margin: 0;
}


    /* Main top bar */
    .topbar {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 13px;
        padding: 13px 19px;
        margin-bottom: 17px;
    }

    .brand-name {
        color: #2362B3;
        font-size: 28px;
        font-weight: 850;
        letter-spacing: -1.4px;
    }

    .brand-divider {
        color: #CBD5E1;
        font-size: 23px;
    }

    .brand-subtitle {
        color: #172D50;
        font-size: 14px;
        font-weight: 650;
    }

    /* Welcome banner */
    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(112deg, #DCEEFF 0%, #C7E2FF 62%, #EDF6FF 100%);
        border: 1px solid #D5E8FC;
        border-radius: 17px;
        padding: 26px 28px;
        min-height: 175px;
        margin-bottom: 23px;
    }

    .hero-label {
        color: #24528B;
        font-size: 12px;
        font-weight: 750;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    .hero h1 {
        color: #102D59;
        font-size: clamp(25px, 2.2vw, 35px);
        font-weight: 800;
        margin: 0 0 9px;
        line-height: 1.2;
    }

    .hero p {
        color: #31547E;
        font-size: 14px;
        margin: 0;
    }

    .hero-art {
        position: absolute;
        right: 30px;
        top: 30px;
        font-size: 66px;
        opacity: .8;
    }

    /* Section headings */
    .section-heading {
        color: var(--ink);
        font-size: 21px;
        font-weight: 780;
        margin: 7px 0 3px;
    }

    .section-caption {
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 13px;
    }

    /* Service cards */
    .service-card {
        min-height: 178px;
        border: 1px solid #E2EAF5;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 8px;
        transition: border-color .2s ease, box-shadow .2s ease;
    }

    .service-card:hover {
        border-color: #9EC5F5;
        box-shadow: 0 5px 18px rgba(30,70,120,.08);
    }

    .service-icon {
        width: 46px;
        height: 46px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 23px;
        margin-bottom: 12px;
    }

    .service-card h3 {
        color: #142B50;
        font-size: 15px;
        font-weight: 750;
        line-height: 1.3;
        margin: 0 0 7px;
    }

    .service-card p {
        color: #667893;
        font-size: 12px;
        line-height: 1.5;
        margin: 0;
    }

    .fee-card { background: #F4F8FF; }
    .policy-card { background: #F2FBF7; }
    .support-card { background: #F8F5FF; }
    .ai-card { background: #FFF8F0; }

    .fee-icon { background: #DCEAFF; color: #1760D1; }
    .policy-icon { background: #D9F4E8; color: #07965B; }
    .support-icon { background: #EAE0FF; color: #6336CC; }
    .ai-icon { background: #FFE9D2; color: #DA7400; }

    /* Right-hand information panels */
    .info-card {
        background: #FFFFFF;
        border: 1px solid #E6EDF6;
        border-radius: 15px;
        padding: 16px;
        margin-bottom: 14px;
    }

    .info-card-title {
        color: #142B50;
        font-size: 15px;
        font-weight: 750;
        margin: 0 0 13px;
    }

    .profile-avatar {
        width: 46px;
        height: 46px;
        flex: 0 0 46px;
        border-radius: 50%;
        background: #DFEDFF;
        color: #174A91;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        font-weight: 800;
    }

    .profile-name {
        color: #142B50;
        font-weight: 750;
        font-size: 14px;
    }

    .profile-detail {
        color: #71829B;
        font-size: 11px;
        margin-top: 3px;
    }

    .profile-meta {
        color: #60728D;
        font-size: 11px;
        line-height: 1.55;
        margin-top: 13px;
        border-top: 1px solid #EDF1F6;
        padding-top: 10px;
    }

    .update-item {
        padding: 10px 0;
        border-bottom: 1px solid #EDF1F6;
    }

    .update-item:last-child {
        border-bottom: 0;
        padding-bottom: 0;
    }

    .update-item strong {
        color: #1A3154;
        font-size: 12px;
    }

    .update-item p {
        color: #7889A1;
        font-size: 11px;
        line-height: 1.45;
        margin: 4px 0 0;
    }

    .help-card {
        background: linear-gradient(130deg, #DCEEFF, #EAF4FF);
        border: 1px solid #D6E9FD;
        border-radius: 15px;
        padding: 17px;
        margin-bottom: 10px;
    }

    .help-card h4 {
        color: #173B70;
        margin: 0 0 7px;
        font-size: 16px;
    }

    .help-card p {
        color: #607B9E;
        font-size: 12px;
        line-height: 1.5;
        margin: 0;
    }

   
/* ---------- CHAT AREA ---------- */

.chat-heading {
    color: #142B50 !important;
    font-size: 20px;
    font-weight: 780;
    margin: 19px 0 2px;
}

.chat-subheading {
    color: #71829B !important;
    font-size: 12px;
    margin-bottom: 12px;
}

/* Chat message containers */
[data-testid="stChatMessage"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5ECF5 !important;
    border-radius: 13px !important;
    padding: 14px !important;
    margin-bottom: 10px !important;
}

/* Force assistant and user text to navy */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    color: #142B50 !important;
}

/* Chat input container */
[data-testid="stChatInput"] {
    background: #FFFFFF !important;
    border: 1px solid #CFE0F5 !important;
    border-radius: 13px !important;
    box-shadow: 0 2px 8px rgba(30,70,120,0.04);
}

/* Chat input text */
[data-testid="stChatInput"] textarea {
    background: #FFFFFF !important;
    color: #142B50 !important;
    -webkit-text-fill-color: #142B50 !important;
    font-size: 14px !important;
}

/* Placeholder */
[data-testid="stChatInput"] textarea::placeholder {
    color: #8796AA !important;
    -webkit-text-fill-color: #8796AA !important;
}

/* Chat input send button */
[data-testid="stChatInput"] button {
    background: #2663EB !important;
    color: #FFFFFF !important;
    border-radius: 9px !important;
}

/* Suggested question labels */
[data-testid="stCaptionContainer"] {
    color: #71829B !important;
}

    
/* ---------- MAIN BUTTON STYLING ---------- */

div[data-testid="stButton"] > button {
    background: #2663EB !important;
    background-color: #2663EB !important;
    color: #FFFFFF !important;
    border: 1px solid #2663EB !important;
    border-radius: 9px !important;
    font-weight: 650 !important;
    min-height: 42px;
    box-shadow: none !important;
    transition: all 0.2s ease;
}

/* Force button text to white */
div[data-testid="stButton"] > button p,
div[data-testid="stButton"] > button span {
    color: #FFFFFF !important;
}

/* Hover effect */
div[data-testid="stButton"] > button:hover {
    background: #174A91 !important;
    background-color: #174A91 !important;
    border-color: #174A91 !important;
    color: #FFFFFF !important;
}

/* Sidebar buttons retain transparent styling */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: transparent !important;
    border-color: transparent !important;
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button p,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button span {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,0.15) !important;
}


    /* Footer */
    .footer {
        border-top: 1px solid #E5ECF5;
        padding-top: 14px;
        margin-top: 24px;
        color: #8796AA;
        text-align: center;
        font-size: 11px;
    }

    @media (max-width: 900px) {
        .hero-art { display: none; }
        .block-container { padding-left: 1rem; padding-right: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

def set_prompt(prompt: str) -> None:
    """Queue a suggested question for the chat input handler."""
    st.session_state.pending_prompt = prompt



def collect_agent_activity(result: dict) -> dict:
    """Collect tracing and measurement fields without inventing missing values."""
    result = result or {}
    token_usage = result.get("token_usage") or result.get("usage") or {}

    def first_value(*values):
        for value in values:
            if value is not None:
                return value
        return None

    return {
        "tools_used": result.get("tools_used", []),
        "latency": first_value(
            result.get("execution_time"),
            result.get("elapsed_seconds"),
            result.get("latency_seconds"),
            result.get("latency"),
        ),
        "input_tokens": first_value(
            result.get("input_tokens"),
            token_usage.get("input_tokens") if isinstance(token_usage, dict) else None,
            token_usage.get("prompt_tokens") if isinstance(token_usage, dict) else None,
        ),
        "output_tokens": first_value(
            result.get("output_tokens"),
            token_usage.get("output_tokens") if isinstance(token_usage, dict) else None,
            token_usage.get("completion_tokens") if isinstance(token_usage, dict) else None,
        ),
        "total_tokens": first_value(
            result.get("total_tokens"),
            token_usage.get("total_tokens") if isinstance(token_usage, dict) else None,
        ),
        "steps": first_value(
            result.get("steps_executed"),
            result.get("step_count"),
            result.get("steps"),
        ),
        "trace": first_value(
            result.get("execution_trace"),
            result.get("trace"),
            result.get("events"),
            [],
        ),
        "retrieved_evidence": first_value(
            result.get("retrieved_evidence"),
            result.get("evidence"),
            result.get("retrieved_chunks"),
            [],
        ),
    }


def render_agent_activity(activity: dict) -> None:
    """Render available agent measurements and trace details in the chat."""
    activity = activity or {}
    tools = activity.get("tools_used") or []
    latency = activity.get("latency")
    input_tokens = activity.get("input_tokens")
    output_tokens = activity.get("output_tokens")
    total_tokens = activity.get("total_tokens")
    steps = activity.get("steps")
    trace = activity.get("trace") or []
    evidence = activity.get("retrieved_evidence") or []

    with st.expander("View agent activity", expanded=False):
        st.markdown("**Run measurements**")

        metric_columns = st.columns(4)
        metrics = [
            ("Latency", f"{latency:.3f} s" if isinstance(latency, (int, float)) else (str(latency) if latency is not None else "Not reported")),
            ("Input tokens", str(input_tokens) if input_tokens is not None else "Not reported"),
            ("Output tokens", str(output_tokens) if output_tokens is not None else "Not reported"),
            ("Agent steps", str(steps) if steps is not None else "Not reported"),
        ]

        for column, (label, value) in zip(metric_columns, metrics):
            with column:
                st.metric(label, value)

        if total_tokens is not None:
            st.caption(f"Total tokens: {total_tokens}")
        elif input_tokens is not None or output_tokens is not None:
            if isinstance(input_tokens, (int, float)) and isinstance(output_tokens, (int, float)):
                st.caption(f"Total tokens: {int(input_tokens + output_tokens)} (calculated from reported input and output)")

        st.markdown("**Tools executed**")
        if tools:
            for tool in tools:
                st.write(f"✓ {tool}")
        else:
            st.write("No tools were used for this question.")

        st.markdown("**Execution trace**")
        if trace:
            if isinstance(trace, list):
                for index, event in enumerate(trace, start=1):
                    if isinstance(event, dict):
                        event_name = event.get("event") or event.get("type") or f"Event {index}"
                        details = {key: value for key, value in event.items() if key not in {"event", "type"}}
                        with st.container(border=True):
                            st.markdown(f"**{index}. {event_name.replace('_', ' ').title()}**")
                            if details:
                                st.json(details, expanded=False)
                    else:
                        st.write(f"{index}. {event}")
            else:
                st.json(trace, expanded=False)
        else:
            st.caption("The agent did not return detailed execution events for this run.")

        st.markdown("**Retrieved evidence**")
        if evidence:
            if isinstance(evidence, (list, tuple)):
                for index, item in enumerate(evidence, start=1):
                    with st.container(border=True):
                        st.write(f"Evidence {index}")
                        if isinstance(item, (dict, list)):
                            st.json(item, expanded=False)
                        else:
                            st.write(item)
            else:
                st.write(evidence)
        else:
            st.caption("No policy chunks or memory evidence were reported for this run.")


# =========================================================
# 4. AUTHENTICATION
# =========================================================

initialize_auth_db()

# Keep student and administrator sessions separate.
if "authenticated_student_id" not in st.session_state:
    st.session_state.authenticated_student_id = None

if "authenticated_admin_username" not in st.session_state:
    st.session_state.authenticated_admin_username = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# LOGIN SCREEN
if (
    not st.session_state.authenticated_student_id
    and not st.session_state.authenticated_admin_username
):
    st.title("🎓 Student Support Portal")
    st.write("Sign in to continue.")

    # Dropdown avoids the tab-label visibility problem.
    login_mode = st.selectbox(
        "Choose your login type",
        options=["Student Login", "Administrator Login"],
        index=0,
        key="login_mode",
    )

    if login_mode == "Student Login":
        st.subheader("Student Login")
        with st.form("student_login_form"):
            login_id = st.text_input("Student ID", placeholder="e.g. STU1001")
            login_password = st.text_input("Password", type="password")
            student_login_button = st.form_submit_button(
                "Sign In", use_container_width=True
            )

        if student_login_button:
            result = authenticate_student(login_id, login_password)
            if result.get("success"):
                st.session_state.authenticated_student_id = result["student_id"]
                st.session_state.authenticated_admin_username = None
                st.session_state.messages = []
                st.session_state.pending_prompt = None
                st.success("Student login successful!")
                st.rerun()
            else:
                st.error(result.get("message", "Student login failed."))

    else:
        st.subheader("Administrator Login")
        with st.form("admin_login_form"):
            admin_username = st.text_input("Admin Username", key="admin_username_input")
            admin_password = st.text_input(
                "Admin Password", type="password", key="admin_password_input"
            )
            admin_login_button = st.form_submit_button(
                "Administrator Sign In", use_container_width=True
            )

        if admin_login_button:
            result = authenticate_admin(admin_username, admin_password)
            if result.get("success"):
                st.session_state.authenticated_admin_username = result["username"]
                st.session_state.authenticated_student_id = None
                st.session_state.messages = []
                st.session_state.pending_prompt = None
                st.success("Administrator login successful!")
                st.rerun()
            else:
                st.error(result.get("message", "Administrator login failed."))

    st.stop()


# ADMINISTRATOR PORTAL - separate from the student dashboard.
if st.session_state.authenticated_admin_username:
    initialize_approval_db()

    admin_username = st.session_state.authenticated_admin_username
    st.title("🛡️ Administrator Portal")
    st.write(f"Logged in as: **{html.escape(admin_username)}**")
    st.caption("Review student fee due-date change requests.")

    pending_requests = list_pending_due_date_requests(
    admin_username=admin_username
)

    total_pending = len(pending_requests)
    st.metric("Pending approval requests", total_pending)

    st.subheader("Pending Fee Due-Date Requests")

    if not pending_requests:
        st.success("There are no pending requests to review.")
    else:
        for request in pending_requests:
            request_id = request["request_id"]

            with st.container(border=True):
                st.markdown(f"**Request ID:** `{request_id}`")
                col1, col2, col3 = st.columns(3)
                col1.markdown(
                    f"**Student ID**\n\n{request['student_id']}"
                )
                col2.markdown(
                    f"**Current due date**\n\n{request['current_due_date']}"
                )
                col3.markdown(
                    f"**Requested due date**\n\n{request['requested_due_date']}"
                )

                # Display the reason supplied by the student.
                student_reason = (
                    request.get("reason")
                    or request.get("request_reason")
                    or "No reason was provided."
                )
                st.markdown("**Student's reason for the request**")
                st.info(student_reason)

                st.caption(f"Submitted: {request['requested_at']}")

                decision_note = st.text_input(
                    "Review note (optional)",
                    key=f"review_note_{request_id}",
                    placeholder="Add a short reason or comment",
                )

                approve_col, reject_col = st.columns(2)

                with approve_col:
                    if st.button(
                        "Approve request",
                        key=f"approve_{request_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        result = review_due_date_request(
                            request_id=request_id,
                            decision="APPROVE",
                            admin_username=admin_username,
                            note=decision_note,
                        )
                        if result.get("success"):
                            st.success(result["message"])
                        else:
                            st.error(result.get("message", result.get("error", "Approval failed.")))
                        st.rerun()

                with reject_col:
                    if st.button(
                        "Reject request",
                        key=f"reject_{request_id}",
                        use_container_width=True,
                    ):
                        result = review_due_date_request(
                            request_id=request_id,
                            decision="REJECT",
                            admin_username=admin_username,
                            note=decision_note,
                        )
                        if result.get("success"):
                            st.warning(result["message"])
                        else:
                            st.error(result.get("message", result.get("error", "Rejection failed.")))
                        st.rerun()

    st.divider()
    st.subheader("Audit Log")
    audit_entries = get_audit_log(
    limit=100,
    admin_username=admin_username
)

    if audit_entries:
        st.dataframe(
            [
                {
                    "Time": entry["created_at"],
                    "Actor type": entry["actor_type"],
                    "Actor": entry["actor_id"],
                    "Action": entry["action"],
                    "Request ID": entry["request_id"],
                    "Student ID": entry["student_id"],
                    "Outcome": entry["outcome"],
                    "Details": json.dumps(entry["details"], ensure_ascii=False),
                }
                for entry in audit_entries
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No audit events have been recorded yet.")

    if st.button("Refresh dashboard", key="admin_refresh_button"):
        st.rerun()

    if st.button("Logout", key="admin_logout_button"):
        st.session_state.authenticated_admin_username = None
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    st.stop()


# 4. SIDEBAR
# =========================================================


# =========================================================
# 4. SIDEBAR
# =========================================================

with st.sidebar:

    # BRAND
    st.markdown(
        """
        <div class="sidebar-brand">
            <h2>🎓 Student Support</h2>
            <p>Your AI Learning Assistant</p>
        </div>
        <div class="sidebar-divider"></div>
        """,
        unsafe_allow_html=True
    )
    # AUTHENTICATED STUDENT
    st.markdown("### Student Account")

    st.markdown(
        f"**{html.escape(st.session_state.authenticated_student_id)}**"
    )

    if st.button(
        "Logout",
        use_container_width=True,
        key="logout_button"
    ):
        st.session_state.authenticated_student_id = None
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    st.markdown(
        '<div class="sidebar-divider"></div>',
        unsafe_allow_html=True
    )
    # NAVIGATION
    st.markdown("### Navigation")

    if st.button("⌂   Home", use_container_width=True, key="nav_home"):
        st.session_state.pending_prompt = None
        st.rerun()

    if st.button("▣   Fee & Payments", use_container_width=True, key="nav_fees"):
        set_prompt("What is my current fee status and pending amount?")
        st.rerun()

    if st.button("▤   Student Policies", use_container_width=True, key="nav_policies"):
        set_prompt("What are the important student policies?")
        st.rerun()

    if st.button("♧   Support Requests", use_container_width=True, key="nav_support"):
        set_prompt(
            "I need help with a student-related issue. "
            "How can I raise a support request?"
        )
        st.rerun()

    if st.button("✦   AI Learning Assistant", use_container_width=True, key="nav_ai"):
        set_prompt("Help me understand an academic topic.")
        st.rerun()

    st.markdown(
        '<div class="sidebar-divider"></div>',
        unsafe_allow_html=True
    )

    # HELP CARD
    st.markdown(
        """
        <div class="sidebar-note">
            <h4>🤖 Need help?</h4>
            <p>
                Ask me anything about academics,
                student policies or support.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # CLEAR CONVERSATION
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "↻   Clear conversation",
        use_container_width=True,
        key="sidebar_clear"
    ):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()


# =========================================================
# 5. DASHBOARD COLUMNS
# =========================================================

main_col, right_col = st.columns([3.15, 1.15], gap="large")


# =========================================================
# 6. MAIN DASHBOARD
# =========================================================

with main_col:
    student_id = st.session_state.authenticated_student_id or "Student"
    safe_student_id = html.escape(student_id)

    st.markdown(
        """
        <div class="topbar">
            <span class="brand-name">adani</span>
            <span class="brand-divider">|</span>
            <span class="brand-subtitle">Student Support Portal</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-label">YOUR PERSONAL STUDENT ASSISTANT</div>
            <h1>Welcome back, {safe_student_id} 👋</h1>
            <p>How can I help you today?</p>
            <p>I'm your AI-powered student support assistant.</p>
            <div class="hero-art">🎓</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-heading">Quick Access</div>
        <div class="section-caption">
            Explore common services or start a conversation.
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_columns = st.columns(4, gap="small")

    services = [
        {
            "title": "Fee & Payments",
            "description": "Check your fee status, payment history and upcoming dues.",
            "emoji": "▣",
            "card_class": "fee-card",
            "icon_class": "fee-icon",
            "prompt": "What is my pending fee amount?",
        },
        {
            "title": "Student Policies",
            "description": "Find answers from your student handbook and academic guidelines.",
            "emoji": "▤",
            "card_class": "policy-card",
            "icon_class": "policy-icon",
            "prompt": "What should I do if the payment portal fails?",
        },
        {
            "title": "Support Requests",
            "description": "Raise a ticket for technical or administrative support.",
            "emoji": "♧",
            "card_class": "support-card",
            "icon_class": "support-icon",
            "prompt": "Please help me create a support ticket.",
        },
        {
            "title": "AI Learning Assistant",
            "description": "Get personalized help with academic concepts and studies.",
            "emoji": "✦",
            "card_class": "ai-card",
            "icon_class": "ai-icon",
            "prompt": "Explain supervised learning in simple English.",
        },
    ]

    for index, service in enumerate(services):
        with card_columns[index]:
            st.markdown(
                f"""
                <div class="service-card {service['card_class']}">
                    <div class="service-icon {service['icon_class']}">
                        {service['emoji']}
                    </div>
                    <h3>{service['title']}</h3>
                    <p>{service['description']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Explore →",
                key=f"service_{index}",
                use_container_width=True,
            ):
                set_prompt(service["prompt"])
                st.rerun()

    
    # =====================================================
    # CHAT INTERFACE
    # =====================================================

    # Process prompts selected from dashboard buttons
    pending_question = st.session_state.pending_prompt

    if pending_question:
        st.session_state.pending_prompt = None

        st.session_state.messages.append({
            "role": "user",
            "content": pending_question
        })

        try:
            with st.spinner("Your AI assistant is thinking..."):

                result = run_agent(
                    pending_question,
                    student_id=st.session_state.authenticated_student_id
                )

                answer = result.get(
                    "answer",
                    "I could not generate a response."
                )

                tools_used = result.get("tools_used", [])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "tools_used": tools_used,
                    "agent_activity": collect_agent_activity(result)
                })

        except Exception as error:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "I encountered a technical issue. Please try again."
            })

        st.rerun()


    # Chat heading
    chat_title_col, chat_clear_col = st.columns([5, 1])

    with chat_title_col:
        st.markdown(
            """
            <div class="chat-heading">
                ✨ Chat with your AI Assistant
            </div>
            <div class="chat-subheading">
                Ask anything about fees, policies, support or academics.
            </div>
            """,
            unsafe_allow_html=True
        )

    with chat_clear_col:
        if st.button("Clear chat", key="main_clear"):
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.rerun()


    # =====================================================
    # CONVERSATION HISTORY
    # =====================================================

    if not st.session_state.messages:

        with st.chat_message("assistant", avatar="🤖"):

            st.markdown("""
            **Hello! Welcome to your Student Support Portal. 👋**

            I'm your personal AI assistant. I can help you with:

            - 💰 **Fees:** Check payments and pending dues.
            - 📚 **Policies:** Understand student handbook guidelines.
            - 🎫 **Support:** Create technical or administrative tickets.
            - 🧠 **Academics:** Understand complex topics in simple language.

            **What would you like help with today?**
            """)

    else:

        for message in st.session_state.messages:

            avatar = (
                "🧑‍🎓"
                if message["role"] == "user"
                else "🤖"
            )

            with st.chat_message(
                message["role"],
                avatar=avatar
            ):

                st.markdown(message["content"])

                if message["role"] == "assistant" and message.get("agent_activity"):
                    render_agent_activity(message["agent_activity"])
                elif message["role"] == "assistant" and message.get("tools_used"):
                    # Backward compatibility for messages created before this update.
                    with st.expander("View agent activity"):
                        st.markdown("**Tools executed**")
                        for tool in message["tools_used"]:
                            st.write(f"✓ {tool}")


    # =====================================================
    # SUGGESTED QUESTIONS
    # Show only before the conversation starts
    # =====================================================

    if not st.session_state.messages:

        st.caption("Suggested questions")

        suggestions = [
            ("What is my pending fee?", "What is my pending fee amount?"),
            ("How to apply for leave?", "What is the leave application policy?"),
            ("Create a support ticket", "Please create a support ticket."),
            ("Explain supervised learning", "Explain supervised learning in simple English.")
        ]

        suggestion_columns = st.columns(4, gap="small")

        for index, (label, prompt) in enumerate(suggestions):

            with suggestion_columns[index]:

                if st.button(
                    label,
                    key=f"suggestion_{index}",
                    use_container_width=True
                ):

                    set_prompt(prompt)
                    st.rerun()


    # =====================================================
    # CHAT INPUT - ALWAYS AT THE END
    # =====================================================

    typed_question = st.chat_input(
        "Ask your question here..."
    )

    if typed_question:

        st.session_state.messages.append({
            "role": "user",
            "content": typed_question
        })

        try:

            with st.spinner("Your AI assistant is thinking..."):

                result = run_agent(
                    typed_question,
                    student_id=st.session_state.authenticated_student_id
                )

                answer = result.get(
                    "answer",
                    "I could not generate a response."
                )

                tools_used = result.get("tools_used", [])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "tools_used": tools_used,
                    "agent_activity": collect_agent_activity(result)
                })

        except Exception as error:

            st.session_state.messages.append({
                "role": "assistant",
                "content": "I encountered a technical issue. Please try again."
            })

            st.error(str(error))

        st.rerun()



# =========================================================
# 7. RIGHT INFORMATION PANEL
# =========================================================

with right_col:
    profile_id = html.escape(
        st.session_state.authenticated_student_id
    )

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-card-title">👤 Student Profile</div>
            <div style="display:flex;align-items:center;gap:11px;">
                <div class="profile-avatar">ST</div>
                <div>
                    <div class="profile-name">{profile_id}</div>
                    <div class="profile-detail">PGDM in Big Data Analytics</div>
                </div>
            </div>
            <div class="profile-meta">
                ✉ &nbsp; Student account<br>
                ▦ &nbsp; Academic year 2026–2027<br>
                ⌖ &nbsp; Student portal
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Use native Streamlit markdown for updates.
    # This avoids raw HTML being displayed as code/text.
    with st.container(border=True):
        st.markdown("**📢 Important Updates**")

        st.markdown(
            """
            <div class="update-item">
                <strong>💰 Fee Payment Window</strong>
                <p>Check your next payment due date.</p>
            </div>
            <div class="update-item">
                <strong>📅 Academic Calendar</strong>
                <p>Refer to your programme calendar.</p>
            </div>
            <div class="update-item">
                <strong>📚 Student Handbook</strong>
                <p>Ask the AI assistant about student policies.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="help-card">
            <h4>💬 Still need help?</h4>
            <p>
                Raise a support request and get assistance with your issue.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "Create a Support Request →",
        key="right_support",
        use_container_width=True,
    ):
        set_prompt(
            "I need help with a student-related issue. "
            "Please help me create a support ticket."
        )
        st.rerun()


# =========================================================
# 8. FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        Intelligent Student Support Agent
        &nbsp;|&nbsp; Powered by Groq, Python, SQLite and Streamlit
        <br><br>
        Academic demonstration project
    </div>
    """,
    unsafe_allow_html=True,
)
