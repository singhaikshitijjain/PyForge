import ast
import base64
import black
import requests
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PyForge — Backend Generator")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────

def format_code(code: str) -> str:
    try:
        return black.format_str(code, mode=black.FileMode())
    except Exception:
        return code


def is_valid_python(code: str) -> bool:
    try:
        compile(code, "<generated>", "exec")
        return True
    except Exception:
        return False


def indent(lines, level=1):
    prefix = " " * 4 * level
    return "\n".join(prefix + line if line.strip() else line for line in lines)


# ─────────────────────────────────────────
# AST ANALYSIS
# ─────────────────────────────────────────

def analyze_code(code: str):
    tree = ast.parse(code)
    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
            })
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        "name": item.name,
                        "args": [a.arg for a in item.args.args if a.arg != "self"],
                    })
            classes.append({"class_name": node.name, "methods": methods})

    return functions, classes


# ─────────────────────────────────────────
# CODE BUILDERS
# ─────────────────────────────────────────

def build_fastapi_routes(selected: list[str], functions: list, classes: list) -> str:
    routes = ""

    for func in functions:
        if func["name"] in selected:
            args = func["args"]
            arg_lines = [f"{a} = data.get('{a}')" for a in args]
            call_args = ", ".join(args)
            body = arg_lines + [
                f"result = {func['name']}({call_args})",
                "return {'result': result}",
            ]
            routes += f"""
@app.post("/{func['name']}")
async def {func['name']}_api(data: dict = {{}}):
    try:
{indent(body, 2)}
    except Exception as e:
{indent(["return {'error': str(e)}"], 2)}
"""

    for cls in classes:
        for method in cls["methods"]:
            key = f"{cls['class_name']}.{method['name']}"
            if key in selected:
                args = method["args"]
                arg_lines = [f"{a} = data.get('{a}')" for a in args]
                call_args = ", ".join(args)
                body = arg_lines + [
                    f"obj = {cls['class_name']}()",
                    f"result = obj.{method['name']}({call_args})",
                    "return {'result': result}",
                ]
                routes += f"""
@app.post("/{cls['class_name'].lower()}/{method['name']}")
async def {cls['class_name']}_{method['name']}_api(data: dict = {{}}):
    try:
{indent(body, 2)}
    except Exception as e:
{indent(["return {'error': str(e)}"], 2)}
"""

    return routes


def build_streamlit_app(
    selected: list[str],
    functions: list,
    classes: list,
    original_code: str,
) -> str:
    ui_code = [
        "import streamlit as st",
        "",
        "# Original user code",
        original_code,
        "",
        "st.title('Generated Streamlit App')",
    ]

    for func in functions:
        if func["name"] in selected:
            args = func["args"]
            ui_code.append(f"\nst.subheader('{func['name']}')")
            for a in args:
                ui_code.append(f"{a} = st.text_input('{a}')")
            call_args = ", ".join(args)
            ui_code.append(f"""
if st.button("Run {func['name']}"):
    try:
        result = {func['name']}({call_args})
        st.success(result)
    except Exception as e:
        st.error(str(e))
""")

    return "\n".join(ui_code)


# ─────────────────────────────────────────
# ANALYZE
# ─────────────────────────────────────────

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """Parse the uploaded .py file and return all discoverable function/method names."""
    try:
        code = (await file.read()).decode()
        functions, classes = analyze_code(code)

        endpoints = [f["name"] for f in functions]
        for c in classes:
            for m in c["methods"]:
                endpoints.append(f"{c['class_name']}.{m['name']}")

        return {"available_endpoints": endpoints}

    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Python syntax error: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────
# GENERATE
# ─────────────────────────────────────────

@app.post("/generate")
async def generate(
    file: UploadFile = File(...),
    selected: str = Form(...),
    mode: str = Form(...),
):
    """Generate FastAPI or Streamlit code for the selected endpoints."""
    try:
        code = (await file.read()).decode()
        selected_list = [s.strip() for s in selected.split(",") if s.strip()]
        functions, classes = analyze_code(code)

        if mode == "fastapi":
            routes = build_fastapi_routes(selected_list, functions, classes)
            final_code = f"""from fastapi import FastAPI

app = FastAPI()

# ── Original code ──
{code}

# ── Generated routes ──
{routes}

# Run: uvicorn main:app --reload
"""
        elif mode == "streamlit":
            final_code = build_streamlit_app(selected_list, functions, classes, code)
        else:
            raise HTTPException(status_code=400, detail="Invalid mode — use 'fastapi' or 'streamlit'")

        final_code = format_code(final_code)

        if not is_valid_python(final_code):
            raise HTTPException(status_code=500, detail="Generated code failed Python validation")

        return PlainTextResponse(final_code)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────
# GITHUB PUSH
# ─────────────────────────────────────────

@app.post("/github/push")
async def push_to_github(
    file: UploadFile = File(...),
    selected: str = Form(...),
    mode: str = Form(...),
    repo_name: str = Form(...),
    github_token: str = Form(...),
):
    """Generate code and push it to a new GitHub repository."""
    try:
        if not github_token:
            raise HTTPException(status_code=400, detail="GitHub token required")
        if not repo_name:
            raise HTTPException(status_code=400, detail="Repository name required")

        # Accept full GitHub URLs — strip to bare name
        repo_name = repo_name.strip().split("/")[-1]

        code = (await file.read()).decode()
        selected_list = [s.strip() for s in selected.split(",") if s.strip()]
        functions, classes = analyze_code(code)

        if mode == "fastapi":
            routes = build_fastapi_routes(selected_list, functions, classes)
            final_code = f"""from fastapi import FastAPI

app = FastAPI()

{code}
{routes}
"""
            filename = "main.py"

        elif mode == "streamlit":
            final_code = build_streamlit_app(selected_list, functions, classes, code)
            filename = "app.py"

        else:
            raise HTTPException(status_code=400, detail="Invalid mode — use 'fastapi' or 'streamlit'")

        final_code = format_code(final_code)

        if not is_valid_python(final_code):
            raise HTTPException(status_code=500, detail="Generated code failed Python validation")

        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github+json",
        }

        # Create repository
        repo_res = requests.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json={"name": repo_name, "private": False},
            timeout=15,
        )

        if repo_res.status_code == 422:
            return {"error": "A repository with that name already exists on your account."}
        if repo_res.status_code == 401:
            return {"error": "GitHub token is invalid or expired."}
        if repo_res.status_code not in (200, 201):
            return {"error": repo_res.json()}

        repo_data = repo_res.json()
        owner = repo_data["owner"]["login"]

        # Push file
        push_res = requests.put(
            f"https://api.github.com/repos/{owner}/{repo_name}/contents/{filename}",
            headers=headers,
            json={
                "message": "Initial commit — generated by PyForge",
                "content": base64.b64encode(final_code.encode()).decode(),
            },
            timeout=15,
        )

        if push_res.status_code not in (200, 201):
            return {"error": push_res.json()}

        return {"repo_url": repo_data["html_url"]}

    except HTTPException:
        raise
    except requests.Timeout:
        return {"error": "GitHub API request timed out. Check your network connection."}
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────

@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")