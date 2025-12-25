/**
 * Application Constants for NTU Exchange Finder
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
export const WS_SEARCH_ENDPOINT = `${WS_BASE_URL}/ws/search`;

// Countries are now fetched dynamically from API
// No hardcoded country list

// Modules are now entered dynamically by users
// No hardcoded module list

// NTU SSO Domains
export const DOMAINS = ['Student', 'Staff'];

// Progress Step Names
export const PROGRESS_STEPS = {
  1: 'PDF Extraction',
  2: 'Module Mapping Scraping',
  3: 'Processing & Ranking'
};

// NTU Brand Colors (official)
export const NTU_COLORS = {
  red: '#EF3340',
  blue: '#003D7C',
  redLight: '#FF4757',
  redDark: '#D12938',
  blueLight: '#0056A8',
  blueDark: '#002654'
};

// Search Configuration Defaults
export const DEFAULT_MIN_MAPPABLE_MODULES = 2;
export const DEFAULT_USE_CACHE = true;
