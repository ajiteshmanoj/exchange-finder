/**
 * HTTP API Client for NTU Exchange Finder
 * Handles REST API requests (health check, cache management, etc.)
 */

import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30 seconds
});

// API Methods
export const api = {
  /**
   * Verify NTU SSO credentials
   * @param {Object} credentials - {username, password, domain}
   * @returns {Promise} Login result
   */
  verifyLogin: async (credentials) => {
    // Longer timeout for login (5 minutes)
    // Includes: browser start, SSO login, country pre-fetch
    const response = await apiClient.post('/api/login', {
      credentials
    }, {
      timeout: 300000 // 5 minutes
    });
    return response.data;
  },

  /**
   * Health check
   * @returns {Promise} Server status
   */
  healthCheck: async () => {
    const response = await apiClient.get('/');
    return response.data;
  },

  /**
   * Clear all caches
   * @returns {Promise} Cache clear result
   */
  clearCache: async () => {
    const response = await apiClient.post('/api/cache/clear');
    return response.data;
  },

  /**
   * Clear university cache only
   * @returns {Promise} Cache clear result
   */
  clearUniversityCache: async () => {
    const response = await apiClient.post('/api/cache/clear/universities');
    return response.data;
  },

  /**
   * Clear mapping caches only
   * @returns {Promise} Cache clear result
   */
  clearMappingCache: async () => {
    const response = await apiClient.post('/api/cache/clear/mappings');
    return response.data;
  },

  /**
   * Get all countries and universities from NTU
   * @param {Object} credentials - NTU credentials
   * @param {Boolean} useCache - Whether to use cache
   * @returns {Promise} Countries and universities
   */
  getCountriesUniversities: async (credentials, useCache = true) => {
    // Longer timeout for this endpoint (10 minutes)
    // Includes: browser start, SSO login, 2FA wait, country scraping
    const response = await apiClient.post('/api/countries-universities', {
      credentials,
      use_cache: useCache
    }, {
      timeout: 600000 // 10 minutes
    });
    return response.data;
  }
};

export default api;
