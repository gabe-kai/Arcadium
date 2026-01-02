import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { Editor } from '../components/editor/Editor';
import { EditorToolbar } from '../components/editor/EditorToolbar';
import { MetadataForm } from '../components/editor/MetadataForm';
import { usePage, createPage, updatePage, useVersionHistory } from '../services/api/pages';
import { htmlToMarkdown, markdownToHtml, parseFrontmatter, addFrontmatter } from '../utils/markdown';
import { highlightCodeBlocks } from '../utils/syntaxHighlight';
import { processLinks } from '../utils/linkHandler';
import { useNotificationContext } from '../components/common/NotificationProvider';
import { SyncConflictWarning } from '../components/common/SyncConflictWarning';

/**
 * EditPage component - WYSIWYG editor for creating/editing pages
 */
export function EditPage() {
  const { pageId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useNotificationContext();
  const isNewPage = !pageId || pageId === 'new';

  // Check if we have default values from navigation state (e.g., creating home page)
  const defaultSlug = location.state?.defaultSlug;
  const defaultTitle = location.state?.defaultTitle;

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
  const [showPreview, setShowPreview] = useState(false);
  const editorRef = useRef(null);
  const previewRef = useRef(null);
  const autoSaveTimerRef = useRef(null);
  const metadataLoadedRef = useRef(false);

  // Load page if editing existing page
  const { data: page, isLoading: isLoadingPage } = usePage(isNewPage ? null : pageId);

  // Get current version from page data (API includes version field)
  const currentVersion = page?.version;

  // Handle editor ready
  const handleEditorReady = (editorInstance) => {
    setEditor(editorInstance);
  };

  // Load page content and metadata into editor
  useEffect(() => {
    if (page && editor) {
      // Always load metadata from page (it's separate from content)
      // Only skip if we've already loaded it and user hasn't made changes
      if (!metadataLoadedRef.current || !hasUnsavedChanges) {
        setTitle(page.title || '');
        setMetadata({
          title: page.title || '',
          slug: page.slug || '',
          parent_id: page.parent_id || null,
          section: page.section || null,
          order: page.order !== undefined ? page.order : null,
          status: page.status || 'draft',
        });
        metadataLoadedRef.current = true;
      }

      // Load content only if we haven't loaded it yet or there are no unsaved changes
      if (page.content && (!metadataLoadedRef.current || !hasUnsavedChanges)) {
        // Parse frontmatter to get markdown content (frontmatter should not be in editor)
        const { markdown: markdownContent } = parseFrontmatter(page.content);

        // Convert markdown to HTML for editor (without frontmatter)
        const html = markdownToHtml(markdownContent);
        editor.commands.setContent(html);
        setContent(html);
      }
    }
  }, [page, editor]);

  // Reset metadata loaded flag when pageId changes
  useEffect(() => {
    metadataLoadedRef.current = false;
  }, [pageId]);

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

  // Load draft from localStorage on mount, or use default values
  useEffect(() => {
    if (isNewPage) {
      const draftKey = 'arcadium_draft_new';
      try {
        const draftJson = localStorage.getItem(draftKey);
        if (draftJson) {
          const draft = JSON.parse(draftJson);
          setTitle(draft.title || defaultTitle || '');
          setContent(draft.content || '');
          if (draft.metadata) {
            setMetadata({
              ...draft.metadata,
              slug: draft.metadata.slug || defaultSlug || '',
              title: draft.metadata.title || defaultTitle || '',
            });
          } else if (defaultTitle || defaultSlug) {
            setMetadata({
              title: defaultTitle || '',
              slug: defaultSlug || '',
              parent_id: null,
              section: null,
              order: null,
              status: 'draft',
            });
          }
          setHasUnsavedChanges(true);
        } else if (defaultTitle || defaultSlug) {
          // No draft, but we have default values
          setTitle(defaultTitle || '');
          setMetadata({
            title: defaultTitle || '',
            slug: defaultSlug || '',
            parent_id: null,
            section: null,
            order: null,
            status: 'draft',
          });
        }
      } catch (e) {
        console.warn('Failed to load draft from localStorage:', e);
        // If error loading draft, still set defaults
        if (defaultTitle || defaultSlug) {
          setTitle(defaultTitle || '');
          setMetadata({
            title: defaultTitle || '',
            slug: defaultSlug || '',
            parent_id: null,
            section: null,
            order: null,
            status: 'draft',
          });
        }
      }
    }
  }, [isNewPage, defaultTitle, defaultSlug]);

  // Create page mutation
  const createMutation = useMutation({
    mutationFn: (pageData) => createPage(pageData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['page', data.id] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
      queryClient.invalidateQueries({ queryKey: ['homePageId'] }); // Invalidate home page ID cache
      showSuccess('Page created successfully');
      // If this is the home page, navigate to home, otherwise to the page
      if (data.slug === 'home') {
        navigate('/');
      } else {
        navigate(`/pages/${data.id}`);
      }
    },
    onError: (error) => {
      if (error.response?.status === 401) {
        // Token expired or invalid - error handler in apiClient will redirect
        console.error('Authentication failed. Please sign in again.');
      } else {
        showError(error.response?.data?.error || 'Failed to create page');
      }
    },
  });

  // Update page mutation
  const updateMutation = useMutation({
    mutationFn: ({ pageId, pageData }) => updatePage(pageId, pageData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
      // Invalidate home page cache if this page is or becomes the home page
      const newSlug = metadata.slug; // Use the slug from the request metadata
      const wasHomePage = page?.slug === 'home';
      const isHomePage = newSlug === 'home';
      if (wasHomePage || isHomePage) {
        queryClient.invalidateQueries({ queryKey: ['homePageId'] });
      }
      setHasUnsavedChanges(false);

      // Show conflict warning if present in response
      if (data.sync_conflict) {
        // Conflict warning will be shown via the page data refresh
        // Don't navigate immediately if there's a conflict, let user see the warning
        queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      }

      showSuccess('Page saved successfully');
      // Navigate to view mode after successful save
      // If this is the home page (slug: "home"), navigate to home, otherwise to the page
      if (isHomePage) {
        navigate('/');
      } else {
        navigate(`/pages/${pageId}`);
      }
    },
    onError: (error) => {
      if (error.response?.status === 401) {
        // Token expired or invalid - error handler in apiClient will redirect
        console.error('Authentication failed. Please sign in again.');
      } else {
        showError(error.response?.data?.error || 'Failed to update page');
      }
    },
  });

  const handleSave = async () => {
    if (!metadata.title || !metadata.title.trim()) {
      showError('Please enter a page title');
      return;
    }

    if (!metadata.slug || !metadata.slug.trim()) {
      showError('Please enter a valid slug');
      return;
    }

    if (!editorRef.current) return;

    const html = content || editorRef.current.getHTML();
    const markdown = htmlToMarkdown(html);

    // Reconstruct frontmatter from metadata and prepend to markdown
    // Preserve any existing frontmatter fields (e.g., custom fields from AI system)
    // Frontmatter is needed for AI content management system but hidden from editor
    const originalContent = page?.content || null;
    const contentWithFrontmatter = addFrontmatter(metadata, markdown, originalContent);

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
      content: contentWithFrontmatter,  // Include frontmatter for AI system
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
    // Only update if metadata actually changed to prevent unnecessary re-renders
    setMetadata((prevMetadata) => {
      // Compare objects to avoid unnecessary updates
      if (JSON.stringify(prevMetadata) === JSON.stringify(newMetadata)) {
        return prevMetadata;
      }
      setHasUnsavedChanges(true);
      return newMetadata;
    });
    // Update title state if it changed
    if (newMetadata.title !== title) {
      setTitle(newMetadata.title || '');
    }
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
      <div className="arc-content-wrapper">
        <div className="arc-content-scrollable">
          <div className="arc-edit-page">
        <div className="arc-edit-page-header">
          <div className="arc-edit-page-header-top">
            <h2 className="arc-edit-page-header-title">
              {isNewPage ? 'Create New Page' : 'Edit Page'}
            </h2>
            {!isNewPage && currentVersion && (
              <div className="arc-edit-page-version-info">
                <span className="arc-edit-page-version-label">Version:</span>
                <span className="arc-edit-page-version-number">{currentVersion}</span>
                <Link
                  to={`/pages/${pageId}/history`}
                  className="arc-edit-page-history-link"
                  title="View version history"
                >
                  View History
                </Link>
              </div>
            )}
          </div>
          {hasUnsavedChanges && (
            <div className="arc-edit-page-unsaved-warning">
              <span className="arc-edit-page-unsaved-icon">⚠️</span>
              <span className="arc-edit-page-unsaved">You have unsaved changes</span>
            </div>
          )}
        </div>

        {/* Sync Conflict Warning */}
        {!isNewPage && page?.sync_conflict && (
          <SyncConflictWarning conflict={page.sync_conflict} />
        )}

        {/* Metadata Form */}
        <div className="arc-edit-page-metadata">
          <MetadataForm
            initialData={metadata}
            onChange={handleMetadataChange}
            isNewPage={isNewPage}
            excludePageId={pageId}
            key={pageId || 'new'} // Force re-render when page changes
          />
        </div>

        <div className="arc-edit-page-toolbar-wrapper">
          <div className="arc-edit-page-toolbar-header">
            {editor && <EditorToolbar editor={editor} pageId={pageId} />}
            <button
              type="button"
              className="arc-edit-page-preview-toggle"
              onClick={() => setShowPreview(!showPreview)}
              aria-label={showPreview ? 'Show editor' : 'Show preview'}
            >
              {showPreview ? '✏️ Edit' : '👁️ Preview'}
            </button>
          </div>
        </div>

        <div className="arc-edit-page-editor-wrapper" data-testid="editor-wrapper">
          {showPreview ? (
            <div
              ref={previewRef}
              className="arc-edit-page-preview arc-reading-body"
              dangerouslySetInnerHTML={{
                __html: markdownToHtml(htmlToMarkdown(content || editorRef.current?.getHTML() || '')),
              }}
            />
          ) : (
            <Editor
              ref={editorRef}
              content={page?.content || ''}
              onEditorReady={handleEditorReady}
              onChange={(html) => {
                setContent(html);
                setHasUnsavedChanges(true);
              }}
            />
          )}
        </div>

        {/* Process preview content after render */}
        {showPreview && (
          <PreviewProcessor contentRef={previewRef} />
        )}

        <div className="arc-edit-page-actions">
          <div className="arc-edit-page-actions-left">
            {!isNewPage && (
              <Link
                to={`/pages/${pageId}/history`}
                className="arc-edit-page-button arc-edit-page-button-history"
                title="View version history"
              >
                📜 History
              </Link>
            )}
          </div>
          <div className="arc-edit-page-actions-right">
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
        </div>
        </div>
      </div>
    </Layout>
  );
}

/**
 * PreviewProcessor component - Handles syntax highlighting and link processing for preview
 */
function PreviewProcessor({ contentRef }) {
  useEffect(() => {
    if (contentRef.current) {
      highlightCodeBlocks(contentRef.current);
      processLinks(contentRef.current);
    }
  }, [contentRef]);

  return null;
}
