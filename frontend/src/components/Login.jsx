/**
 * Login Component
 * Handles NTU SSO credentials input and verification
 */

import React, { useState } from 'react';
import { DOMAINS } from '../utils/constants';
import api from '../services/api';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [domain, setDomain] = useState('Student');
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [loginError, setLoginError] = useState(null);

  const validateForm = () => {
    const newErrors = {};

    if (!username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setLoginError(null);

    const credentials = {
      username: username.trim(),
      password,
      domain
    };

    try {
      // Actually verify with NTU SSO
      const result = await api.verifyLogin(credentials);

      if (result.success) {
        // Login successful - proceed to main app
        onLogin(credentials);
      } else {
        // Login failed
        setLoginError(result.message || 'Login failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      const errorMsg = err.response?.data?.message || err.message || 'Login failed';
      setLoginError(`Error: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-ntu-blue rounded-full mb-4">
              <span className="text-white text-2xl font-bold">NTU</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Welcome to Exchange Finder
            </h2>
            <p className="text-gray-600">
              Sign in with your NTU credentials
            </p>
          </div>

          {/* Login Error */}
          {loginError && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{loginError}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Username
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-ntu-blue focus:border-transparent ${
                  errors.username ? 'border-red-500' : 'border-gray-300'
                } ${isLoading ? 'bg-gray-100' : ''}`}
                placeholder="e.g., AJITESH001"
              />
              {errors.username && (
                <p className="text-red-500 text-sm mt-1">{errors.username}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-ntu-blue focus:border-transparent ${
                  errors.password ? 'border-red-500' : 'border-gray-300'
                } ${isLoading ? 'bg-gray-100' : ''}`}
                placeholder="Enter your password"
              />
              {errors.password && (
                <p className="text-red-500 text-sm mt-1">{errors.password}</p>
              )}
            </div>

            {/* Domain */}
            <div>
              <label
                htmlFor="domain"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Domain
              </label>
              <select
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                disabled={isLoading}
                className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ntu-blue focus:border-transparent ${
                  isLoading ? 'bg-gray-100' : ''
                }`}
              >
                {DOMAINS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={`w-full font-semibold py-3 rounded-lg transition-colors duration-200 ${
                isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-ntu-red hover:bg-ntu-red-light text-white'
              }`}
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Verifying with NTU...
                </div>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Loading Info */}
          {isLoading && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-sm text-gray-600 space-y-1">
                <p className="font-medium text-gray-800">Authenticating with NTU SSO...</p>
                <ul className="list-disc list-inside text-gray-500 text-xs">
                  <li>Starting secure browser session</li>
                  <li>Logging into NTU SSO</li>
                  <li>Fetching all exchange countries (first time only)</li>
                </ul>
                <p className="text-xs text-gray-500 mt-2">
                  First login: 1-2 minutes (fetching countries)
                </p>
                <p className="text-xs text-green-600">
                  Next logins: 10-30 seconds (countries cached)
                </p>
              </div>
            </div>
          )}

          {/* Security Note */}
          {!isLoading && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600 text-center">
                <span className="font-semibold">Security:</span> Credentials are verified with NTU SSO and are not stored
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;
