import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { usePage, useVersion, compareVersions } from '../services/api/pages';
import { useQuery } from '@tanstack/react-query';
import { markdownToHtml } from '../utils/markdown';

/**
 * PageVersionCompare component - Compares two versions of a page
 */
export function PageVersionCompare() {
  const { pageId } = useParams();
  const [searchParams] = useSearchParams();
  const fromVersion = searchParams.get('from') ? parseInt(searchParams.get('from'), 10) : null;
  const toVersion = searchParams.get('to') === 'latest' ? null : (searchParams.get('to') ? parseInt(searchParams.get('to'), 10) : null);
  const [viewMode, setViewMode] = useState('side-by-side'); // 'side-by-side' or 'inline'

  const { data: page } = usePage(pageId);
  const { data: fromVersionData } = useVersion(pageId, fromVersion);
  const { data: toVersionData } = useVersion(pageId, toVersion || page?.version);

  const { data: comparisonData } = useQuery({
    queryKey: ['versionCompare', pageId, fromVersion, toVersion || page?.version],
    queryFn: () => compareVersions(pageId, fromVersion, toVersion || page?.version),
    enabled: Boolean(pageId && fromVersion && (toVersion || page?.version)),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  const fromRef = useRef(null);
  const toRef = useRef(null);

  // Sync scroll between side-by-side views
  useEffect(() => {
    if (viewMode !== 'side-by-side' || !fromRef.current || !toRef.current) return;

    const fromEl = fromRef.current;
    const toEl = toRef.current;

    const handleScroll = (source, target) => {
      const scrollPercent = source.scrollTop / (source.scrollHeight - source.clientHeight);
      target.scrollTop = scrollPercent * (target.scrollHeight - target.clientHeight);
    };

    const fromHandler = () => handleScroll(fromEl, toEl);
    const toHandler = () => handleScroll(toEl, fromEl);

    fromEl.addEventListener('scroll', fromHandler);
    toEl.addEventListener('scroll', toHandler);

    return () => {
      fromEl.removeEventListener('scroll', fromHandler);
      toEl.removeEventListener('scroll', toHandler);
    };
  }, [viewMode]);

  if (!fromVersion || (!toVersion && !page?.version)) {
    return (
      <Layout sidebar={<Sidebar />}>
        <div>
          <h1>Invalid Comparison</h1>
          <p>Please specify both versions to compare.</p>
          <Link to={`/pages/${pageId}/history`}>View Version History</Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-page-version-compare">
        <div className="arc-page-version-compare-header">
          <div className="arc-page-version-compare-header-top">
            <h1 className="arc-page-version-compare-title">Compare Versions</h1>
            <Link
              to={`/pages/${pageId}/history`}
              className="arc-page-version-compare-back-link"
            >
              ← Back to History
            </Link>
          </div>
          <div className="arc-page-version-compare-info">
            <div className="arc-page-version-compare-info-item">
              <span className="arc-page-version-compare-info-label">From:</span>
              <Link to={`/pages/${pageId}/versions/${fromVersion}`}>
                Version {fromVersion}
              </Link>
            </div>
            <div className="arc-page-version-compare-info-item">
              <span className="arc-page-version-compare-info-label">To:</span>
              <Link to={`/pages/${pageId}/versions/${toVersion || page?.version}`}>
                Version {toVersion || page?.version}
              </Link>
            </div>
            {comparisonData?.diff && (
              <div className="arc-page-version-compare-stats">
                <span className="arc-page-version-compare-stat arc-page-version-compare-stat-additions">
                  +{comparisonData.diff.additions || 0} additions
                </span>
                <span className="arc-page-version-compare-stat arc-page-version-compare-stat-deletions">
                  -{comparisonData.diff.deletions || 0} deletions
                </span>
              </div>
            )}
          </div>
          <div className="arc-page-version-compare-view-toggle">
            <button
              type="button"
              className={`arc-page-version-compare-toggle-button ${viewMode === 'side-by-side' ? 'arc-page-version-compare-toggle-active' : ''}`}
              onClick={() => setViewMode('side-by-side')}
            >
              Side-by-Side
            </button>
            <button
              type="button"
              className={`arc-page-version-compare-toggle-button ${viewMode === 'inline' ? 'arc-page-version-compare-toggle-active' : ''}`}
              onClick={() => setViewMode('inline')}
            >
              Inline Diff
            </button>
          </div>
        </div>

        <div className="arc-page-version-compare-content">
          {viewMode === 'side-by-side' ? (
            <div className="arc-page-version-compare-side-by-side">
              <div className="arc-page-version-compare-panel">
                <div className="arc-page-version-compare-panel-header">
                  <h2>Version {fromVersion}</h2>
                  {fromVersionData?.created_at && (
                    <span className="arc-page-version-compare-panel-date">
                      {new Date(fromVersionData.created_at).toLocaleString()}
                    </span>
                  )}
                </div>
                <div
                  ref={fromRef}
                  className="arc-page-version-compare-panel-content arc-reading-body"
                  dangerouslySetInnerHTML={{
                    __html: fromVersionData?.html_content || markdownToHtml(fromVersionData?.content || ''),
                  }}
                />
              </div>
              <div className="arc-page-version-compare-panel">
                <div className="arc-page-version-compare-panel-header">
                  <h2>Version {toVersion || page?.version}</h2>
                  {toVersionData?.created_at && (
                    <span className="arc-page-version-compare-panel-date">
                      {new Date(toVersionData.created_at).toLocaleString()}
                    </span>
                  )}
                </div>
                <div
                  ref={toRef}
                  className="arc-page-version-compare-panel-content arc-reading-body"
                  dangerouslySetInnerHTML={{
                    __html: toVersionData?.html_content || markdownToHtml(toVersionData?.content || ''),
                  }}
                />
              </div>
            </div>
          ) : (
            <div className="arc-page-version-compare-inline">
              {comparisonData?.diff?.changes ? (
                <div className="arc-page-version-compare-diff">
                  {comparisonData.diff.changes.map((change, index) => (
                    <div
                      key={index}
                      className={`arc-page-version-compare-diff-line arc-page-version-compare-diff-${change.type}`}
                    >
                      <span className="arc-page-version-compare-diff-line-number">
                        {change.line}
                      </span>
                      <span className="arc-page-version-compare-diff-line-content">
                        {change.content}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="arc-page-version-compare-diff-fallback">
                  <p>Diff data not available. Showing versions side-by-side.</p>
                  <div className="arc-page-version-compare-side-by-side">
                    <div className="arc-page-version-compare-panel">
                      <div className="arc-page-version-compare-panel-header">
                        <h2>Version {fromVersion}</h2>
                      </div>
                      <div
                        className="arc-page-version-compare-panel-content arc-reading-body"
                        dangerouslySetInnerHTML={{
                          __html: fromVersionData?.html_content || markdownToHtml(fromVersionData?.content || ''),
                        }}
                      />
                    </div>
                    <div className="arc-page-version-compare-panel">
                      <div className="arc-page-version-compare-panel-header">
                        <h2>Version {toVersion || page?.version}</h2>
                      </div>
                      <div
                        className="arc-page-version-compare-panel-content arc-reading-body"
                        dangerouslySetInnerHTML={{
                          __html: toVersionData?.html_content || markdownToHtml(toVersionData?.content || ''),
                        }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
