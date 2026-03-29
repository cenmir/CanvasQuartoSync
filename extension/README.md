# Canvas Quarto Sync — VS Code Extension

Write your course in Quarto. Preview it live. Sync to Canvas in one click.

## Quick Start (2 minutes)

1. **Install prerequisites**: [Python 3.8+](https://www.python.org/downloads/), [Node.js 18+](https://nodejs.org/)
2. **Install CanvasQuartoSync**: Run `install.ps1` from the repo root
3. **Install the extension**: `Ctrl+Shift+P` → "Extensions: Install from VSIX..." → select the `.vsix` file
4. **Create a course**: Click the graduation cap icon in the sidebar → "New Project"
5. **Edit your config.toml** with your Canvas course ID and API token
6. **Write content** in `.qmd` files
7. **Preview**: Open a `.qmd` file → click the preview icon in the editor title bar
8. **Sync**: Click "Sync to Canvas" in the status bar

## Features

### Sidebar Panel
A dedicated sidebar (graduation cap icon) with quick access to all actions:
- **Project**: New Project, Open config.toml, Extension Settings
- **Sync**: Sync All Files, Sync Current File
- **Tools**: Import from Canvas, Diff with Canvas, Open Preview

### Sync to Canvas
- **Status bar button** with toggle flags (Force, Calendar, Drift)
- **Sync menu**: Choose "Sync All" or "Sync Current File", toggle options
- **Right-click**: Sync a single `.qmd` file from the editor or file explorer
- **Terminal output**: Live color-coded output (gray=debug, cyan=info, yellow=warning, red=error)
- **Progress notification**: Shows the latest status in the bottom-right corner

### Live QMD Preview
Side-by-side preview panel that renders `.qmd` files matching Canvas styling:
- Canvas branding colors (headings, links, tables)
- Callouts with Canvas-exact colors (tip, note, warning, important, caution)
- KaTeX math rendering
- Syntax-highlighted code blocks with copy button
- Mermaid diagram rendering
- Tabset panels
- Cross-references and bibliography citations
- Live updates as you type (400ms debounce)

### Inline Comments
Select text in the preview to add comments:
- Comments stored as HTML comments in the `.qmd` file (invisible to Canvas sync)
- Yellow highlight on commented text
- Click a highlight to view/delete the comment
- Toggle comments on/off with the toolbar button

### New Project Wizard
Full-page form to create a new course project:
- Course name, code, Canvas ID, API URL, token file, semester, language
- Creates: `config.toml`, `_quarto.yml`, study guide template, folder structure

### Import from Canvas
Pull content from Canvas into local `.qmd` files:
- Scope picker: Full import, Pages only, Assignments only, Quizzes only
- Dry run option to preview without writing files

### Diff with Canvas
Check if content was modified directly on Canvas since your last sync:
- Check all files or just the current file
- Colored diff output in the terminal

## Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Quarto CLI](https://quarto.org/docs/get-started/) (for rendering)
- CanvasQuartoSync installed via `install.ps1`
- Canvas API token ([setup guide](../Guides/Canvas_token_setup.md))

## Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `cqs.pythonVenvPath` | `""` (auto-detect) | Path to the Python venv |
| `cqs.autoPreviewOnOpen` | `false` | Auto-open QMD preview when a .qmd file is opened |

## Writing Content

### Frontmatter

Every `.qmd` file needs YAML frontmatter to tell Canvas what to create:

```yaml
---
title: "My Page Title"
canvas:
  type: page           # page, assignment, quiz, study_guide
  preprocess: true      # run Quarto rendering before upload
  published: true       # publish on Canvas immediately
---
```

### Callouts

```markdown
:::note
This is a note callout.
:::

:::warning
This is a warning callout.
:::
```

### Math

```markdown
Inline: $E = mc^2$

Display: $$\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$
```

### Code blocks

````markdown
```cpp
void setup() {
  Serial.begin(115200);
}
```
````

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

## Example Project

The [Mechatronics course](https://github.com/cenmir/Mechatronics) is the canonical example:

```
Mechatronics/
├── config.toml                      # Course settings + Canvas API config
├── _quarto.yml                      # Quarto project config
├── 01_Fundamentals/                 # → Canvas module "Fundamentals"
│   ├── 01_Report_Writing_Guide.qmd  #   → Canvas page
│   ├── 02_Lab0_PlatformIO_Setup.qmd #   → Canvas assignment
│   └── graphics/                    #   → Images (auto-uploaded)
├── 02_PWM and Analog Control/       # → Canvas module
│   ├── 01_Lab4_PWM_Dimming.qmd      #   Callouts, math, code blocks
│   └── 02_Lab5_Potentiometer_Control.qmd
└── ...
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python virtual environment not found" | Run `install.ps1` or set `cqs.pythonVenvPath` in settings |
| Sync button doesn't appear | Ensure `config.toml` exists in the workspace root |
| Preview is blank | Run `npm run build` in the extension folder, then reload |
| Images not showing in preview | Use relative paths from the `.qmd` file's directory |
| Canvas API errors | Check your token file path and API URL in `config.toml` |

## Development

See [devInstructions.md](devInstructions.md) for build setup, debugging, and project structure.
