import TurndownService from 'turndown';
import { marked } from 'marked';

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
  });
  
  return marked.parse(markdown);
}
