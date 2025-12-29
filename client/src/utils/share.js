/**
 * Share utilities for copying links and sharing pages
 */

export function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }

  // Fallback for older browsers
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    document.execCommand('copy');
    return Promise.resolve();
  } catch (err) {
    return Promise.reject(err);
  } finally {
    document.body.removeChild(textArea);
  }
}

export function getPageUrl(pageId) {
  const baseUrl = window.location.origin;
  return `${baseUrl}/pages/${pageId}`;
}

export function sharePage(pageId, title) {
  const url = getPageUrl(pageId);

  if (navigator.share) {
    return navigator.share({
      title: title || 'Arcadium Wiki Page',
      text: `Check out this page: ${title}`,
      url: url,
    });
  }

  // Fallback: copy to clipboard
  return copyToClipboard(url).then(() => {
    return { copied: true };
  });
}

export function copyPageLink(pageId) {
  const url = getPageUrl(pageId);
  return copyToClipboard(url);
}
