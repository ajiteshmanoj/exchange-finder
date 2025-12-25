/**
 * UniversityCard Component
 * Displays individual university result with module mappings
 */

import React, { useState } from 'react';

const UniversityCard = ({ university }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-ntu-blue to-ntu-blue-light px-6 py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              {/* Rank Badge */}
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
                <span className="text-ntu-blue font-bold text-lg">
                  #{university.rank}
                </span>
              </div>

              {/* University Info */}
              <div>
                <h3 className="text-xl font-bold text-white">
                  {university.name}
                </h3>
                <p className="text-blue-100 text-sm">{university.country}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 bg-gray-50">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Sem 1 Spots
          </div>
          <div className="text-2xl font-bold text-gray-800">
            {university.sem1_spots}
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Min CGPA
          </div>
          <div className="text-2xl font-bold text-gray-800">
            {university.min_cgpa.toFixed(2)}
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Mappable
          </div>
          <div className="text-2xl font-bold text-green-600">
            {university.mappable_count}
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Coverage
          </div>
          <div className="text-2xl font-bold text-ntu-blue">
            {university.coverage_score.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Show Details Toggle */}
      <div className="px-6 py-3 border-t border-gray-200">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-ntu-blue hover:text-ntu-blue-light font-medium text-sm flex items-center space-x-2"
        >
          <span>{showDetails ? 'Hide Details' : 'Show Details'}</span>
          <svg
            className={`w-4 h-4 transform transition-transform ${
              showDetails ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      </div>

      {/* Detailed Information (expandable) */}
      {showDetails && (
        <div className="px-6 pb-6 space-y-4">
          {/* Mappable Modules */}
          {Object.keys(university.mappable_modules).length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Mappable Modules
              </h4>
              <div className="space-y-3">
                {Object.entries(university.mappable_modules).map(
                  ([ntuModule, mappings]) => (
                    <div
                      key={ntuModule}
                      className="border border-green-200 rounded-lg p-3 bg-green-50"
                    >
                      <div className="font-semibold text-green-800 mb-2">
                        {ntuModule}
                      </div>
                      <div className="space-y-2">
                        {mappings.map((mapping, idx) => (
                          <div
                            key={idx}
                            className="text-sm bg-white rounded p-2 border border-green-100"
                          >
                            <div className="font-medium text-gray-800">
                              {mapping.partner_module_code} -{' '}
                              {mapping.partner_module_name}
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              {mapping.academic_units} AU • Semester{' '}
                              {mapping.semester} • {mapping.status} (
                              {mapping.approval_year})
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>
          )}

          {/* Unmappable Modules */}
          {university.unmappable_modules.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
                <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                Unmappable Modules
              </h4>
              <div className="flex flex-wrap gap-2">
                {university.unmappable_modules.map((module) => (
                  <span
                    key={module}
                    className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm"
                  >
                    {module}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Remarks */}
          {university.remarks && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-700">
                <span className="font-semibold">Remarks:</span>{' '}
                {university.remarks}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UniversityCard;
