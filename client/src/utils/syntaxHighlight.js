/**
 * Syntax highlighting utility using Prism.js
 * Call this after rendering HTML content to highlight code blocks
 */
let PrismLoaded = false;

export function highlightCodeBlocks(container) {
  if (!container || typeof window === 'undefined') {
    return;
  }

  // Wait for Prism to load
  if (!PrismLoaded || !window.Prism) {
    // Try again after a short delay
    setTimeout(() => highlightCodeBlocks(container), 100);
    return;
  }

  // Find all code blocks
  const codeBlocks = container.querySelectorAll('pre code');
  codeBlocks.forEach((block) => {
    // Only highlight if not already highlighted
    if (!block.classList.contains('language-none') && !block.parentElement.classList.contains('language-none')) {
      try {
        window.Prism.highlightElement(block);
      } catch (e) {
        // Ignore highlighting errors
        console.debug('Prism highlighting error:', e);
      }
    }
  });
}

/**
 * Initialize Prism.js for syntax highlighting
 * Call this once when the app loads
 */
export function initSyntaxHighlighting() {
  if (typeof window === 'undefined') {
    return;
  }

  // Import Prism and languages
  import('prismjs').then((PrismModule) => {
    window.Prism = PrismModule.default;
    PrismLoaded = true;

    // Load common languages
    Promise.all([
      import('prismjs/components/prism-javascript'),
      import('prismjs/components/prism-typescript'),
      import('prismjs/components/prism-python'),
      import('prismjs/components/prism-bash'),
      import('prismjs/components/prism-json'),
      import('prismjs/components/prism-markdown'),
      import('prismjs/components/prism-css'),
      import('prismjs/components/prism-sql'),
    ]).catch((err) => {
      console.debug('Error loading Prism languages:', err);
    });
  }).catch((err) => {
    console.warn('Failed to load Prism.js:', err);
  });
}
