import * as vscode from 'vscode';
import { syncToCanvas } from './commands/syncToCanvas';
import { openPreview } from './commands/openPreview';
import { initCourse } from './commands/initCourse';
import { importFromCanvas } from './commands/importFromCanvas';
import { diffWithCanvas } from './commands/diffWithCanvas';
import { createStatusBar, updateVisibility, dispose as disposeStatusBar } from './providers/statusBar';

export function activate(context: vscode.ExtensionContext) {
  console.log('CanvasQuartoSync extension activated');

  // Status bar
  const statusBar = createStatusBar();
  context.subscriptions.push(statusBar);

  // Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('cqs.syncToCanvas', () =>
      syncToCanvas(context.extensionPath)
    ),
    vscode.commands.registerCommand('cqs.openPreview', () =>
      openPreview()
    ),
    vscode.commands.registerCommand('cqs.initCourse', () =>
      initCourse()
    ),
    vscode.commands.registerCommand('cqs.importFromCanvas', () =>
      importFromCanvas()
    ),
    vscode.commands.registerCommand('cqs.diffWithCanvas', () =>
      diffWithCanvas()
    )
  );

  // Re-check status bar visibility when workspace folders change
  context.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders(() => updateVisibility())
  );
}

export function deactivate() {
  disposeStatusBar();
}
