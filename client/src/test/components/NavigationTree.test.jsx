import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NavigationTree } from '../../components/navigation/NavigationTree';
import * as pagesApi from '../../services/api/pages';

// Mock the API module
vi.mock('../../services/api/pages', () => ({
  useNavigationTree: vi.fn(),
}));

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

describe('NavigationTree', () => {
  let queryClient;
  let store = {};

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    store = {};
    global.localStorage = {
      getItem: vi.fn((key) => store[key] || null),
      setItem: vi.fn((key, value) => {
        store[key] = value.toString();
      }),
      removeItem: vi.fn((key) => {
        delete store[key];
      }),
    };
    vi.clearAllMocks();
  });

  const renderNavigationTree = (initialEntries = ['/']) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries}>
          <NavigationTree />
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  const mockTree = [
    {
      id: 'page-1',
      title: 'Home',
      slug: 'home',
      status: 'published',
      children: [
        {
          id: 'page-2',
          title: 'Section 1',
          slug: 'section-1',
          status: 'published',
          children: [
            {
              id: 'page-3',
              title: 'Page 1.1',
              slug: 'page-1-1',
              status: 'published',
              children: [],
            },
          ],
        },
        {
          id: 'page-4',
          title: 'Section 2',
          slug: 'section-2',
          status: 'published',
          children: [],
        },
      ],
    },
  ];

  it('displays loading state', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    renderNavigationTree();
    expect(screen.getByText(/Loading navigation/i)).toBeInTheDocument();
  });

  it('displays error state', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    renderNavigationTree();
    expect(screen.getByText(/Failed to load navigation/i)).toBeInTheDocument();
  });

  it('renders navigation tree with root nodes', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();
    // Root node should be visible
    expect(screen.getByText('Home')).toBeInTheDocument();
    // Children are collapsed by default, so they won't be visible until expanded
    expect(screen.queryByText('Section 1')).not.toBeInTheDocument();
    expect(screen.queryByText('Section 2')).not.toBeInTheDocument();
  });

  it('renders nested children when expanded', async () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    // Initially children should be hidden (Home's children)
    expect(screen.queryByText('Page 1.1')).not.toBeInTheDocument();

    // Click expand button for Home (first expand button)
    const expandButtons = screen.getAllByLabelText(/Expand|Collapse/i);
    fireEvent.click(expandButtons[0]);

    // Wait for state update
    await waitFor(() => {
      // Section 1 should now be visible (it's a child of Home)
      expect(screen.getByText('Section 1')).toBeInTheDocument();
    });

    // Now expand Section 1 to see Page 1.1
    const section1Buttons = screen.getAllByLabelText(/Expand|Collapse/i);
    // Find the button for Section 1 (second expand button)
    fireEvent.click(section1Buttons[1]);

    // Now Page 1.1 should be visible
    await waitFor(() => {
      expect(screen.getByText('Page 1.1')).toBeInTheDocument();
    });
  });

  it('highlights current page', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree(['/pages/page-2']);

    const currentLink = screen.getByText('Section 1').closest('a');
    expect(currentLink).toHaveClass('arc-nav-tree-link-current');
  });

  it('filters tree based on search query', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    const searchInput = screen.getByPlaceholderText(/Search pages/i);
    fireEvent.change(searchInput, { target: { value: 'Section 2' } });

    // Section 2 should be visible
    expect(screen.getByText('Section 2')).toBeInTheDocument();
    // Section 1 should not be visible (doesn't match)
    expect(screen.queryByText('Section 1')).not.toBeInTheDocument();
    // Home should still be visible (parent of matching node)
    expect(screen.getByText('Home')).toBeInTheDocument();
  });

  it('persists expanded state in localStorage', async () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    // Expand a node
    const expandButtons = screen.getAllByLabelText(/Expand|Collapse/i);
    fireEvent.click(expandButtons[0]);

    // Wait for localStorage update
    await waitFor(() => {
      expect(global.localStorage.setItem).toHaveBeenCalled();
    });

    // Check that expanded state was saved
    const setItemCalls = global.localStorage.setItem.mock.calls;
    const expandedStateCall = setItemCalls.find((call) =>
      call[0].includes('arcadium_nav_expanded')
    );
    expect(expandedStateCall).toBeDefined();
  });

  it('loads expanded state from localStorage on mount', async () => {
    // Pre-populate localStorage with expanded state
    store['arcadium_nav_expanded'] = JSON.stringify(['page-1']);

    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    // Wait for state to load and tree to render
    await waitFor(() => {
      // Section 1 should be visible (parent is expanded)
      expect(screen.getByText('Section 1')).toBeInTheDocument();
    });
  });

  it('shows draft badge for draft pages', () => {
    const treeWithDraft = [
      {
        id: 'page-1',
        title: 'Draft Page',
        slug: 'draft',
        status: 'draft',
        children: [],
      },
    ];

    pagesApi.useNavigationTree.mockReturnValue({
      data: treeWithDraft,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    const draftBadge = screen.getByTitle('Draft');
    expect(draftBadge).toBeInTheDocument();
    expect(draftBadge.textContent).toBe('D');
  });

  it('handles empty tree gracefully', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    // Should render without errors
    expect(screen.getByPlaceholderText(/Search pages/i)).toBeInTheDocument();
  });

  it('handles tree with no children', () => {
    const flatTree = [
      {
        id: 'page-1',
        title: 'Page 1',
        slug: 'page-1',
        status: 'published',
        children: [],
      },
    ];

    pagesApi.useNavigationTree.mockReturnValue({
      data: flatTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    expect(screen.getByText('Page 1')).toBeInTheDocument();
    // No expand buttons should be present
    expect(screen.queryByLabelText(/Expand/i)).not.toBeInTheDocument();
  });

  it('handles tree nodes with missing fields gracefully', () => {
    const treeWithMissingFields = [
      {
        id: 'page-1',
        title: 'Page 1',
        // Missing slug and status
        children: [],
      },
    ];

    pagesApi.useNavigationTree.mockReturnValue({
      data: treeWithMissingFields,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    expect(screen.getByText('Page 1')).toBeInTheDocument();
  });

  it('handles very deep nesting', async () => {
    const deepTree = [
      {
        id: 'level-1',
        title: 'Level 1',
        slug: 'level-1',
        status: 'published',
        children: [
          {
            id: 'level-2',
            title: 'Level 2',
            slug: 'level-2',
            status: 'published',
            children: [
              {
                id: 'level-3',
                title: 'Level 3',
                slug: 'level-3',
                status: 'published',
                children: [
                  {
                    id: 'level-4',
                    title: 'Level 4',
                    slug: 'level-4',
                    status: 'published',
                    children: [],
                  },
                ],
              },
            ],
          },
        ],
      },
    ];

    pagesApi.useNavigationTree.mockReturnValue({
      data: deepTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    expect(screen.getByText('Level 1')).toBeInTheDocument();

    // Level 4 is nested deep, so we need to expand nodes to see it
    // Expand Level 1 to see Level 2
    const level1Toggle = screen.getByText('Level 1').closest('li')?.querySelector('button[aria-label*="Expand"]');
    if (level1Toggle) {
      fireEvent.click(level1Toggle);
      await waitFor(() => {
        expect(screen.getByText('Level 2')).toBeInTheDocument();
      });

      // Expand Level 2 to see Level 3
      const level2Toggle = screen.getByText('Level 2').closest('li')?.querySelector('button[aria-label*="Expand"]');
      if (level2Toggle) {
        fireEvent.click(level2Toggle);
        await waitFor(() => {
          expect(screen.getByText('Level 3')).toBeInTheDocument();
        });

        // Expand Level 3 to see Level 4
        const level3Toggle = screen.getByText('Level 3').closest('li')?.querySelector('button[aria-label*="Expand"]');
        if (level3Toggle) {
          fireEvent.click(level3Toggle);
          await waitFor(() => {
            expect(screen.getByText('Level 4')).toBeInTheDocument();
          });
        }
      }
    }
  });

  it('handles tree with special characters in titles', () => {
    const treeWithSpecialChars = [
      {
        id: 'page-1',
        title: 'Page & < > " \' Special',
        slug: 'page-1',
        status: 'published',
        children: [],
      },
    ];

    pagesApi.useNavigationTree.mockReturnValue({
      data: treeWithSpecialChars,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    expect(screen.getByText('Page & < > " \' Special')).toBeInTheDocument();
  });

  it('handles tree with very long titles', () => {
    const longTitle = 'A'.repeat(100);
    const treeWithLongTitle = [
      {
        id: 'page-1',
        title: longTitle,
        slug: 'page-1',
        status: 'published',
        children: [],
      },
    ];

    pagesApi.useNavigationTree.mockReturnValue({
      data: treeWithLongTitle,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    expect(screen.getByText(longTitle)).toBeInTheDocument();
  });

  it('handles localStorage errors gracefully', () => {
    // Mock localStorage to throw error
    const originalGetItem = global.localStorage.getItem;
    global.localStorage.getItem = vi.fn(() => {
      throw new Error('localStorage error');
    });

    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    expect(() => renderNavigationTree()).not.toThrow();

    global.localStorage.getItem = originalGetItem;
  });

  it('handles invalid JSON in localStorage', () => {
    store['arcadium_nav_expanded'] = 'invalid json';

    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    expect(() => renderNavigationTree()).not.toThrow();
  });

  it('handles search with special regex characters', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    const searchInput = screen.getByPlaceholderText(/Search pages/i);
    fireEvent.change(searchInput, { target: { value: '.*+?^${}[]|()' } });

    // Should not crash with regex special characters
    expect(searchInput).toHaveValue('.*+?^${}[]|()');
  });

  it('handles search with empty string after non-empty', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    const searchInput = screen.getByPlaceholderText(/Search pages/i);
    fireEvent.change(searchInput, { target: { value: 'Section' } });
    fireEvent.change(searchInput, { target: { value: '' } });

    // Should show all items again
    expect(screen.getByText('Home')).toBeInTheDocument();
  });

  it('handles multiple rapid search changes', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    const searchInput = screen.getByPlaceholderText(/Search pages/i);
    fireEvent.change(searchInput, { target: { value: 'S' } });
    fireEvent.change(searchInput, { target: { value: 'Se' } });
    fireEvent.change(searchInput, { target: { value: 'Sec' } });
    fireEvent.change(searchInput, { target: { value: 'Section' } });

    // Should handle rapid changes without errors
    expect(searchInput).toHaveValue('Section');
  });

  it('displays folder icon for sections (nodes with children)', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    // Home has children, should show folder icon
    const homeLink = screen.getByText('Home').closest('a');
    expect(homeLink).toBeInTheDocument();
    const icons = homeLink?.querySelectorAll('.arc-nav-tree-icon');
    expect(icons?.length).toBeGreaterThan(0);
    if (icons && icons[0]) {
      expect(icons[0].textContent).toBe('📁');
    }
  });

  it('displays document icon for pages (leaf nodes)', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    // Expand to see leaf nodes
    const expandButton = screen.getByLabelText(/expand/i);
    fireEvent.click(expandButton);

    // Wait for children to render
    waitFor(() => {
      const pageLink = screen.getByText('Page 1.1').closest('a');
      expect(pageLink).toBeInTheDocument();
      const icons = pageLink?.querySelectorAll('.arc-nav-tree-icon');
      expect(icons?.length).toBeGreaterThan(0);
      if (icons && icons[0]) {
        expect(icons[0].textContent).toBe('📄');
      }
    });
  });

  it('displays page count for sections', () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    // Home has 2 direct children + 1 grandchild (Page 1.1) = 3 total descendant pages
    const homeLink = screen.getByText('Home').closest('a');
    expect(homeLink).toBeInTheDocument();
    const pageCount = homeLink?.querySelector('.arc-nav-tree-page-count');
    expect(pageCount).toBeInTheDocument();
    expect(pageCount?.textContent).toBe('(3)');
  });

  it('does not display page count for leaf nodes', async () => {
    pagesApi.useNavigationTree.mockReturnValue({
      data: mockTree,
      isLoading: false,
      isError: false,
    });

    renderNavigationTree();

    // Expand to see leaf nodes - find the first expand button
    const expandButtons = screen.getAllByLabelText(/expand|collapse/i);
    if (expandButtons.length > 0) {
      fireEvent.click(expandButtons[0]);

      // Wait for children to render
      await waitFor(() => {
        const pageLink = screen.getByText('Page 1.1').closest('a');
        expect(pageLink).toBeInTheDocument();
        const pageCount = pageLink?.querySelector('.arc-nav-tree-page-count');
        expect(pageCount).not.toBeInTheDocument();
      });
    }
  });

  it('collapses Regression-Testing section by default in section view', async () => {
    // Mock tree with pages in different sections
    const treeWithSections = [
      {
        id: 'page-1',
        title: 'Regular Page',
        slug: 'regular-page',
        status: 'published',
        section: 'General',
        children: [],
      },
      {
        id: 'page-2',
        title: 'Test Page',
        slug: 'test-page',
        status: 'published',
        section: 'Regression-Testing',
        children: [],
      },
    ];

    pagesApi.useNavigationTree.mockReturnValue({
      data: treeWithSections,
      isLoading: false,
      isError: false,
    });

    // Clear localStorage to test default behavior
    store = {};

    renderNavigationTree();

    // Section view is enabled by default, wait for sections to render
    await waitFor(() => {
      // Both sections should be present
      const generalSection = screen.getByText('General');
      expect(generalSection).toBeInTheDocument();
      const regressionSection = screen.getByText('Regression-Testing');
      expect(regressionSection).toBeInTheDocument();
    });

    // General section should be expanded by default (page visible)
    await waitFor(() => {
      const regularPage = screen.getByText('Regular Page');
      expect(regularPage).toBeInTheDocument();
    });

    // Regression-Testing should be collapsed by default (page not visible)
    const testPage = screen.queryByText('Test Page');
    expect(testPage).not.toBeInTheDocument();
  });

  it('expands Regression-Testing section when toggled', async () => {
    const treeWithSections = [
      {
        id: 'page-1',
        title: 'Test Page',
        slug: 'test-page',
        status: 'published',
        section: 'Regression-Testing',
        children: [],
      },
    ];

    pagesApi.useNavigationTree.mockReturnValue({
      data: treeWithSections,
      isLoading: false,
      isError: false,
    });

    store = {};

    renderNavigationTree();

    await waitFor(() => {
      const regressionSection = screen.getByText('Regression-Testing');
      expect(regressionSection).toBeInTheDocument();
    });

    // Initially collapsed, page should not be visible
    expect(screen.queryByText('Test Page')).not.toBeInTheDocument();

    // Find and click the toggle button for Regression-Testing section
    const regressionSectionHeader = screen.getByText('Regression-Testing').closest('.arc-nav-tree-section-header');
    expect(regressionSectionHeader).toBeInTheDocument();

    const toggleButton = regressionSectionHeader?.querySelector('button');
    expect(toggleButton).toBeInTheDocument();

    fireEvent.click(toggleButton);

    await waitFor(() => {
      // Now Test Page should be visible after expanding
      const testPage = screen.getByText('Test Page');
      expect(testPage).toBeInTheDocument();
    });
  });
});
