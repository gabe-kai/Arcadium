import React, { useState } from 'react';
import { useEditor } from '@tiptap/react';
import { LinkDialog } from './LinkDialog';
import { ImageUploadDialog } from './ImageUploadDialog';

/**
 * Editor Toolbar Component
 * Provides formatting buttons for the Tiptap editor
 */
export function EditorToolbar({ editor, pageId }) {
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [showImageDialog, setShowImageDialog] = useState(false);

  if (!editor) {
    return null;
  }

  const setLink = () => {
    setShowLinkDialog(true);
  };

  const previousUrl = editor.getAttributes('link').href || '';

  const handleInsertLink = (url) => {
    if (!url) {
      // Empty URL removes the link
      editor.chain().focus().extendMarkRange('link').unsetLink().run();
      return;
    }

    // Add link
    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
  };

  const addImage = () => {
    setShowImageDialog(true);
  };

  const handleInsertImage = (url) => {
    if (url) {
      // Ensure URL is absolute - if it's relative, make it absolute
      let imageUrl = url;
      if (url.startsWith('/uploads/')) {
        // Relative URL from uploads - prepend API base URL
        const baseURL = import.meta.env.VITE_WIKI_API_BASE_URL || 'http://localhost:5000/api';
        imageUrl = `${baseURL}${url}`;
      } else if (url.startsWith('/') && !url.startsWith('//')) {
        // Other relative URLs - prepend API base URL
        const baseURL = import.meta.env.VITE_WIKI_API_BASE_URL || 'http://localhost:5000/api';
        imageUrl = `${baseURL}${url}`;
      }
      // If already absolute (http:// or https://), use as-is
      editor.chain().focus().setImage({ src: imageUrl }).run();
    }
  };

  return (
    <div className="arc-editor-toolbar">
      {/* Format Dropdown */}
      <select
        value={editor.getAttributes('heading').level || 'paragraph'}
        onChange={(e) => {
          const value = e.target.value;
          if (value === 'paragraph') {
            editor.chain().focus().setParagraph().run();
          } else {
            editor.chain().focus().toggleHeading({ level: parseInt(value) }).run();
          }
        }}
        className="arc-editor-toolbar-select"
      >
        <option value="paragraph">Paragraph</option>
        <option value="1">Heading 1</option>
        <option value="2">Heading 2</option>
        <option value="3">Heading 3</option>
        <option value="4">Heading 4</option>
        <option value="5">Heading 5</option>
        <option value="6">Heading 6</option>
      </select>

      {/* Text Formatting */}
      <div className="arc-editor-toolbar-group">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          disabled={!editor.can().chain().focus().toggleBold().run()}
          className={editor.isActive('bold') ? 'arc-editor-toolbar-button-active' : ''}
          title="Bold (Ctrl+B)"
        >
          <strong>B</strong>
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          disabled={!editor.can().chain().focus().toggleItalic().run()}
          className={editor.isActive('italic') ? 'arc-editor-toolbar-button-active' : ''}
          title="Italic (Ctrl+I)"
        >
          <em>I</em>
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleCode().run()}
          disabled={!editor.can().chain().focus().toggleCode().run()}
          className={editor.isActive('code') ? 'arc-editor-toolbar-button-active' : ''}
          title="Inline Code"
        >
          {'</>'}
        </button>
      </div>

      {/* Lists */}
      <div className="arc-editor-toolbar-group">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={editor.isActive('bulletList') ? 'arc-editor-toolbar-button-active' : ''}
          title="Bullet List"
        >
          • List
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={editor.isActive('orderedList') ? 'arc-editor-toolbar-button-active' : ''}
          title="Numbered List"
        >
          1. List
        </button>
      </div>

      {/* Links and Media */}
      <div className="arc-editor-toolbar-group">
        <button
          type="button"
          onClick={setLink}
          className={editor.isActive('link') ? 'arc-editor-toolbar-button-active' : ''}
          title="Insert Link"
        >
          🔗 Link
        </button>
        <button
          type="button"
          onClick={addImage}
          title="Insert Image"
        >
          🖼️ Image
        </button>
      </div>

      {/* Code Block and Table */}
      <div className="arc-editor-toolbar-group">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={editor.isActive('codeBlock') ? 'arc-editor-toolbar-button-active' : ''}
          title="Code Block"
        >
          {'</>'} Code
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
          title="Insert Table"
        >
          ⧉ Table
        </button>
      </div>

      {/* Undo/Redo */}
      <div className="arc-editor-toolbar-group">
        <button
          type="button"
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().chain().focus().undo().run()}
          title="Undo (Ctrl+Z)"
        >
          ↶ Undo
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().chain().focus().redo().run()}
          title="Redo (Ctrl+Y)"
        >
          ↷ Redo
        </button>
      </div>

      <LinkDialog
        isOpen={showLinkDialog}
        onClose={() => setShowLinkDialog(false)}
        onInsert={handleInsertLink}
        initialUrl={previousUrl}
      />

      <ImageUploadDialog
        isOpen={showImageDialog}
        onClose={() => setShowImageDialog(false)}
        onInsert={handleInsertImage}
        pageId={pageId}
      />
    </div>
  );
}
