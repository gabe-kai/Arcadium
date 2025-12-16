import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Header } from '../../components/layout/Header';
import { Footer } from '../../components/layout/Footer';
import { Layout } from '../../components/layout/Layout';

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
  });
});
