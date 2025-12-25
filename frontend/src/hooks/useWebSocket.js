/**
 * useWebSocket Hook
 * Manages WebSocket state and provides interface for real-time search
 */

import { useState, useRef, useCallback } from 'react';
import { WebSocketSearchClient } from '../services/websocket';

export const useWebSocket = () => {
  const [progressMessages, setProgressMessages] = useState([]);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [executionTime, setExecutionTime] = useState(null);
  const [cacheUsed, setCacheUsed] = useState(false);

  const clientRef = useRef(null);

  /**
   * Start a new search with WebSocket
   * @param {Object} searchRequest - Search request payload
   */
  const startSearch = useCallback(async (searchRequest) => {
    // Reset state
    setProgressMessages([]);
    setResults(null);
    setError(null);
    setIsSearching(true);
    setCurrentStep(0);
    setExecutionTime(null);
    setCacheUsed(false);

    try {
      // Create new WebSocket client
      const client = new WebSocketSearchClient();
      clientRef.current = client;

      // Register message handlers
      client.on('progress', (message) => {
        setProgressMessages(prev => [...prev, {
          timestamp: new Date(),
          step: message.step,
          stepName: message.step_name,
          message: message.message,
          details: message.details
        }]);
        setCurrentStep(message.step);
      });

      client.on('complete', (message) => {
        setResults(message.results);
        setExecutionTime(message.execution_time);
        setCacheUsed(message.cache_used);
        setIsSearching(false);
        setProgressMessages(prev => [...prev, {
          timestamp: new Date(),
          step: 3,
          stepName: 'Complete',
          message: message.message,
          details: null
        }]);
      });

      client.on('error', (message) => {
        setError(message.error);
        setIsSearching(false);
        setProgressMessages(prev => [...prev, {
          timestamp: new Date(),
          step: 0,
          stepName: 'Error',
          message: message.error,
          details: message.details
        }]);
      });

      // Connect and send request
      await client.connect(searchRequest);

    } catch (err) {
      console.error('WebSocket connection error:', err);
      setError('Failed to connect to server');
      setIsSearching(false);
    }
  }, []);

  /**
   * Cancel ongoing search
   */
  const cancelSearch = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }
    setIsSearching(false);
    setProgressMessages(prev => [...prev, {
      timestamp: new Date(),
      step: 0,
      stepName: 'Cancelled',
      message: 'Search cancelled by user',
      details: null
    }]);
  }, []);

  /**
   * Reset to initial state
   */
  const reset = useCallback(() => {
    setProgressMessages([]);
    setResults(null);
    setError(null);
    setIsSearching(false);
    setCurrentStep(0);
    setExecutionTime(null);
    setCacheUsed(false);

    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }
  }, []);

  return {
    // State
    progressMessages,
    results,
    error,
    isSearching,
    currentStep,
    executionTime,
    cacheUsed,

    // Methods
    startSearch,
    cancelSearch,
    reset
  };
};
