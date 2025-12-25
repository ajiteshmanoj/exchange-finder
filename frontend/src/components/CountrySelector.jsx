/**
 * CountrySelector Component
 * Searchable multi-select dropdown for selecting countries
 * Shows university count per country (e.g., "Australia (45 universities)")
 */

import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import api from '../services/api';

const CountrySelector = ({ selectedCountries, onChange, credentials }) => {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [cacheUsed, setCacheUsed] = useState(false);

  // Fetch countries on mount
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await api.getCountriesUniversities(credentials, true);

        // Transform to react-select format with university count
        const options = response.countries
          .map(c => ({
            value: c.country,
            label: `${c.country} (${c.university_count} ${c.university_count === 1 ? 'university' : 'universities'})`,
            universityCount: c.university_count,
            universities: c.universities
          }))
          .sort((a, b) => a.value.localeCompare(b.value)); // Alphabetical sort

        setCountries(options);
        setCacheUsed(response.cache_used);
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch countries:', err);
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to load countries';
        setError(`Error: ${errorMsg}`);
        setLoading(false);
      }
    };

    if (credentials) {
      fetchCountries();
    }
  }, [credentials]);

  const handleChange = (selectedOptions) => {
    const selected = selectedOptions ? selectedOptions.map(opt => opt.value) : [];
    onChange(selected);
  };

  const handleSelectAll = () => {
    onChange(countries.map(c => c.value));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  // Get selected options for react-select
  const selectedOptions = countries.filter(c => selectedCountries.includes(c.value));

  // Custom styles for react-select (NTU colors)
  const customStyles = {
    control: (base, state) => ({
      ...base,
      borderColor: state.isFocused ? '#003D7C' : '#E5E7EB',
      boxShadow: state.isFocused ? '0 0 0 2px rgba(0, 61, 124, 0.1)' : 'none',
      '&:hover': {
        borderColor: '#003D7C'
      }
    }),
    multiValue: (base) => ({
      ...base,
      backgroundColor: '#EBF5FF',
      borderRadius: '0.375rem'
    }),
    multiValueLabel: (base) => ({
      ...base,
      color: '#003D7C',
      fontWeight: '500'
    }),
    multiValueRemove: (base) => ({
      ...base,
      color: '#003D7C',
      ':hover': {
        backgroundColor: '#EF3340',
        color: 'white'
      }
    })
  };

  if (loading) {
    return (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-800">
          Target Countries
        </h3>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center mb-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-ntu-blue"></div>
            <span className="ml-3 font-medium text-gray-800">Loading countries from NTU...</span>
          </div>
          <div className="text-sm text-gray-600 space-y-1">
            <p>This may take 2-5 minutes on first load:</p>
            <ul className="list-disc list-inside ml-2 text-gray-500">
              <li>Starting browser...</li>
              <li>Logging into NTU SSO with your credentials...</li>
              <li>Scraping all countries and universities...</li>
            </ul>
            <p className="mt-2 text-green-600 font-medium">
              Next time will be instant (cached for 30 days)
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-800">
          Target Countries
        </h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 text-sm text-ntu-blue hover:text-ntu-blue-light font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">
          Target Countries
          <span className="ml-2 text-sm font-normal text-gray-500">
            ({selectedCountries.length} of {countries.length} selected)
          </span>
          {cacheUsed && (
            <span className="ml-2 text-xs text-green-600 font-normal">
              • Cached
            </span>
          )}
        </h3>
        <div className="space-x-2">
          <button
            type="button"
            onClick={handleSelectAll}
            className="text-sm text-ntu-blue hover:text-ntu-blue-light font-medium"
          >
            Select All
          </button>
          <span className="text-gray-300">|</span>
          <button
            type="button"
            onClick={handleClearAll}
            className="text-sm text-ntu-red hover:text-ntu-red-light font-medium"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Searchable Multi-Select Dropdown */}
      <Select
        isMulti
        options={countries}
        value={selectedOptions}
        onChange={handleChange}
        styles={customStyles}
        placeholder="Search and select countries..."
        noOptionsMessage={() => "No countries found"}
        closeMenuOnSelect={false}
        className="react-select-container"
        classNamePrefix="react-select"
      />

      {/* Info text */}
      <p className="text-sm text-gray-500">
        Search by typing country name. {countries.length} countries available with{' '}
        {countries.reduce((sum, c) => sum + c.universityCount, 0)} total universities.
      </p>
    </div>
  );
};

export default CountrySelector;
