import os
import re
import json
import subprocess
import asyncio
import tempfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="CoTEACH Web")

# Allow frontend (in development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",                     # local dev
        "https://co-teach-three.vercel.app",       # production Vercel
        # optional: allow preview deployments
        "https://co-teach-*-feiran-zhang-s-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Configuration ----------
AGENT_DIR = Path(__file__).parent
REQUIRED_MCPS = ["exa"]
REQUIRED_SKILLS = ["docx", "pptx", "xlsx", "pdf"]
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com/anthropic"

# ---------- Helper Functions (reuse your logic) ----------
def check_mcps():
    not_installed, not_connected = [], []
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            cwd=AGENT_DIR,
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return REQUIRED_MCPS.copy(), []
        output = result.stdout
        for name in REQUIRED_MCPS:
            pattern = rf"^{re.escape(name)}\s*:.*$"
            lines = re.findall(pattern, output, re.MULTILINE)
            if not lines:
                not_installed.append(name)
            elif any("✓ Connected" in line for line in lines):
                pass
            else:
                not_connected.append(name)
    except Exception:
        return REQUIRED_MCPS.copy(), []
    return not_installed, not_connected

def check_skills():
    missing = []
    local_dir = AGENT_DIR / "skills"
    global_dir = Path.home() / ".claude" / "plugins" / "marketplaces"
    for skill in REQUIRED_SKILLS:
        found = False
        if local_dir.exists() and (local_dir/skill).exists() and any((local_dir/skill).iterdir()):
            found = True
        elif global_dir.exists() and (global_dir/skill).exists() and any((global_dir/skill).iterdir()):
            found = True
        if not found:
            missing.append(skill)
    return missing

def install_skill(skill: str):
    proc = subprocess.run(
        ["claude", "plugin", "install", skill],
        cwd=AGENT_DIR,
        capture_output=True, text=True, timeout=60
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())

def add_mcp_exa(exa_key: str):
    proc = subprocess.run(
        ["claude", "mcp", "add", "--transport", "http", "exa", "https://mcp.exa.ai/mcp",
        "--header", f"x-api-key: {exa_key}"],
        cwd=AGENT_DIR,
        capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())

# ---------- Endpoints ----------
@app.get("/verify")
async def verify():
    not_installed, not_connected = check_mcps()
    missing_skills = check_skills()
    return JSONResponse({
        "mcps_not_installed": not_installed,
        "mcps_not_connected": not_connected,
        "skills_missing": missing_skills
    })

@app.post("/install")
async def install(
    exa_api_key: str = Form(None),
    install_exa: bool = Form(False),
    install_skills: List[str] = Form([])
):
    errors = []
    # Install skills
    for skill in install_skills:
        try:
            install_skill(skill)
        except Exception as e:
            errors.append(f"skill/{skill}: {str(e)}")
    # Install exa if requested
    if install_exa and exa_api_key:
        try:
            add_mcp_exa(exa_api_key)
        except Exception as e:
            errors.append(f"mcp/exa: {str(e)}")
    return JSONResponse({"status": "completed", "errors": errors})

@app.post("/run")
async def run_agent(
    folder: str = Form(...),
    prompt: str = Form(...),
    api_key: str = Form(...),
    base_url: str = Form(DEFAULT_BASE_URL),
    model: str = Form(DEFAULT_MODEL),
):
    """
    Runs the Claude Code agent in the given folder and streams the output
    via Server-Sent Events (SSE).
    """
    async def event_stream():
        env = os.environ.copy()
        env["ANTHROPIC_API_KEY"] = api_key
        env["ANTHROPIC_BASE_URL"] = base_url
        env["ANTHROPIC_MODEL"] = model
        env["CLAUDE_PROJECT_DIR"] = str(AGENT_DIR)
        env.pop("CLAUDECODE", None)
        env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        full_prompt = (
            f"{prompt}\n\n"
            f"You MUST use the coteach-planning skill.\n"
            f"Note: You are operating inside the folder '{folder}'. "
            f"Use the Write tool to create output files; it automatically creates directories."
        )

        cmd = [
            "claude",
            "-p", full_prompt,
            "--no-session-persistence",
            "--permission-mode", "bypassPermissions",
            "--allowedTools", "Read,Edit,Bash,Write,WebFetch,mcp__exa:*",
            #"--output-format", "text",
            "--verbose"
        ]

        proc = subprocess.Popen(
            cmd,
            cwd=folder,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        try:
            for line in proc.stdout:
                # SSE format: "data: <text>\n\n"
                yield f"data: {line.strip()}\n\n"
                await asyncio.sleep(0.01)  # yield control
            proc.wait()
            if proc.returncode == 0:
                yield "data: [DONE] Agent finished successfully.\n\n"
            else:
                yield f"data: [ERROR] Agent exited with code {proc.returncode}\n\n"
        finally:
            # Ensure process cleanup
            if proc.poll() is None:
                proc.terminate()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # for nginx
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")