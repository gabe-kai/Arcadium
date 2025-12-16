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
});
