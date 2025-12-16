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
});
