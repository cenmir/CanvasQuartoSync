import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import type { Comment } from '../preprocessing/commentParser';
import {
  extractComments, serializeComments, anchorComments,
  injectCommentHighlights, generateCommentId,
  locatePosition, extractContext,
} from '../preprocessing/commentParser';

/**
 * Comment management hook — adapted from MDViewer for VS Code.
 * Uses postMessage to the extension host for file I/O instead of Tauri invoke.
 */
export function useComments(
  rawContent: string,
  vscodeApi: { postMessage(msg: any): void }
) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [showComments, setShowComments] = useState(true);
  const cleanContentRef = useRef('');
  const rawContentRef = useRef('');

  // Parse comments when content changes
  useEffect(() => {
    if (!rawContent) {
      setComments([]);
      cleanContentRef.current = '';
      rawContentRef.current = '';
      setIsDirty(false);
      return;
    }
    const { cleanContent, comments: parsed } = extractComments(rawContent);
    cleanContentRef.current = cleanContent;
    rawContentRef.current = rawContent;
    const anchored = anchorComments(cleanContent, parsed);
    setComments(anchored);
    setIsDirty(false);
  }, [rawContent]);

  const cleanContent = useMemo(() => {
    if (!rawContent) return '';
    return cleanContentRef.current || extractComments(rawContent).cleanContent;
  }, [rawContent]);

  const displayContent = useMemo(() => {
    if (!showComments || comments.length === 0) return cleanContent;
    return injectCommentHighlights(cleanContent, comments);
  }, [cleanContent, comments, showComments]);

  const addComment = useCallback((targetText: string, charOffset: number, body: string) => {
    const clean = cleanContentRef.current;
    const { section, paragraph } = locatePosition(clean, charOffset);
    const { contextBefore, contextAfter } = extractContext(clean, charOffset, targetText.length);
    const now = new Date().toISOString().slice(0, 10);

    const newComment: Comment = {
      id: generateCommentId(), section, paragraph, targetText,
      contextBefore, contextAfter, body,
      createdAt: now, updatedAt: now, _offset: charOffset,
    };

    setComments(prev => anchorComments(clean, [...prev, newComment]));
    setIsDirty(true);
  }, []);

  const deleteComment = useCallback((id: string) => {
    setComments(prev => prev.filter(c => c.id !== id));
    setIsDirty(true);
  }, []);

  const saveComments = useCallback(() => {
    const newContent = serializeComments(rawContentRef.current, comments);
    // Send to extension host to write to disk
    vscodeApi.postMessage({ type: 'saveComment', content: newContent });
    rawContentRef.current = newContent;
    setIsDirty(false);
  }, [comments, vscodeApi]);

  const toggleShowComments = useCallback(() => {
    setShowComments(prev => !prev);
  }, []);

  return {
    comments, showComments, isDirty, cleanContent, displayContent,
    addComment, deleteComment, saveComments, toggleShowComments,
  };
}
