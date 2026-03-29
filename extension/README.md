# Canvas Quarto Sync — VS Code Extension

Write your course in Quarto. Preview it live. Sync to Canvas in one click.

## Install

1. Download `canvasquartosync-X.X.X.vsix` from the [latest release](https://github.com/cenmir/CanvasQuartoSync/releases)
2. In VS Code: **Ctrl+Shift+P** → `Extensions: Install from VSIX...` → select the file
3. Reload VS Code

**Prerequisites:** [Python 3.8+](https://www.python.org/downloads/) with CanvasQuartoSync installed (run `install.ps1` from the repo root).

## Quick Start

1. Click the **graduation cap** icon in the sidebar → **New Project**
2. Fill in your course name, Canvas course ID, API URL, and token file
3. Click **Create Project** — this generates `config.toml`, a study guide template, and folder structure
4. Write content in `.qmd` files
5. Click **preview icon** in the editor title bar to see a live preview
6. Click **Sync to Canvas** in the status bar to push to Canvas

## Features

- **Sidebar panel** — New Project, Sync, Import, Diff, Preview
- **Sync menu** — Sync All or Sync Current File, with toggle flags (Force, Calendar, Drift)
- **Right-click sync** — Sync a single `.qmd` from editor or file explorer
- **Live QMD preview** — Canvas-matching styling, KaTeX math, code highlighting, Mermaid diagrams, callouts, tabsets
- **Inline comments** — Select text in the preview, add comments stored as HTML comments in the `.qmd` file (invisible to Canvas)
- **Import from Canvas** — Pull content from Canvas into local `.qmd` files
- **Diff with Canvas** — Check if content was modified directly on Canvas
- **Color-coded terminal output** — Live sync progress with colored log levels

## Config Reference

`config.toml` in the course root:

```toml
course_id = 12345
course_name = "Mechatronics"
course_code = "TMRK16"
credits = "7.5 ECTS"
semester = "Spring 2026"
canvas_api_url = "https://canvas.university.edu/api/v1"
canvas_token_path = "C:/Users/you/privateCanvasToken"
language = "english"
```

## Development

See [devInstructions.md](devInstructions.md) for build setup, debugging, and project structure.

## Example Project

The [Mechatronics course](https://github.com/cenmir/Mechatronics) is the canonical example.
