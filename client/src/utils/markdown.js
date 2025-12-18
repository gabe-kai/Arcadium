import TurndownService from 'turndown';
import { marked } from 'marked';

/**
 * Parse frontmatter from markdown content
 * @param {string} content - Markdown content with optional YAML frontmatter
 * @returns {Object} - { frontmatter: object, markdown: string }
 */
export function parseFrontmatter(content) {
  if (!content || !content.startsWith('---')) {
    return { frontmatter: {}, markdown: content || '' };
  }
  
  const parts = content.split('---');
  if (parts.length < 3) {
    return { frontmatter: {}, markdown: content };
  }
  
  const frontmatterStr = parts[1].trim();
  const markdown = parts.slice(2).join('---').trim();
  
  let frontmatter = {};
  if (frontmatterStr) {
    try {
      // Simple YAML parsing (basic key: value pairs)
      const lines = frontmatterStr.split('\n');
      for (const line of lines) {
        const match = line.match(/^(\w+):\s*(.+)$/);
        if (match) {
          const key = match[1];
          let value = match[2].trim();
          // Remove quotes if present
          if ((value.startsWith('"') && value.endsWith('"')) || 
              (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
          }
          frontmatter[key] = value;
        }
      }
    } catch (e) {
      console.warn('Failed to parse frontmatter:', e);
    }
  }
  
  return { frontmatter, markdown };
}

/**
 * Reconstruct frontmatter from metadata and prepend to markdown
 * Preserves any existing frontmatter fields that aren't in the metadata form
 * @param {Object} metadata - Page metadata (title, slug, section, status, etc.)
 * @param {string} markdown - Markdown content without frontmatter
 * @param {string} originalContent - Original content with frontmatter (to preserve custom fields)
 * @returns {string} - Markdown content with frontmatter prepended
 */
export function addFrontmatter(metadata, markdown, originalContent = null) {
  if (!metadata) return markdown || '';
  
  // Parse existing frontmatter to preserve custom fields (e.g., from AI system)
  let existingFrontmatter = {};
  if (originalContent) {
    const parsed = parseFrontmatter(originalContent);
    existingFrontmatter = parsed.frontmatter || {};
  }
  
  // Start with existing frontmatter to preserve custom fields
  const frontmatter = { ...existingFrontmatter };
  
  // Override with metadata form values (user-editable fields)
  if (metadata.title) frontmatter.title = metadata.title;
  if (metadata.slug) frontmatter.slug = metadata.slug;
  if (metadata.section !== undefined) {
    if (metadata.section) {
      frontmatter.section = metadata.section;
    } else {
      // Remove section if cleared
      delete frontmatter.section;
    }
  }
  if (metadata.status) frontmatter.status = metadata.status;
  if (metadata.order !== null && metadata.order !== undefined) {
    frontmatter.order = metadata.order;
  } else if (metadata.order === null || metadata.order === '') {
    // Remove order if cleared
    delete frontmatter.order;
  }
  
  // Build YAML frontmatter string
  const frontmatterLines = [];
  // Sort keys: standard fields first, then custom fields
  const standardKeys = ['title', 'slug', 'section', 'status', 'order', 'parent_slug'];
  const sortedKeys = [
    ...standardKeys.filter(k => k in frontmatter),
    ...Object.keys(frontmatter).filter(k => !standardKeys.includes(k)).sort()
  ];
  
  for (const key of sortedKeys) {
    const value = frontmatter[key];
    if (value !== null && value !== undefined && value !== '') {
      // Escape values that need quotes
      const needsQuotes = typeof value === 'string' && (
        value.includes(':') || 
        value.includes('#') || 
        value.includes('|') ||
        value.includes('&') ||
        value.startsWith(' ') ||
        value.endsWith(' ')
      );
      const formattedValue = needsQuotes ? `"${value.replace(/"/g, '\\"')}"` : value;
      frontmatterLines.push(`${key}: ${formattedValue}`);
    }
  }
  
  if (frontmatterLines.length === 0) {
    return markdown || '';
  }
  
  return `---\n${frontmatterLines.join('\n')}\n---\n${markdown || ''}`;
}

/**
 * Convert HTML to Markdown
 * Used when saving editor content (Tiptap outputs HTML)
 */
export function htmlToMarkdown(html) {
  if (!html) return '';
  
  const turndownService = new TurndownService({
    headingStyle: 'atx', // Use # for headings
    codeBlockStyle: 'fenced', // Use ``` for code blocks
    bulletListMarker: '-', // Use - for bullet lists
  });
  
  return turndownService.turndown(html);
}

/**
 * Convert Markdown to HTML
 * Used when loading page content into editor (API provides markdown)
 */
export function markdownToHtml(markdown) {
  if (!markdown) return '';
  
  // Configure marked options
  marked.setOptions({
    breaks: true, // Convert line breaks to <br>
    gfm: true, // GitHub Flavored Markdown
    headerIds: false, // Disable header IDs for cleaner HTML
    mangle: false, // Don't mangle email addresses
  });
  
  return marked.parse(markdown);
}
