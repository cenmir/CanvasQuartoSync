import * as vscode from 'vscode';

// Placeholder — will be implemented in Phase 2 with the React webview
export async function openPreview(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor || !editor.document.fileName.endsWith('.qmd')) {
    vscode.window.showWarningMessage('Open a .qmd file first.');
    return;
  }

  vscode.window.showInformationMessage(
    'QMD Preview is coming soon. The webview renderer is under development.'
  );
}
