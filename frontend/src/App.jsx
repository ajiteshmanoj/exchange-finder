/**
 * App Component
 * Root application component - public access (no login required)
 */

import React from 'react';
import Navbar from './components/Navbar';
import Search from './components/Search';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <Navbar isAuthenticated={false} onLogout={() => {}} />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Search />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="container mx-auto px-4 py-6">
          <p className="text-center text-gray-600 text-sm">
            NTU Exchange University Finder
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
