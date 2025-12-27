/**
 * App Component
 * Root application component with conditional routing
 */

import React, { useState } from 'react';
import { useSession } from './hooks/useSession';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Search from './components/Search';
import AdminPanel from './components/AdminPanel';

function App() {
  const { session, createSession, clearSession, isAuthenticated } = useSession();
  const [activeTab, setActiveTab] = useState('search'); // 'search' or 'admin'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <Navbar
        isAuthenticated={isAuthenticated()}
        onLogout={clearSession}
      />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {!isAuthenticated() ? (
          <Login onLogin={createSession} />
        ) : (
          <>
            {/* Tab Navigation */}
            <div className="flex gap-4 mb-8">
              <button
                onClick={() => setActiveTab('search')}
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'search'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                }`}
              >
                Search
              </button>
              <button
                onClick={() => setActiveTab('admin')}
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'admin'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                }`}
              >
                Admin Panel
              </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'search' ? (
              <Search credentials={session.credentials} />
            ) : (
              <AdminPanel credentials={session.credentials} />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="container mx-auto px-4 py-6">
          <p className="text-center text-gray-600 text-sm">
            NTU Exchange University Finder • For personal educational use
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
