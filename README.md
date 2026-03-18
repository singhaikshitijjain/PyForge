PyForge: AI Python → Backend Generator

OVERVIEW:
This project converts a single Python file into a working backend (FastAPI or Streamlit) automatically using AST parsing and dynamic code generation. It also allows running the generated app locally and pushing it to GitHub.

--------------------------------------------------

CORE FLOW:

1. USER INPUT (Frontend)
- Upload a Python file
- Select endpoints (functions/classes)
- Choose mode:
  → FastAPI (backend APIs)
  → Streamlit (UI app)

--------------------------------------------------

2. ANALYSIS (Backend - /analyze)

- Uses Python AST (Abstract Syntax Tree)
- Extracts:
  → Functions (name + arguments)
  → Classes (methods + arguments)

OUTPUT:
{
  "available_endpoints": ["func1", "Class.method"]
}

--------------------------------------------------

3. CODE GENERATION (/generate)

INPUT:
- Python file
- Selected endpoints
- Mode (fastapi / streamlit)

PROCESS:

A) FASTAPI MODE:
- Wraps functions into API routes
- Creates:
  POST /function_name
- Extracts inputs from request body
- Calls original function
- Returns JSON response

B) STREAMLIT MODE:
- Generates UI automatically
- Creates input fields for each function argument
- Adds buttons to execute functions
- Displays output

OUTPUT:
- Fully working backend code (string)

--------------------------------------------------

4. RUN GENERATED CODE (/run)

- Creates temporary folder
- Writes generated code to file
- Runs:
  → FastAPI → uvicorn
  → Streamlit → streamlit run

OUTPUT:
- Returns URL
  → FastAPI → /docs
  → Streamlit → app UI

--------------------------------------------------

5. GITHUB INTEGRATION (/github/push)

INPUT:
- GitHub token (user provided)
- Repo name
- Generated code

PROCESS:
- Creates new repository via GitHub API
- Encodes code (base64)
- Pushes file (main.py / app.py)

OUTPUT:
{
  "repo_url": "github repo link"
}

--------------------------------------------------

KEY COMPONENTS:

1. AST PARSER
- Converts code → tree structure
- Identifies functions and classes
- Enables generic automation

2. ROUTE GENERATOR
- Dynamically builds API endpoints
- Handles function arguments
- Wraps logic inside try/catch

3. STREAMLIT BUILDER
- Converts backend logic → UI
- Generates inputs dynamically
- Executes functions interactively

4. CODE FORMATTER
- Uses black for clean formatting
- Ensures valid Python syntax

5. VALIDATOR
- compile() checks if generated code runs

6. PROCESS RUNNER
- subprocess launches apps dynamically
- Assigns random ports

--------------------------------------------------

FRONTEND (HTML + JS):

FEATURES:
- File upload
- Endpoint selection (checkbox / accordion)
- Mode selection
- Code viewer (textarea)
- Run / Download / Copy buttons
- GitHub push modal
- Loader + Toast notifications

--------------------------------------------------

ARCHITECTURE:

Frontend (HTML/JS)
        ↓
FastAPI Backend
        ↓
AST Analysis → Code Generation → Execution
        ↓
Optional: GitHub API Integration

--------------------------------------------------

USE CASES:

- Convert scripts → APIs instantly
- Rapid backend prototyping
- AI dev tools / SaaS
- Code-to-product automation

--------------------------------------------------

LIMITATIONS:

- Assumes clean Python functions
- No complex dependency handling
- Creates new repo only (no update logic)

--------------------------------------------------

EXTENSIONS (NEXT LEVEL):

- Add requirements.txt auto-generation
- Auto deploy (Render / Railway)
- Monaco editor (VS Code UI)
- API testing panel
- Repo update instead of create

--------------------------------------------------

SUMMARY:

INPUT → Python file  
PROCESS → AST + Dynamic Code Generation  
OUTPUT → Working Backend (FastAPI / Streamlit)  
EXTRA → Run locally + Push to GitHub  

This is a full pipeline from code → product.