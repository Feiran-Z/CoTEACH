# CoTEACH

## Prerequisites
1. Claude Code CLI: [Overview](https://code.claude.com/docs/en/overview)
2. Python 3.12+: [Downloads](https://www.python.org/downloads/)
3. Anthropic-compatible LLM (e.g. Claude, Deepseek, Kimi, GLM, etc.) API key
4. Exa API Key: Obtainable for free from [Exa.ai](https://exa.ai/)

## Set up
1. Download this repository as a zip
2. Unzip the files into a folder
3. In your terminal (e.g., Bash, PowerShell, CMD, etc.), run the following to compile the executable:
   ```bash
   cd path/to/your/unzipped/folder/
   pip install -r requirements.txt
   pyinstaller --onefile coteach-gui.py
   ```
4. Run the compiled executable file under the `dist/` subfolder
5. Enjoy
