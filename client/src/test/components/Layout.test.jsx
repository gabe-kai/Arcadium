import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Header } from '../../components/layout/Header';
import { Footer } from '../../components/layout/Footer';
import { Layout } from '../../components/layout/Layout';
import React from 'react';

// Mock AuthContext to avoid provider requirements in layout tests
vi.mock('../../services/auth/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    isAuthenticated: false,
    user: null,
    signOut: vi.fn(),
    signIn: vi.fn(),
  })),
  AuthProvider: ({ children }) => <>{children}</>,
}));

// Mock navigation tree hook to avoid API calls
vi.mock('../../services/api/pages', () => ({
  useNavigationTree: vi.fn(() => ({ data: [], isLoading: false, isError: false })),
}));

describe('Layout Components', () => {
  describe('Header', () => {
    it('renders logo and search', () => {
      render(
        <MemoryRouter>
          <Header />
        </MemoryRouter>
      );
      expect(screen.getByText(/Arcadium Wiki/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Search the wiki/i)).toBeInTheDocument();
    });
  });

  describe('Footer', () => {
    it('renders footer text', () => {
      render(<Footer />);
      expect(screen.getByText(/Arcadium Wiki/i)).toBeInTheDocument();
    });
  });

  describe('Layout', () => {
    it('renders children', () => {
      render(
        <MemoryRouter>
          <Layout>
            <div>Test Content</div>
          </Layout>
        </MemoryRouter>
      );
      expect(screen.getByText(/Test Content/i)).toBeInTheDocument();
    });

    it('renders sidebar when provided', () => {
      render(
        <MemoryRouter>
          <Layout sidebar={<div>Sidebar Content</div>}>
            <div>Main Content</div>
          </Layout>
        </MemoryRouter>
      );
      expect(screen.getByText(/Sidebar Content/i)).toBeInTheDocument();
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('renders right sidebar when provided', () => {
      render(
        <MemoryRouter>
          <Layout rightSidebar={<div>Right Sidebar</div>}>
            <div>Main Content</div>
          </Layout>
        </MemoryRouter>
      );
      expect(screen.getByText(/Right Sidebar/i)).toBeInTheDocument();
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('renders both sidebars when provided', () => {
      render(
        <MemoryRouter>
          <Layout
            sidebar={<div>Left Sidebar</div>}
            rightSidebar={<div>Right Sidebar</div>}
          >
            <div>Main Content</div>
          </Layout>
        </MemoryRouter>
      );
      expect(screen.getByText(/Left Sidebar/i)).toBeInTheDocument();
      expect(screen.getByText(/Right Sidebar/i)).toBeInTheDocument();
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('applies correct CSS class when right sidebar is present', () => {
      const { container } = render(
        <MemoryRouter>
          <Layout rightSidebar={<div>Right Sidebar</div>}>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );
      
      const main = container.querySelector('.arc-main');
      expect(main).toHaveClass('arc-main-with-right-sidebar');
    });

    it('does not apply right sidebar class when right sidebar is absent', () => {
      const { container } = render(
        <MemoryRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );
      
      const main = container.querySelector('.arc-main');
      expect(main).not.toHaveClass('arc-main-with-right-sidebar');
    });

    it('handles null sidebar gracefully', () => {
      render(
        <MemoryRouter>
          <Layout sidebar={null}>
            <div>Main Content</div>
          </Layout>
        </MemoryRouter>
      );
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('handles null right sidebar gracefully', () => {
      render(
        <MemoryRouter>
          <Layout rightSidebar={null}>
            <div>Main Content</div>
          </Layout>
        </MemoryRouter>
      );
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('renders Header and Footer', () => {
      render(
        <MemoryRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );
      
      const logos = screen.getAllByText(/Arcadium Wiki/i);
      expect(logos.length).toBeGreaterThan(0);
    });
  });
});
