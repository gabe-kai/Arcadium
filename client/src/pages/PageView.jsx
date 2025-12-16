import React, { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { SidebarPlaceholder } from '../components/layout/Sidebar';
import { Breadcrumb } from '../components/navigation/Breadcrumb';
import { PageNavigation } from '../components/navigation/PageNavigation';
import { usePage, useBreadcrumb, usePageNavigation } from '../services/api/pages';
import { highlightCodeBlocks } from '../utils/syntaxHighlight';
import { processLinks } from '../utils/linkHandler';

export function PageView() {
  const { pageId } = useParams();
  const { data: page, isLoading, isError } = usePage(pageId);
  const { data: breadcrumb } = useBreadcrumb(pageId);
  const { data: navigation } = usePageNavigation(pageId);
  const contentRef = useRef(null);

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
        {breadcrumb && <Breadcrumb breadcrumb={breadcrumb} currentPageId={pageId} />}
        
        <header className="arc-page-header">
          <h1>{page.title}</h1>
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
      </>
    );
  }

  return (
    <Layout sidebar={<SidebarPlaceholder />}>
      {content}
    </Layout>
  );
}
