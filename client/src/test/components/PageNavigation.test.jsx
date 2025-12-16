import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PageNavigation } from '../../components/navigation/PageNavigation';

describe('PageNavigation', () => {
  it('renders nothing when navigation is null', () => {
    const { container } = render(
      <MemoryRouter>
        <PageNavigation navigation={null} />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when both previous and next are null', () => {
    const navigation = { previous: null, next: null };
    const { container } = render(
      <MemoryRouter>
        <PageNavigation navigation={navigation} />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders previous link when available', () => {
    const navigation = {
      previous: { id: 'page-1', title: 'Previous Page', slug: 'previous' },
      next: null,
    };

    render(
      <MemoryRouter>
        <PageNavigation navigation={navigation} />
      </MemoryRouter>
    );

    const prevLink = screen.getByText('Previous Page').closest('a');
    expect(prevLink).toBeInTheDocument();
    expect(prevLink).toHaveAttribute('href', '/pages/page-1');
    expect(prevLink).toHaveClass('arc-page-nav-prev');
  });

  it('renders next link when available', () => {
    const navigation = {
      previous: null,
      next: { id: 'page-2', title: 'Next Page', slug: 'next' },
    };

    render(
      <MemoryRouter>
        <PageNavigation navigation={navigation} />
      </MemoryRouter>
    );

    const nextLink = screen.getByText('Next Page').closest('a');
    expect(nextLink).toBeInTheDocument();
    expect(nextLink).toHaveAttribute('href', '/pages/page-2');
    expect(nextLink).toHaveClass('arc-page-nav-next');
  });

  it('renders both previous and next links', () => {
    const navigation = {
      previous: { id: 'page-1', title: 'Previous Page', slug: 'previous' },
      next: { id: 'page-3', title: 'Next Page', slug: 'next' },
    };

    render(
      <MemoryRouter>
        <PageNavigation navigation={navigation} />
      </MemoryRouter>
    );

    expect(screen.getByText('Previous Page')).toBeInTheDocument();
    expect(screen.getByText('Next Page')).toBeInTheDocument();
  });

  it('displays disabled state when previous is null', () => {
    const navigation = {
      previous: null,
      next: { id: 'page-2', title: 'Next Page', slug: 'next' },
    };

    render(
      <MemoryRouter>
        <PageNavigation navigation={navigation} />
      </MemoryRouter>
    );

    const prevDisabled = screen.getByText('—').closest('.arc-page-nav-disabled');
    expect(prevDisabled).toBeInTheDocument();
    expect(prevDisabled).toHaveClass('arc-page-nav-prev');
  });

  it('displays disabled state when next is null', () => {
    const navigation = {
      previous: { id: 'page-1', title: 'Previous Page', slug: 'previous' },
      next: null,
    };

    render(
      <MemoryRouter>
        <PageNavigation navigation={navigation} />
      </MemoryRouter>
    );

    const nextDisabled = screen.getByText('—').closest('.arc-page-nav-disabled');
    expect(nextDisabled).toBeInTheDocument();
    expect(nextDisabled).toHaveClass('arc-page-nav-next');
  });

  it('displays labels correctly', () => {
    const navigation = {
      previous: { id: 'page-1', title: 'Previous Page', slug: 'previous' },
      next: { id: 'page-2', title: 'Next Page', slug: 'next' },
    };

    render(
      <MemoryRouter>
        <PageNavigation navigation={navigation} />
      </MemoryRouter>
    );

    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('has proper aria-label for accessibility', () => {
    const navigation = {
      previous: { id: 'page-1', title: 'Previous Page', slug: 'previous' },
      next: { id: 'page-2', title: 'Next Page', slug: 'next' },
    };

    render(
      <MemoryRouter>
        <PageNavigation navigation={navigation} />
      </MemoryRouter>
    );

    const nav = screen.getByLabelText('Page navigation');
    expect(nav).toBeInTheDocument();
  });
});
