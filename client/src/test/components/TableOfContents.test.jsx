import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TableOfContents } from '../../components/navigation/TableOfContents';

describe('TableOfContents', () => {
  let contentRef;
  let container;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    contentRef = { current: container };
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  it('returns null when toc is null', () => {
    const { container: result } = render(<TableOfContents toc={null} contentRef={contentRef} />);
    expect(result.firstChild).toBeNull();
  });

  it('returns null when toc is empty array', () => {
    const { container: result } = render(<TableOfContents toc={[]} contentRef={contentRef} />);
    expect(result.firstChild).toBeNull();
  });

  it('renders table of contents with items', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
      { anchor: 'section-2', text: 'Section 2', level: 2 },
      { anchor: 'subsection-2-1', text: 'Subsection 2.1', level: 3 },
    ];

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    expect(screen.getByText('Contents')).toBeInTheDocument();
    expect(screen.getByText('Section 1')).toBeInTheDocument();
    expect(screen.getByText('Section 2')).toBeInTheDocument();
    expect(screen.getByText('Subsection 2.1')).toBeInTheDocument();
  });

  it('applies correct level classes', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
      { anchor: 'subsection-1', text: 'Subsection', level: 3 },
      { anchor: 'subsubsection-1', text: 'Subsubsection', level: 4 },
    ];

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    const items = screen.getAllByRole('button');
    const section1 = items.find(item => item.textContent === 'Section 1');
    const subsection = items.find(item => item.textContent === 'Subsection');
    const subsubsection = items.find(item => item.textContent === 'Subsubsection');
    
    expect(section1.closest('li')).toHaveClass('arc-toc-item-level-2');
    expect(subsection.closest('li')).toHaveClass('arc-toc-item-level-3');
    expect(subsubsection.closest('li')).toHaveClass('arc-toc-item-level-4');
  });

  it('scrolls to section when item is clicked', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
    ];

    // Create a mock element with the anchor ID
    const mockElement = document.createElement('h2');
    mockElement.id = 'section-1';
    mockElement.textContent = 'Section 1';
    container.appendChild(mockElement);

    // Mock scrollIntoView
    mockElement.scrollIntoView = vi.fn();

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    const button = screen.getByRole('button', { name: 'Section 1' });
    fireEvent.click(button);

    expect(mockElement.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start',
    });
  });

  it('handles missing contentRef gracefully', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
    ];

    expect(() => {
      render(<TableOfContents toc={toc} contentRef={null} />);
    }).not.toThrow();
  });

  it('handles missing element in contentRef gracefully', () => {
    const toc = [
      { anchor: 'nonexistent', text: 'Nonexistent Section', level: 2 },
    ];

    expect(() => {
      render(<TableOfContents toc={toc} contentRef={contentRef} />);
      const button = screen.getByText('Nonexistent Section');
      fireEvent.click(button);
    }).not.toThrow();
  });

  it('sets active section when item is clicked', async () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
    ];

    const mockElement = document.createElement('h2');
    mockElement.id = 'section-1';
    container.appendChild(mockElement);
    mockElement.scrollIntoView = vi.fn();

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    const button = screen.getByRole('button', { name: 'Section 1' });
    fireEvent.click(button);

    await waitFor(() => {
      expect(button).toHaveAttribute('aria-current', 'location');
    });
  });

  it('has proper ARIA labels', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
    ];

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    const nav = screen.getByRole('navigation', { name: 'Table of contents' });
    expect(nav).toBeInTheDocument();
  });

  it('handles multiple items with same anchor', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
      { anchor: 'section-1', text: 'Section 1 Duplicate', level: 2 },
    ];

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    expect(screen.getByText('Section 1')).toBeInTheDocument();
    expect(screen.getByText('Section 1 Duplicate')).toBeInTheDocument();
  });

  it('handles TOC items with missing fields gracefully', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1' }, // Missing level
      { anchor: 'section-2', level: 2 }, // Missing text
      { text: 'Section 3', level: 2 }, // Missing anchor
    ];

    expect(() => {
      render(<TableOfContents toc={toc} contentRef={contentRef} />);
    }).not.toThrow();
  });

  it('handles very long section titles', () => {
    const longTitle = 'A'.repeat(200);
    const toc = [
      { anchor: 'section-1', text: longTitle, level: 2 },
    ];

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    expect(screen.getByText(longTitle)).toBeInTheDocument();
  });

  it('handles special characters in section titles', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section & < > " \' Special', level: 2 },
    ];

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    expect(screen.getByText('Section & < > " \' Special')).toBeInTheDocument();
  });

  it('handles all heading levels (2-6)', () => {
    const toc = [
      { anchor: 'h2', text: 'H2', level: 2 },
      { anchor: 'h3', text: 'H3', level: 3 },
      { anchor: 'h4', text: 'H4', level: 4 },
      { anchor: 'h5', text: 'H5', level: 5 },
      { anchor: 'h6', text: 'H6', level: 6 },
    ];

    render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    expect(screen.getByText('H2')).toBeInTheDocument();
    expect(screen.getByText('H3')).toBeInTheDocument();
    expect(screen.getByText('H4')).toBeInTheDocument();
    expect(screen.getByText('H5')).toBeInTheDocument();
    expect(screen.getByText('H6')).toBeInTheDocument();
  });

  it('handles invalid level values gracefully', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 1 }, // Level 1 not typically used
      { anchor: 'section-2', text: 'Section 2', level: 7 }, // Level 7 doesn't exist
      { anchor: 'section-3', text: 'Section 3', level: 0 }, // Invalid level
    ];

    expect(() => {
      render(<TableOfContents toc={toc} contentRef={contentRef} />);
    }).not.toThrow();
  });

  it('handles scroll event cleanup', async () => {
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
    ];

    // Create a mock element so the scroll handler is set up
    const mockElement = document.createElement('h2');
    mockElement.id = 'section-1';
    container.appendChild(mockElement);

    const { unmount } = render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    // Wait for scroll listener to be added
    await waitFor(() => {
      expect(addEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function), { passive: true });
    });
    
    // Get the handler function that was added
    const scrollHandler = addEventListenerSpy.mock.calls.find(
      call => call[0] === 'scroll'
    )?.[1];
    
    unmount();
    
    // Cleanup should be called with the same handler function
    if (scrollHandler) {
      expect(removeEventListenerSpy).toHaveBeenCalledWith('scroll', scrollHandler);
    } else {
      // If we can't find the exact handler, at least verify cleanup was attempted
      expect(removeEventListenerSpy).toHaveBeenCalled();
    }
    
    addEventListenerSpy.mockRestore();
    removeEventListenerSpy.mockRestore();
  });

  it('handles contentRef becoming null after mount', () => {
    const toc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
    ];

    const { rerender } = render(<TableOfContents toc={toc} contentRef={contentRef} />);
    
    // Change contentRef to null
    rerender(<TableOfContents toc={toc} contentRef={{ current: null }} />);
    
    // Should not crash
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });

  it('shows collapse button for short pages (< 5 items)', () => {
    const shortToc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
      { anchor: 'section-2', text: 'Section 2', level: 2 },
    ];

    render(<TableOfContents toc={shortToc} contentRef={contentRef} />);
    
    const toggleButton = screen.getByLabelText(/Collapse table of contents/i);
    expect(toggleButton).toBeInTheDocument();
  });

  it('does not show collapse button for long pages (>= 5 items)', () => {
    const longToc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
      { anchor: 'section-2', text: 'Section 2', level: 2 },
      { anchor: 'section-3', text: 'Section 3', level: 2 },
      { anchor: 'section-4', text: 'Section 4', level: 2 },
      { anchor: 'section-5', text: 'Section 5', level: 2 },
    ];

    render(<TableOfContents toc={longToc} contentRef={contentRef} />);
    
    const toggleButton = screen.queryByLabelText(/Collapse table of contents/i);
    expect(toggleButton).not.toBeInTheDocument();
  });

  it('collapses TOC when toggle button is clicked', async () => {
    const user = userEvent.setup();
    const shortToc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
    ];

    render(<TableOfContents toc={shortToc} contentRef={contentRef} />);
    
    const toggleButton = screen.getByLabelText(/Collapse table of contents/i);
    expect(screen.getByText('Section 1')).toBeInTheDocument();
    
    await user.click(toggleButton);
    
    expect(screen.queryByText('Section 1')).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Expand table of contents/i)).toBeInTheDocument();
  });

  it('expands TOC when toggle button is clicked again', async () => {
    const user = userEvent.setup();
    const shortToc = [
      { anchor: 'section-1', text: 'Section 1', level: 2 },
    ];

    render(<TableOfContents toc={shortToc} contentRef={contentRef} />);
    
    const toggleButton = screen.getByLabelText(/Collapse table of contents/i);
    await user.click(toggleButton);
    
    const expandButton = screen.getByLabelText(/Expand table of contents/i);
    await user.click(expandButton);
    
    expect(screen.getByText('Section 1')).toBeInTheDocument();
  });
});
