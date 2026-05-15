import tkinter as tk
#from tkinter import filedialog, messagebox, scrolledtext, simpledialog
#from tkinter import ttk
import customtkinter as ctk
from customtkinter import filedialog, CTkInputDialog
from CTkMessagebox import CTkMessagebox
import subprocess
import os
import threading
import json
import re
from pathlib import Path

class AgentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CoTEACH Agent GUI")
        self.root.geometry("900x750")
        self.agent_dir = Path("/Users/teacher/Desktop/CoTEACH").resolve()  # adjust path if needed

        # --- User inputs ---
        # Folder selection
        ctk.CTkLabel(root, text="User folder (with input files & output)").pack()
        self.folder_path = ctk.StringVar()
        folder_frame = ctk.CTkFrame(root)
        folder_frame.pack()
        ctk.CTkEntry(folder_frame, textvariable=self.folder_path, width=480).pack(side=tk.LEFT)
        ctk.CTkButton(folder_frame, text="Browse", command=self.select_folder).pack(side=tk.LEFT)

        # Prompt
        ctk.CTkLabel(root, text="Your prompt for the CoTeach agent").pack()
        self.prompt_text = ctk.CTkTextbox(root, height=150, width=600)
        self.prompt_text.pack()

        # API credentials
        cred_frame = tk.LabelFrame(root, text="API credentials", padx=5, pady=5)
        cred_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(cred_frame, text="API Key").grid(row=0, column=0, sticky="e")
        self.api_key = ctk.CTkEntry(cred_frame, show="*", width=480)
        self.api_key.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(cred_frame, text="Base URL (optional)").grid(row=1, column=0, sticky="e")
        self.base_url = ctk.CTkEntry(cred_frame, width=480)
        self.base_url.grid(row=1, column=1, padx=5)
        self.base_url.insert(0, "https://api.deepseek.com/anthropic")   # default

        ctk.CTkLabel(cred_frame, text="Model (optional)").grid(row=2, column=0, sticky="e")
        self.model = ctk.CTkEntry(cred_frame, width=480)
        self.model.grid(row=2, column=1, padx=5)
        self.model.insert(0, "deepseek-v4-flash")       # default

        # Buttons
        btn_frame = ctk.CTkFrame(root)
        btn_frame.pack(pady=10)
        self.verify_btn = ctk.CTkButton(btn_frame, text="Verify Setup", command=self.verify_setup)
        self.verify_btn.pack(side=tk.LEFT, padx=5)
        self.install_btn = ctk.CTkButton(btn_frame, text="Install Missing", command=self.install_missing) 
        self.install_btn.pack(side=tk.LEFT, padx=5)
        self.run_btn = ctk.CTkButton(btn_frame, text="Run Agent", command=self.run_agent)
        self.run_btn.pack(side=tk.LEFT, padx=5)

        # Output area
        ctk.CTkLabel(root, text="Agent output").pack()
        self.output_area = ctk.CTkTextbox(root, height=240, width=600, state="disabled")
        self.output_area.pack()

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select user folder")
        if folder:
            self.folder_path.set(folder)

    # ----- verification -----
    def verify_setup(self):
        # runs in a thread to not block GUI
        threading.Thread(target=self._verify_thread, daemon=True).start()

    def verify_setup(self):
        threading.Thread(target=self._verify_thread, daemon=True).start()

    def _verify_thread(self):
        self._log_output("🔍 Verifying environment...\n")
        # 1. Check CLI
        try:
            subprocess.run(["claude", "--version"], capture_output=True, check=True)
            self._log_output("✅ Claude CLI found.\n")
        except Exception:
            self._log_output("❌ Claude CLI not found. Install it and add to PATH.\n")
            return

        # 2. Agent directory
        if not self.agent_dir.exists():
            self._log_output(f"❌ Agent directory '{self.agent_dir}' not found.\n")
            return
        self._log_output(f"✅ Agent directory: {self.agent_dir}\n")

        # 3. MCP servers – now returns (not_installed, not_connected)
        not_installed, not_connected = self._check_mcps()

        # 4. Skills
        missing_skills = self._check_skills()

        # Summarise
        if not_installed:
            self._log_output(f"\n❌ Missing MCPs (not installed): {', '.join(not_installed)}\n")
        if not_connected:
            self._log_output(f"⚠️ MCPs installed but connection failed: {', '.join(not_connected)}\n")
        if missing_skills:
            self._log_output(f"⚠️ Missing Skills: {', '.join(missing_skills)}\n")
        if not not_installed and not not_connected and not missing_skills:
            self._log_output("🎉 All MCPs and skills are ready.\n")

        self._log_output("✅ Verification complete.\n")

    # ------------------------------------------------------------------
    #  HELPERS: check MCPs / skills (return missing)
    # ------------------------------------------------------------------
    def _check_mcps(self):
        """
        Returns (not_installed, not_connected) – two lists of MCP server names.
        Also logs detailed status to the output area.
        """
        required_mcps = ["exa"]            # extend as you like
        not_installed = []
        not_connected = []

        try:
            result = subprocess.run(
                ["claude", "mcp", "list"],
                cwd=self.agent_dir,
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                self._log_output(f"⚠️ MCP list command failed: {result.stderr}\n")
                # Assume all required are not installed
                return (required_mcps.copy(), [])

            output = result.stdout
            self._log_output("📋 MCP servers status:\n")

            for name in required_mcps:
                # Search for the server name at the beginning of a line (common pattern)
                # Claude often outputs "server_name: ... - status"
                pattern = rf"^{re.escape(name)}\s*:.*$"
                lines_with_name = re.findall(pattern, output, re.MULTILINE)

                if not lines_with_name:
                    self._log_output(f"   - {name}: ❌ not installed\n")
                    not_installed.append(name)
                    continue

                # Check if any line for this server shows "✓ Connected"
                connected = any("✓ Connected" in line for line in lines_with_name)
                if connected:
                    self._log_output(f"   - {name}: ✅ connected\n")
                else:
                    self._log_output(f"   - {name}: ⚠️ installed but NOT connected (check API key / network)\n")
                    not_connected.append(name)

        except Exception as e:
            self._log_output(f"❌ Could not check MCP: {e}\n")
            return (required_mcps.copy(), [])

        return (not_installed, not_connected)


    def _check_skills(self):
        """Return list of missing skill names (checking project and global)."""
        required_skills = ["docx", "pptx", "xlsx", "pdf"]
        local_dir = self.agent_dir / "skills"
        global_dir = Path.home() / ".claude" / "plugins" / "marketplaces" / "anthropic-agent-skills" / "skills"
        missing = []

        for skill in required_skills:
            found = False
            # check local
            if local_dir.exists():
                if (local_dir / skill).exists() and any((local_dir / skill).iterdir()):
                    found = True
                    self._log_output(f"✅ Skill '{skill}' found locally.\n")
            # check global
            if not found and global_dir.exists():
                if (global_dir / skill).exists() and any((global_dir / skill).iterdir()):
                    found = True
                    self._log_output(f"✅ Skill '{skill}' found globally.\n")
            if not found:
                self._log_output(f"⚠️ Skill '{skill}' missing.\n")
                missing.append(skill)
        return missing

    # ------------------------------------------------------------------
    #  INSTALL MISSING (NEW)
    # ------------------------------------------------------------------
    def install_missing(self):
        """
        Detects missing skills and not-installed MCPs.
        For MCPs that are installed but not connected, it shows a warning.
        Then installs the truly missing ones.
        """
        # Run detection synchronously
        not_installed, not_connected = self._check_mcps()
        missing_skills = self._check_skills()

        # Warn about broken connections but don't try to re-install
        if not_connected:
            CTkMessagebox(title="Connection Issues",
                          message=f"These MCP servers are installed but cannot connect:\n{', '.join(not_connected)}\n\nCheck your API keys and network.",
                          icon="warning")

        if not not_installed and not missing_skills:
            if not not_connected:
                CTkMessagebox(title="All good", message="Everything is already installed and connected.")
            else:
                CTkMessagebox(title="Done", message="All missing items are installed. Fix connection issues manually.")
            return

        # Ask for Exa key only if exa is truly not installed
        exa_key = None
        if "exa" in not_installed:
            dialog = CTkInputDialog(
                title="Exa API Key",
                text="Enter your Exa API key:",
                show="*"
            )
            exa_key = dialog.get_input()
            if not exa_key:
                self._log_output("❌ Install cancelled – Exa API key is required.\n")
                return

        self.install_btn.configure(state="disabled")
        threading.Thread(
            target=self._install_thread,
            args=(missing_skills, not_installed, exa_key),
            daemon=True
        ).start()

    def _install_thread(self, missing_skills, not_installed_mcps, exa_key):
        self._log_output("🚀 Installing missing components...\n")

        # 1. Install skills using claude plugin install
        for skill in missing_skills:
            self._log_output(f"⬇️ Installing skill: {skill} ...\n")
            try:
                result = subprocess.run(
                    ["claude", "plugin", "install", skill],
                    cwd=self.agent_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    self._log_output(f"✅ Skill '{skill}' installed successfully.\n")
                else:
                    self._log_output(f"❌ Failed to install '{skill}': {result.stderr.strip()}\n")
            except Exception as e:
                self._log_output(f"❌ Error installing '{skill}': {e}\n")

        # 2. Install MCPs (currently only exa)
        for mcp in not_installed_mcps:
            if mcp == "exa" and exa_key:
                self._log_output(f"⬇️ Adding MCP server: {mcp} ...\n")
                try:
                    cmd = [
                        "claude", "mcp", "add", "--transport", "http", mcp, "https://mcp.exa.ai/mcp",
                        "--header", f"x-api-key: {exa_key}"
                        # "--env", f"EXA_API_KEY={exa_key}"
                    ]
                    result = subprocess.run(
                        cmd,
                        cwd=self.agent_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        self._log_output(f"✅ MCP server '{mcp}' added.\n")
                    else:
                        self._log_output(
                            f"❌ Failed to add MCP server '{mcp}': {result.stderr.strip()}\n"
                        )
                except Exception as e:
                    self._log_output(f"❌ Error adding MCP server '{mcp}': {e}\n")
            elif mcp == "exa" and not exa_key:
                self._log_output(f"⚠️ Skipping Exa MCP – no API key provided.\n")

        self._log_output("✅ Installation finished.\n")
        # Re-enable install button
        self.root.after(0, lambda: self.install_btn.configure(state="normal"))

    # ----- running the agent -----
    def run_agent(self):
        folder = self.folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            CTkMessagebox(title="Error", message=f"Please select a valid user folder.", icon="cancel")
            return
        prompt = self.prompt_text.get("1.0", "end-1c").strip()
        if not prompt:
            CTkMessagebox(title="Error", message=f"Please enter a prompt.", icon="cancel")
            return
        api_key = self.api_key.get().strip()
        if not api_key:
            CTkMessagebox(title="Error", message=f"Please enter your API key.", icon="cancel")
            return

        self.run_btn.configure(state="disabled")
        threading.Thread(target=self._run_thread, args=(folder, prompt, api_key), daemon=True).start()

    def _run_thread(self, folder, prompt, api_key):
        self._log_output("🚀 Starting agent...\n")

        env = os.environ.copy()
        env["ANTHROPIC_API_KEY"] = api_key
        base_url = self.base_url.get().strip()
        if base_url:
            env["ANTHROPIC_BASE_URL"] = base_url
        model = self.model.get().strip()
        if model:
            env["ANTHROPIC_MODEL"] = model
        env["CLAUDE_PROJECT_DIR"] = str(self.agent_dir)   # load agent config

        # Add a system instruction to make sure the agent works inside the user folder
        full_prompt = (
            f"{prompt}\n\n"
            f"You MUST use the coteach-planning skill in 'CoTEACH GUI/.claude/skills/coteach-planning/SKILL.md'.\n"
            f"(Note: You are operating inside the folder '{folder}'. "
            f"Please create all output files in the '{folder}/output/' subfolder.)"
        )

        cmd = [
            "claude",
            "-p", full_prompt,
            #"--agent", "coteach-agent",
            "--no-session-persistence",
            "--permission-mode", "bypassPermissions",
            #"--output-format", "text",
            "--verbose"               # optional, gives more progress
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=folder,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            # Read lines live and show in GUI
            for line in proc.stdout:
                self._log_output(line)
            proc.wait()
            if proc.returncode == 0:
                self._log_output("\n✅ Agent finished successfully.\n")
            else:
                self._log_output(f"\n⚠️ Agent exited with code {proc.returncode}.\n")
        except Exception as e:
            self._log_output(f"\n❌ Error running agent: {e}\n")
        finally:
            self.root.after(0, lambda: self.run_btn.configure(state="normal"))

    def _log_output(self, text):
        # Must be called from the main thread (use `after` if needed)
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, self._log_output, text)
            return
        self.output_area.configure(state="normal")
        self.output_area.insert(tk.END, text)
        self.output_area.see(tk.END)
        self.output_area.configure(state="disabled")

if __name__ == "__main__":
    root = ctk.CTk()
    ctk.set_appearance_mode("Light")   # "System", "Dark", "Light"
    ctk.set_default_color_theme("blue") # "blue", "green", "dark-blue"
    app = AgentGUI(root)
    root.mainloop()