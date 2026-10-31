# Intelligent Student Support Agent

An AI-powered student support system built using Python, Groq LLM, Streamlit, SQLite, and a tool-based agent architecture. The system assists students with fee-related queries, support requests, institutional policies, and general student information.

## 1. Project Overview

The Intelligent Student Support Agent is designed to simplify student support by providing an interactive AI assistant.

Instead of relying only on predefined responses, the agent can understand user queries, decide which tools are required, retrieve relevant information, and generate context-aware responses.

## 2. Key Features

- **Student Fee Assistance:** Retrieves student-specific fee information.
- **Support Request Management:** Creates support tickets for student issues.
- **Policy Retrieval:** Searches the institutional policy knowledge base and answers policy-related questions.
- **Persistent Memory:** Stores and retrieves useful information across conversations.
- **Context Management:** Selects relevant student context before processing queries.
- **Agent Execution Tracing:** Records agent events, tool calls, and execution results.
- **Performance Monitoring:** Displays response latency, token usage, and agent steps.
- **Interactive Dashboard:** Provides a Streamlit-based student support interface.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| LLM | Groq API |
| User Interface | Streamlit |
| Database | SQLite |
| Agent Framework | Custom tool-based agent loop |
| Environment Management | Python Virtual Environment |
| Configuration | Python dotenv |

## 4. Project Architecture

The system follows a tool-based agent architecture.

1. **User Interface:** Students submit questions through the Streamlit application.
2. **Context Manager:** Selects relevant student information and conversation context.
3. **AI Agent:** Processes the query using the Groq LLM.
4. **Tool Selection:** The agent determines whether a registered tool is required.
5. **Tool Execution:** The selected tool retrieves information or performs an action.
6. **Memory Manager:** Saves and retrieves relevant information.
7. **Response Generation:** The agent generates a response for the student.
8. **Monitoring:** Execution traces and performance measurements are displayed.

## 5. Available Agent Tools

| Tool | Purpose |
|---|---|
| `get_student_fee_status` | Retrieves student fee details |
| `create_support_request` | Creates a support ticket |
| `search_policy` | Searches institutional policy information |
| `save_memory` | Stores useful information in memory |
| `get_memories` | Retrieves previously stored memories |

## 6. Project Structure

The project is organized into the following modules:

```text
Intelligent-Student-Support-Agent/
│
├── agent/
│   ├── agent.py
│   └── context_manager.py
│
├── tools/
│   ├── student_tools.py
│   ├── support_tools.py
│   └── policy_tools.py
│
├── memory/
│   └── memory_manager.py
│
├── data/
│   ├── students.db
│   └── policies/
│
├── app.py
├── test_agent.py
├── test_groq.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

*Note: Adjust the structure above if your actual project contains additional or differently named files.*

## 7. Installation and Setup

### Prerequisites

- Python installed on your system.
- A Groq API key.
- Visual Studio Code or another Python-compatible IDE.

### Step 1: Clone or Download the Project

Download the project and open its root folder in Visual Studio Code.

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment.

**Windows:**

```bash
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory.

Add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace the placeholder with your actual API key. Never commit your API key to GitHub or share it publicly.

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser.

## 8. Testing

The agent was evaluated using five functional test scenarios:

1. Student fee status retrieval.
2. Support request creation.
3. General student support questions.
4. Payment policy retrieval.
5. Attendance policy retrieval.

The evaluation included:

- Response behaviour and task completion.
- Tools executed.
- Response latency.
- Input and output token consumption.
- Number of agent steps.
- Execution traces.

Run the agent tests using:

```bash
python test_agent.py
```

## 9. Performance Monitoring and Execution Tracing

The application provides an agent activity section that displays:

- Response latency in seconds.
- Input, output, and total token usage.
- Number of agent steps.
- Tools executed.
- Detailed execution trace events.

These measurements help understand the agent's decision-making process and operational performance.

## 10. Future Enhancements

- Add more student support tools.
- Expand the institutional policy knowledge base.
- Introduce role-based access and authentication.
- Improve retrieval accuracy.
- Add more comprehensive evaluation datasets.
- Enhance error handling and monitoring.
- Integrate additional institutional services.

## 11. Security Considerations

- Store API keys in environment variables.
- Keep `.env` out of version control.
- Avoid exposing sensitive student information in execution logs.
- Apply appropriate access controls before deployment.

## 12. Conclusion

The Intelligent Student Support Agent demonstrates how agentic AI can combine language models, tool execution, memory, context management, and information retrieval to provide a more interactive and efficient student support experience.