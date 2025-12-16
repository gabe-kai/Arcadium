import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
});
