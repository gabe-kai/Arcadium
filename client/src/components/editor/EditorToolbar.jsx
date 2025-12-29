import React, { useState, useEffect } from 'react';
import { useEditor } from '@tiptap/react';
import { LinkDialog } from './LinkDialog';
import { ImageUploadDialog } from './ImageUploadDialog';
import { TableDialog } from './TableDialog';

/**
 * Editor Toolbar Component
 * Provides formatting buttons for the Tiptap editor
 */
export function EditorToolbar({ editor, pageId }) {
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [showImageDialog, setShowImageDialog] = useState(false);
  const [showTableDialog, setShowTableDialog] = useState(false);
  const [isInTable, setIsInTable] = useState(false);

  if (!editor) {
    return null;
  }

  // Track table state reactively - check on every selection/update
  useEffect(() => {
    const updateTableState = () => {
      try {
        // Method 1: Check if table commands are available (most reliable)
        const canAddColumn = editor.can().addColumnBefore() || editor.can().addColumnAfter();
        const canAddRow = editor.can().addRowBefore() || editor.can().addRowAfter();

        // Method 2: Use isActive
        const isActiveTable = editor.isActive('tableCell') || editor.isActive('tableHeader') || editor.isActive('table');

        // Method 3: Check selection's parent nodes
        let inTableByNode = false;
        try {
          const { selection } = editor.state;
          const { $anchor } = selection;

          // Walk up the node tree to find a table
          for (let depth = $anchor.depth; depth > 0; depth--) {
            const node = $anchor.node(depth);
            const nodeType = node.type.name;
            if (nodeType === 'table' ||
                nodeType === 'tableCell' ||
                nodeType === 'tableHeader' ||
                nodeType === 'tableRow') {
              inTableByNode = true;
              break;
            }
          }
        } catch (e) {
          // Ignore errors in node traversal
        }

        // If any method indicates we're in a table, we are
        const inTable = canAddColumn || canAddRow || isActiveTable || inTableByNode;

        setIsInTable(inTable);
      } catch (error) {
        // Fallback to false on error
        setIsInTable(false);
      }
    };

    // Update on selection changes and content updates
    const handleSelectionUpdate = () => updateTableState();
    const handleUpdate = () => updateTableState();
    const handleFocus = () => updateTableState();
    const handleClick = () => {
      // Small delay to ensure selection is updated
      setTimeout(updateTableState, 10);
    };

    // Use Tiptap's event system
    if (editor.view && editor.view.dom) {
      editor.view.dom.addEventListener('focus', handleFocus);
      editor.view.dom.addEventListener('click', handleClick);
      editor.view.dom.addEventListener('keydown', handleSelectionUpdate);
    }

    // Listen to editor events (if available)
    if (typeof editor.on === 'function') {
      editor.on('selectionUpdate', handleSelectionUpdate);
      editor.on('update', handleUpdate);
      editor.on('focus', handleFocus);
    }

    // Initial check
    updateTableState();

    return () => {
      if (typeof editor.off === 'function') {
        editor.off('selectionUpdate', handleSelectionUpdate);
        editor.off('update', handleUpdate);
        editor.off('focus', handleFocus);
      }
      if (editor.view && editor.view.dom) {
        editor.view.dom.removeEventListener('focus', handleFocus);
        editor.view.dom.removeEventListener('click', handleClick);
        editor.view.dom.removeEventListener('keydown', handleSelectionUpdate);
      }
    };
  }, [editor]);

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
      // VITE_WIKI_API_BASE_URL is typically http://localhost:5000/api (with /api)
      const baseURL = import.meta.env.VITE_WIKI_API_BASE_URL || 'http://localhost:5000/api';

      if (url.startsWith('http://') || url.startsWith('https://')) {
        // Already absolute, use as-is
        imageUrl = url;
      } else if (url.startsWith('/api/')) {
        // URL already has /api prefix (e.g., /api/uploads/images/...)
        // Remove /api from baseURL if present, then prepend
        const baseWithoutApi = baseURL.endsWith('/api') ? baseURL.slice(0, -4) : baseURL.replace(/\/api$/, '');
        imageUrl = `${baseWithoutApi}${url}`;
      } else if (url.startsWith('/')) {
        // Relative URL starting with / (e.g., /uploads/images/...)
        // Add /api prefix and prepend base URL (without /api)
        const baseWithoutApi = baseURL.endsWith('/api') ? baseURL.slice(0, -4) : baseURL.replace(/\/api$/, '');
        imageUrl = `${baseWithoutApi}/api${url}`;
      } else {
        // Relative URL without leading / - prepend base URL
        imageUrl = `${baseURL}/${url}`;
      }
      editor.chain().focus().setImage({ src: imageUrl }).run();
    }
  };


  return (
    <div className="arc-editor-toolbar">
      {/* Main Toolbar Row */}
      <div className="arc-editor-toolbar-row">
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
            onClick={() => setShowTableDialog(true)}
            className={isInTable ? 'arc-editor-toolbar-button-active' : ''}
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
      </div>

      {/* Table Controls Row - Only show when inside a table */}
      {isInTable && (
        <div className="arc-editor-toolbar-row arc-editor-toolbar-row-secondary">
          <div className="arc-editor-toolbar-group arc-editor-toolbar-table-controls">
            <button
              type="button"
              onClick={() => editor.chain().focus().addColumnBefore().run()}
              disabled={!editor.can().addColumnBefore()}
              title="Add Column Before"
              className="arc-editor-toolbar-button-small"
            >
              + Col ←
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().addColumnAfter().run()}
              disabled={!editor.can().addColumnAfter()}
              title="Add Column After"
              className="arc-editor-toolbar-button-small"
            >
              + Col →
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().deleteColumn().run()}
              disabled={!editor.can().deleteColumn()}
              title="Delete Column"
              className="arc-editor-toolbar-button-small"
            >
              − Col
            </button>
            <div className="arc-editor-toolbar-separator" />
            <button
              type="button"
              onClick={() => editor.chain().focus().addRowBefore().run()}
              disabled={!editor.can().addRowBefore()}
              title="Add Row Before"
              className="arc-editor-toolbar-button-small"
            >
              + Row ↑
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().addRowAfter().run()}
              disabled={!editor.can().addRowAfter()}
              title="Add Row After"
              className="arc-editor-toolbar-button-small"
            >
              + Row ↓
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().deleteRow().run()}
              disabled={!editor.can().deleteRow()}
              title="Delete Row"
              className="arc-editor-toolbar-button-small"
            >
              − Row
            </button>
            <div className="arc-editor-toolbar-separator" />
            <button
              type="button"
              onClick={() => editor.chain().focus().deleteTable().run()}
              disabled={!editor.can().deleteTable()}
              title="Delete Table"
              className="arc-editor-toolbar-button-small"
            >
              × Table
            </button>
          </div>
        </div>
      )}

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

      <TableDialog
        isOpen={showTableDialog}
        onClose={() => setShowTableDialog(false)}
        onInsert={({ rows, cols, withHeaderRow }) => {
          editor.chain().focus().insertTable({ rows, cols, withHeaderRow }).run();
        }}
      />
    </div>
  );
}
