import * as vscode from 'vscode';
import * as path from 'path';
import { resolvePython, resolveCqsRoot } from '../python/venvResolver';
import { runPythonScript } from '../python/runner';
import { getWorkspaceRoot } from '../config/configLoader';
import { setSyncing } from '../providers/statusBar';

export async function syncToCanvas(extensionPath: string): Promise<void> {
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    vscode.window.showErrorMessage('No workspace folder open.');
    return;
  }

  const pythonPath = resolvePython();
  if (!pythonPath) {
    const action = await vscode.window.showErrorMessage(
      'Python virtual environment not found. Run install.ps1 first, or configure cqs.pythonVenvPath in settings.',
      'Open Settings'
    );
    if (action === 'Open Settings') {
      vscode.commands.executeCommand(
        'workbench.action.openSettings',
        'cqs.pythonVenvPath'
      );
    }
    return;
  }

  const cqsRoot = resolveCqsRoot(extensionPath);
  const scriptPath = path.join(cqsRoot, 'sync_to_canvas.py');

  setSyncing(true);

  try {
    const result = await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Syncing to Canvas',
        cancellable: true,
      },
      async (progress, token) => {
        return runPythonScript(
          pythonPath,
          scriptPath,
          [workspaceRoot, '--verbose'],
          workspaceRoot,
          progress,
          token
        );
      }
    );

    if (result.exitCode === 0) {
      vscode.window.showInformationMessage('Canvas sync completed successfully.');
    } else {
      const action = await vscode.window.showErrorMessage(
        `Canvas sync failed (exit code ${result.exitCode}).`,
        'View Output'
      );
      if (action === 'View Output') {
        const channel = vscode.window.createOutputChannel('Canvas Quarto Sync');
        channel.append(result.stdout);
        if (result.stderr) {
          channel.append('\n--- STDERR ---\n');
          channel.append(result.stderr);
        }
        channel.show();
      }
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    vscode.window.showErrorMessage(`Canvas sync error: ${message}`);
  } finally {
    setSyncing(false);
  }
}
