import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api/client';

const HOME_PAGE_SLUG = 'home';

/**
 * Fetch home page ID by slug
 */
function fetchHomePageId() {
  return apiClient
    .get('/pages', { params: { slug: HOME_PAGE_SLUG } })
    .then((res) => {
      const pages = res.data.pages || [];
      if (pages.length === 0) {
        return null;
      }
      return pages[0].id;
    })
    .catch(() => null);
}

/**
 * HomePage component - Redirects to the home page (slug: "home")
 * This makes the home page a standard wiki page that can be edited normally
 */
export function HomePage() {
  const navigate = useNavigate();

  // Fetch home page ID
  const { data: homePageId, isLoading, isError } = useQuery({
    queryKey: ['homePageId'],
    queryFn: fetchHomePageId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Redirect to the home page when we have the ID
  useEffect(() => {
    if (homePageId) {
      navigate(`/pages/${homePageId}`, { replace: true });
    }
  }, [homePageId, navigate]);

  // Show loading or error state
  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p className="arc-muted">Loading home page…</p>
      </div>
    );
  }

  if (isError || !homePageId) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p className="arc-error">
          Home page not found. Please create a page with slug &quot;home&quot;.
        </p>
      </div>
    );
  }

  // This shouldn't render, but just in case
  return null;
}
