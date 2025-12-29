import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { App } from '../App';
import React from 'react';

// Mock AuthContext to avoid provider requirements in tests
vi.mock('../services/auth/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    isAuthenticated: false,
    user: null,
    signOut: vi.fn(),
    signIn: vi.fn(),
  })),
  AuthProvider: ({ children }) => <>{children}</>,
}));

// Mock navigation tree hook to avoid API calls
vi.mock('../services/api/pages', () => ({
  useNavigationTree: vi.fn(() => ({ data: [], isLoading: false, isError: false })),
}));

// Mock BrowserRouter to use MemoryRouter for testing
let mockInitialEntries = ['/'];
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    BrowserRouter: ({ children, future }) => {
      const { MemoryRouter } = actual;
      return <MemoryRouter initialEntries={mockInitialEntries} future={future}>{children}</MemoryRouter>;
    },
  };
});

describe('App', () => {
  beforeEach(() => {
    mockInitialEntries = ['/'];
  });

  it('renders without crashing', () => {
    render(<App />);
    const logos = screen.getAllByText(/Arcadium Wiki/i);
    expect(logos.length).toBeGreaterThan(0);
  });

  it('renders the header with logo', () => {
    render(<App />);
    const logos = screen.getAllByText(/Arcadium Wiki/i);
    expect(logos.length).toBeGreaterThan(0);
  });

  it('renders the home page by default', () => {
    render(<App />);
    expect(screen.getByText(/Welcome to the Arcadium Wiki/i)).toBeInTheDocument();
  });
});
