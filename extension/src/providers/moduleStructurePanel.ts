import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { resolvePython, resolveCqsRoot } from '../python/venvResolver';
import { getWorkspaceRoot } from '../config/configLoader';
import { setSyncing } from './statusBar';

// ── Module Structure Panel ──────────────────────────────────────────
//
// Fetches the Canvas module structure and displays it in a webview,
// showing which items exist locally and which are Canvas-only.
// All HTML is rendered server-side (in TypeScript) to avoid webview
// messaging / document.write issues.

let currentPanel: vscode.WebviewPanel | undefined;
const log = vscode.window.createOutputChannel('CQS Module Structure');

interface ModuleItem {
  title: string;
  type: string;
  published: boolean;
  indent: number;
  local_path: string | null;
  external_url?: string;
  content_id?: number | null;
  page_url?: string | null;
  module_item_id?: number | null;
  html_url?: string;
}

interface Module {
  name: string;
  id: number;
  published: boolean;
  items: ModuleItem[];
}

interface StructureData {
  course_name: string;
  course_code: string;
  course_id: number;
  modules: Module[];
  unmatched_local_files: string[];
}

export async function openModuleStructurePanel(extensionPath: string): Promise<void> {
  log.appendLine('[open] called');

  if (currentPanel) {
    currentPanel.reveal();
    await refreshPanel(extensionPath);
    return;
  }

  currentPanel = vscode.window.createWebviewPanel(
    'cqs.moduleStructure',
    'Canvas Module Structure',
    vscode.ViewColumn.One,
    { enableScripts: true, retainContextWhenHidden: true }
  );

  currentPanel.webview.onDidReceiveMessage(async (msg) => {
    const ws = getWorkspaceRoot();
    if (msg.type === 'openFile') {
      if (ws && msg.path) {
        const uri = vscode.Uri.file(path.join(ws, msg.path));
        vscode.window.showTextDocument(uri);
      }
    } else if (msg.type === 'refresh') {
      await refreshPanel(extensionPath);
    } else if (msg.type === 'diff') {
      if (ws && msg.localPath) {
        await handleDiff(extensionPath, ws, msg.localPath);
      }
    } else if (msg.type === 'sync') {
      if (ws && msg.localPath) {
        const uri = vscode.Uri.file(path.join(ws, msg.localPath));
        await vscode.commands.executeCommand('cqs.syncFile', uri);
      }
    } else if (msg.type === 'import') {
      await handleImport(extensionPath, msg.itemData);
    } else if (msg.type === 'importModule') {
      // Import all canvas-only items in a module sequentially
      const items: Record<string, unknown>[] = msg.items;
      let imported = 0;
      let failed = 0;
      for (const itemData of items) {
        try {
          await handleImport(extensionPath, itemData);
          imported++;
        } catch {
          failed++;
        }
      }
      const summary = `Module import: ${imported} imported` + (failed ? `, ${failed} failed` : '');
      if (failed) {
        vscode.window.showWarningMessage(summary);
      } else {
        vscode.window.showInformationMessage(summary);
      }
      await refreshPanel(extensionPath);
    } else if (msg.type === 'batchSync') {
      // Sync multiple local items sequentially
      const ws = getWorkspaceRoot();
      if (ws) {
        let synced = 0;
        for (const localPath of msg.paths as string[]) {
          const uri = vscode.Uri.file(path.join(ws, localPath));
          await vscode.commands.executeCommand('cqs.syncFile', uri);
          synced++;
        }
        vscode.window.showInformationMessage(`Synced ${synced} item(s) to Canvas.`);
        await refreshPanel(extensionPath);
      }
    } else if (msg.type === 'batchImport') {
      // Import multiple canvas-only items sequentially
      const items: Record<string, unknown>[] = msg.items;
      let imported = 0;
      let failed = 0;
      for (const itemData of items) {
        try {
          await handleImport(extensionPath, itemData);
          imported++;
        } catch {
          failed++;
        }
      }
      const summary = `Batch import: ${imported} imported` + (failed ? `, ${failed} failed` : '');
      if (failed) {
        vscode.window.showWarningMessage(summary);
      } else {
        vscode.window.showInformationMessage(summary);
      }
      await refreshPanel(extensionPath);
    } else if (msg.type === 'openUrl') {
      if (msg.url) {
        vscode.env.openExternal(vscode.Uri.parse(msg.url));
      }
    }
  });

  currentPanel.onDidDispose(() => { currentPanel = undefined; });

  // Show loading, then fetch and render
  currentPanel.webview.html = wrapHtml('<div class="loading">Fetching module structure from Canvas...</div>');
  await refreshPanel(extensionPath);
}

