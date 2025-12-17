import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Backlinks } from '../../components/navigation/Backlinks';

describe('Backlinks', () => {
  const renderBacklinks = (backlinks) => {
    return render(
      <MemoryRouter>
        <Backlinks backlinks={backlinks} />
      </MemoryRouter>
    );
  };

  it('returns null when backlinks is null', () => {
    const { container } = renderBacklinks(null);
    expect(container.firstChild).toBeNull();
  });

  it('returns null when backlinks is empty array', () => {
    const { container } = renderBacklinks([]);
    expect(container.firstChild).toBeNull();
  });

  it('renders backlinks list with items', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'Linking Page 1' },
      { page_id: 'page-2', title: 'Linking Page 2' },
      { page_id: 'page-3', title: 'Linking Page 3' },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText('Pages Linking Here')).toBeInTheDocument();
    expect(screen.getByText('(3)')).toBeInTheDocument();
    expect(screen.getByText('Linking Page 1')).toBeInTheDocument();
    expect(screen.getByText('Linking Page 2')).toBeInTheDocument();
    expect(screen.getByText('Linking Page 3')).toBeInTheDocument();
  });

  it('displays correct backlink count', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'Page 1' },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText('(1)')).toBeInTheDocument();
  });

  it('renders links with correct hrefs', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'Linking Page 1' },
      { page_id: 'page-2', title: 'Linking Page 2' },
    ];

    renderBacklinks(backlinks);
    
    const links = screen.getAllByRole('link');
    expect(links[0]).toHaveAttribute('href', '/pages/page-1');
    expect(links[1]).toHaveAttribute('href', '/pages/page-2');
  });

  it('has proper ARIA labels', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'Linking Page 1' },
    ];

    renderBacklinks(backlinks);
    
    const nav = screen.getByRole('navigation', { name: 'Pages linking here' });
    expect(nav).toBeInTheDocument();
  });

  it('handles single backlink', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'Only Linking Page' },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText('Pages Linking Here')).toBeInTheDocument();
    expect(screen.getByText('(1)')).toBeInTheDocument();
    expect(screen.getByText('Only Linking Page')).toBeInTheDocument();
  });

  it('handles many backlinks', () => {
    const backlinks = Array.from({ length: 10 }, (_, i) => ({
      page_id: `page-${i + 1}`,
      title: `Linking Page ${i + 1}`,
    }));

    renderBacklinks(backlinks);
    
    expect(screen.getByText('(10)')).toBeInTheDocument();
    expect(screen.getByText('Linking Page 1')).toBeInTheDocument();
    expect(screen.getByText('Linking Page 10')).toBeInTheDocument();
  });

  it('renders list items with correct structure', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'Linking Page 1' },
    ];

    renderBacklinks(backlinks);
    
    const list = screen.getByRole('list');
    expect(list).toBeInTheDocument();
    expect(list.children.length).toBe(1);
    
    const listItem = screen.getByRole('listitem');
    expect(listItem).toBeInTheDocument();
    
    const link = screen.getByRole('link');
    expect(link).toBeInTheDocument();
    expect(link.textContent).toBe('Linking Page 1');
  });

  it('handles backlinks with missing fields gracefully', () => {
    const backlinks = [
      { page_id: 'page-1' }, // Missing title
      { title: 'Page 2' }, // Missing page_id
    ];

    expect(() => {
      renderBacklinks(backlinks);
    }).not.toThrow();
  });

  it('handles very long backlink titles', () => {
    const longTitle = 'A'.repeat(200);
    const backlinks = [
      { page_id: 'page-1', title: longTitle },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText(longTitle)).toBeInTheDocument();
  });

  it('handles special characters in backlink titles', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'Page & < > " \' Special' },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText('Page & < > " \' Special')).toBeInTheDocument();
  });

  it('handles duplicate page_ids', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'First Link' },
      { page_id: 'page-1', title: 'Second Link' },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText('First Link')).toBeInTheDocument();
    expect(screen.getByText('Second Link')).toBeInTheDocument();
    expect(screen.getByText('(2)')).toBeInTheDocument();
  });

  it('handles empty string titles', () => {
    const backlinks = [
      { page_id: 'page-1', title: '' },
    ];

    renderBacklinks(backlinks);
    
    // Should still render structure
    expect(screen.getByText('Pages Linking Here')).toBeInTheDocument();
  });

  it('handles null page_id gracefully', () => {
    const backlinks = [
      { page_id: null, title: 'Link' },
    ];

    expect(() => {
      renderBacklinks(backlinks);
    }).not.toThrow();
  });

  it('displays context snippet when available', () => {
    const backlinks = [
      {
        page_id: 'page-1',
        title: 'Linking Page',
        context: 'This page links to the current page in the introduction section.',
      },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText('Linking Page')).toBeInTheDocument();
    expect(screen.getByText(/This page links to the current page/i)).toBeInTheDocument();
  });

  it('does not display context snippet when not available', () => {
    const backlinks = [
      { page_id: 'page-1', title: 'Linking Page' },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText('Linking Page')).toBeInTheDocument();
    const contextElements = screen.queryAllByText(/context/i);
    expect(contextElements.length).toBe(0);
  });

  it('handles backlinks with and without context', () => {
    const backlinks = [
      {
        page_id: 'page-1',
        title: 'Page with Context',
        context: 'Context snippet here',
      },
      { page_id: 'page-2', title: 'Page without Context' },
    ];

    renderBacklinks(backlinks);
    
    expect(screen.getByText('Page with Context')).toBeInTheDocument();
    expect(screen.getByText('Context snippet here')).toBeInTheDocument();
    expect(screen.getByText('Page without Context')).toBeInTheDocument();
  });

  it('displays context with proper styling', () => {
    const backlinks = [
      {
        page_id: 'page-1',
        title: 'Linking Page',
        context: 'Context snippet',
      },
    ];

    renderBacklinks(backlinks);
    
    const contextElement = screen.getByText('Context snippet');
    expect(contextElement).toHaveClass('arc-backlinks-context');
  });
});
