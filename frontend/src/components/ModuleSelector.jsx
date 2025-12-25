/**
 * ModuleSelector Component
 * Dynamic input for adding custom NTU modules
 * Users can add/remove modules with code and name
 */

import React, { useState } from 'react';

const ModuleSelector = ({ selectedModules, onChange }) => {
  const [moduleCode, setModuleCode] = useState('');
  const [moduleName, setModuleName] = useState('');

  const handleAddModule = () => {
    const code = moduleCode.trim().toUpperCase();
    const name = moduleName.trim();

    if (!code) {
      alert('Please enter a module code');
      return;
    }

    // Check if module already exists
    if (selectedModules.some(m => m.code === code)) {
      alert('Module already added');
      return;
    }

    // Add module to list
    onChange([...selectedModules, { code, name: name || code }]);

    // Clear inputs
    setModuleCode('');
    setModuleName('');
  };

  const handleRemoveModule = (code) => {
    onChange(selectedModules.filter(m => m.code !== code));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddModule();
    }
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">
          Target Modules
          <span className="ml-2 text-sm font-normal text-gray-500">
            ({selectedModules.length} module{selectedModules.length !== 1 ? 's' : ''})
          </span>
        </h3>
      </div>

      {/* Input Fields */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Module Code *
            </label>
            <input
              type="text"
              value={moduleCode}
              onChange={(e) => setModuleCode(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., SC4001"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ntu-blue focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Module Name (optional)
            </label>
            <input
              type="text"
              value={moduleName}
              onChange={(e) => setModuleName(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., Neural Networks & Deep Learning"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ntu-blue focus:border-transparent"
            />
          </div>
        </div>
        <button
          type="button"
          onClick={handleAddModule}
          className="w-full md:w-auto px-4 py-2 bg-ntu-blue hover:bg-ntu-blue-light text-white font-medium rounded-lg transition-colors"
        >
          + Add Module
        </button>
      </div>

      {/* Added Modules List */}
      {selectedModules.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Added Modules:</p>
          <div className="space-y-2">
            {selectedModules.map((module) => (
              <div
                key={module.code}
                className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-ntu-blue transition-colors"
              >
                <div className="flex-1">
                  <div className="font-semibold text-gray-800">
                    {module.code}
                  </div>
                  {module.name && module.name !== module.code && (
                    <div className="text-sm text-gray-600">{module.name}</div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveModule(module.code)}
                  className="ml-3 px-3 py-1 text-sm text-ntu-red hover:bg-red-50 font-medium rounded transition-colors"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedModules.length === 0 && (
        <div className="text-center py-6 text-gray-500 text-sm border border-dashed border-gray-300 rounded-lg">
          No modules added yet. Add your NTU modules above.
        </div>
      )}
    </div>
  );
};

export default ModuleSelector;
