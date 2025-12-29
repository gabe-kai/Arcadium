import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { useAuth } from '../services/auth/AuthContext';
import { authApi } from '../services/api/auth';
import './SignInPage.css';

export function SignInPage() {
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form state
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      let response;
      if (mode === 'register') {
        if (!username || !email || !password) {
          setError('All fields are required');
          setLoading(false);
          return;
        }
        response = await authApi.register(username, email, password);
        setSuccess('Registration successful! You are now signed in.');
      } else {
        if (!username || !password) {
          setError('Username and password are required');
          setLoading(false);
          return;
        }
        response = await authApi.login(username, password);
      }

      // Store token and user info
      await signIn(response.token, response.user);

      // Set flag to indicate we just signed in (so pages can refetch with new permissions)
      sessionStorage.setItem('justSignedIn', 'true');

      // Check for stored redirect path, otherwise go to home
      // Prevent redirecting back to sign-in page to avoid loops
      const redirectPath = sessionStorage.getItem('redirectAfterLogin');
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin');
      }
      const targetPath = (redirectPath && !redirectPath.startsWith('/signin')) ? redirectPath : '/';

      // Redirect after a brief delay to show success message
      setTimeout(() => {
        navigate(targetPath);
      }, mode === 'register' ? 1500 : 0);
    } catch (err) {
      const errorMessage =
        err.response?.data?.error || err.message || 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError(null);
    setSuccess(null);
    setUsername('');
    setEmail('');
    setPassword('');
  };

  return (
    <Layout>
      <div className="arc-signin-page">
        <div className="arc-signin-container">
          <h1>{mode === 'login' ? 'Sign In' : 'Create Account'}</h1>
          <p className="arc-signin-subtitle">
            {mode === 'login'
              ? 'Sign in to your Arcadium account'
              : 'Create a new account to get started'}
          </p>

          {error && (
            <div className="arc-signin-error" role="alert">
              {error}
            </div>
          )}

          {success && (
            <div className="arc-signin-success" role="alert">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="arc-signin-form">
            <div className="arc-form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                disabled={loading}
              />
            </div>

            {mode === 'register' && (
              <div className="arc-form-group">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  disabled={loading}
                />
              </div>
            )}

            <div className="arc-form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              className="arc-signin-submit"
              disabled={loading}
            >
              {loading
                ? 'Please wait...'
                : mode === 'login'
                  ? 'Sign In'
                  : 'Create Account'}
            </button>
          </form>

          <div className="arc-signin-switch">
            {mode === 'login' ? (
              <>
                Don't have an account?{' '}
                <button
                  type="button"
                  className="arc-link-button"
                  onClick={switchMode}
                  disabled={loading}
                >
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button
                  type="button"
                  className="arc-link-button"
                  onClick={switchMode}
                  disabled={loading}
                >
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
