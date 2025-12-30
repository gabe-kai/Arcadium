import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ServiceManagementPage } from '../../pages/ServiceManagementPage';
import * as servicesApi from '../../services/api/services';
import { useAuth } from '../../services/auth/AuthContext';
import { useNotificationContext } from '../../components/common/NotificationProvider';

// Mock dependencies
vi.mock('../../services/auth/AuthContext');
vi.mock('../../components/common/NotificationProvider');
vi.mock('../../services/api/services');
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children, sidebar }) => (
    <div data-testid="layout">
      {sidebar}
      {children}
    </div>
  ),
}));
vi.mock('../../components/layout/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar" />,
}));

const mockShowSuccess = vi.fn();
const mockShowError = vi.fn();

describe('ServiceManagementPage', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();

    useAuth.mockReturnValue({
      isAuthenticated: true,
      user: { role: 'admin' },
      isLoading: false,
      token: 'test-token',
    });

    useNotificationContext.mockReturnValue({
      showSuccess: mockShowSuccess,
      showError: mockShowError,
    });
  });

  it('renders loading state', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/loading service status/i)).toBeInTheDocument();
  });

  it('renders error state', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: { message: 'Failed to load' },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/error loading service status/i)).toBeInTheDocument();
  });

  it('renders service cards for healthy services', async () => {
    const mockServices = {
      wiki: {
        name: 'Wiki Service',
        description: 'Core wiki service',
        status: 'healthy',
        response_time_ms: 5.2,
        last_check: '2024-01-01T12:00:00Z',
        process_info: {
          pid: 12345,
          uptime_seconds: 3600,
          cpu_percent: 2.5,
          memory_mb: 150.3,
          memory_percent: 1.2,
          threads: 8,
        },
        version: '1.0.0',
      },
      auth: {
        name: 'Auth Service',
        description: 'Authentication service',
        status: 'healthy',
        response_time_ms: 12.0,
        last_check: '2024-01-01T12:00:00Z',
        process_info: {
          pid: 67890,
          uptime_seconds: 7200,
          cpu_percent: 0.5,
          memory_mb: 87.8,
          memory_percent: 0.6,
          threads: 5,
        },
        version: '1.0.0',
      },
    };

    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: mockServices,
        last_updated: '2024-01-01T12:00:00Z',
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Wiki Service')).toBeInTheDocument();
      expect(screen.getByText('Auth Service')).toBeInTheDocument();
    });
  });

  it('displays status reason for degraded services', async () => {
    const mockServices = {
      auth: {
        name: 'Auth Service',
        description: 'Authentication service',
        status: 'degraded',
        status_reason: 'Slow response time (1107ms exceeds 1500ms threshold)',
        response_time_ms: 1107.0,
        last_check: '2024-01-01T12:00:00Z',
      },
    };

    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: mockServices,
        last_updated: '2024-01-01T12:00:00Z',
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/slow response time/i)).toBeInTheDocument();
    });
  });

  it('displays process information', async () => {
    const mockServices = {
      wiki: {
        name: 'Wiki Service',
        status: 'healthy',
        process_info: {
          pid: 12345,
          uptime_seconds: 3661, // 1h 1m 1s
          cpu_percent: 2.5,
          memory_mb: 150.3,
          memory_percent: 1.2,
          threads: 8,
        },
      },
    };

    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: mockServices,
        last_updated: '2024-01-01T12:00:00Z',
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/12345/)).toBeInTheDocument();
      expect(screen.getByText(/1h 1m 1s/)).toBeInTheDocument();
      expect(screen.getByText(/2\.5%/)).toBeInTheDocument();
      expect(screen.getByText(/150\.3 MB/)).toBeInTheDocument();
    });
  });

  it('handles refresh button click', async () => {
    const mockRefresh = vi.fn().mockResolvedValue({});
    servicesApi.useRefreshServiceStatus.mockReturnValue({
      mutateAsync: mockRefresh,
      isPending: false,
    });

    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: {
          wiki: { name: 'Wiki Service', status: 'healthy' },
        },
        last_updated: '2024-01-01T12:00:00Z',
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      const refreshButton = screen.getByText(/refresh/i);
      fireEvent.click(refreshButton);
    });

    await waitFor(() => {
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  it('displays summary statistics', async () => {
    const mockServices = {
      wiki: { name: 'Wiki Service', status: 'healthy' },
      auth: { name: 'Auth Service', status: 'degraded' },
      notification: { name: 'Notification Service', status: 'unhealthy' },
    };

    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: mockServices,
        last_updated: '2024-01-01T12:00:00Z',
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/1 Healthy/)).toBeInTheDocument();
      expect(screen.getByText(/1 Degraded/)).toBeInTheDocument();
      expect(screen.getByText(/1 Unhealthy/)).toBeInTheDocument();
    });
  });

  it('handles empty services gracefully', () => {
    servicesApi.useServiceStatus.mockReturnValue({
      data: {
        services: {},
        last_updated: '2024-01-01T12:00:00Z',
      },
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ServiceManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/service status unavailable/i)).toBeInTheDocument();
  });
});
