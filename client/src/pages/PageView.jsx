import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { Breadcrumb } from '../components/navigation/Breadcrumb';
import { PageNavigation } from '../components/navigation/PageNavigation';
import { TableOfContents } from '../components/navigation/TableOfContents';
import { Backlinks } from '../components/navigation/Backlinks';
import { CommentsPanel } from '../components/comments/CommentsPanel';
import { DeleteArchiveDialog } from '../components/page/DeleteArchiveDialog';
import { ShareButton } from '../components/common/ShareButton';
import { usePage, useBreadcrumb, usePageNavigation, deletePage, archivePage, unarchivePage } from '../services/api/pages';
import { useComments } from '../services/api/comments';
import { useAuth } from '../services/auth/AuthContext';
import { highlightCodeBlocks } from '../utils/syntaxHighlight';
import { processLinks } from '../utils/linkHandler';
import { useNotificationContext } from '../components/common/NotificationProvider';

export function PageView() {
  const { pageId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  const { showSuccess, showError } = useNotificationContext();
  const { data: page, isLoading, isError } = usePage(pageId);
  const { data: breadcrumb } = useBreadcrumb(pageId);
  const { data: navigation } = usePageNavigation(pageId);
  const { data: comments } = useComments(pageId);
  const contentRef = useRef(null);

  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showArchiveDialog, setShowArchiveDialog] = useState(false);
  const [showUnarchiveDialog, setShowUnarchiveDialog] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => deletePage(pageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
      queryClient.invalidateQueries({ queryKey: ['index'] });
      showSuccess('Page deleted successfully');
      navigate('/');
    },
    onError: (error) => {
      showError(error.response?.data?.error || 'Failed to delete page');
    },
  });

  const archiveMutation = useMutation({
    mutationFn: () => archivePage(pageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
      queryClient.invalidateQueries({ queryKey: ['index'] });
      showSuccess('Page archived successfully');
      setShowArchiveDialog(false);
    },
    onError: (error) => {
      showError(error.response?.data?.error || 'Failed to archive page');
    },
  });

  const unarchiveMutation = useMutation({
    mutationFn: () => unarchivePage(pageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
      queryClient.invalidateQueries({ queryKey: ['index'] });
      showSuccess('Page unarchived successfully');
      setShowUnarchiveDialog(false);
    },
    onError: (error) => {
      showError(error.response?.data?.error || 'Failed to unarchive page');
    },
  });

  const handleEditClick = () => {
    if (pageId) {
      navigate(`/pages/${pageId}/edit`);
    }
  };

  const handleDeleteClick = () => {
    setShowDeleteDialog(true);
  };

  const handleArchiveClick = () => {
    setShowArchiveDialog(true);
  };

  const handleUnarchiveClick = () => {
    setShowUnarchiveDialog(true);
  };

  const handleDeleteConfirm = () => {
    deleteMutation.mutate();
  };

  const handleArchiveConfirm = () => {
    archiveMutation.mutate();
  };

  const handleUnarchiveConfirm = () => {
    unarchiveMutation.mutate();
  };

  // Refetch page data when authentication state changes (to update permission flags)
  const prevAuthRef = useRef(isAuthenticated);
  useEffect(() => {
    if (!pageId) return;

    const authChanged = prevAuthRef.current !== isAuthenticated;

    // Check if we just signed in (flag set by SignInPage)
    const justSignedIn = sessionStorage.getItem('justSignedIn') === 'true';

    // Refetch if:
    // 1. Authentication state changed (user signed in/out while on this page), OR
    // 2. We just signed in (flag is set, meaning we navigated here after sign-in)
    const shouldRefetch = authChanged || justSignedIn;

    if (shouldRefetch) {
      // Force refetch of all page-related queries to get updated permissions
      // Use refetchQueries to ensure immediate refetch regardless of staleTime
      queryClient.refetchQueries({ queryKey: ['page', pageId] });
      queryClient.refetchQueries({ queryKey: ['breadcrumb', pageId] });
      queryClient.refetchQueries({ queryKey: ['pageNavigation', pageId] });
      queryClient.refetchQueries({ queryKey: ['comments', pageId] });

      // Clear the flag after refetching
      if (justSignedIn) {
        sessionStorage.removeItem('justSignedIn');
      }
    }

    // Update ref to track current auth state
    prevAuthRef.current = isAuthenticated;
  }, [isAuthenticated, pageId, queryClient]);

  // Process content after it's rendered (syntax highlighting, link processing)
  useEffect(() => {
    if (contentRef.current && page?.html_content) {
      highlightCodeBlocks(contentRef.current);
      processLinks(contentRef.current);
    }
  }, [page?.html_content]);

  let content;

  if (!pageId) {
    content = <p className="arc-muted">No page selected.</p>;
  } else if (isLoading) {
    content = <p className="arc-muted">Loading page…</p>;
  } else if (isError || !page) {
    content = (
      <p className="arc-error">
        Unable to load page. Please verify the URL or try again.
      </p>
    );
  } else {
    content = (
      <>
        <div className="arc-content-wrapper">
          <div className="arc-content-scrollable">
            {breadcrumb && <Breadcrumb breadcrumb={breadcrumb} currentPageId={pageId} />}

            <header className="arc-page-header">
              <div className="arc-page-header-top">
                <h1>{page.title}</h1>
                <div className="arc-page-header-actions">
                  <ShareButton pageId={pageId} pageTitle={page.title} />
                  {page.can_edit && (
                    <button
                      type="button"
                      className="arc-edit-button"
                      onClick={handleEditClick}
                      aria-label="Edit this page"
                    >
                      Edit
                    </button>
                  )}
                  {page.status === 'archived' && page.can_archive && (
                    <button
                      type="button"
                      className="arc-page-action-button arc-page-action-button-unarchive"
                      onClick={handleUnarchiveClick}
                      aria-label="Unarchive this page"
                    >
                      Unarchive
                    </button>
                  )}
                  {page.status !== 'archived' && page.can_archive && (
                    <button
                      type="button"
                      className="arc-page-action-button arc-page-action-button-archive"
                      onClick={handleArchiveClick}
                      aria-label="Archive this page"
                    >
                      Archive
                    </button>
                  )}
                  {page.can_delete && (
                    <button
                      type="button"
                      className="arc-page-action-button arc-page-action-button-delete"
                      onClick={handleDeleteClick}
                      aria-label="Delete this page"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
              <div className="arc-page-meta">
                {page.updated_at && (
                  <span>
                    Last updated:{' '}
                    {new Date(page.updated_at).toLocaleString(undefined, {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </span>
                )}
                {typeof page.word_count === 'number' && (
                  <span> · {page.word_count} words</span>
                )}
                {typeof page.content_size_kb === 'number' && (
                  <span> · {page.content_size_kb.toFixed(1)} KB</span>
                )}
                {page.status && <span> · {page.status}</span>}
              </div>
            </header>

            <article className="arc-reading-view">
              <div
                ref={contentRef}
                className="arc-reading-body"
                // Backend supplies sanitized HTML (`html_content`)
                dangerouslySetInnerHTML={{ __html: page.html_content || '' }}
              />
            </article>

            {navigation && <PageNavigation navigation={navigation} />}
          </div>

          {pageId && <CommentsPanel pageId={pageId} comments={comments || []} />}
        </div>
      </>
    );
  }

  // Build right sidebar with TOC and Backlinks
  const rightSidebar = page && (page.table_of_contents || page.backlinks) ? (
    <div className="arc-right-sidebar-content">
      {page.table_of_contents && (
        <TableOfContents toc={page.table_of_contents} contentRef={contentRef} />
      )}
      {page.backlinks && <Backlinks backlinks={page.backlinks} />}
    </div>
  ) : null;

  return (
    <>
      <Layout sidebar={<Sidebar />} rightSidebar={rightSidebar}>
        {content}
      </Layout>

      {showDeleteDialog && (
        <DeleteArchiveDialog
          isOpen={showDeleteDialog}
          onClose={() => setShowDeleteDialog(false)}
          onConfirm={handleDeleteConfirm}
          action="delete"
          pageTitle={page?.title || ''}
          isProcessing={deleteMutation.isPending}
        />
      )}

      {showArchiveDialog && (
        <DeleteArchiveDialog
          isOpen={showArchiveDialog}
          onClose={() => setShowArchiveDialog(false)}
          onConfirm={handleArchiveConfirm}
          action="archive"
          pageTitle={page?.title || ''}
          isProcessing={archiveMutation.isPending}
        />
      )}

      {showUnarchiveDialog && (
        <DeleteArchiveDialog
          isOpen={showUnarchiveDialog}
          onClose={() => setShowUnarchiveDialog(false)}
          onConfirm={handleUnarchiveConfirm}
          action="unarchive"
          pageTitle={page?.title || ''}
          isProcessing={unarchiveMutation.isPending}
        />
      )}
    </>
  );
}
