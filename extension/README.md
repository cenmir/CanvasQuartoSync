# Canvas Quarto Sync — VS Code Extension

Write your course in Quarto. Preview it live. Sync to Canvas in one click.

## Status

**Phase 1 complete** — extension scaffold with sync button.
Phase 2 (live QMD preview), Phase 3 (commenting), and Phase 4 (init wizard, import, diff) are planned.

### What works now

- **Sync to Canvas** button in the status bar (visible when `config.toml` exists in workspace)
- Click to run `sync_to_canvas.py` with a progress notification
- Spinner animation during sync, success/failure message on completion
- "View Output" action on failure to inspect Python stdout/stderr
- All 5 commands registered in the Command Palette under "Canvas Quarto Sync"
- Auto-detection of Python virtual environment
- Parsing of `config.toml` with environment variable overrides

### What is placeholder

- **Open QMD Preview** — registered but shows "coming soon" (Phase 2)
- **Initialize Course** — registered but not yet implemented (Phase 4)
- **Import from Canvas** — registered but not yet implemented (Phase 4)
- **Diff with Canvas** — registered but not yet implemented (Phase 4)

## Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Quarto CLI](https://quarto.org/docs/get-started/)
- CanvasQuartoSync installed via `install.ps1` (creates venv at `~/venvs/canvas_quarto_env/`)
- Canvas API token ([setup guide](../Guides/Canvas_token_setup.md))

## Development Setup

```bash
cd CanvasQuartoSync/extension
npm install
npm run build
```

### Testing the extension

1. Open the `extension/` folder in VS Code
2. Press **F5** to launch the Extension Development Host
3. The dev host opens with the Mechatronics folder pre-loaded
4. The "Sync to Canvas" button should appear in the bottom status bar
5. Press `Ctrl+Shift+P` and type "Canvas Quarto Sync" to see all commands

### Build commands

| Command | What it does |
|---------|-------------|
| `npm run build` | Build everything (extension + webview) |
| `npm run build:extension` | Build extension host only |
| `npm run build:webview` | Build React webview only |
| `npm run watch` | Watch mode for both (auto-rebuild on change) |
| `npm run watch:extension` | Watch extension host only |

### Real-world example: Mechatronics

The [Mechatronics course](https://github.com/cenmir/Mechatronics) is the canonical example project:

```
Mechatronics/
├── config.toml                      # Course settings + Canvas API config
├── _quarto.yml                      # Quarto project config
├── 01_Fundamentals/                 # → Canvas module "Fundamentals"
│   ├── 01_Report_Writing_Guide.qmd  #   → Canvas page
│   ├── 02_Lab0_PlatformIO_Setup.qmd #   → Canvas assignment
│   └── graphics/                    #   → Images (auto-uploaded)
├── 02_PWM and Analog Control/       # → Canvas module "PWM and Analog Control"
│   ├── 01_Lab4_PWM_Dimming.qmd      #   Callouts, math, code blocks
│   └── 02_Lab5_Potentiometer_Control.qmd
└── ...
```

Clone it and open in the Extension Development Host to test the sync button against a real course.

## Architecture

```
extension/
├── src/                          # Extension host (Node.js, runs in VS Code)
│   ├── extension.ts              # Entry point — registers commands + status bar
│   ├── commands/
│   │   ├── syncToCanvas.ts       # Spawns sync_to_canvas.py with progress
│   │   ├── openPreview.ts        # (Phase 2) Opens QMD preview webview
│   │   ├── initCourse.ts         # (Phase 4) Course scaffolding wizard
│   │   ├── importFromCanvas.ts   # (Phase 4) Reverse sync
│   │   └── diffWithCanvas.ts     # (Phase 4) Canvas vs local diff
│   ├── providers/
│   │   └── statusBar.ts          # Status bar button + spinner
│   ├── python/
│   │   ├── venvResolver.ts       # Finds Python in venv
│   │   └── runner.ts             # Spawns Python, strips Rich/ANSI, reports progress
│   ├── config/
│   │   └── configLoader.ts       # Parses config.toml + env vars
│   └── utils/
│       ├── webviewMessaging.ts    # Typed message protocol (host ↔ webview)
│       └── fileWatcher.ts         # Debounced .qmd file watcher
│
├── webview/                       # React app (runs in sandboxed webview iframe)
│   ├── index.html                 # Shell HTML
│   ├── index.tsx                  # React entry
│   └── App.tsx                    # (Phase 2) Preview renderer
│
├── dist/                          # Build output (gitignored)
│   ├── extension.js               # Bundled extension host
│   └── webview/                   # Bundled React app
│
├── esbuild.mjs                    # Extension host bundler
├── vite.config.ts                 # Webview React bundler
├── tsconfig.json                  # TypeScript config (extension host)
├── tsconfig.webview.json          # TypeScript config (webview React)
└── package.json                   # Manifest, dependencies, scripts
```

### How the sync button works

1. User clicks "Sync to Canvas" in status bar (or runs command from palette)
2. `syncToCanvas.ts` resolves the Python venv path via `venvResolver.ts`
3. Locates `sync_to_canvas.py` relative to the extension directory (one level up)
4. Spawns `python sync_to_canvas.py <workspace> --verbose` via `runner.ts`
5. `runner.ts` strips Rich markup and ANSI codes from stdout, forwards clean lines to `vscode.Progress`
6. Status bar shows spinner during sync, reverts on completion
7. On failure, "View Output" action opens a channel with full stdout/stderr

### Python venv resolution order

1. `cqs.pythonVenvPath` extension setting (if configured)
2. `CANVAS_QUARTO_VENV` environment variable
3. `~/venvs/canvas_quarto_env/` (default from `install.ps1`)
4. `.venv/` in the workspace root

### Config loading

`configLoader.ts` reads `config.toml` from the workspace root. Environment variables `CANVAS_API_URL` and `CANVAS_API_TOKEN` override the file values. If `canvas_token_path` is set in the TOML, the token is read from that file.

## Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `cqs.pythonVenvPath` | `""` (auto-detect) | Path to the Python venv |
| `cqs.autoPreviewOnOpen` | `false` | Auto-open QMD preview when a .qmd file is opened |

## Roadmap

### Phase 2: Live QMD Preview
React webview rendering .qmd files with Canvas-matching styling. Ported from [MDViewer](https://github.com/JonssonLogic/MDViewer). Includes callouts, math (KaTeX), code highlighting, mermaid diagrams, tabsets, and live reload on save.

### Phase 3: Commenting / Annotation
Inline comment system ported from MDViewer. Select text in the preview, add comments stored as HTML comments in the .qmd file. Invisible to Canvas sync.

### Phase 4: Init Wizard, Import, Diff
- **Initialize Course** — command palette wizard to scaffold a new course project
- **Import from Canvas** — reverse sync an existing Canvas course into local .qmd files
- **Diff with Canvas** — compare local content with what is live on Canvas

### Phase 5: Documentation & Onboarding
Welcome tab for first-time users, VS Code walkthrough integration, Mechatronics as the guided example.
