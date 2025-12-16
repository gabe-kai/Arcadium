import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { Editor } from '../components/editor/Editor';
import { EditorToolbar } from '../components/editor/EditorToolbar';
import { MetadataForm } from '../components/editor/MetadataForm';
import { usePage, createPage, updatePage } from '../services/api/pages';
import { htmlToMarkdown, markdownToHtml } from '../utils/markdown';

/**
 * EditPage component - WYSIWYG editor for creating/editing pages
 */
export function EditPage() {
  const { pageId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isNewPage = !pageId || pageId === 'new';
  
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [metadata, setMetadata] = useState({
    title: '',
    slug: '',
    parent_id: null,
    section: null,
    order: null,
    status: 'draft',
  });
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [editor, setEditor] = useState(null);
  const editorRef = useRef(null);
  const autoSaveTimerRef = useRef(null);

  // Load page if editing existing page
  const { data: page, isLoading: isLoadingPage } = usePage(isNewPage ? null : pageId);

  // Handle editor ready
  const handleEditorReady = (editorInstance) => {
    setEditor(editorInstance);
  };

  // Load page content and metadata into editor
  useEffect(() => {
    if (page && editor && !hasUnsavedChanges) {
      setTitle(page.title || '');
      setMetadata({
        title: page.title || '',
        slug: page.slug || '',
        parent_id: page.parent_id || null,
        section: page.section || null,
        order: page.order !== undefined ? page.order : null,
        status: page.status || 'draft',
      });
      if (page.content) {
        // Convert markdown to HTML for editor
        const html = markdownToHtml(page.content);
        editor.commands.setContent(html);
        setContent(html);
      }
    }
  }, [page, editor, hasUnsavedChanges]);

  // Auto-save to localStorage
  useEffect(() => {
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    if (hasUnsavedChanges && (metadata.title || content)) {
      autoSaveTimerRef.current = setTimeout(() => {
        const draftKey = isNewPage ? 'arcadium_draft_new' : `arcadium_draft_${pageId}`;
        const draft = {
          title: metadata.title,
          content,
          metadata,
          timestamp: Date.now(),
        };
        try {
          localStorage.setItem(draftKey, JSON.stringify(draft));
        } catch (e) {
          console.warn('Failed to save draft to localStorage:', e);
        }
      }, 2000); // Auto-save after 2 seconds of inactivity
    }

    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [metadata, content, hasUnsavedChanges, isNewPage, pageId]);

  // Load draft from localStorage on mount
  useEffect(() => {
    if (isNewPage) {
      const draftKey = 'arcadium_draft_new';
      try {
        const draftJson = localStorage.getItem(draftKey);
        if (draftJson) {
          const draft = JSON.parse(draftJson);
          setTitle(draft.title || '');
          setContent(draft.content || '');
          if (draft.metadata) {
            setMetadata(draft.metadata);
          }
          setHasUnsavedChanges(true);
        }
      } catch (e) {
        console.warn('Failed to load draft from localStorage:', e);
      }
    }
  }, [isNewPage]);

  // Create page mutation
  const createMutation = useMutation({
    mutationFn: (pageData) => createPage(pageData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['page', data.id] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
      navigate(`/pages/${data.id}`);
    },
  });

  // Update page mutation
  const updateMutation = useMutation({
    mutationFn: ({ pageId, pageData }) => updatePage(pageId, pageData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
      setHasUnsavedChanges(false);
      // Optionally show success message
    },
  });

  const handleSave = async () => {
    if (!metadata.title || !metadata.title.trim()) {
      alert('Please enter a page title');
      return;
    }

    if (!metadata.slug || !metadata.slug.trim()) {
      alert('Please enter a valid slug');
      return;
    }

    if (!editorRef.current) return;

    const html = content || editorRef.current.getHTML();
    const markdown = htmlToMarkdown(html);

    // Clear draft from localStorage on successful save
    const clearDraft = () => {
      const draftKey = isNewPage ? 'arcadium_draft_new' : `arcadium_draft_${pageId}`;
      try {
        localStorage.removeItem(draftKey);
      } catch (e) {
        console.warn('Failed to clear draft from localStorage:', e);
      }
    };

    const pageData = {
      title: metadata.title.trim(),
      slug: metadata.slug.trim(),
      content: markdown,
      status: metadata.status,
    };

    // Add optional fields if they have values
    if (metadata.parent_id) {
      pageData.parent_id = metadata.parent_id;
    }
    if (metadata.section) {
      pageData.section = metadata.section.trim();
    }
    if (metadata.order !== null && metadata.order !== undefined) {
      pageData.order = metadata.order;
    }

    if (isNewPage) {
      createMutation.mutate(pageData, {
        onSuccess: clearDraft,
      });
    } else {
      updateMutation.mutate(
        {
          pageId,
          pageData,
        },
        {
          onSuccess: clearDraft,
        }
      );
    }
  };

  const handleMetadataChange = (newMetadata) => {
    setMetadata(newMetadata);
    setTitle(newMetadata.title || '');
    setHasUnsavedChanges(true);
  };

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      if (!confirm('You have unsaved changes. Are you sure you want to leave?')) {
        return;
      }
    }
    if (isNewPage) {
      navigate('/');
    } else {
      navigate(`/pages/${pageId}`);
    }
  };

  if (isLoadingPage && !isNewPage) {
    return (
      <Layout sidebar={<Sidebar />}>
        <div>Loading page...</div>
      </Layout>
    );
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-edit-page">
        <div className="arc-edit-page-header">
          <h2 className="arc-edit-page-header-title">
            {isNewPage ? 'Create New Page' : 'Edit Page'}
          </h2>
          {hasUnsavedChanges && (
            <span className="arc-edit-page-unsaved">Unsaved changes</span>
          )}
        </div>

        {/* Metadata Form */}
        <div className="arc-edit-page-metadata">
          <MetadataForm
            initialData={metadata}
            onChange={handleMetadataChange}
            isNewPage={isNewPage}
            excludePageId={pageId}
          />
        </div>

        <div className="arc-edit-page-toolbar-wrapper">
          {editor && <EditorToolbar editor={editor} />}
        </div>

        <div className="arc-edit-page-editor-wrapper">
          <Editor
            ref={editorRef}
            content={page?.content || ''}
            onEditorReady={handleEditorReady}
            onChange={(html) => {
              setContent(html);
              setHasUnsavedChanges(true);
            }}
          />
        </div>

        <div className="arc-edit-page-actions">
          <button
            type="button"
            onClick={handleCancel}
            className="arc-edit-page-button arc-edit-page-button-cancel"
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="arc-edit-page-button arc-edit-page-button-save"
            disabled={isSaving || !metadata.title?.trim() || !metadata.slug?.trim()}
          >
            {isSaving ? 'Saving...' : isNewPage ? 'Create Page' : 'Save Changes'}
          </button>
        </div>
      </div>
    </Layout>
  );
}
