# CanvasQuartoSync VS Code Extension — Project Plan

## Context

**CanvasQuartoSync** (`CanvasQuartoSync/`) is a Python tool that syncs Quarto (.qmd) course content to Canvas LMS. Key entry points:
- `sync_to_canvas.py` — main sync CLI (296 LOC)
- `import_from_canvas.py` — reverse import (1,071 LOC)
- `init_course.bat` — course scaffolding (batch script)
- `handlers/` — 17 handler modules (page, assignment, quiz, calendar, etc.)
- Python venv at `~/venvs/canvas_quarto_env/`, installed via `install.ps1`

**MDViewer** ([github.com/JonssonLogic/MDViewer](https://github.com/JonssonLogic/MDViewer)) is a standalone Tauri+React desktop app by collaborator Kalle that renders .qmd files. We are porting its rendering pipeline into the VS Code extension.

**Mechatronics** ([github.com/cenmir/Mechatronics](https://github.com/cenmir/Mechatronics)) is the canonical example course project used for testing and documentation.

**Goal**: A VS Code extension inside `CanvasQuartoSync/extension/` that:
1. Wraps the Python sync/import tools with GUI (status bar, wizards, progress)
2. Provides a live QMD preview matching Canvas styling (ported from MDViewer)
3. Includes inline commenting/annotation
4. Ships with clear docs and a quick-start using Mechatronics as the example

---

## Current Progress

### Phase 1: Scaffold + Sync Button — COMPLETE

All files created, builds successfully (`npm run build` produces `dist/extension.js` + `dist/webview/`).

**Files implemented:**

| File | Status | Purpose |
|------|--------|---------|
| `package.json` | Done | Extension manifest — 5 commands, settings, .qmd language, editor title menu |
| `esbuild.mjs` | Done | Bundles `src/extension.ts` → `dist/extension.js` (Node/CJS) |
| `vite.config.ts` | Done | Bundles `webview/` → `dist/webview/` (React/ESM, stable filenames) |
| `tsconfig.json` | Done | Extension host TypeScript config (CommonJS, ES2020) |
| `tsconfig.webview.json` | Done | Webview React TypeScript config (ESNext, JSX) |
| `.vscodeignore` | Done | Excludes source from packaged extension |
| `.vscode/launch.json` | Done | F5 launches Extension Dev Host with Mechatronics folder |
| `.vscode/tasks.json` | Done | Pre-launch build task |
| `src/extension.ts` | Done | Entry point — registers 5 commands + status bar |
| `src/commands/syncToCanvas.ts` | Done | Spawns `sync_to_canvas.py` with `vscode.window.withProgress` |
| `src/commands/openPreview.ts` | Placeholder | Registered, shows "coming soon" |
| `src/commands/initCourse.ts` | Placeholder | Registered, not implemented |
| `src/commands/importFromCanvas.ts` | Placeholder | Registered, not implemented |
| `src/commands/diffWithCanvas.ts` | Placeholder | Registered, not implemented |
| `src/providers/statusBar.ts` | Done | "Sync to Canvas" button with spinner animation |
| `src/python/venvResolver.ts` | Done | Finds Python (setting → env var → default → workspace .venv) |
| `src/python/runner.ts` | Done | Spawns Python, strips Rich/ANSI markup, reports progress |
| `src/config/configLoader.ts` | Done | Parses config.toml, merges env vars, resolves token file |
| `src/utils/webviewMessaging.ts` | Done | Typed message protocol (ToWebviewMessage / ToExtensionMessage) |
| `src/utils/fileWatcher.ts` | Done | Debounced .qmd file watcher (300ms) |
| `webview/index.html` | Done | Shell HTML for React webview |
| `webview/index.tsx` | Done | React entry point |
| `webview/App.tsx` | Placeholder | Renders "coming soon" (Phase 2 replaces this) |

**How to test Phase 1:**
1. `cd extension && npm install && npm run build`
2. Open `extension/` in VS Code, press F5
3. Extension Dev Host opens with Mechatronics folder
4. Status bar shows "Sync to Canvas" button (requires `config.toml` in workspace)
5. `Ctrl+Shift+P` → "Canvas Quarto Sync" shows all 5 commands

---

## Phase 2: Live QMD Preview — NOT STARTED

**Goal**: Side-by-side React webview that renders .qmd files matching Canvas styling.

### MDViewer components to port

| MDViewer file | Action | Target location | Notes |
|---------------|--------|-----------------|-------|
| `src/utils/qmdPreprocess.ts` | Copy as-is | `webview/preprocessing/qmdPreprocess.ts` | Strips YAML, converts `:::` fenced divs, tabsets, `{{< video >}}` shortcodes, cross-refs, bibliography. Zero Tauri deps. |
| `src/utils/remarkCallouts.ts` | Copy as-is | `webview/preprocessing/remarkCallouts.ts` | Remark plugin for `:::{.callout-note}` syntax. Pure remark, no platform deps. |
| `src/components/MarkdownRenderer.tsx` | Copy + minor adapt | `webview/components/MarkdownRenderer.tsx` | Remove Tauri event handlers. Plugin chain: remark-gfm, remark-math, remark-directive, rehype-katex, rehype-highlight, rehype-slug, rehype-raw. |
| `src/components/CodeBlock.tsx` | Copy as-is | `webview/components/CodeBlock.tsx` | Syntax highlighting + copy button. Uses `navigator.clipboard`. |
| `src/components/TabsetBlock.tsx` | Copy as-is | `webview/components/TabsetBlock.tsx` | Interactive tab panels. Pure React useState. |
| `src/components/MermaidBlock.tsx` | Copy as-is | `webview/components/MermaidBlock.tsx` | Mermaid diagram rendering. Runs in-browser. |
| `src/components/TableOfContents.tsx` | Copy as-is | `webview/components/TableOfContents.tsx` | Heading TOC with IntersectionObserver. |
| `src/styles/markdown.css` | Copy as-is | `webview/styles/markdown.css` | ~1000 lines, comprehensive markdown styling. |
| `src/App.tsx` | Rewrite | `webview/App.tsx` | Heavy Tauri deps. Rewrite as thin shell receiving content via postMessage. |

### New files to create

| File | Purpose |
|------|---------|
| `webview/components/CalloutBlock.tsx` | Renders callouts with Canvas-matching colors (not in MDViewer) |
| `webview/styles/canvas-overrides.css` | Exact Canvas colors extracted from `base_handler.py` |
| `webview/hooks/useFileContent.ts` | Listens for `postMessage` updates from extension host |
| `webview/vscode.d.ts` | Type declarations for `acquireVsCodeApi()` |
| `src/providers/previewProvider.ts` | WebviewPanel in `ViewColumn.Beside`, sends content, resolves images |

### Canvas styling to match

Extract from `handlers/base_handler.py`:

**Callout styles** (line ~10):
```
tip:       border #198754, bg #d1e7dd, icon 💡
important: border #dc3545, bg #f8d7da, icon ❗
warning:   border #ffc107, bg #fff3cd, icon ⚠️
note:      border #0d6efd, bg #cfe2ff, icon 📝
caution:   border #fd7e14, bg #ffe5d0, icon 🔶
```

**Code block styles** (line ~263-355):
- Container: bg `#f7f7f7`, padding 12px 16px, radius 4px, text `#003B4F`
- 27 token types with specific colors (keyword `#003B4F` bold, string `#20794D`, etc.)

**Branding**: Parse `branding.css` from workspace for `--brand-*` CSS variables.

### Architecture

- `previewProvider.ts` creates `WebviewPanel` in `ViewColumn.Beside`
- Extension host reads `.qmd` file, batch-resolves image paths to `webview.asWebviewUri()`, sends via `postMessage({type: 'updateContent', ...})`
- File watching: `onDidSaveTextDocument` triggers re-send (debounced 300ms via `fileWatcher.ts`)
- `localResourceRoots` includes workspace folder for image loading
- Webview `App.tsx` receives content, runs `qmdPreprocess()` + remark/rehype pipeline, renders via React

### Webview npm dependencies (already in package.json)

react, react-dom, unified, remark-parse, remark-gfm, remark-math, remark-directive, remark-rehype, rehype-katex, rehype-highlight, rehype-slug, rehype-raw, rehype-react, react-markdown, mermaid, katex

---

## Phase 3: Commenting / Annotation — NOT STARTED

**Goal**: Port MDViewer's inline comment system.

### MDViewer components to port

| MDViewer file | Action | Target location |
|---------------|--------|-----------------|
| `src/components/CommentInput.tsx` | Copy as-is | `webview/components/CommentInput.tsx` |
| `src/hooks/useComments.ts` | Adapt (70%) | `webview/hooks/useComments.ts` |

### Key changes from MDViewer

- Replace `invoke('read_file')` / `invoke('write_file')` (Tauri) with `vscode.postMessage({type: 'saveComment', ...})` / `postMessage({type: 'deleteComment', ...})`
- Extension host handles file I/O via `vscode.workspace.fs`
- Comment storage format unchanged: `<!-- COMMENT:{"id":"...","line":42,"text":"..."} -->` appended to .qmd file
- Comments are invisible to Canvas sync (HTML comments are stripped)

---

## Phase 4: Init Wizard, Import, Diff — NOT STARTED

### initCourse.ts
Replace `init_course.bat` with multi-step VS Code wizard:
1. `showInputBox` — Course name, code, Canvas course ID
2. `showInputBox` — Canvas API URL (default from settings)
3. `showOpenDialog` — Token file path
4. `showInputBox` — Semester
5. `showQuickPick` — Language (English/Swedish)

Creates: `config.toml`, `_quarto.yml`, `01_Course_Info/01_StudyGuide.qmd`, `graphics/`, `run_sync_here.bat`

Template sources: `CanvasQuartoSync/Example/` directory and `init_course.bat` (lines 80-121).

### importFromCanvas.ts
- `showQuickPick` for scope: "Full import" / "Pages only" / "Assignments only"
- Optional `--dry-run` checkbox
- Runs `import_from_canvas.py <workspace> [--include types] [--dry-run]` via `runner.ts`
- Progress via `withProgress`

### diffWithCanvas.ts
1. Read `.canvas_sync_map.json` from workspace to get Canvas page IDs
2. Fetch Canvas HTML via REST API (`GET /api/v1/courses/{id}/pages/{url}`) using token from `configLoader.ts`
3. Write Canvas HTML and local rendered HTML to temp files
4. Open VS Code diff: `vscode.commands.executeCommand('vscode.diff', canvasUri, localUri, title)`

---

## Phase 5: Documentation & Onboarding — NOT STARTED

### README.md
Quick-start guide (2-minute path: install → init → write → preview → sync).
Mechatronics as real-world example with clone instructions.
Sections: Prerequisites, Installation, First Course, Writing Content (frontmatter ref), Preview, Syncing, Importing, Commenting, Config Reference, Troubleshooting.

### In-extension onboarding
- **Welcome tab**: On first activation (no `config.toml`), show webview with "Create New Course" and "Open Example (Mechatronics)" buttons
- **VS Code Walkthrough**: `contributes.walkthroughs` entry in `package.json` with step-by-step checklist

### Mechatronics as canonical example
- README links to `github.com/cenmir/Mechatronics`
- Welcome page offers to clone it
- Walkthrough references specific .qmd files (e.g., `02_PWM and Analog Control/01_Lab4_PWM_Dimming.qmd` for callouts + math + code)

---

## Critical Files Reference

These files in the parent repo contain logic/data that the extension must replicate or invoke:

| File | What the extension needs from it |
|------|----------------------------------|
| `handlers/base_handler.py` | Callout styles (line ~10), inline CSS for code syntax highlighting (line ~263-355) |
| `handlers/config.py` | Config resolution logic (env vars → TOML → token file) |
| `sync_to_canvas.py` | CLI interface and argument parsing |
| `import_from_canvas.py` | CLI interface for reverse sync |
| `handlers/content_utils.py` | `.canvas_sync_map.json` format (needed by diff command) |
| `Example/branding.css` | CSS custom property convention (`--brand-*`) |
| `init_course.bat` | Course scaffold template (lines 80-121) |

## Build System

| Tool | Scope | Config file |
|------|-------|-------------|
| esbuild | Extension host (`src/` → `dist/extension.js`) | `esbuild.mjs` |
| Vite + React plugin | Webview (`webview/` → `dist/webview/`) | `vite.config.ts` |
| TypeScript | Extension host types | `tsconfig.json` |
| TypeScript | Webview React types | `tsconfig.webview.json` |

Stable filenames in Vite output (no hashes) so the extension can reference `dist/webview/index.html` and `dist/webview/assets/index.js` predictably.

## Verification Checklist

- [ ] Open `Mechatronics/` as workspace → status bar "Sync to Canvas" button appears
- [ ] Click sync → progress notification → success/failure with "View Output"
- [ ] Open any `.qmd` → `Ctrl+Shift+V` → side-by-side preview (Phase 2)
- [ ] Preview shows Canvas-matching callouts, math, code, mermaid (Phase 2)
- [ ] Edit and save `.qmd` → preview updates within 500ms (Phase 2)
- [ ] Select text in preview → add inline comment (Phase 3)
- [ ] Run "Initialize Course" in empty folder → full scaffold created (Phase 4)
- [ ] Run "Import from Canvas" → reverse sync with progress (Phase 4)
- [ ] Run "Diff with Canvas" → diff editor opens (Phase 4)
- [ ] Visual comparison: Canvas page screenshot vs preview → identical styling (Phase 2)
