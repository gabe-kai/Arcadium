import { describe, it, expect } from 'vitest';
import { generateSlug } from '../../utils/slug';

describe('slug utility', () => {
  describe('generateSlug', () => {
    it('generates slug from simple title', () => {
      expect(generateSlug('Hello World')).toBe('hello-world');
    });

    it('converts to lowercase', () => {
      expect(generateSlug('HELLO WORLD')).toBe('hello-world');
    });

    it('replaces spaces with hyphens', () => {
      expect(generateSlug('Hello World Test')).toBe('hello-world-test');
    });

    it('replaces underscores with hyphens', () => {
      expect(generateSlug('hello_world')).toBe('hello-world');
    });

    it('removes special characters', () => {
      expect(generateSlug('Hello & World!')).toBe('hello-world');
      expect(generateSlug('Hello (World)')).toBe('hello-world');
      expect(generateSlug('Hello @ World #')).toBe('hello-world');
    });

    it('removes multiple consecutive hyphens', () => {
      expect(generateSlug('Hello---World')).toBe('hello-world');
      expect(generateSlug('Hello   World')).toBe('hello-world');
    });

    it('removes leading and trailing hyphens', () => {
      expect(generateSlug('-Hello World-')).toBe('hello-world');
      expect(generateSlug('---Hello World---')).toBe('hello-world');
    });

    it('handles empty string', () => {
      expect(generateSlug('')).toBe('');
    });

    it('handles null', () => {
      expect(generateSlug(null)).toBe('');
    });

    it('handles undefined', () => {
      expect(generateSlug(undefined)).toBe('');
    });

    it('preserves numbers', () => {
      expect(generateSlug('Page 123')).toBe('page-123');
      expect(generateSlug('Version 2.0')).toBe('version-20');
    });

    it('handles special characters in title', () => {
      expect(generateSlug('Page & < > " \' Special')).toBe('page-special');
    });

    it('handles very long titles', () => {
      const longTitle = 'A'.repeat(100) + ' ' + 'B'.repeat(100);
      const slug = generateSlug(longTitle);
      expect(slug).toBe('a'.repeat(100) + '-' + 'b'.repeat(100));
    });

    it('handles titles with only special characters', () => {
      expect(generateSlug('!@#$%^&*()')).toBe('');
    });

    it('handles mixed case and special characters', () => {
      expect(generateSlug('Hello World! This Is A Test')).toBe('hello-world-this-is-a-test');
    });

    it('handles unicode characters', () => {
      expect(generateSlug('Café')).toBe('caf');
      expect(generateSlug('Müller')).toBe('mller');
    });

    it('handles titles with numbers at start', () => {
      expect(generateSlug('123 Hello World')).toBe('123-hello-world');
    });

    it('handles titles with numbers at end', () => {
      expect(generateSlug('Hello World 123')).toBe('hello-world-123');
    });

    it('trims whitespace', () => {
      expect(generateSlug('  Hello World  ')).toBe('hello-world');
    });

    it('handles single word', () => {
      expect(generateSlug('Hello')).toBe('hello');
    });

    it('handles single character', () => {
      expect(generateSlug('A')).toBe('a');
    });
  });
});
