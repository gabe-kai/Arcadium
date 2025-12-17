import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { usePage, useVersionHistory } from '../services/api/pages';

/**
 * PageHistoryPage component - Displays version history for a page
 */
export function PageHistoryPage() {
  const { pageId } = useParams();
  const navigate = useNavigate();
  
  const { data: page, isLoading: isLoadingPage } = usePage(pageId);
  const { data: versions, isLoading: isLoadingVersions } = useVersionHistory(pageId);

  if (isLoadingPage || isLoadingVersions) {
    return (
      <Layout sidebar={<Sidebar />}>
        <div>Loading version history...</div>
      </Layout>
    );
  }

  if (!page) {
    return (
      <Layout sidebar={<Sidebar />}>
        <div>
          <h1>Page Not Found</h1>
          <p>The requested page does not exist.</p>
          <Link to="/">Return to Home</Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-page-history">
        <div className="arc-page-history-header">
          <div className="arc-page-history-header-top">
            <h1 className="arc-page-history-title">Version History</h1>
            <Link
              to={`/pages/${pageId}`}
              className="arc-page-history-back-link"
            >
              ← Back to Page
            </Link>
          </div>
          <div className="arc-page-history-page-info">
            <Link to={`/pages/${pageId}`} className="arc-page-history-page-title">
              {page.title}
            </Link>
            <span className="arc-page-history-page-meta">
              Current Version: {page.version || 'N/A'}
            </span>
          </div>
        </div>

        {!versions || versions.length === 0 ? (
          <div className="arc-page-history-empty">
            <p>No version history available for this page.</p>
          </div>
        ) : (
          <div className="arc-page-history-list">
            {versions.map((version) => (
              <div key={version.version} className="arc-page-history-item">
                <div className="arc-page-history-item-header">
                  <div className="arc-page-history-item-left">
                    <span className="arc-page-history-version-number">
                      Version {version.version}
                    </span>
                    {version.version === page.version && (
                      <span className="arc-page-history-current-badge">Current</span>
                    )}
                  </div>
                  <div className="arc-page-history-item-right">
                    <span className="arc-page-history-date">
                      {version.created_at
                        ? new Date(version.created_at).toLocaleString()
                        : 'Unknown date'}
                    </span>
                  </div>
                </div>
                {version.changed_by && (
                  <div className="arc-page-history-author">
                    Changed by: {version.changed_by.username || version.changed_by.id}
                  </div>
                )}
                {version.change_summary && (
                  <div className="arc-page-history-summary">
                    {version.change_summary}
                  </div>
                )}
                {version.diff_stats && (
                  <div className="arc-page-history-stats">
                    <span className="arc-page-history-stat arc-page-history-stat-additions">
                      +{version.diff_stats.additions || 0} additions
                    </span>
                    <span className="arc-page-history-stat arc-page-history-stat-deletions">
                      -{version.diff_stats.deletions || 0} deletions
                    </span>
                  </div>
                )}
                <div className="arc-page-history-actions">
                  <Link
                    to={`/pages/${pageId}/versions/${version.version}`}
                    className="arc-page-history-action-link"
                  >
                    View Version
                  </Link>
                  {version.version !== page.version && versions.length > 1 && (
                    <Link
                      to={`/pages/${pageId}/versions/compare?from=${version.version}&to=${page.version}`}
                      className="arc-page-history-action-link"
                    >
                      Compare with Current
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
