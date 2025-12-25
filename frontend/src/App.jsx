/**
 * App Component
 * Root application component with conditional routing
 */

import React from 'react';
import { useSession } from './hooks/useSession';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Search from './components/Search';

function App() {
  const { session, createSession, clearSession, isAuthenticated } = useSession();

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
          <Search credentials={session.credentials} />
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
