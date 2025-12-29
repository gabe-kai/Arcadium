/**
 * Generate a URL-friendly slug from a title
 * @param {string} title - The title to convert to a slug
 * @returns {string} - The generated slug
 */
export function generateSlug(title) {
  if (!title) return '';

  return title
    .toLowerCase()
    .trim()
    // Replace spaces and underscores with hyphens
    .replace(/[\s_]+/g, '-')
    // Remove special characters except hyphens
    .replace(/[^a-z0-9-]/g, '')
    // Remove multiple consecutive hyphens
    .replace(/-+/g, '-')
    // Remove leading/trailing hyphens
    .replace(/^-+|-+$/g, '');
}
