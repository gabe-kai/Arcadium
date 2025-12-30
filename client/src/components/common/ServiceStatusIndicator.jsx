import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useServiceStatus } from '../../services/api/services';
import { useAuth } from '../../services/auth/AuthContext';
import './ServiceStatusIndicator.css';

/**
 * ServiceStatusIndicator component - Shows overall service health status
 * Visible to everyone regardless of authentication status
 */
export function ServiceStatusIndicator() {
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAuth();
  // Fetch status for everyone - use token if authenticated, but allow anonymous access
  const { data: statusData, isLoading, isError, error } = useServiceStatus(true, true, token);

  const handleClick = () => {
    navigate('/services');
  };

  // Calculate overall status
  const getOverallStatus = () => {
    // Check if we have no data (401/403 for non-admin/anonymous users, or empty result)
    const hasNoData = !statusData?.services || Object.keys(statusData.services || {}).length === 0;

    if (isLoading || hasNoData) {
      return null; // Unknown/loading/no-access state
    }

    if (isError) {
      return null; // Error state
    }

    const services = Object.values(statusData.services);
    const statuses = services.map((s) => s.status);

    // Red if any unhealthy
    if (statuses.some((s) => s === 'unhealthy')) {
      return 'unhealthy';
    }
    // Amber if any degraded
    if (statuses.some((s) => s === 'degraded')) {
      return 'degraded';
    }
    // Green if all healthy
    if (statuses.every((s) => s === 'healthy')) {
      return 'healthy';
    }
    return null;
  };

  const overallStatus = getOverallStatus();

  // Generate tooltip text
  const getTooltip = () => {
    if (isLoading) {
      return 'Loading service status...';
    }

    // Check if we have no data (401/403 for non-admin/anonymous users)
    const hasNoAccess = !statusData?.services || Object.keys(statusData.services || {}).length === 0;

    if (hasNoAccess) {
      return 'Service status unavailable. Click to view details.';
    }

    if (isError) {
      return 'Service status unavailable. Click to view details.';
    }

    const services = Object.values(statusData.services);
    const healthy = services.filter((s) => s.status === 'healthy').length;
    const degraded = services.filter((s) => s.status === 'degraded').length;
    const unhealthy = services.filter((s) => s.status === 'unhealthy').length;
    const total = services.length;

    let tooltip = `Service Status: ${total} total\n\n`;
    tooltip += `🟢 Healthy: ${healthy}\n`;
    tooltip += `🟡 Degraded: ${degraded}\n`;
    tooltip += `🔴 Unhealthy: ${unhealthy}\n\n`;

    if (overallStatus === 'healthy') {
      tooltip += 'All services are operating normally.';
    } else if (overallStatus === 'degraded') {
      tooltip += 'Some services are experiencing degraded performance.';
    } else if (overallStatus === 'unhealthy') {
      tooltip += 'Some services are experiencing issues.';
    }

    if (statusData.last_updated) {
      const lastUpdate = new Date(statusData.last_updated);
      tooltip += `\n\nLast updated: ${lastUpdate.toLocaleString()}`;
    }

    tooltip += '\n\nClick to view service details.';

    return tooltip;
  };

  return (
    <button
      type="button"
      className={`arc-service-status-indicator arc-service-status-indicator-${overallStatus || 'unknown'}`}
      onClick={handleClick}
      title={getTooltip()}
      aria-label="Service status"
    >
      <span className="arc-service-status-indicator-light" />
    </button>
  );
}
