/**
 * Search Component
 * Main search interface - uses pre-scraped database for instant results
 */

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { DEFAULT_MIN_MAPPABLE_MODULES } from '../utils/constants';
import ModuleSelector from './ModuleSelector';
import UniversityCard from './UniversityCard';

const Search = ({ credentials }) => {
  // Form state
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [selectedModules, setSelectedModules] = useState([]);
  const [minMappableModules, setMinMappableModules] = useState(DEFAULT_MIN_MAPPABLE_MODULES);

  // Search state
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [executionTime, setExecutionTime] = useState(null);
  const [dbStatus, setDbStatus] = useState(null);

  // Available countries from database
  const [availableCountries, setAvailableCountries] = useState([]);
  const [loadingCountries, setLoadingCountries] = useState(true);

  // Load database status and available countries on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [status, countriesData] = await Promise.all([
          api.getDatabaseStatus(),
          api.getAvailableCountries()
        ]);
        setDbStatus(status);
        setAvailableCountries(countriesData.countries || []);
      } catch (err) {
        console.error('Failed to load database info:', err);
        setError('Failed to load database. Please run admin scrape first.');
      } finally {
        setLoadingCountries(false);
      }
    };
    loadData();
  }, []);

  const handleSearch = async () => {
    if (selectedModules.length === 0) {
      alert('Please select at least one module');
      return;
    }

    setIsSearching(true);
    setError(null);
    setResults(null);

    try {
      const response = await api.searchDatabase(
        selectedModules.map(m => m.code),
        selectedCountries.length > 0 ? selectedCountries : null,
        minMappableModules
      );

      setResults(response.results);
      setExecutionTime(response.execution_time_seconds);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed. Is the database populated?');
    } finally {
      setIsSearching(false);
    }
  };

  const handleNewSearch = () => {
    setResults(null);
    setError(null);
    setExecutionTime(null);
  };

  const showForm = !isSearching && !results && !error;
  const showResults = !isSearching && results;
  const showError = !isSearching && error && !results;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Search Exchange Universities
        </h2>
        <p className="text-gray-600">
          Find universities that match your module requirements
        </p>
        {dbStatus && (
          <div className="mt-3 text-sm text-gray-500">
            Database: {dbStatus.total_universities} universities, {dbStatus.total_mappings.toLocaleString()} mappings
            {dbStatus.last_scrape && ` (Last updated: ${new Date(dbStatus.last_scrape).toLocaleDateString()})`}
          </div>
        )}
      </div>

      {/* Search Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
          {/* Database not populated warning */}
          {dbStatus && !dbStatus.populated && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-yellow-800">
                Database is empty. Please go to Admin Panel and run a full scrape first.
              </p>
            </div>
          )}

          {/* Country Selector - Simple multi-select from database */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Countries (optional)
            </label>
            {loadingCountries ? (
              <div className="text-gray-500">Loading countries...</div>
            ) : (
              <select
                multiple
                value={selectedCountries}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  setSelectedCountries(values);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                style={{ minHeight: '120px' }}
              >
                {availableCountries.map(country => (
                  <option key={country} value={country}>{country}</option>
                ))}
              </select>
            )}
            <p className="text-xs text-gray-500 mt-1">
              Hold Ctrl/Cmd to select multiple. Leave empty to search all countries.
            </p>
          </div>

          {/* Module Selector */}
          <ModuleSelector
            selectedModules={selectedModules}
            onChange={setSelectedModules}
          />

          {/* Settings */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Mappable Modules
            </label>
            <input
              type="number"
              min="1"
              max={selectedModules.length || 10}
              value={minMappableModules}
              onChange={(e) => setMinMappableModules(parseInt(e.target.value) || 1)}
              className="w-32 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Start Search Button */}
          <div>
            <button
              onClick={handleSearch}
              disabled={isSearching || !dbStatus?.populated}
              className={`w-full font-semibold py-4 rounded-lg transition-colors duration-200 ${
                isSearching || !dbStatus?.populated
                  ? 'bg-gray-400 cursor-not-allowed text-gray-200'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>
            <p className="text-sm text-green-600 mt-2 text-center font-medium">
              Instant results from pre-scraped database
            </p>
          </div>
        </div>
      )}

      {/* Error Display */}
      {showError && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-semibold text-red-800 mb-2">
              Search Failed
            </h3>
            <p className="text-red-700">{error}</p>
          </div>

          <button
            onClick={handleNewSearch}
            className="w-full bg-ntu-blue hover:bg-ntu-blue-light text-white font-semibold py-3 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Results Display */}
      {showResults && (
        <div className="space-y-6">
          {/* Results Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <h3 className="text-2xl font-bold text-green-600 mb-1">
                  Search Complete!
                </h3>
                <p className="text-gray-600">
                  Found <span className="font-semibold">{results.length}</span> universities
                  matching your criteria
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Execution time: {(executionTime * 1000).toFixed(0)}ms (from pre-scraped database)
                </p>
              </div>

              <button
                onClick={handleNewSearch}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
              >
                New Search
              </button>
            </div>
          </div>

          {/* University Cards */}
          <div className="space-y-4">
            {results.map((university) => (
              <UniversityCard key={university.rank} university={university} />
            ))}
          </div>

          {results.length === 0 && (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <p className="text-gray-600 text-lg">
                No universities found matching your criteria.
              </p>
              <p className="text-gray-500 mt-2">
                Try adjusting your search parameters or reducing the minimum mappable modules.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Search;
