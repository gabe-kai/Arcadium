import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { useAuth } from '../services/auth/AuthContext';

/**
 * ProfilePage component - Displays information about the currently logged-in user
 */
export function ProfilePage() {
  const navigate = useNavigate();
  const { isAuthenticated, user, isLoading } = useAuth();

  // Redirect to sign-in if not authenticated
  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/signin');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <Layout sidebar={<Sidebar />}>
        <div style={{ padding: '2rem' }}>
          <p>Loading...</p>
        </div>
      </Layout>
    );
  }

  if (!isAuthenticated || !user) {
    return null; // Will redirect
  }

  const getRoleDisplayName = (role) => {
    switch (role) {
      case 'admin':
        return 'Administrator';
      case 'writer':
        return 'Writer';
      case 'viewer':
        return 'Viewer';
      default:
        return role || 'Unknown';
    }
  };

  const getRoleDescription = (role) => {
    switch (role) {
      case 'admin':
        return 'Full access to all features including service management and administrative functions.';
      case 'writer':
        return 'Can create, edit, and manage wiki pages.';
      case 'viewer':
        return 'Can view wiki pages and search content.';
      default:
        return 'Limited access to wiki content.';
    }
  };

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-profile-page">
        <div className="arc-profile-header">
          <h1 className="arc-profile-title">User Profile</h1>
        </div>

        <div className="arc-profile-content">
          <div className="arc-profile-section">
            <h2 className="arc-profile-section-title">Account Information</h2>
            <div className="arc-profile-info-grid">
              <div className="arc-profile-info-item">
                <label className="arc-profile-info-label">Username</label>
                <div className="arc-profile-info-value">{user.username || 'N/A'}</div>
              </div>
              <div className="arc-profile-info-item">
                <label className="arc-profile-info-label">Email</label>
                <div className="arc-profile-info-value">{user.email || 'Not provided'}</div>
              </div>
              <div className="arc-profile-info-item">
                <label className="arc-profile-info-label">User ID</label>
                <div className="arc-profile-info-value" style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  {user.id || 'N/A'}
                </div>
              </div>
            </div>
          </div>

          <div className="arc-profile-section">
            <h2 className="arc-profile-section-title">Permissions</h2>
            <div className="arc-profile-role-card">
              <div className="arc-profile-role-header">
                <span className="arc-profile-role-name">{getRoleDisplayName(user.role)}</span>
                <span className="arc-profile-role-badge" data-role={user.role}>
                  {user.role?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
              <p className="arc-profile-role-description">{getRoleDescription(user.role)}</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
