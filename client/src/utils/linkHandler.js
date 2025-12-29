/**
 * Utility to handle internal vs external links in rendered HTML
 * Adds classes and converts internal links to React Router links
 */

/**
 * Check if a URL is an internal wiki link
 * Internal links are:
 * - Relative paths (starting with /pages/)
 * - Links to page IDs (UUID format)
 * - Links without protocol (http/https) that aren't mailto or anchors
 */
export function isInternalLink(href) {
  if (!href) return false;

  // External links have protocols (http, https, mailto, etc.)
  if (/^https?:\/\//.test(href)) {
    return false;
  }

  if (href.startsWith('mailto:') || href.startsWith('tel:')) {
    return false;
  }

  // Anchors are internal
  if (href.startsWith('#')) {
    return true;
  }

  // Internal links start with /pages/ or are relative
  if (href.startsWith('/pages/') || href.startsWith('./') || href.startsWith('../')) {
    return true;
  }

  // Check if it's a UUID (page ID)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (uuidRegex.test(href)) {
    return true;
  }

  // Relative paths without protocol are likely internal
  if (!href.includes('://')) {
    return true;
  }

  return false;
}

/**
 * Process links in rendered HTML content
 * Adds classes to distinguish internal vs external links
 */
export function processLinks(container) {
  if (!container) return;

  const links = container.querySelectorAll('a');
  links.forEach((link) => {
    const href = link.getAttribute('href');

    if (isInternalLink(href)) {
      link.classList.add('arc-link-internal');
      // Add external link icon for external links (opposite)
    } else if (href && !href.startsWith('#')) {
      link.classList.add('arc-link-external');
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });

  // Process images - convert relative URLs to absolute
  const images = container.querySelectorAll('img');
  // VITE_WIKI_API_BASE_URL is typically http://localhost:5000/api (with /api)
  const baseURL = import.meta.env.VITE_WIKI_API_BASE_URL || 'http://localhost:5000/api';
  const baseWithoutApi = baseURL.endsWith('/api') ? baseURL.slice(0, -4) : baseURL.replace(/\/api$/, '');

  images.forEach((img) => {
    const src = img.getAttribute('src');
    if (!src) return;

    // Skip if already processed (prevents duplicate processing on re-renders)
    if (img.hasAttribute('data-processed')) {
      return;
    }

    // Skip if already absolute (http:// or https://) - no processing needed
    if (src.startsWith('http://') || src.startsWith('https://')) {
      img.setAttribute('data-processed', 'true');
      return;
    }

    // Calculate new src
    let newSrc = src;
    if (src.startsWith('/api/')) {
      // Already has /api prefix (e.g., /api/uploads/images/...)
      newSrc = `${baseWithoutApi}${src}`;
    } else if (src.startsWith('/')) {
      // Relative URL starting with / (e.g., /uploads/images/...)
      // Add /api prefix
      newSrc = `${baseWithoutApi}/api${src}`;
    } else {
      // Relative URL without leading / - shouldn't happen, but mark as processed
      img.setAttribute('data-processed', 'true');
      return;
    }

    // Only update if src actually changed (prevents aborting in-flight requests)
    if (newSrc !== src) {
      // Mark as processed BEFORE changing src to prevent re-processing
      img.setAttribute('data-processed', 'true');
      img.setAttribute('src', newSrc);
    } else {
      // Mark as processed even if src didn't change
      img.setAttribute('data-processed', 'true');
    }

    // Add error handler to silently handle failed loads (prevents console noise)
    // Only add if not already set
    if (!img.hasAttribute('data-error-handler')) {
      img.setAttribute('data-error-handler', 'true');
      img.onerror = function() {
        // Silently handle image load errors - don't log to console
        // The broken image icon will still show, but we won't spam the console
        // Optionally hide broken images after a delay
        setTimeout(() => {
          if (this.naturalWidth === 0 || this.naturalHeight === 0) {
            // Image failed to load - could hide it or show placeholder
            // For now, just leave it (broken image icon is fine)
          }
        }, 100);
      };
    }

    // Add loading="lazy" for better performance (browser will load when visible)
    // This also helps prevent unnecessary requests during navigation
    if (!img.hasAttribute('loading')) {
      img.setAttribute('loading', 'lazy');
    }
  });
}
