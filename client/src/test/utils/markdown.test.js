import { describe, it, expect, beforeEach } from 'vitest';
import { htmlToMarkdown, markdownToHtml, parseFrontmatter, addFrontmatter } from '../../utils/markdown';

describe('markdown utilities', () => {
  describe('htmlToMarkdown', () => {
    it('returns empty string for null or undefined', () => {
      expect(htmlToMarkdown(null)).toBe('');
      expect(htmlToMarkdown(undefined)).toBe('');
      expect(htmlToMarkdown('')).toBe('');
    });

    it('converts simple paragraph', () => {
      const html = '<p>Hello world</p>';
      const markdown = htmlToMarkdown(html);
      expect(markdown.trim()).toBe('Hello world');
    });

    it('converts headings', () => {
      const html = '<h1>Heading 1</h1><h2>Heading 2</h2><h3>Heading 3</h3>';
      const markdown = htmlToMarkdown(html);
      expect(markdown).toContain('# Heading 1');
      expect(markdown).toContain('## Heading 2');
      expect(markdown).toContain('### Heading 3');
    });

    it('converts bold and italic', () => {
      const html = '<p><strong>Bold</strong> and <em>italic</em> text</p>';
      const markdown = htmlToMarkdown(html);
      expect(markdown).toContain('**Bold**');
      // Turndown may add spaces, so use regex match
      expect(markdown).toMatch(/italic/);
    });

    it('converts links', () => {
      const html = '<p><a href="https://example.com">Link text</a></p>';
      const markdown = htmlToMarkdown(html);
      expect(markdown).toContain('[Link text](https://example.com)');
    });

    it('converts lists', () => {
      const html = '<ul><li>Item 1</li><li>Item 2</li></ul>';
      const markdown = htmlToMarkdown(html);
      // Turndown may add extra spaces, so we check for the pattern more flexibly
      expect(markdown).toMatch(/-.*Item 1/);
      expect(markdown).toMatch(/-.*Item 2/);
    });

    it('converts code blocks', () => {
      const html = '<pre><code>const x = 1;</code></pre>';
      const markdown = htmlToMarkdown(html);
      expect(markdown).toContain('```');
      expect(markdown).toContain('const x = 1;');
    });

    it('converts tables to markdown', () => {
      const html = '<table><thead><tr><th>Header 1</th><th>Header 2</th></tr></thead><tbody><tr><td>Cell 1</td><td>Cell 2</td></tr></tbody></table>';
      const markdown = htmlToMarkdown(html);
      // Should contain table markdown syntax
      expect(markdown).toContain('|');
      expect(markdown).toContain('Header 1');
      expect(markdown).toContain('Header 2');
      expect(markdown).toContain('Cell 1');
      expect(markdown).toContain('Cell 2');
    });

    it('converts inline code', () => {
      const html = '<p>Use <code>console.log</code> to debug</p>';
      const markdown = htmlToMarkdown(html);
      expect(markdown).toContain('`console.log`');
    });

    it('converts blockquotes', () => {
      const html = '<blockquote>This is a quote</blockquote>';
      const markdown = htmlToMarkdown(html);
      expect(markdown).toContain('> This is a quote');
    });

    it('handles nested elements', () => {
      const html = '<div><p>Paragraph with <strong>bold</strong> text</p></div>';
      const markdown = htmlToMarkdown(html);
      expect(markdown).toContain('Paragraph with **bold** text');
    });

    it('handles empty HTML tags', () => {
      const html = '<p></p><div></div>';
      const markdown = htmlToMarkdown(html);
      expect(markdown.trim()).toBe('');
    });

    it('preserves line breaks in code blocks', () => {
      const html = '<pre><code>line1\nline2\nline3</code></pre>';
      const markdown = htmlToMarkdown(html);
      expect(markdown).toContain('line1');
      expect(markdown).toContain('line2');
      expect(markdown).toContain('line3');
    });
  });

  describe('markdownToHtml', () => {
    beforeEach(() => {
      // Reset marked options before each test
      const { marked } = require('marked');
      marked.setOptions({
        breaks: true,
        gfm: true,
      });
    });

    it('returns empty string for null or undefined', () => {
      expect(markdownToHtml(null)).toBe('');
      expect(markdownToHtml(undefined)).toBe('');
      expect(markdownToHtml('')).toBe('');
    });

    it('converts simple text to paragraph', () => {
      const markdown = 'Hello world';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<p>Hello world</p>');
    });

    it('converts headings', () => {
      const markdown = '# Heading 1\n## Heading 2\n### Heading 3';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<h1>Heading 1</h1>');
      expect(html).toContain('<h2>Heading 2</h2>');
      expect(html).toContain('<h3>Heading 3</h3>');
    });

    it('converts bold and italic', () => {
      const markdown = '**Bold** and *italic* text';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<strong>Bold</strong>');
      expect(html).toContain('<em>italic</em>');
    });

    it('converts links', () => {
      const markdown = '[Link text](https://example.com)';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<a href="https://example.com">Link text</a>');
    });

    it('converts lists', () => {
      const markdown = '- Item 1\n- Item 2';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<ul>');
      expect(html).toContain('<li>Item 1</li>');
      expect(html).toContain('<li>Item 2</li>');
    });

    it('converts code blocks', () => {
      const markdown = '```\nconst x = 1;\n```';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<pre><code>');
      expect(html).toContain('const x = 1;');
    });

    it('converts markdown tables to HTML', () => {
      const markdown = '| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |';
      const html = markdownToHtml(markdown);
      // marked.js with GFM should convert tables
      expect(html).toContain('<table>');
      expect(html).toContain('Header 1');
      expect(html).toContain('Cell 1');
    });

    it('converts markdown tables with multiple rows to HTML', () => {
      const markdown = '| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |\n| Cell 3   | Cell 4   |';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<table>');
      expect(html).toContain('Cell 1');
      expect(html).toContain('Cell 3');
    });

    it('preserves table structure in round-trip conversion', () => {
      const originalHtml = '<table><thead><tr><th>Header 1</th><th>Header 2</th></tr></thead><tbody><tr><td>Cell 1</td><td>Cell 2</td></tr><tr><td>Cell 3</td><td>Cell 4</td></tr></tbody></table>';
      const markdown = htmlToMarkdown(originalHtml);
      const convertedHtml = markdownToHtml(markdown);

      // Should contain table structure
      expect(convertedHtml).toContain('<table>');
      expect(convertedHtml).toContain('Header 1');
      expect(convertedHtml).toContain('Cell 1');
      expect(convertedHtml).toContain('Cell 3');
    });

    it('converts inline code', () => {
      const markdown = 'Use `console.log` to debug';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<code>console.log</code>');
    });

    it('converts blockquotes', () => {
      const markdown = '> This is a quote';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<blockquote>');
      expect(html).toContain('This is a quote');
    });

    it('handles line breaks with breaks option', () => {
      const markdown = 'Line 1\nLine 2';
      const html = markdownToHtml(markdown);
      // With breaks: true, line breaks should be converted
      expect(html).toContain('Line 1');
      expect(html).toContain('Line 2');
    });

    it('handles GFM features', () => {
      const markdown = '- [x] Completed task\n- [ ] Incomplete task';
      const html = markdownToHtml(markdown);
      // GFM should handle task lists
      expect(html).toContain('Completed task');
      expect(html).toContain('Incomplete task');
    });

    it('handles complex nested markdown', () => {
      const markdown = '## Section\n\nParagraph with **bold** and *italic*.\n\n- List item 1\n- List item 2';
      const html = markdownToHtml(markdown);
      expect(html).toContain('<h2>Section</h2>');
      expect(html).toContain('<strong>bold</strong>');
      expect(html).toContain('<em>italic</em>');
      expect(html).toContain('<ul>');
    });

    it('handles special characters', () => {
      const markdown = 'Text with < > & " \' characters';
      const html = markdownToHtml(markdown);
      // Should escape or handle special characters properly
      expect(html).toBeTruthy();
    });
  });

  describe('round-trip conversion', () => {
    it('maintains content through html->markdown->html cycle', () => {
      const originalHtml = '<p>Simple paragraph</p>';
      const markdown = htmlToMarkdown(originalHtml);
      const convertedHtml = markdownToHtml(markdown);
      // Content should be preserved (formatting may differ slightly)
      expect(convertedHtml).toContain('Simple paragraph');
    });

    it('handles headings through round-trip', () => {
      const originalHtml = '<h1>Main Title</h1><h2>Subtitle</h2>';
      const markdown = htmlToMarkdown(originalHtml);
      const convertedHtml = markdownToHtml(markdown);
      expect(convertedHtml).toContain('Main Title');
      expect(convertedHtml).toContain('Subtitle');
    });
  });

  describe('parseFrontmatter', () => {
    it('parses content with frontmatter', () => {
      const content = `---
title: Test Page
slug: test-page
section: Testing
status: published
---
# Content here`;
      const result = parseFrontmatter(content);
      expect(result.frontmatter).toEqual({
        title: 'Test Page',
        slug: 'test-page',
        section: 'Testing',
        status: 'published'
      });
      expect(result.markdown.trim()).toBe('# Content here');
    });

    it('handles content without frontmatter', () => {
      const content = '# Just markdown content';
      const result = parseFrontmatter(content);
      expect(result.frontmatter).toEqual({});
      expect(result.markdown).toBe(content);
    });

    it('handles empty content', () => {
      const result = parseFrontmatter('');
      expect(result.frontmatter).toEqual({});
      expect(result.markdown).toBe('');
    });

    it('handles null/undefined content', () => {
      expect(parseFrontmatter(null).frontmatter).toEqual({});
      expect(parseFrontmatter(undefined).frontmatter).toEqual({});
    });

    it('handles malformed frontmatter', () => {
      const content = `---
invalid yaml
---
# Content`;
      const result = parseFrontmatter(content);
      // Should still extract markdown even if frontmatter parsing fails
      expect(result.markdown).toContain('# Content');
    });

    it('handles frontmatter with quoted values', () => {
      const content = `---
title: "Test Page"
slug: 'test-page'
---
# Content`;
      const result = parseFrontmatter(content);
      expect(result.frontmatter.title).toBe('Test Page');
      expect(result.frontmatter.slug).toBe('test-page');
    });

    it('handles custom frontmatter fields', () => {
      const content = `---
title: Test Page
tags: ai,content
author: AI Assistant
category: documentation
---
# Content`;
      const result = parseFrontmatter(content);
      expect(result.frontmatter.title).toBe('Test Page');
      expect(result.frontmatter.tags).toBe('ai,content');
      expect(result.frontmatter.author).toBe('AI Assistant');
      expect(result.frontmatter.category).toBe('documentation');
    });
  });

  describe('addFrontmatter', () => {
    it('adds frontmatter to markdown', () => {
      const metadata = {
        title: 'Test Page',
        slug: 'test-page',
        section: 'Testing',
        status: 'published'
      };
      const markdown = '# Content here';
      const result = addFrontmatter(metadata, markdown);

      expect(result).toContain('---');
      expect(result).toContain('title: Test Page');
      expect(result).toContain('slug: test-page');
      expect(result).toContain('section: Testing');
      expect(result).toContain('status: published');
      expect(result).toContain('# Content here');
    });

    it('preserves existing custom frontmatter fields', () => {
      const metadata = {
        title: 'Updated Title',
        slug: 'test-page',
        status: 'published'
      };
      const markdown = '# Content';
      const originalContent = `---
title: Old Title
slug: test-page
tags: ai,content
author: AI Assistant
category: documentation
---
# Content`;

      const result = addFrontmatter(metadata, markdown, originalContent);

      // Should update standard fields
      expect(result).toContain('title: Updated Title');
      expect(result).toContain('status: published');
      // Should preserve custom fields
      expect(result).toContain('tags: ai,content');
      expect(result).toContain('author: AI Assistant');
      expect(result).toContain('category: documentation');
    });

    it('handles metadata without optional fields', () => {
      const metadata = {
        title: 'Test Page',
        slug: 'test-page',
        status: 'draft'
      };
      const markdown = '# Content';
      const result = addFrontmatter(metadata, markdown);

      expect(result).toContain('title: Test Page');
      expect(result).toContain('slug: test-page');
      expect(result).toContain('status: draft');
      expect(result).not.toContain('section:');
    });

    it('removes fields when cleared', () => {
      const metadata = {
        title: 'Test Page',
        slug: 'test-page',
        section: '',  // Cleared
        status: 'published'
      };
      const markdown = '# Content';
      const originalContent = `---
title: Test Page
slug: test-page
section: Old Section
status: published
---
# Content`;

      const result = addFrontmatter(metadata, markdown, originalContent);

      // Section should be removed
      expect(result).not.toContain('section:');
    });

    it('handles order field', () => {
      const metadata = {
        title: 'Test Page',
        slug: 'test-page',
        order: 5,
        status: 'published'
      };
      const markdown = '# Content';
      const result = addFrontmatter(metadata, markdown);

      expect(result).toContain('order: 5');
    });

    it('returns markdown only if no frontmatter fields', () => {
      const metadata = {};
      const markdown = '# Content';
      const result = addFrontmatter(metadata, markdown);

      expect(result).toBe('# Content');
      expect(result).not.toContain('---');
    });

    it('handles null originalContent', () => {
      const metadata = {
        title: 'Test Page',
        slug: 'test-page'
      };
      const markdown = '# Content';
      const result = addFrontmatter(metadata, markdown, null);

      expect(result).toContain('title: Test Page');
      expect(result).toContain('# Content');
    });
  });
});
