import axios from 'axios';

const authBaseURL = import.meta.env.VITE_AUTH_API_BASE_URL || 'http://localhost:8000/api';

export const authApi = {
  /**
   * Register a new user
   * @param {string} username
   * @param {string} email
   * @param {string} password
   * @returns {Promise<{user: object, token: string, refresh_token: string, expires_in: number}>}
   */
  async register(username, email, password) {
    const response = await axios.post(`${authBaseURL}/auth/register`, {
      username,
      email,
      password,
    });
    return response.data;
  },

  /**
   * Login with username and password
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{user: object, token: string, refresh_token: string, expires_in: number}>}
   */
  async login(username, password) {
    const response = await axios.post(`${authBaseURL}/auth/login`, {
      username,
      password,
    });
    return response.data;
  },

  /**
   * Verify a token
   * @param {string} token
   * @returns {Promise<{valid: boolean, user?: object, expires_at?: string, error?: string}>}
   */
  async verifyToken(token) {
    const response = await axios.post(
      `${authBaseURL}/auth/verify`,
      { token },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      },
    );
    return response.data;
  },
};
