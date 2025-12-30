import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import {
  useServiceStatus,
  useRefreshServiceStatus,
  useServiceLogs,
  useControlService,
} from '../services/api/services';
import { useAuth } from '../services/auth/AuthContext';
import { useNotificationContext } from '../components/common/NotificationProvider';
import { copyToClipboard } from '../utils/share';

/**
 * ServiceControlButton component - Button to control a service (start/stop/restart)
 */
function ServiceControlButton({ serviceId, service }) {
  const [showControl, setShowControl] = React.useState(false);
  const { token } = useAuth();
  const { showSuccess, showError } = useNotificationContext();
  const controlMutation = useControlService();

  // Check if service can be controlled
  const controllableServices = ['wiki', 'auth', 'web-client', 'file-watcher'];
  const canControl = controllableServices.includes(serviceId);
  const isRunning = service?.status === 'healthy' || service?.status === 'degraded';

  const handleControl = async (action) => {
    try {
      const result = await controlMutation.mutateAsync({
        serviceId,
        action,
        token,
      });
      if (result.success) {
        showSuccess(result.message || `Service ${action}ed successfully`);
        setShowControl(false);
      } else {
        showError(result.message || `Failed to ${action} service`);
      }
    } catch (error) {
      showError(
        error?.response?.data?.message ||
          error?.response?.data?.error ||
          `Failed to ${action} service: ${error.message}`
      );
    }
  };

  if (!canControl) {
    return (
      <button
        type="button"
        className="arc-service-card-action-button"
        disabled
        title="Service control not available for this service"
      >
        ⚙️ Control
      </button>
    );
  }

  return (
    <>
      <button
        type="button"
        className="arc-service-card-action-button"
        onClick={() => setShowControl(!showControl)}
        title="Control service (start/stop/restart)"
      >
        ⚙️ Control
      </button>
      {showControl && (
        <div className="arc-service-control-modal">
          <div className="arc-service-control-content">
            <div className="arc-service-control-header">
              <h3>Control {service.name}</h3>
              <button
                type="button"
                className="arc-service-control-close"
                onClick={() => setShowControl(false)}
                title="Close control menu"
              >
                ×
              </button>
            </div>
            <div className="arc-service-control-body">
              <p>Current status: <strong>{service.status || 'unknown'}</strong></p>
              <div className="arc-service-control-actions">
                {!isRunning && (
                  <button
                    type="button"
                    className="arc-service-control-action-button arc-service-control-start"
                    onClick={() => handleControl('start')}
                    disabled={controlMutation.isPending}
                    title="Start the service"
                  >
                    ▶️ Start
                  </button>
                )}
                {isRunning && (
                  <>
                    <button
                      type="button"
                      className="arc-service-control-action-button arc-service-control-stop"
                      onClick={() => handleControl('stop')}
                      disabled={controlMutation.isPending}
                      title="Stop the service"
                    >
                      ⏹️ Stop
                    </button>
                    <button
                      type="button"
                      className="arc-service-control-action-button arc-service-control-restart"
                      onClick={() => handleControl('restart')}
                      disabled={controlMutation.isPending}
                      title="Restart the service"
                    >
                      🔄 Restart
                    </button>
                  </>
                )}
              </div>
              {controlMutation.isPending && (
                <p className="arc-service-control-status">Processing...</p>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/**
 * ServiceLogsButton component - Button to view logs for a service
 */
function ServiceLogsButton({ serviceId, service }) {
  const [showLogs, setShowLogs] = React.useState(false);
  const { token } = useAuth();
  const { data: logsData, isLoading: logsLoading, error: logsError } = useServiceLogs(
    serviceId,
    showLogs, // Only fetch when logs are shown
    100,
    null,
    token
  );

  // Check if service has logs endpoint
  // Check both serviceId and service name to be more flexible
  const hasLogs = serviceId === 'wiki' ||
                  serviceId === 'auth' ||
                  service?.name?.toLowerCase().includes('wiki') ||
                  service?.name?.toLowerCase().includes('auth');

  // Debug: log serviceId to help troubleshoot
  console.log('ServiceLogsButton - serviceId:', serviceId, 'hasLogs:', hasLogs, 'service:', service?.name);

  if (!hasLogs) {
    return (
      <button
        type="button"
        className="arc-service-card-action-button"
        disabled
        title="Logs not available for this service"
      >
        📋 Logs
      </button>
    );
  }

  return (
    <>
      <button
        type="button"
        className="arc-service-card-action-button"
        onClick={() => setShowLogs(!showLogs)}
        title="View recent logs"
      >
        📋 Logs
      </button>
      {showLogs && (
        <div className="arc-service-logs-modal">
          <div className="arc-service-logs-content">
            <div className="arc-service-logs-header">
              <h3>{service.name} - Recent Logs</h3>
              <button
                type="button"
                className="arc-service-logs-close"
                onClick={() => setShowLogs(false)}
                title="Close logs"
              >
                ×
              </button>
            </div>
            <div className="arc-service-logs-body">
              {logsLoading && <p>Loading logs...</p>}
              {logsError && (
                <p className="arc-service-logs-error">
                  Error loading logs: {logsError.message || 'Unknown error'}
                </p>
              )}
              {logsData && logsData.error && (
                <p className="arc-service-logs-error">{logsData.error}</p>
              )}
              {logsData && logsData.logs && logsData.logs.length === 0 && (
                <p>No logs available</p>
              )}
              {logsData && logsData.logs && logsData.logs.length > 0 && (
                <div className="arc-service-logs-list">
                  {logsData.logs.map((log, index) => (
                    <div
                      key={index}
                      className={`arc-service-log-entry arc-service-log-${log.level.toLowerCase()}`}
                    >
                      <span className="arc-service-log-timestamp">{log.timestamp}</span>
                      <span className="arc-service-log-level">{log.level}</span>
                      <span className="arc-service-log-message">{log.raw_message || log.message}</span>
                    </div>
                  ))}
                </div>
              )}
              {logsData && logsData.count && (
                <div className="arc-service-logs-footer">
                  <p>Showing {logsData.count} of {logsData.total_available || 0} log entries</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/**
 * ServiceManagementPage component - Displays service status and management controls
 */
export function ServiceManagementPage() {
  const { isAuthenticated, user, isLoading: authLoading, token } = useAuth();
  const { showSuccess, showError } = useNotificationContext();

  // Temporarily removed auth requirements - fetch for everyone
  // Check if user is admin (for future use)
  const isAdmin = isAuthenticated && user?.role === 'admin';

  // Fetch service status for everyone (temporarily), wait for auth to be ready
  // Pass token directly to avoid localStorage timing issues
  const { data: statusData, isLoading, isError, error, refetch } = useServiceStatus(!authLoading, !authLoading, token);
  const refreshMutation = useRefreshServiceStatus();

  // Check if we got empty services (indicates 401/403 - no access)
  const hasEmptyServices = statusData?.services && Object.keys(statusData.services).length === 0;

  // Debug logging
  useEffect(() => {
    console.log('ServiceManagementPage state:', {
      isAdmin,
      isAuthenticated,
      userRole: user?.role,
      hasEmptyServices,
      isLoading,
      isError,
      statusData: statusData ? {
        hasServices: !!statusData.services,
        serviceCount: statusData.services ? Object.keys(statusData.services).length : 0,
        authError: statusData.authError,
        error: statusData.error
      } : null,
    });

    if (isError) {
      console.error('ServiceManagementPage error:', error);
      console.error('Error details:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        message: error?.message,
      });
    }
  }, [isAdmin, isAuthenticated, user?.role, hasEmptyServices, isLoading, isError, error, statusData]);

  const handleRefresh = async () => {
    try {
      await refreshMutation.mutateAsync();
      showSuccess('Service status refreshed');
      refetch();
    } catch (error) {
      showError('Failed to refresh service status');
    }
  };

  const getStatusIndicator = (status) => {
    switch (status) {
      case 'healthy':
        return '🟢';
      case 'degraded':
        return '🟡';
      case 'unhealthy':
        return '🔴';
      default:
        return '⚪';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'var(--arc-success-text)';
      case 'degraded':
        return '#fbbf24'; // yellow
      case 'unhealthy':
        return 'var(--arc-error-text)';
      default:
        return 'var(--arc-text-subtle)';
    }
  };

  const formatLastCheck = (timestamp) => {
    if (!timestamp) return 'Never';
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);

      if (diffSec < 60) return 'Just now';
      if (diffMin < 60) return `${diffMin}m ago`;
      return date.toLocaleTimeString();
    } catch {
      return 'Unknown';
    }
  };

  const formatServiceInfo = (serviceId, service) => {
    const lines = [];
    lines.push(`Service: ${service.name}`);
    if (service.description) {
      lines.push(`Description: ${service.description}`);
    }
    lines.push(`Status: ${service.status || 'unknown'}${service.is_internal ? ' (internal)' : ''}`);
    lines.push(`Response Time: ${service.response_time_ms ? `${service.response_time_ms.toFixed(0)}ms` : 'N/A'}`);
    lines.push(`Last Check: ${formatLastCheck(service.last_check)}`);

    if (service.process_info) {
      if (service.process_info.pid) {
        lines.push(`Process ID: ${service.process_info.pid}`);
      }
      // Check for formatted uptime first (from backend), then fall back to calculating from uptime_seconds
      if (service.uptime) {
        lines.push(`Uptime: ${service.uptime}`);
      } else if (service.process_info.uptime_seconds !== undefined && service.process_info.uptime_seconds !== null) {
        const uptimeSeconds = service.process_info.uptime_seconds;
        const hours = Math.floor(uptimeSeconds / 3600);
        const minutes = Math.floor((uptimeSeconds % 3600) / 60);
        const seconds = Math.floor(uptimeSeconds % 60);
        let uptimeText = '';
        if (hours > 0) {
          uptimeText = `${hours}h ${minutes}m ${seconds}s`;
        } else if (minutes > 0) {
          uptimeText = `${minutes}m ${seconds}s`;
        } else {
          uptimeText = `${seconds}s`;
        }
        lines.push(`Uptime: ${uptimeText}`);
      }
      if (service.process_info.cpu_percent !== undefined && service.process_info.cpu_percent !== null) {
        lines.push(`CPU Usage: ${service.process_info.cpu_percent.toFixed(1)}%`);
      }
      if (service.process_info.memory_mb !== undefined && service.process_info.memory_mb !== null) {
        const memoryText = `${service.process_info.memory_mb.toFixed(1)} MB`;
        const memoryPercent = service.process_info.memory_percent !== undefined && service.process_info.memory_percent !== null
          ? ` (${service.process_info.memory_percent.toFixed(1)}%)`
          : '';
        lines.push(`Memory: ${memoryText}${memoryPercent}`);
      }
      if (service.process_info.threads) {
        lines.push(`Threads: ${service.process_info.threads}`);
      }
      if (service.process_info.open_files !== undefined && service.process_info.open_files !== null) {
        lines.push(`Open Files: ${service.process_info.open_files}`);
      }
    }

    if (service.version) {
      lines.push(`Version: ${service.version}`);
    }
    if (service.service_name && service.service_name !== service.name) {
      lines.push(`Service Name: ${service.service_name}`);
    }
    if (service.error) {
      lines.push(`Error: ${service.error}`);
    }
    if (service.manual_notes) {
      const notes = service.manual_notes.notes || JSON.stringify(service.manual_notes);
      lines.push(`Notes: ${notes}`);
    }

    return lines.join('\n');
  };

  const formatAllServicesInfo = (services) => {
    const lines = [];
    lines.push('Arcadium Service Status Report');
    lines.push('='.repeat(50));
    lines.push('');

    if (statusData?.last_updated) {
      lines.push(`Generated: ${new Date(statusData.last_updated).toLocaleString()}`);
      lines.push('');
    }

    // Summary
    const healthy = Object.values(services).filter(s => s.status === 'healthy').length;
    const degraded = Object.values(services).filter(s => s.status === 'degraded').length;
    const unhealthy = Object.values(services).filter(s => s.status === 'unhealthy').length;
    lines.push('Summary:');
    lines.push(`  Healthy: ${healthy}`);
    lines.push(`  Degraded: ${degraded}`);
    lines.push(`  Unhealthy: ${unhealthy}`);
    lines.push('');
    lines.push('='.repeat(50));
    lines.push('');

    // Individual services
    Object.entries(services).forEach(([serviceId, service]) => {
      lines.push(formatServiceInfo(serviceId, service));
      lines.push('');
      lines.push('-'.repeat(50));
      lines.push('');
    });

    return lines.join('\n');
  };

  const handleCopyService = async (serviceId, service) => {
    try {
      const text = formatServiceInfo(serviceId, service);
      await copyToClipboard(text);
      showSuccess(`Service information copied to clipboard`);
    } catch (error) {
      showError('Failed to copy service information');
    }
  };

  const handleCopyAll = async () => {
    if (!statusData?.services || Object.keys(statusData.services).length === 0) {
      showError('No service data available to copy');
      return;
    }
    try {
      const text = formatAllServicesInfo(statusData.services);
      await copyToClipboard(text);
      showSuccess('All service information copied to clipboard');
    } catch (error) {
      showError('Failed to copy service information');
    }
  };

  // Temporarily removed access check - allow everyone to view
  // TODO: Re-enable auth requirements once core functionality is working
  // if (!isAdmin) {
  //   return (
  //     <Layout sidebar={<Sidebar />}>
  //       <div className="arc-service-management-page">
  //         <div className="arc-service-management-error">
  //           <h1>Access Denied</h1>
  //           <p>You must be an administrator to access service management.</p>
  //         </div>
  //       </div>
  //     </Layout>
  //   );
  // }

  // For admin users, if we got empty services due to 401/403, show auth error instead of access denied
  // This indicates the token might be expired or invalid
  if (hasEmptyServices && !isLoading && !isError && statusData?.error?.includes('timeout')) {
    // Timeout case - show timeout message
    return (
      <Layout sidebar={<Sidebar />}>
        <div className="arc-service-management-page">
          <div className="arc-service-management-error">
            <h1>Service Status Unavailable</h1>
            <p>The service status check timed out. Some services may be slow or unreachable.</p>
            <p style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
              <button
                type="button"
                onClick={() => refetch()}
                className="arc-service-management-refresh-button"
                style={{ marginTop: '0.5rem' }}
              >
                Try Again
              </button>
            </p>
          </div>
        </div>
      </Layout>
    );
  }

  // If we got empty services without a timeout error, it's likely a 401/403
  // For admin users, this suggests an auth issue
  if (hasEmptyServices && !isLoading && !isError && (statusData?.authError || !statusData?.error)) {
    return (
      <Layout sidebar={<Sidebar />}>
        <div className="arc-service-management-page">
          <div className="arc-service-management-error">
            <h1>Authentication Error</h1>
            <p>Unable to fetch service status. {statusData?.error || 'Your session may have expired.'}</p>
            <p style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
              Please try signing out and signing back in, or check that your authentication token is valid.
            </p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-service-management-page">
        <div className="arc-service-management-header">
          <div>
            <h1 className="arc-service-management-title">Service Management</h1>
            <p className="arc-service-management-subtitle">
              Monitor and manage Arcadium services
            </p>
          </div>
          <div className="arc-service-management-header-actions">
            {statusData?.services && Object.keys(statusData.services).length > 0 && (
              <button
                type="button"
                className="arc-service-management-copy-button"
                onClick={handleCopyAll}
                title="Copy all service information to clipboard"
              >
                📋 Copy All
              </button>
            )}
            <button
              type="button"
              className="arc-service-management-refresh-button"
              onClick={handleRefresh}
              disabled={refreshMutation.isPending}
            >
              {refreshMutation.isPending ? 'Refreshing...' : '🔄 Refresh'}
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="arc-service-management-loading">
            <p>Loading service status...</p>
          </div>
        )}

        {isError && (
          <div className="arc-service-management-error">
            <p>Error loading service status. Please try again.</p>
            {error && (
              <details style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
                <summary style={{ cursor: 'pointer', color: 'var(--arc-text-subtle)' }}>
                  Error details
                </summary>
                <pre style={{ marginTop: '0.5rem', padding: '0.5rem', background: 'var(--arc-surface)', borderRadius: '0.25rem', overflow: 'auto' }}>
                  {error?.response?.data?.error || error?.message || 'Unknown error'}
                  {error?.response?.status && ` (HTTP ${error.response.status})`}
                </pre>
              </details>
            )}
          </div>
        )}

        {/* Show message if we got empty services due to timeout */}
        {statusData?.error && !isLoading && !isError && (
          <div className="arc-service-management-error">
            <p>{statusData.error}</p>
            <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
              The service status check timed out. Some services may be slow to respond or unreachable.
            </p>
          </div>
        )}

        {statusData?.services && Object.keys(statusData.services).length > 0 && !isLoading && !isError && (
          <>
            <div className="arc-service-management-stats">
              <div className="arc-service-management-stat">
                <span className="arc-service-management-stat-value">
                  {Object.values(statusData.services).filter(
                    (s) => s.status === 'healthy'
                  ).length}
                </span>
                <span className="arc-service-management-stat-label">
                  Healthy
                </span>
              </div>
              <div className="arc-service-management-stat">
                <span className="arc-service-management-stat-value">
                  {Object.values(statusData.services).filter(
                    (s) => s.status === 'degraded'
                  ).length}
                </span>
                <span className="arc-service-management-stat-label">
                  Degraded
                </span>
              </div>
              <div className="arc-service-management-stat">
                <span className="arc-service-management-stat-value">
                  {Object.values(statusData.services).filter(
                    (s) => s.status === 'unhealthy'
                  ).length}
                </span>
                <span className="arc-service-management-stat-label">
                  Unhealthy
                </span>
              </div>
            </div>

            <div className="arc-service-management-grid">
              {Object.entries(statusData.services).map(([serviceId, service]) => (
                <div
                  key={serviceId}
                  className="arc-service-card"
                  data-status={service.status}
                >
                  <div className="arc-service-card-header">
                    <div className="arc-service-card-title-row">
                      <h3 className="arc-service-card-title">
                        {service.name}
                      </h3>
                      <span
                        className="arc-service-card-indicator"
                        style={{ color: getStatusColor(service.status) }}
                      >
                        {getStatusIndicator(service.status)}
                      </span>
                    </div>
                    {service.description && (
                      <p className="arc-service-card-description">
                        {service.description}
                      </p>
                    )}
                    <div className="arc-service-card-status-row">
                      <span
                        className="arc-service-card-status"
                        style={{ color: getStatusColor(service.status) }}
                      >
                        {service.status || 'unknown'}
                        {service.is_internal && ' (internal)'}
                      </span>
                      {service.status !== 'healthy' && service.status_reason && (
                        <span className="arc-service-card-status-reason">
                          {service.status_reason}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="arc-service-card-body">
                    <div className="arc-service-card-metric">
                      <span className="arc-service-card-metric-label">
                        Response Time:
                      </span>
                      <span className="arc-service-card-metric-value">
                        {service.response_time_ms
                          ? `${service.response_time_ms.toFixed(0)}ms`
                          : 'N/A'}
                      </span>
                    </div>

                    <div className="arc-service-card-metric">
                      <span className="arc-service-card-metric-label">
                        Last Check:
                      </span>
                      <span className="arc-service-card-metric-value">
                        {formatLastCheck(service.last_check)}
                      </span>
                    </div>

                    {/* Process information and metadata */}
                    {service.process_info && (
                      <>
                        {service.process_info.pid && (
                          <div className="arc-service-card-metric">
                            <span className="arc-service-card-metric-label">
                              Process ID:
                            </span>
                            <span className="arc-service-card-metric-value">
                              {service.process_info.pid}
                            </span>
                          </div>
                        )}
                        {service.uptime && (
                          <div className="arc-service-card-metric">
                            <span className="arc-service-card-metric-label">
                              Uptime:
                            </span>
                            <span className="arc-service-card-metric-value">
                              {service.uptime}
                            </span>
                          </div>
                        )}
                        {service.process_info.cpu_percent !== undefined && service.process_info.cpu_percent !== null && (
                          <div className="arc-service-card-metric">
                            <span className="arc-service-card-metric-label">
                              CPU Usage:
                            </span>
                            <span className="arc-service-card-metric-value">
                              {service.process_info.cpu_percent.toFixed(1)}%
                            </span>
                          </div>
                        )}
                        {(service.process_info.memory_mb !== undefined && service.process_info.memory_mb !== null) && (
                          <div className="arc-service-card-metric">
                            <span className="arc-service-card-metric-label">
                              Memory:
                            </span>
                            <span className="arc-service-card-metric-value">
                              {service.process_info.memory_mb.toFixed(1)} MB
                              {service.process_info.memory_percent !== undefined && service.process_info.memory_percent !== null
                                ? ` (${service.process_info.memory_percent.toFixed(1)}%)`
                                : ''}
                            </span>
                          </div>
                        )}
                        {service.process_info.threads && (
                          <div className="arc-service-card-metric">
                            <span className="arc-service-card-metric-label">
                              Threads:
                            </span>
                            <span className="arc-service-card-metric-value">
                              {service.process_info.threads}
                            </span>
                          </div>
                        )}
                      </>
                    )}

                    {/* Additional metadata from health endpoint */}
                    {service.version && (
                      <div className="arc-service-card-metric">
                        <span className="arc-service-card-metric-label">
                          Version:
                        </span>
                        <span className="arc-service-card-metric-value">
                          {service.version}
                        </span>
                      </div>
                    )}
                    {service.service_name && service.service_name !== service.name && (
                      <div className="arc-service-card-metric">
                        <span className="arc-service-card-metric-label">
                          Service:
                        </span>
                        <span className="arc-service-card-metric-value">
                          {service.service_name}
                        </span>
                      </div>
                    )}

                    {/* File Watcher specific metadata */}
                    {service.watcher_metadata && (
                      <>
                        {service.watcher_metadata.debounce_seconds && (
                          <div className="arc-service-card-metric">
                            <span className="arc-service-card-metric-label">
                              Debounce Time:
                            </span>
                            <span className="arc-service-card-metric-value">
                              {service.watcher_metadata.debounce_seconds}s
                            </span>
                          </div>
                        )}
                        {service.watcher_metadata.watched_directory && (
                          <div className="arc-service-card-metric">
                            <span className="arc-service-card-metric-label">
                              Watched Directory:
                            </span>
                            <span className="arc-service-card-metric-value">
                              {service.watcher_metadata.watched_directory}
                            </span>
                          </div>
                        )}
                      </>
                    )}
                    {service.is_running !== undefined && (
                      <div className="arc-service-card-metric">
                        <span className="arc-service-card-metric-label">
                          Running:
                        </span>
                        <span className="arc-service-card-metric-value">
                          {service.is_running ? 'Yes' : 'No'}
                        </span>
                      </div>
                    )}

                    {service.error && (
                      <div className="arc-service-card-error">
                        <strong>Error:</strong> {service.error}
                      </div>
                    )}

                    {service.manual_notes && (
                      <div className="arc-service-card-notes">
                        <strong>Notes:</strong>{' '}
                        {service.manual_notes.notes || JSON.stringify(service.manual_notes)}
                      </div>
                    )}
                  </div>

                  <div className="arc-service-card-actions">
                    <button
                      type="button"
                      className="arc-service-card-action-button"
                      onClick={() => handleCopyService(serviceId, service)}
                      title="Copy service information to clipboard"
                    >
                      📋 Copy
                    </button>
                    <ServiceControlButton serviceId={serviceId} service={service} />
                    <ServiceLogsButton serviceId={serviceId} service={service} />
                  </div>
                </div>
              ))}
            </div>

            {statusData.last_updated && (
              <div className="arc-service-management-footer">
                <p>
                  Last updated:{' '}
                  {new Date(statusData.last_updated).toLocaleString()}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
