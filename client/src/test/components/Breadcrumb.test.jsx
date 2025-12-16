import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Breadcrumb } from '../../components/navigation/Breadcrumb';

describe('Breadcrumb', () => {
  it('renders nothing when breadcrumb is null', () => {
    const { container } = render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={null} currentPageId="page-1" />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when breadcrumb is empty', () => {
    const { container } = render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={[]} currentPageId="page-1" />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when only one item (root page)', () => {
    const breadcrumb = [{ id: 'page-1', title: 'Home', slug: 'home' }];
    const { container } = render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="page-1" />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders breadcrumb trail with multiple items', () => {
    const breadcrumb = [
      { id: 'page-1', title: 'Home', slug: 'home' },
      { id: 'page-2', title: 'Section', slug: 'section' },
      { id: 'page-3', title: 'Current Page', slug: 'current' },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="page-3" />
      </MemoryRouter>
    );

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Section')).toBeInTheDocument();
    expect(screen.getByText('Current Page')).toBeInTheDocument();
  });

  it('makes all items except last clickable', () => {
    const breadcrumb = [
      { id: 'page-1', title: 'Home', slug: 'home' },
      { id: 'page-2', title: 'Section', slug: 'section' },
      { id: 'page-3', title: 'Current Page', slug: 'current' },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="page-3" />
      </MemoryRouter>
    );

    const homeLink = screen.getByText('Home').closest('a');
    const sectionLink = screen.getByText('Section').closest('a');
    const currentPage = screen.getByText('Current Page').closest('span');

    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute('href', '/pages/page-1');
    expect(sectionLink).toBeInTheDocument();
    expect(sectionLink).toHaveAttribute('href', '/pages/page-2');
    expect(currentPage).toBeInTheDocument();
    expect(currentPage).toHaveClass('arc-breadcrumb-current');
  });

  it('displays separators between items', () => {
    const breadcrumb = [
      { id: 'page-1', title: 'Home', slug: 'home' },
      { id: 'page-2', title: 'Section', slug: 'section' },
      { id: 'page-3', title: 'Current Page', slug: 'current' },
    ];

    const { container } = render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="page-3" />
      </MemoryRouter>
    );

    // Check for separator elements by class instead of text (text is split)
    const separators = container.querySelectorAll('.arc-breadcrumb-separator');
    expect(separators).toHaveLength(2); // Between Home-Section and Section-Current
  });

  it('marks current page correctly even if not last in array', () => {
    const breadcrumb = [
      { id: 'page-1', title: 'Home', slug: 'home' },
      { id: 'page-2', title: 'Current Page', slug: 'current' },
      { id: 'page-3', title: 'Child Page', slug: 'child' },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="page-2" />
      </MemoryRouter>
    );

    const currentPage = screen.getByText('Current Page').closest('span');
    expect(currentPage).toHaveClass('arc-breadcrumb-current');
    expect(currentPage).toHaveAttribute('aria-current', 'page');
  });

  it('handles breadcrumb items with missing fields gracefully', () => {
    const breadcrumb = [
      { id: 'page-1', title: 'Home' }, // Missing slug
      { id: 'page-2', slug: 'section' }, // Missing title
      { id: 'page-3', title: 'Current', slug: 'current' },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="page-3" />
      </MemoryRouter>
    );

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('handles very long breadcrumb trails', () => {
    const breadcrumb = Array.from({ length: 10 }, (_, i) => ({
      id: `page-${i + 1}`,
      title: `Level ${i + 1}`,
      slug: `level-${i + 1}`,
    }));

    render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="page-10" />
      </MemoryRouter>
    );

    expect(screen.getByText('Level 1')).toBeInTheDocument();
    expect(screen.getByText('Level 10')).toBeInTheDocument();
  });

  it('handles breadcrumb with special characters in titles', () => {
    const breadcrumb = [
      { id: 'page-1', title: 'Home & < > " \' Special', slug: 'home' },
      { id: 'page-2', title: 'Current', slug: 'current' },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="page-2" />
      </MemoryRouter>
    );

    expect(screen.getByText('Home & < > " \' Special')).toBeInTheDocument();
  });

  it('handles empty string currentPageId', () => {
    const breadcrumb = [
      { id: 'page-1', title: 'Home', slug: 'home' },
      { id: 'page-2', title: 'Current', slug: 'current' },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId="" />
      </MemoryRouter>
    );

    // Should still render, treating empty as not current
    expect(screen.getByText('Home')).toBeInTheDocument();
  });

  it('handles null currentPageId', () => {
    const breadcrumb = [
      { id: 'page-1', title: 'Home', slug: 'home' },
      { id: 'page-2', title: 'Current', slug: 'current' },
    ];

    render(
      <MemoryRouter>
        <Breadcrumb breadcrumb={breadcrumb} currentPageId={null} />
      </MemoryRouter>
    );

    // Should still render
    expect(screen.getByText('Home')).toBeInTheDocument();
  });
});
