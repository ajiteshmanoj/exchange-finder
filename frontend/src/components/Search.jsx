/**
 * Search Component
 * Main search interface with inline progress and results
 */

import React, { useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { DEFAULT_MIN_MAPPABLE_MODULES, DEFAULT_USE_CACHE } from '../utils/constants';
import ModuleSelector from './ModuleSelector';
import CountrySelector from './CountrySelector';
import ProgressDisplay from './ProgressDisplay';
import UniversityCard from './UniversityCard';

const Search = ({ credentials }) => {
  // Form state
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [selectedModules, setSelectedModules] = useState([]);
  const [minMappableModules, setMinMappableModules] = useState(DEFAULT_MIN_MAPPABLE_MODULES);
  const [useCache, setUseCache] = useState(DEFAULT_USE_CACHE);

  // WebSocket state
  const {
    progressMessages,
    results,
    error,
    isSearching,
    currentStep,
    executionTime,
    cacheUsed,
    startSearch,
    cancelSearch,
    reset
  } = useWebSocket();

  const handleSearch = () => {
    if (selectedCountries.length === 0) {
      alert('Please select at least one country');
      return;
    }

    if (selectedModules.length === 0) {
      alert('Please select at least one module');
      return;
    }

    const searchRequest = {
      credentials,
      target_countries: selectedCountries,
      target_modules: selectedModules.map(m => m.code), // Extract module codes
      min_mappable_modules: minMappableModules,
      use_cache: useCache
    };

    startSearch(searchRequest);
  };

  const handleNewSearch = () => {
    reset();
  };

  const showForm = !isSearching && !results && !error;
  const showProgress = isSearching;
  const showResults = !isSearching && results;
  const showError = !isSearching && error;

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
      </div>

      {/* Search Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
          {/* Country Selector */}
          <CountrySelector
            selectedCountries={selectedCountries}
            onChange={setSelectedCountries}
            credentials={credentials}
          />

          {/* Module Selector */}
          <ModuleSelector
            selectedModules={selectedModules}
            onChange={setSelectedModules}
          />

          {/* Settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Min Mappable Modules */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Mappable Modules
              </label>
              <input
                type="number"
                min="1"
                max={selectedModules.length}
                value={minMappableModules}
                onChange={(e) => setMinMappableModules(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ntu-blue focus:border-transparent"
              />
            </div>

            {/* Use Cache */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cache Settings
              </label>
              <label className="flex items-center p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={useCache}
                  onChange={(e) => setUseCache(e.target.checked)}
                  className="w-4 h-4 text-ntu-blue border-gray-300 rounded focus:ring-ntu-blue"
                />
                <span className="ml-2 text-gray-700">
                  Use cached data (recommended for faster results)
                </span>
              </label>
            </div>
          </div>

          {/* Start Search Button */}
          <div>
            <button
              onClick={handleSearch}
              className="w-full bg-ntu-red hover:bg-ntu-red-light text-white font-semibold py-4 rounded-lg transition-colors duration-200"
            >
              Start Search
            </button>
            <p className="text-sm text-gray-500 mt-2 text-center">
              First search may take 15-25 minutes. Subsequent searches are instant with cache.
            </p>
          </div>
        </div>
      )}

      {/* Progress Display */}
      {showProgress && (
        <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-800">
              Search in Progress
            </h3>
            <button
              onClick={cancelSearch}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>

          <ProgressDisplay
            progressMessages={progressMessages}
            currentStep={currentStep}
            isSearching={isSearching}
          />
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
                  Execution time: {executionTime?.toFixed(2)}s •{' '}
                  {cacheUsed ? 'Loaded from cache' : 'Fresh data'}
                </p>
              </div>

              <button
                onClick={handleNewSearch}
                className="px-6 py-3 bg-ntu-blue hover:bg-ntu-blue-light text-white font-semibold rounded-lg transition-colors"
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
                Try adjusting your search parameters.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Search;
