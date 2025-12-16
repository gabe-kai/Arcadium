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
}
