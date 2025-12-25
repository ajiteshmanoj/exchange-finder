/**
 * Navbar Component
 * Top navigation bar with NTU branding
 */

import React from 'react';

const Navbar = ({ isAuthenticated, onLogout }) => {
  return (
    <nav className="bg-ntu-blue text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-ntu-red rounded-lg flex items-center justify-center font-bold text-lg">
              NTU
            </div>
            <h1 className="text-xl font-bold">Exchange Finder</h1>
          </div>

          {/* Navigation Actions */}
          <div className="flex items-center space-x-4">
            {isAuthenticated && (
              <button
                onClick={onLogout}
                className="px-4 py-2 bg-ntu-red hover:bg-ntu-red-light rounded-lg transition-colors duration-200"
              >
                Logout
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
