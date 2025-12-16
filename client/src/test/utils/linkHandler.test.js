import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { isInternalLink, processLinks } from '../../utils/linkHandler';

describe('linkHandler utilities', () => {
  describe('isInternalLink', () => {
    it('returns false for null or undefined', () => {
      expect(isInternalLink(null)).toBe(false);
      expect(isInternalLink(undefined)).toBe(false);
    });

    it('returns false for external HTTP links', () => {
      expect(isInternalLink('http://example.com')).toBe(false);
      expect(isInternalLink('https://example.com/page')).toBe(false);
    });

    it('returns false for mailto links', () => {
      expect(isInternalLink('mailto:test@example.com')).toBe(false);
    });

    it('returns false for tel links', () => {
      expect(isInternalLink('tel:+1234567890')).toBe(false);
    });

    it('returns true for anchor links', () => {
      expect(isInternalLink('#section')).toBe(true);
      expect(isInternalLink('#anchor-id')).toBe(true);
    });

    it('returns true for /pages/ links', () => {
      expect(isInternalLink('/pages/page-id')).toBe(true);
      expect(isInternalLink('/pages/123e4567-e89b-12d3-a456-426614174000')).toBe(true);
    });

    it('returns true for relative paths', () => {
      expect(isInternalLink('./page')).toBe(true);
      expect(isInternalLink('../parent/page')).toBe(true);
      expect(isInternalLink('relative/path')).toBe(true);
    });

    it('returns true for UUID page IDs', () => {
      expect(isInternalLink('123e4567-e89b-12d3-a456-426614174000')).toBe(true);
      expect(isInternalLink('00000000-0000-0000-0000-000000000001')).toBe(true);
    });

    it('returns true for relative paths without protocol', () => {
      expect(isInternalLink('page/slug')).toBe(true);
      expect(isInternalLink('section/page')).toBe(true);
    });

    it('returns false for links with other protocols', () => {
      expect(isInternalLink('ftp://example.com')).toBe(false);
      expect(isInternalLink('file:///path/to/file')).toBe(false);
    });
  });

  describe('processLinks', () => {
    let container;

    beforeEach(() => {
      container = document.createElement('div');
      document.body.appendChild(container);
    });

    afterEach(() => {
      document.body.removeChild(container);
    });

    it('does nothing when container is null', () => {
      expect(() => processLinks(null)).not.toThrow();
    });

    it('adds internal link class to internal links', () => {
      container.innerHTML = '<a href="/pages/page-1">Internal Link</a>';
      processLinks(container);

      const link = container.querySelector('a');
      expect(link.classList.contains('arc-link-internal')).toBe(true);
      expect(link.classList.contains('arc-link-external')).toBe(false);
    });

    it('adds external link class to external links', () => {
      container.innerHTML = '<a href="https://example.com">External Link</a>';
      processLinks(container);

      const link = container.querySelector('a');
      expect(link.classList.contains('arc-link-external')).toBe(true);
      expect(link.classList.contains('arc-link-internal')).toBe(false);
      expect(link.getAttribute('target')).toBe('_blank');
      expect(link.getAttribute('rel')).toBe('noopener noreferrer');
    });

    it('does not modify anchor links', () => {
      container.innerHTML = '<a href="#section">Anchor Link</a>';
      processLinks(container);

      const link = container.querySelector('a');
      expect(link.classList.contains('arc-link-internal')).toBe(true);
      expect(link.getAttribute('target')).toBeNull();
    });

    it('processes multiple links correctly', () => {
      container.innerHTML = `
        <a href="/pages/page-1">Internal</a>
        <a href="https://example.com">External</a>
        <a href="#section">Anchor</a>
      `;
      processLinks(container);

      const links = container.querySelectorAll('a');
      expect(links[0].classList.contains('arc-link-internal')).toBe(true);
      expect(links[1].classList.contains('arc-link-external')).toBe(true);
      expect(links[2].classList.contains('arc-link-internal')).toBe(true);
    });

    it('handles links without href', () => {
      container.innerHTML = '<a>No href</a>';
      expect(() => processLinks(container)).not.toThrow();
    });
  });
});
