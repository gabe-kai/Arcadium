import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { App } from '../App';

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
    expect(screen.getByText(/Arcadium Wiki/i)).toBeInTheDocument();
  });

  it('renders the header with logo', () => {
    render(<App />);
    const logo = screen.getByText(/Arcadium Wiki/i);
    expect(logo).toBeInTheDocument();
  });

  it('renders the home page by default', () => {
    render(<App />);
    expect(screen.getByText(/Welcome to the Arcadium Wiki/i)).toBeInTheDocument();
  });
});
