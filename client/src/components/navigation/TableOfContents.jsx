import React, { useState, useEffect, useRef } from 'react';

/**
 * TableOfContents component displays page headings as a navigation menu
 *
 * Features:
 * - Auto-generated from page headings (H2-H6)
 * - Click to scroll to section (smooth scroll)
 * - Highlight current section while scrolling
 * - Sticky positioning
 * - Indentation for nested headings
 * - Active section highlighting
 * - Collapsible for short pages
 */
export function TableOfContents({ toc, contentRef }) {
  const [activeSection, setActiveSection] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const tocRef = useRef(null);

  // Determine if page is "short" (fewer than 5 TOC items)
  const isShortPage = toc && toc.length < 5;

  // Scroll to section when TOC item is clicked
  const scrollToSection = (anchor) => {
    if (!contentRef?.current) return;

    try {
      // Validate anchor is a valid CSS selector
      const element = contentRef.current.querySelector(`#${anchor}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Update active section immediately
        setActiveSection(anchor);
      }
    } catch (error) {
      // Invalid selector (e.g., starts with number) - silently fail
      // These are from old pages saved before the anchor fix
      // The anchor will be fixed when the page is next saved
    }
  };

  // Highlight current section while scrolling
  useEffect(() => {
    if (!toc || !contentRef?.current) return;

    const headings = toc.map((item) => {
      try {
        // Validate anchor is a valid CSS selector (e.g., doesn't start with number)
        // querySelector will throw if selector is invalid
        const element = contentRef.current.querySelector(`#${item.anchor}`);
        return { anchor: item.anchor, element };
      } catch (error) {
        // Invalid selector (e.g., starts with number) - skip this heading silently
        // These are from old pages saved before the anchor fix
        return { anchor: item.anchor, element: null };
      }
    }).filter((item) => item.element);

    if (headings.length === 0) return;

    const handleScroll = () => {
      const scrollPosition = window.scrollY + 100; // Offset for header

      // Find the current section based on scroll position
      let current = null;
      for (let i = headings.length - 1; i >= 0; i--) {
        const heading = headings[i];
        if (heading.element && heading.element.offsetTop <= scrollPosition) {
          current = heading.anchor;
          break;
        }
      }

      setActiveSection(current);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // Check initial position

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [toc, contentRef]);

  if (!toc || toc.length === 0) {
    return null;
  }

  return (
    <nav className="arc-toc" ref={tocRef} aria-label="Table of contents">
      <div className="arc-toc-header">
        <h3 className="arc-toc-title">Contents</h3>
        {isShortPage && (
          <button
            type="button"
            className="arc-toc-toggle"
            onClick={() => setIsCollapsed(!isCollapsed)}
            aria-expanded={!isCollapsed}
            aria-label={isCollapsed ? 'Expand table of contents' : 'Collapse table of contents'}
          >
            <span className="arc-toc-toggle-icon">
              {isCollapsed ? '▶' : '▼'}
            </span>
          </button>
        )}
      </div>
      {!isCollapsed && (
        <ul className="arc-toc-list">
          {toc.map((item, index) => (
            <li
              key={`${item.anchor}-${index}`}
              className={`arc-toc-item arc-toc-item-level-${item.level} ${
                activeSection === item.anchor ? 'arc-toc-item-active' : ''
              }`}
            >
              <button
                type="button"
                className="arc-toc-link"
                onClick={() => scrollToSection(item.anchor)}
                aria-current={activeSection === item.anchor ? 'location' : undefined}
              >
                {item.text}
              </button>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}
