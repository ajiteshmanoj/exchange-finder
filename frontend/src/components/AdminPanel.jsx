/**
 * AdminPanel Component
 * Interface for managing database scraping and viewing status
 */

import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

function AdminPanel({ credentials }) {
  const [dbStatus, setDbStatus] = useState(null);
  const [scrapeJob, setScrapeJob] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [headless, setHeadless] = useState(true);
  const pollingRef = useRef(null);

  // Fetch database status on mount
  useEffect(() => {
    fetchDatabaseStatus();
    fetchLatestScrape();
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // Poll for scrape status if job is running
  useEffect(() => {
    if (scrapeJob?.status === 'running') {
      pollingRef.current = setInterval(fetchScrapeStatus, 3000);
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [scrapeJob?.status]);

  const fetchDatabaseStatus = async () => {
    try {
      const data = await api.getDatabaseStatus();
      setDbStatus(data);
    } catch (err) {
      console.error('Failed to fetch database status:', err);
    }
  };

  const fetchLatestScrape = async () => {
    try {
      const data = await api.getLatestScrape();
      setScrapeJob(data);
    } catch (err) {
      // No scrape jobs yet
      console.log('No scrape jobs found');
    }
  };

  const fetchScrapeStatus = async () => {
    if (!scrapeJob?.job_id) return;
    try {
      const data = await api.getScrapeStatus(scrapeJob.job_id);
      setScrapeJob(data);
      // Also refresh database status
      fetchDatabaseStatus();
    } catch (err) {
      console.error('Failed to fetch scrape status:', err);
    }
  };

  const startScrape = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.startScrape(credentials, headless);
      setScrapeJob({
        job_id: data.job_id,
        status: 'running',
        total_countries: 0,
        completed_countries: 0,
        total_universities: 0,
        completed_universities: 0
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start scrape');
    } finally {
      setIsLoading(false);
    }
  };

  const cancelScrape = async () => {
    if (!scrapeJob?.job_id) return;
    try {
      await api.cancelScrape(scrapeJob.job_id);
      fetchScrapeStatus();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to cancel scrape. Try Force Cancel if the job is stuck.');
    }
  };

  const forceCancelScrape = async () => {
    try {
      const result = await api.forceCancelScrape();
      setError(null);
      // Refresh status
      fetchLatestScrape();
      fetchDatabaseStatus();
      alert(result.message || 'Force cancelled stale jobs');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to force cancel');
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  const getProgressPercent = () => {
    if (!scrapeJob || !scrapeJob.total_universities) return 0;
    return Math.round((scrapeJob.completed_universities / scrapeJob.total_universities) * 100);
  };

  const getEstimatedTime = () => {
    if (!scrapeJob || !scrapeJob.total_universities || !scrapeJob.completed_universities) {
      return 'Calculating...';
    }
    const remaining = scrapeJob.total_universities - scrapeJob.completed_universities;
    const avgTimePerUni = 5; // seconds
    const remainingSeconds = remaining * avgTimePerUni;
    if (remainingSeconds < 60) return `${remainingSeconds}s`;
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = remainingSeconds % 60;
    return `${minutes}m ${seconds}s`;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Admin Panel</h2>

      {/* Database Status */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">Database Status</h3>

        {dbStatus ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">Status</div>
              <div className={`text-lg font-bold ${dbStatus.populated ? 'text-green-600' : 'text-yellow-600'}`}>
                {dbStatus.populated ? 'Populated' : 'Empty'}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">Countries</div>
              <div className="text-lg font-bold text-gray-800">{dbStatus.total_countries}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">Universities</div>
              <div className="text-lg font-bold text-gray-800">{dbStatus.total_universities}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500">Mappings</div>
              <div className="text-lg font-bold text-gray-800">{dbStatus.total_mappings}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 col-span-2">
              <div className="text-sm text-gray-500">Last Scrape</div>
              <div className="text-lg font-bold text-gray-800">{formatDate(dbStatus.last_scrape)}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 col-span-2">
              <div className="text-sm text-gray-500">Unique Modules</div>
              <div className="text-lg font-bold text-gray-800">{dbStatus.unique_modules}</div>
            </div>
          </div>
        ) : (
          <div className="text-gray-500">Loading database status...</div>
        )}
      </div>

      {/* Scrape Controls */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">Full Database Scrape</h3>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <div className="flex items-center gap-4 mb-4">
          <label className="flex items-center gap-2 text-gray-700">
            <input
              type="checkbox"
              checked={headless}
              onChange={(e) => setHeadless(e.target.checked)}
              className="w-4 h-4 text-blue-600"
            />
            Run in headless mode
          </label>
        </div>

        {scrapeJob?.status === 'running' ? (
          <div>
            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Progress: {getProgressPercent()}%</span>
                <span>ETA: {getEstimatedTime()}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-blue-600 h-4 rounded-full transition-all duration-500"
                  style={{ width: `${getProgressPercent()}%` }}
                ></div>
              </div>
            </div>

            {/* Current Status */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <div className="text-sm text-blue-700">
                <div className="font-semibold mb-2">Scraping in progress...</div>
                <div>Country: {scrapeJob.current_country || 'Starting...'}</div>
                <div>University: {scrapeJob.current_university || 'Starting...'}</div>
                <div className="mt-2">
                  Universities: {scrapeJob.completed_universities} / {scrapeJob.total_universities}
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={cancelScrape}
                className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-6 rounded-lg"
              >
                Cancel Scrape
              </button>
              <button
                onClick={forceCancelScrape}
                className="bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-6 rounded-lg"
                title="Use if regular cancel doesn't work (after server restart)"
              >
                Force Cancel
              </button>
            </div>
          </div>
        ) : (
          <div>
            <p className="text-gray-600 mb-4">
              Start a full scrape of all countries, universities, and module mappings.
              This will take approximately 60-90 minutes.
            </p>
            <button
              onClick={startScrape}
              disabled={isLoading}
              className={`font-medium py-2 px-6 rounded-lg ${
                isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isLoading ? 'Starting...' : 'Start Full Scrape'}
            </button>
          </div>
        )}
      </div>

      {/* Latest Scrape Job */}
      {scrapeJob && scrapeJob.status !== 'running' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">Latest Scrape Job</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-500">Job ID</div>
              <div className="font-medium">{scrapeJob.job_id}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Status</div>
              <div className={`font-medium ${
                scrapeJob.status === 'completed' ? 'text-green-600' :
                scrapeJob.status === 'failed' ? 'text-red-600' :
                scrapeJob.status === 'cancelled' ? 'text-yellow-600' :
                'text-gray-600'
              }`}>
                {scrapeJob.status?.charAt(0).toUpperCase() + scrapeJob.status?.slice(1)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Started</div>
              <div className="font-medium">{formatDate(scrapeJob.started_at)}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Completed</div>
              <div className="font-medium">{formatDate(scrapeJob.completed_at)}</div>
            </div>
            {scrapeJob.error_message && (
              <div className="col-span-2">
                <div className="text-sm text-gray-500">Error</div>
                <div className="font-medium text-red-600">{scrapeJob.error_message}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminPanel;
