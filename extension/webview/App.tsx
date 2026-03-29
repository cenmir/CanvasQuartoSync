import React, { useMemo, useEffect, useState, useCallback } from 'react';
import { useFileContent } from './hooks/useFileContent';
import { useComments } from './hooks/useComments';
import MarkdownRenderer, { setVsCodeApi } from './components/MarkdownRenderer';
import CommentInput from './components/CommentInput';
import { preprocessQmd } from './preprocessing/qmdPreprocess';
import { extractComments } from './preprocessing/commentParser';
import './styles/markdown.css';
import './styles/comments.css';

declare function acquireVsCodeApi(): { postMessage(msg: any): void };
const vscode = acquireVsCodeApi();
setVsCodeApi(vscode);

export default function App() {
  const fileContent = useFileContent();
  const { comments, showComments, isDirty, displayContent, addComment,
    deleteComment, saveComments, toggleShowComments } = useComments(
    fileContent?.content ?? '', vscode
  );

  // Preprocess the display content (with comment highlights injected)
  const processed = useMemo(() => {
    if (!displayContent) return '';
    return preprocessQmd(displayContent);
  }, [displayContent]);

  // Signal ready
  useEffect(() => { vscode.postMessage({ type: 'ready' }); }, []);

  // --- Comment selection state ---
  const [selection, setSelection] = useState<{
    text: string; offset: number; rect: { top: number; left: number };
  } | null>(null);
  const [commentInput, setCommentInput] = useState<{
    top: number; left: number;
  } | null>(null);
  const [viewingComment, setViewingComment] = useState<{
    comment: typeof comments[0]; rect: { top: number; left: number };
  } | null>(null);

  // Show "Add comment" button when text is selected in the preview
  const handleMouseUp = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.toString().trim()) {
      setSelection(null);
      return;
    }

    const text = sel.toString();
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // Find char offset of selection in the clean content
    const { cleanContent } = extractComments(fileContent?.content ?? '');
    const offset = cleanContent.indexOf(text);

    if (offset !== -1) {
      setSelection({
        text,
        offset,
        rect: { top: rect.bottom + window.scrollY + 4, left: rect.left + rect.width / 2 },
      });
    }
  }, [fileContent?.content]);

  // Handle clicking on an existing comment highlight
  const handleCommentClick = useCallback((commentId: string, rect: DOMRect) => {
    const comment = comments.find(c => c.id === commentId);
    if (comment) {
      setViewingComment({
        comment,
        rect: { top: rect.bottom + window.scrollY + 4, left: rect.left },
      });
    }
  }, [comments]);

  const handleAddComment = useCallback(() => {
    if (selection) {
      setCommentInput(selection.rect);
    }
  }, [selection]);

  const handleSubmitComment = useCallback((body: string) => {
    if (selection) {
      addComment(selection.text, selection.offset, body);
      setSelection(null);
      setCommentInput(null);
      // Auto-save after adding
      setTimeout(() => saveComments(), 100);
    }
  }, [selection, addComment, saveComments]);

  if (!fileContent) {
    return (
      <div className="loading">
        <p>Open a .qmd file and the preview will appear here.</p>
      </div>
    );
  }

  return (
    <div onMouseUp={handleMouseUp}>
      {/* Comment toolbar */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: '#fff', borderBottom: '1px solid #ddd',
        padding: '4px 16px', display: 'flex', gap: '8px', alignItems: 'center',
        fontSize: '0.8rem',
      }}>
        <button className={`comment-btn ${showComments ? 'comment-btn-primary' : ''}`}
          onClick={toggleShowComments} title="Toggle comment highlights">
          {showComments ? '💬 Comments ON' : '💬 Comments OFF'}
        </button>
        {comments.length > 0 && (
          <span style={{ color: '#6b6b6b' }}>{comments.length} comment{comments.length !== 1 ? 's' : ''}</span>
        )}
        {isDirty && (
          <button className="comment-btn comment-btn-primary" onClick={saveComments}>
            Save comments
          </button>
        )}
      </div>

      <MarkdownRenderer
        content={processed}
        imageMap={fileContent.imageMap}
        onCommentClick={handleCommentClick}
      />

      {/* "Add comment" button appears on text selection */}
      {selection && !commentInput && (
        <button
          className="add-comment-btn"
          style={{ top: selection.rect.top, left: selection.rect.left }}
          onClick={handleAddComment}
        >
          💬 Add comment
        </button>
      )}

      {/* Comment input popup */}
      {commentInput && (
        <CommentInput
          position={commentInput}
          onSubmit={handleSubmitComment}
          onCancel={() => { setCommentInput(null); setSelection(null); }}
        />
      )}

      {/* Viewing existing comment popup */}
      {viewingComment && (
        <div className="comment-popup"
          style={{ top: viewingComment.rect.top, left: viewingComment.rect.left }}>
          <div className="comment-popup-target">"{viewingComment.comment.targetText}"</div>
          <div className="comment-popup-body">{viewingComment.comment.body}</div>
          <div className="comment-popup-date">{viewingComment.comment.updatedAt}</div>
          <div className="comment-popup-actions">
            <button className="comment-btn" onClick={() => {
              deleteComment(viewingComment.comment.id);
              setViewingComment(null);
              setTimeout(() => saveComments(), 100);
            }}>Delete</button>
            <button className="comment-btn" onClick={() => setViewingComment(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
