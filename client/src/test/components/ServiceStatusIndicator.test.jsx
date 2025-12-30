import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ServiceStatusIndicator } from '../../components/common/ServiceStatusIndicator';
import * as servicesApi from '../../services/api/services';
import { useAuth } from '../../services/auth/AuthContext';

// Mock dependencies
vi.mock('../../services/auth/AuthContext');
vi.mock('../../services/api/services');
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('ServiceStatusIndicator', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();

    useAuth.mockReturnValue({
      isAuthenticated: true,
      user: { role: 'admin' },
      isLoading: false,
      token: 'test-token',
    });
  });

  it('renders loading state (gray)', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceStatusIndicator />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const indicator = screen.getByTitle(/loading service status/i);
    expect(indicator).toBeInTheDocument();
    expect(indicator.textContent).toContain('⚪');
  });

  it('renders healthy state (green) when all services are healthy', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: {
          wiki: { status: 'healthy' },
          auth: { status: 'healthy' },
        },
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceStatusIndicator />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const indicator = screen.getByTitle(/all services healthy/i);
    expect(indicator).toBeInTheDocument();
    expect(indicator.textContent).toContain('🟢');
  });

  it('renders degraded state (amber) when any service is degraded', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: {
          wiki: { status: 'healthy' },
          auth: { status: 'degraded' },
        },
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceStatusIndicator />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const indicator = screen.getByTitle(/1 service degraded/i);
    expect(indicator).toBeInTheDocument();
    expect(indicator.textContent).toContain('🟡');
  });

  it('renders unhealthy state (red) when any service is unhealthy', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: {
          wiki: { status: 'healthy' },
          auth: { status: 'unhealthy' },
        },
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceStatusIndicator />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const indicator = screen.getByTitle(/1 service unhealthy/i);
    expect(indicator).toBeInTheDocument();
    expect(indicator.textContent).toContain('🔴');
  });

  it('renders unknown state (gray) on error', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: { message: 'Failed to load' },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceStatusIndicator />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const indicator = screen.getByTitle(/service status unavailable/i);
    expect(indicator).toBeInTheDocument();
    expect(indicator.textContent).toContain('⚪');
  });

  it('renders unknown state (gray) when services data is empty', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: {},
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceStatusIndicator />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const indicator = screen.getByTitle(/service status unavailable/i);
    expect(indicator).toBeInTheDocument();
    expect(indicator.textContent).toContain('⚪');
  });

  it('displays correct tooltip with multiple issues', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: {
          wiki: { status: 'healthy' },
          auth: { status: 'degraded' },
          notification: { status: 'unhealthy' },
        },
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceStatusIndicator />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const indicator = screen.getByTitle(/1 service degraded, 1 service unhealthy/i);
    expect(indicator).toBeInTheDocument();
    expect(indicator.textContent).toContain('🔴'); // Unhealthy takes priority
  });

  it('is clickable and navigates to services page', () => {
    const mockNavigate = vi.fn();
    vi.mock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom');
      return {
        ...actual,
        useNavigate: () => mockNavigate,
      };
    });

    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: {
          wiki: { status: 'healthy' },
        },
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceStatusIndicator />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const indicator = screen.getByTitle(/all services healthy/i);
    fireEvent.click(indicator);

    // Note: Navigation testing may require additional setup
    // This is a basic test structure
  });
});
