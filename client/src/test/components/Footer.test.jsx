import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Footer } from '../../components/layout/Footer';

describe('Footer', () => {
  it('renders footer with text', () => {
    render(<Footer />);
    expect(screen.getByText(/Arcadium Wiki/i)).toBeInTheDocument();
  });

  it('has footer semantic element', () => {
    const { container } = render(<Footer />);
    const footer = container.querySelector('footer');
    expect(footer).toBeInTheDocument();
    expect(footer).toHaveClass('arc-footer');
  });

  it('displays copyright or attribution text', () => {
    render(<Footer />);
    const footerText = screen.getByText(/Arcadium Wiki/i);
    expect(footerText).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    expect(() => render(<Footer />)).not.toThrow();
  });
});
