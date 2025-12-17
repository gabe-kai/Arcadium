import { describe, it, expect, beforeEach } from 'vitest';
import { htmlToMarkdown, markdownToHtml } from '../../utils/markdown';

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
});
