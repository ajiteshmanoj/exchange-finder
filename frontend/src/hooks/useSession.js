/**
 * useSession Hook
 * Manages user session state (in-memory only, cleared on page refresh)
 */

import { useState } from 'react';

export const useSession = () => {
  const [session, setSession] = useState(null);

  /**
   * Create a new session with user credentials
   * @param {Object} credentials - { username, password, domain }
   */
  const createSession = (credentials) => {
    const newSession = {
      credentials,
      timestamp: new Date().toISOString()
    };
    setSession(newSession);
  };

  /**
   * Clear the current session (logout)
   */
  const clearSession = () => {
    setSession(null);
  };

  /**
   * Check if user is authenticated
   * @returns {boolean}
   */
  const isAuthenticated = () => {
    return session !== null && session.credentials !== null;
  };

  /**
   * Get current session data
   * @returns {Object|null}
   */
  const getSession = () => {
    return session;
  };

  /**
   * Get credentials from current session
   * @returns {Object|null}
   */
  const getCredentials = () => {
    return session?.credentials || null;
  };

  return {
    session,
    createSession,
    clearSession,
    isAuthenticated,
    getSession,
    getCredentials
  };
};
