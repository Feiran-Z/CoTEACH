# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoTeach is an educational unit/lesson planning assistant. A Tkinter GUI (`coteach-gui.py`) launches the Claude CLI agent with the `coteach-planning` skill, which orchestrates a 5-phase workflow using five educational expert perspectives (Wiggins/UbD, Erickson/CBCI, Beard/Experiential Learning, Meyer/UDL, Fung/Neurodiversity) to analyze, improve, and generate unit plans and lesson plans.

## Key Files

- `coteach-gui.py` — Main application: Tkinter GUI that accepts user inputs (folder, prompt, API key), verifies the environment (Claude CLI, MCP servers, skills), and runs the Claude CLI agent with the `coteach-planning` skill.
- `.claude/skills/coteach-planning/SKILL.md` — The central skill that defines the phased workflow (Phases 0-4) for unit plan analysis and improvement.
- `.claude/skills/` — Contains five expert perspective skills: `grant-wiggins-perspective`, `lynn-erickson-perspective`, `colin-beard-perspective`, `anne-meyer-perspective`, `lawrence-fung-perspective`.

## Architecture

The system has two key directories:
1. **CoTeach GUI/** — Holds the GUI script, CLAUDE.md, and `.claude/skills/` with all skills.
2. **User folder** — Provided at runtime via the GUI. Contains:
   - `input/` — User-supplied files (syllabi, activities, slides, etc.)
   - `template/` — Unit plan templates (e.g., `IB-unit-planner-default.docx`)
   - `output/` — Where all generated files go:
     - `original-unit/unit-plan.docx` — The source unit plan (Phase 1a or 1.5)
     - `improved-unit/unit-plan.docx` — The improved plan (Phase 3)
     - `lesson-plans/lesson-plans.docx` — Generated lesson plans (Phase 4)
     - `key-info.md`, `analysis.md`, `suggestion.md`, `checklist.md` — Supporting artifacts

## Workflow (5 phases)

You MUST invoke the coteach-planning skill via `CoTeach GUI/.claude/skills/coteach-planning/SKILL.md` first.
| Phase | Description |
|-------|-------------|
| 0 | Create output folders and `checklist.md` |
| 1 | Determine pathway: improvement (user has a plan) or creation (topic only) |
| 1a/1b | Extract key information from the unit plan or infer from materials |
| 1.5 | Generate a new unit plan using UbD (creation pathway only) |
| 2 | Analyze the unit plan using all 5 experts, produce `analysis.md` and `suggestion.md` |
| 3 | Produce an improved `unit-plan.docx` incorporating expert suggestions |
| 4 | Generate lesson plans as `lesson-plans.docx` |

The skill mandates: never skip Phase 2, never rename files, verify all outputs after each phase, never ask the user for clarification.

## Running the Application

```bash
python3 coteach-gui.py
```

The GUI provides:
- **Browse** — Select the user folder containing `input/`
- **Verify Setup** — Checks Claude CLI, Exa MCP, and required skills (docx, pptx, xlsx, pdf)
- **Install Missing** — Installs missing skills and MCPs (prompts for Exa API key)
- **Run Agent** — Launches the Claude CLI agent with the coteach-planning skill

Environment variables set at runtime: `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL`, `CLAUDE_PROJECT_DIR`.

## Key Constraints

- The agent runs with `--permission-mode bypassPermissions` and `--no-session-persistence`
- Default API endpoint: `https://api.deepseek.com/anthropic` with model `deepseek-v4-flash`
- Required MCP server: `exa` (web search)
- Required skills: `docx`, `pptx`, `xlsx`, `pdf`
