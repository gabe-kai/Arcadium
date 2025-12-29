import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { usePage, useVersion, restoreVersion } from '../services/api/pages';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { useAuth } from '../services/auth/AuthContext';
import { markdownToHtml } from '../utils/markdown';
import { highlightCodeBlocks } from '../utils/syntaxHighlight';
import { processLinks } from '../utils/linkHandler';

/**
 * PageVersionView component - Displays a specific version of a page
 */
export function PageVersionView() {
  const { pageId, version } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const versionNumber = version ? parseInt(version, 10) : null;

  const { data: page } = usePage(pageId);
  const { data: versionData, isLoading, isError } = useVersion(pageId, versionNumber);

  const restoreMutation = useMutation({
    mutationFn: () => restoreVersion(pageId, versionNumber),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      queryClient.invalidateQueries({ queryKey: ['versionHistory', pageId] });
      navigate(`/pages/${pageId}`);
    },
  });

  const canRestore = user && (user.role === 'admin' || (user.role === 'writer' && page?.created_by === user.id));

  if (isLoading) {
    return (
      <Layout sidebar={<Sidebar />}>
        <div>Loading version...</div>
      </Layout>
    );
  }

  if (isError || !versionData) {
    return (
      <Layout sidebar={<Sidebar />}>
        <div>
          <h1>Version Not Found</h1>
          <p>The requested version does not exist.</p>
          <Link to={`/pages/${pageId}`}>Return to Page</Link>
        </div>
      </Layout>
    );
  }

  const handleRestore = () => {
    if (window.confirm(`Are you sure you want to restore version ${versionNumber}? This will create a new version with this content.`)) {
      restoreMutation.mutate();
    }
  };

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-page-version-view">
        <div className="arc-page-version-view-header">
          <div className="arc-page-version-view-header-top">
            <h1 className="arc-page-version-view-title">
              Version {versionNumber}
            </h1>
            <Link
              to={`/pages/${pageId}`}
              className="arc-page-version-view-back-link"
            >
              ← Back to Current Version
            </Link>
          </div>
          <div className="arc-page-version-view-meta">
            <div className="arc-page-version-view-meta-item">
              <span className="arc-page-version-view-meta-label">Page:</span>
              <Link to={`/pages/${pageId}`} className="arc-page-version-view-page-link">
                {page?.title || 'Unknown Page'}
              </Link>
            </div>
            {versionData.created_at && (
              <div className="arc-page-version-view-meta-item">
                <span className="arc-page-version-view-meta-label">Date:</span>
                <span>{new Date(versionData.created_at).toLocaleString()}</span>
              </div>
            )}
            {versionData.changed_by && (
              <div className="arc-page-version-view-meta-item">
                <span className="arc-page-version-view-meta-label">Changed by:</span>
                <span>{versionData.changed_by.username || versionData.changed_by.id}</span>
              </div>
            )}
            {versionData.change_summary && (
              <div className="arc-page-version-view-meta-item">
                <span className="arc-page-version-view-meta-label">Summary:</span>
                <span>{versionData.change_summary}</span>
              </div>
            )}
          </div>
        </div>

        <div className="arc-page-version-view-actions">
          <Link
            to={`/pages/${pageId}/versions/compare?from=${versionNumber}&to=${page?.version || 'latest'}`}
            className="arc-page-version-view-action-link"
          >
            Compare with Current
          </Link>
          {canRestore && (
            <button
              type="button"
              className="arc-page-version-view-action-button"
              onClick={handleRestore}
              disabled={restoreMutation.isPending}
            >
              {restoreMutation.isPending ? 'Restoring...' : 'Restore This Version'}
            </button>
          )}
        </div>

        <div className="arc-page-version-view-content">
          <div
            className="arc-page-version-view-html arc-reading-body"
            dangerouslySetInnerHTML={{
              __html: versionData.html_content || markdownToHtml(versionData.content || ''),
            }}
            ref={(el) => {
              if (el) {
                highlightCodeBlocks(el);
                processLinks(el);
              }
            }}
          />
        </div>
      </div>
    </Layout>
  );
}