async function refreshPanel(extensionPath: string): Promise<void> {
  if (!currentPanel) return;
  const result = await fetchStructure(extensionPath);
  if (!currentPanel) return;

  if (result.type === 'error') {
    currentPanel.webview.html = wrapHtml(
      '<div class="error-msg">' + esc(result.message || 'Unknown error') + '</div>'
    );
  } else if (result.data) {
    currentPanel.webview.html = wrapHtml(renderBody(result.data));
  }
}

async function handleDiff(extensionPath: string, ws: string, localPath: string): Promise<void> {
  const pythonPath = resolvePython();
  if (!pythonPath) return;
  const cqsRoot = resolveCqsRoot(extensionPath);
  const scriptPath = path.join(cqsRoot, 'sync_to_canvas.py');
  const args = [scriptPath, ws, '--check-drift', '--diff-json', '--only', localPath];

  setSyncing(true);
  const result = await new Promise<string>((resolve) => {
    let stdout = '';
    const proc = spawn(pythonPath, args, { cwd: ws, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
    proc.stdout?.on('data', (d: Buffer) => { stdout += d.toString(); });
    proc.on('close', () => { setSyncing(false); resolve(stdout); });
    proc.on('error', () => { setSyncing(false); resolve(''); });
  });

  const jsonLine = result.split('\n').find(l => l.trim().startsWith('DRIFT_JSON:'));
  if (!jsonLine) {
    vscode.window.showInformationMessage('No drift detected — Canvas matches local file.');
    return;
  }

  try {
    const items = JSON.parse(jsonLine.trim().replace('DRIFT_JSON:', ''));
    if (items.length === 0) {
      vscode.window.showInformationMessage('No drift detected — Canvas matches local file.');
      return;
    }
    for (const item of items) {
      const canvasUri = vscode.Uri.file(item.canvas_qmd_path);
      const localUri = vscode.Uri.file(item.local_path);
      await vscode.commands.executeCommand('vscode.diff', canvasUri, localUri, 'Canvas \u2194 Local: ' + item.title);
    }
  } catch {
    vscode.window.showErrorMessage('Failed to parse diff results.');
  }
}

async function handleImport(extensionPath: string, itemData: Record<string, unknown>): Promise<void> {
  const ws = getWorkspaceRoot();
  if (!ws) return;
  const pythonPath = resolvePython();
  if (!pythonPath) return;

  const cqsRoot = resolveCqsRoot(extensionPath);
  const scriptPath = path.join(cqsRoot, 'sync_to_canvas.py');
  const itemJson = JSON.stringify(itemData);
  const args = [scriptPath, ws, '--import-item', itemJson];

  setSyncing(true);
  const result = await new Promise<string>((resolve) => {
    let stdout = '';
    let stderr = '';
    const proc = spawn(pythonPath, args, { cwd: ws, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
    proc.stdout?.on('data', (d: Buffer) => { stdout += d.toString(); });
    proc.stderr?.on('data', (d: Buffer) => { stderr += d.toString(); });
    proc.on('close', () => { setSyncing(false); resolve(stdout); });
    proc.on('error', () => { setSyncing(false); resolve(''); });
  });

  const jsonLine = result.split('\n').find(l => l.trim().startsWith('IMPORT_RESULT_JSON:'));
  if (jsonLine) {
    try {
      const res = JSON.parse(jsonLine.trim().replace('IMPORT_RESULT_JSON:', ''));
      if (res.success) {
        vscode.window.showInformationMessage('Imported: ' + res.file);
        // Open the file
        const uri = vscode.Uri.file(path.join(ws, res.file));
        vscode.window.showTextDocument(uri);
        // Refresh the panel
        await refreshPanel(extensionPath);
      } else {
        vscode.window.showErrorMessage('Import failed: ' + res.error);
      }
    } catch {
      vscode.window.showErrorMessage('Failed to parse import result.');
    }
  } else {
    vscode.window.showErrorMessage('Import produced no output.');
  }
}

// ── Fetch from Python ───────────────────────────────────────────────

async function fetchStructure(
  extensionPath: string
): Promise<{ type: string; data?: StructureData; message?: string }> {
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) return { type: 'error', message: 'No workspace folder open.' };

  const pythonPath = resolvePython();
  if (!pythonPath) return { type: 'error', message: 'Python venv not found. Run install.ps1.' };

  const cqsRoot = resolveCqsRoot(extensionPath);
  const scriptPath = path.join(cqsRoot, 'sync_to_canvas.py');
  const args = [scriptPath, workspaceRoot, '--module-structure'];

  log.appendLine('[fetch] python=' + pythonPath);
  log.appendLine('[fetch] cwd=' + workspaceRoot);
  setSyncing(true);

  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';

    const proc = spawn(pythonPath, args, { cwd: workspaceRoot, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
    proc.stdout?.on('data', (d: Buffer) => { stdout += d.toString(); });
    proc.stderr?.on('data', (d: Buffer) => { stderr += d.toString(); });

    proc.on('close', (code) => {
      setSyncing(false);
      log.appendLine('[fetch] exit=' + code);
      if (code !== 0) {
        resolve({ type: 'error', message: 'Python exit ' + code + ': ' + stderr.slice(0, 500) });
        return;
      }
      const line = stdout.split('\n').find(l => l.trim().startsWith('MODULE_STRUCTURE_JSON:'));
      if (!line) {
        resolve({ type: 'error', message: 'No JSON in output. stderr: ' + stderr.slice(0, 300) });
        return;
      }
      try {
        const data = JSON.parse(line.trim().replace('MODULE_STRUCTURE_JSON:', ''));
        resolve({ type: 'structure', data });
      } catch (e) {
        resolve({ type: 'error', message: 'JSON parse error: ' + e });
      }
    });

    proc.on('error', (err) => {
      setSyncing(false);
      resolve({ type: 'error', message: 'Spawn error: ' + err.message });
    });
  });
}

// ── HTML rendering (all server-side) ────────────────────────────────

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const TYPE_ICONS: Record<string, string> = {
  Page: '&#x1F4C4;',
  Assignment: '&#x1F4DD;',
  Quiz: '&#x2753;',
  File: '&#x1F4CE;',
  ExternalUrl: '&#x1F517;',
  ExternalTool: '&#x1F527;',
  SubHeader: '&#x1F4CC;',
};

function renderBody(data: StructureData): string {
  const totalItems = data.modules.reduce((s, m) => s + m.items.length, 0);
  const localItems = data.modules.reduce((s, m) => s + m.items.filter(i => i.local_path).length, 0);
  const canvasOnly = totalItems - localItems;

  let h = '';

  // Header
  h += '<div class="header"><div>';
  const courseTitle = data.course_code
    ? esc(data.course_code) + ' &mdash; ' + esc(data.course_name)
    : esc(data.course_name);
  h += '<h1>' + courseTitle + '</h1>';
  const infoParts: string[] = [];
  infoParts.push('ID: ' + data.course_id);
  if ((data as any).total_students != null) infoParts.push((data as any).total_students + ' students');
  if ((data as any).term) infoParts.push('Term: ' + esc((data as any).term));
  if ((data as any).workflow_state) infoParts.push(esc((data as any).workflow_state));
  infoParts.push(data.modules.length + ' modules');
  infoParts.push(totalItems + ' items');
  h += '<div class="subtitle">' + infoParts.join(' &middot; ') + '</div>';
  h += '</div><button class="refresh-btn" onclick="refresh()">Refresh</button></div>';

  // Stats
  h += '<div class="stats">';
  h += '<div class="stat"><span class="num" style="color:#198754">' + localItems + '</span> synced locally</div>';
  h += '<div class="stat"><span class="num" style="color:#dc3545">' + canvasOnly + '</span> Canvas-only</div>';
  h += '</div>';

  // Legend
  h += '<div class="legend">';
  h += '<div class="legend-item"><span class="dot local"></span> Synced locally</div>';
  h += '<div class="legend-item"><span class="dot canvas-only"></span> Canvas-only (not imported)</div>';
  h += '<div class="legend-item"><span class="dot unpublished"></span> Unpublished</div>';
  h += '</div>';

  // Modules
  for (let mi = 0; mi < data.modules.length; mi++) {
    const mod = data.modules[mi];
    const localCount = mod.items.filter(i => i.local_path).length;
    const pubCls = mod.published ? 'published' : 'draft';
    const pubLbl = mod.published ? 'Published' : 'Draft';

    h += '<div class="module">';
    h += '<div class="module-header">';
    h += '<span class="toggle" id="toggle-' + mi + '" onclick="toggleModule(' + mi + ')">&#9660;</span> ';
    h += '<span onclick="toggleModule(' + mi + ')" style="flex:1;cursor:pointer">' + esc(mod.name) + '</span>';
    h += ' <span class="pub-badge ' + pubCls + '">' + pubLbl + '</span>';

    // "Import Module" button if there are canvas-only items
    const canvasOnlyItems = mod.items.filter(i => !i.local_path);
    if (canvasOnlyItems.length > 0) {
      h += '<button class="action-btn import-btn module-import-btn" onclick="event.stopPropagation();doImportModule(' + mi + ')" title="Import all '
        + canvasOnlyItems.length + ' Canvas-only items in this module">Import Module &#x2193; (' + canvasOnlyItems.length + ')</button>';
    }

    h += '<span class="count">' + localCount + '/' + mod.items.length + ' local</span>';
    h += '</div>';
    h += '<div class="module-items" id="items-' + mi + '">';

    // Find local module dir for import (first matching item's dir, or guess from module name)
    const modDirGuess = mod.items.find(i => i.local_path)?.local_path?.split('/')[0]
      || ((mi + 1).toString().padStart(2, '0') + '_' + mod.name.replace(/[^a-zA-Z0-9åäöÅÄÖ ]/g, '').replace(/ /g, '_'));

    for (const item of mod.items) {
      const icon = TYPE_ICONS[item.type] || '&#x1F4E6;';
      const hasLocal = !!item.local_path;
      const dotCls = hasLocal ? 'local' : 'canvas-only';
      const unpubCls = item.published ? '' : ' unpublished';
      const clickCls = (hasLocal || item.html_url) ? ' clickable' : '';
      const safePath = hasLocal ? esc(item.local_path!.replace(/\\/g, '/')) : '';
      let titleClick = '';
      if (hasLocal) {
        titleClick = ' onclick="openFile(\'' + safePath.replace(/'/g, "\\'") + '\')"';
      } else if (item.html_url) {
        titleClick = ' onclick="openUrl(\'' + esc(item.html_url).replace(/'/g, "\\'") + '\')"';
      }

      // Build import data for canvas-only items (used by checkbox selection)
      const importDataObj = !hasLocal ? {
        module_dir: modDirGuess,
        item_type: item.type,
        content_id: item.content_id || null,
        page_url: item.page_url || null,
        title: item.title,
        published: item.published,
        indent: item.indent,
        external_url: item.external_url || '',
      } : null;

      // 7 grid cells: checkbox, dot, icon, title, badge, path, actions
      const dataKind = hasLocal ? 'sync' : 'import';
      const dataVal = hasLocal ? safePath : esc(JSON.stringify(importDataObj));
      h += '<div class="item' + clickCls + '" data-kind="' + dataKind + '" data-value="' + dataVal.replace(/"/g, '&quot;') + '">';
      h += '<span class="cb-cell"><input type="checkbox" class="item-cb" onclick="event.stopPropagation();onCheckChanged()" data-kind="' + dataKind + '" data-value="' + dataVal.replace(/"/g, '&quot;') + '"></span>';
      h += '<span class="status-dot ' + dotCls + unpubCls + '"></span>';
      h += '<span class="icon">' + icon + '</span>';
      h += '<span class="title"' + titleClick + '>' + esc(item.title) + '</span>';
      h += '<span class="type-badge">' + item.type + '</span>';
      const pathText = hasLocal ? esc(item.local_path!) : (item.external_url ? esc(item.external_url) : '');
      h += '<span class="local-path" title="' + pathText + '">' + pathText + '</span>';

      // Action buttons
      h += '<span class="actions">';
      if (hasLocal) {
        // Diff + Sync buttons
        h += '<button class="action-btn diff-btn" onclick="event.stopPropagation();doDiff(\''
          + safePath.replace(/'/g, "\\'") + '\')" title="Compare with Canvas">Diff</button>';
        h += '<button class="action-btn sync-btn" onclick="event.stopPropagation();doSync(\''
          + safePath.replace(/'/g, "\\'") + '\')" title="Upload to Canvas">Sync &#x2191;</button>';
      } else {
        // Import button (only for canvas-only items)
        const importData = esc(JSON.stringify(importDataObj));
        h += '<button class="action-btn import-btn" onclick="event.stopPropagation();doImport(\''
          + importData.replace(/'/g, '&#39;') + '\')" title="Import from Canvas">Import &#x2193;</button>';
      }
      h += '</span>';
      h += '</div>';
    }

    h += '</div></div>';

    // Hidden data for module-level import
    if (canvasOnlyItems.length > 0) {
      const moduleImportItems = canvasOnlyItems.map(item => ({
        module_dir: modDirGuess,
        item_type: item.type,
        content_id: item.content_id || null,
        page_url: item.page_url || null,
        title: item.title,
        published: item.published,
        indent: item.indent,
        external_url: item.external_url || '',
      }));
      h += '<script>if(!window._moduleImportData)window._moduleImportData={};window._moduleImportData[' + mi + ']='
        + JSON.stringify(JSON.stringify(moduleImportItems)) + ';</script>';
    }
  }

  // Batch action bar (hidden by default, shown when items are checked)
  h += '<div id="batch-bar" class="batch-bar hidden">';
  h += '<span id="batch-count">0 selected</span>';
  h += '<button class="action-btn sync-btn" onclick="doBatchSync()" id="batch-sync-btn" style="display:none">Sync selected &#x2191;</button>';
  h += '<button class="action-btn import-btn" onclick="doBatchImport()" id="batch-import-btn" style="display:none">Import selected &#x2193;</button>';
  h += '<button class="action-btn" onclick="clearSelection()">Clear</button>';
  h += '</div>';

  // Unmatched local files
  if (data.unmatched_local_files && data.unmatched_local_files.length > 0) {
    h += '<div class="unmatched-section">';
    h += '<div class="section-header">Local files not on Canvas (' + data.unmatched_local_files.length + ')</div>';
    for (const f of data.unmatched_local_files) {
      const safeF = esc(f.replace(/\\/g, '/'));
      h += '<div class="unmatched-item" onclick="openFile(\'' + safeF.replace(/'/g, "\\'") + '\')">'
        + esc(f) + '</div>';
    }
    h += '</div>';
  }

  return h;
}

function wrapHtml(body: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);background:var(--vscode-editor-background);padding:16px 24px;line-height:1.5}
.header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid var(--vscode-widget-border)}
.header h1{font-size:18px;font-weight:600}
.header .subtitle{font-size:12px;color:var(--vscode-descriptionForeground);margin-top:2px}
.refresh-btn{background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;padding:6px 14px;border-radius:4px;cursor:pointer;font-size:12px}
.refresh-btn:hover{background:var(--vscode-button-hoverBackground)}
.legend{display:flex;gap:16px;margin-bottom:16px;font-size:12px;color:var(--vscode-descriptionForeground)}
.legend-item{display:flex;align-items:center;gap:4px}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.dot.local{background:#198754}.dot.canvas-only{background:#dc3545}.dot.unpublished{background:#6c757d}
.module{margin-bottom:16px;border:1px solid var(--vscode-widget-border);border-radius:6px;overflow:hidden}
.module-header{background:var(--vscode-sideBar-background);padding:10px 14px;font-weight:600;font-size:14px;display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none}
.module-header:hover{background:var(--vscode-list-hoverBackground)}
.module-header .toggle{font-size:10px;transition:transform 0.15s}
.module-header .toggle.collapsed{transform:rotate(-90deg)}
.module-header .count{font-size:11px;color:var(--vscode-descriptionForeground);font-weight:400;margin-left:auto}
.pub-badge{font-size:10px;padding:1px 6px;border-radius:3px;font-weight:400}
.pub-badge.published{background:rgba(25,135,84,0.15);color:#198754}
.pub-badge.draft{background:rgba(108,117,125,0.15);color:#6c757d}
.module-items{padding:4px 0;display:grid;grid-template-columns:22px 12px 24px 1fr 80px minmax(100px,300px) auto;align-items:center;row-gap:1px}.module-items.hidden{display:none}
.item{display:contents;cursor:default;font-size:13px}
.item>*{padding:4px 0}
.item:hover>*{background:var(--vscode-list-hoverBackground)}
.item.clickable{cursor:pointer}
.item .icon{font-size:14px;text-align:center;padding-left:4px}
.item .title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-left:6px;padding-right:8px}
.item .type-badge{font-size:10px;padding:2px 8px;border-radius:3px;background:var(--vscode-badge-background);color:var(--vscode-badge-foreground);text-align:center;width:80px;justify-self:end}
.item .status-dot{width:8px;height:8px;border-radius:50%;justify-self:center}
.item .status-dot.local{background:#198754}.item .status-dot.canvas-only{background:#dc3545}.item .status-dot.unpublished{opacity:0.5}
.item .local-path{font-size:11px;color:var(--vscode-descriptionForeground);padding-left:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:320px;text-align:right}
.item .actions{display:flex;gap:4px;padding-right:10px;padding-left:6px;justify-self:end}
.action-btn{background:none;border:1px solid var(--vscode-button-secondaryBackground, #333);color:var(--vscode-foreground);padding:2px 8px;border-radius:3px;cursor:pointer;font-size:11px;white-space:nowrap;display:inline-flex;align-items:center;gap:3px}
.action-btn:hover{background:var(--vscode-button-secondaryHoverBackground, #444)}
.action-btn.import-btn{border-color:#0d6efd;color:#6ea8fe}
.action-btn.import-btn:hover{background:rgba(13,110,253,0.15)}
.action-btn.sync-btn{border-color:#198754;color:#75b798}
.action-btn.sync-btn:hover{background:rgba(25,135,84,0.15)}
.action-btn.diff-btn{border-color:#ffc107;color:#ffda6a}
.action-btn.diff-btn:hover{background:rgba(255,193,7,0.15)}
.unmatched-section{margin-top:24px;border:1px solid var(--vscode-widget-border);border-radius:6px;overflow:hidden}
.unmatched-section .section-header{background:var(--vscode-sideBar-background);padding:10px 14px;font-weight:600;font-size:14px;color:var(--vscode-descriptionForeground)}
.unmatched-item{padding:5px 14px 5px 20px;font-size:13px;color:var(--vscode-descriptionForeground);cursor:pointer}
.unmatched-item:hover{background:var(--vscode-list-hoverBackground)}
.loading,.error-msg{padding:40px;text-align:center;font-size:14px}
.error-msg{color:var(--vscode-errorForeground);white-space:pre-wrap}
.stats{display:flex;gap:20px;margin-bottom:16px;font-size:13px}
.stat{display:flex;align-items:center;gap:6px}
.stat .num{font-weight:600;font-size:18px}
.cb-cell{display:flex;align-items:center;justify-content:center}
.item-cb{cursor:pointer;width:14px;height:14px;accent-color:#0d6efd}
.module-import-btn{font-size:11px;padding:2px 8px;margin-left:8px}
.batch-bar{position:fixed;bottom:0;left:0;right:0;background:var(--vscode-sideBar-background);border-top:2px solid var(--vscode-focusBorder);padding:10px 24px;display:flex;align-items:center;gap:12px;z-index:100;font-size:13px}
.batch-bar.hidden{display:none}
#batch-count{font-weight:600;min-width:90px}
</style>
</head>
<body>
<div id="app">${body}</div>
<script>
const vscode=acquireVsCodeApi();
function toggleModule(i){var el=document.getElementById("items-"+i),t=document.getElementById("toggle-"+i);el.classList.toggle("hidden");t.classList.toggle("collapsed")}
function openFile(p){vscode.postMessage({type:"openFile",path:p})}
function refresh(){vscode.postMessage({type:"refresh"})}
function openUrl(u){vscode.postMessage({type:"openUrl",url:u})}
function doDiff(p){vscode.postMessage({type:"diff",localPath:p})}
function doSync(p){vscode.postMessage({type:"sync",localPath:p})}
function doImport(jsonStr){try{var d=JSON.parse(jsonStr);vscode.postMessage({type:"import",itemData:d})}catch(e){console.error(e)}}
function doImportModule(mi){
  if(!window._moduleImportData||!window._moduleImportData[mi])return;
  var items=JSON.parse(window._moduleImportData[mi]);
  if(!confirm('Import '+items.length+' Canvas-only item(s) from this module?'))return;
  vscode.postMessage({type:"importModule",items:items});
}
function onCheckChanged(){
  var cbs=document.querySelectorAll('.item-cb:checked');
  var bar=document.getElementById('batch-bar');
  var countEl=document.getElementById('batch-count');
  var syncBtn=document.getElementById('batch-sync-btn');
  var importBtn=document.getElementById('batch-import-btn');
  var syncCount=0,importCount=0;
  cbs.forEach(function(cb){if(cb.dataset.kind==='sync')syncCount++;else importCount++;});
  var total=syncCount+importCount;
  if(total===0){bar.classList.add('hidden');return;}
  bar.classList.remove('hidden');
  countEl.textContent=total+' selected';
  syncBtn.style.display=syncCount>0?'inline-flex':'none';
  if(syncCount>0)syncBtn.textContent='Sync '+syncCount+' \\u2191';
  importBtn.style.display=importCount>0?'inline-flex':'none';
  if(importCount>0)importBtn.textContent='Import '+importCount+' \\u2193';
}
function doBatchSync(){
  var cbs=document.querySelectorAll('.item-cb:checked[data-kind="sync"]');
  var paths=[];cbs.forEach(function(cb){paths.push(cb.dataset.value);});
  if(paths.length===0)return;
  vscode.postMessage({type:"batchSync",paths:paths});
  clearSelection();
}
function doBatchImport(){
  var cbs=document.querySelectorAll('.item-cb:checked[data-kind="import"]');
  var items=[];cbs.forEach(function(cb){try{items.push(JSON.parse(cb.dataset.value))}catch(e){}});
  if(items.length===0)return;
  vscode.postMessage({type:"batchImport",items:items});
  clearSelection();
}
function clearSelection(){
  document.querySelectorAll('.item-cb:checked').forEach(function(cb){cb.checked=false;});
  onCheckChanged();
}
</script>
</body>
</html>`;
}
