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
  },

  // ============= Admin Endpoints =============

  /**
   * Get database status
   * @returns {Promise} Database statistics
   */
  getDatabaseStatus: async () => {
    const response = await apiClient.get('/api/admin/database/status');
    return response.data;
  },

  /**
   * Start full database scrape
   * @param {Object} credentials - NTU credentials
   * @param {Boolean} headless - Run browser in headless mode
   * @returns {Promise} Scrape job info
   */
  startScrape: async (credentials, headless = true) => {
    const response = await apiClient.post('/api/admin/scrape', {
      credentials,
      headless
    });
    return response.data;
  },

  /**
   * Get scrape job status
   * @param {Number} jobId - Scrape job ID
   * @returns {Promise} Job status
   */
  getScrapeStatus: async (jobId) => {
    const response = await apiClient.get(`/api/admin/scrape/status/${jobId}`);
    return response.data;
  },

  /**
   * Get latest scrape job
   * @returns {Promise} Latest job status
   */
  getLatestScrape: async () => {
    const response = await apiClient.get('/api/admin/scrape/latest');
    return response.data;
  },

  /**
   * Cancel a running scrape job
   * @param {Number} jobId - Scrape job ID
   * @returns {Promise} Cancellation result
   */
  cancelScrape: async (jobId) => {
    const response = await apiClient.delete(`/api/admin/scrape/${jobId}`);
    return response.data;
  },

  /**
   * Force cancel all stale scrape jobs
   * Use when jobs are stuck after server restart
   * @returns {Promise} Force cancellation result
   */
  forceCancelScrape: async () => {
    const response = await apiClient.post('/api/admin/scrape/force-cancel');
    return response.data;
  },

  /**
   * Search pre-scraped database (instant, no credentials)
   * @param {Array} targetModules - List of NTU module codes
   * @param {Array} targetCountries - Optional list of countries
   * @param {Number} targetSemester - Target semester (1, 2, or null for both)
   * @param {Number} minMappableModules - Minimum mappable modules
   * @returns {Promise} Search results
   */
  searchDatabase: async (targetModules, targetCountries = null, targetSemester = null, minMappableModules = 1) => {
    const response = await apiClient.post('/api/search/db', {
      target_modules: targetModules,
      target_countries: targetCountries,
      target_semester: targetSemester,
      min_mappable_modules: minMappableModules
    });
    return response.data;
  },

  /**
   * Get available modules in database
   * @returns {Promise} List of module codes
   */
  getAvailableModules: async () => {
    const response = await apiClient.get('/api/admin/database/modules');
    return response.data;
  },

  /**
   * Get available countries in database
   * @returns {Promise} List of countries
   */
  getAvailableCountries: async () => {
    const response = await apiClient.get('/api/admin/database/countries');
    return response.data;
  },

  /**
   * Clear database
   * @param {Boolean} confirm - Must be true to proceed
   * @returns {Promise} Clear result
   */
  clearDatabase: async (confirm = false) => {
    const response = await apiClient.post(`/api/admin/database/clear?confirm=${confirm}`);
    return response.data;
  }
};

export default api;
