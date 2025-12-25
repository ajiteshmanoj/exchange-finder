/**
 * ProgressDisplay Component
 * Terminal-style display for real-time progress messages
 */

import React, { useRef, useEffect } from 'react';
import { PROGRESS_STEPS } from '../utils/constants';

const ProgressDisplay = ({ progressMessages, currentStep, isSearching }) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [progressMessages]);

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour12: false });
  };

  const getProgressPercentage = () => {
    if (currentStep === 0) return 0;
    if (currentStep === 1) return 33;
    if (currentStep === 2) return 66;
    if (currentStep === 3) return 100;
    return 0;
  };

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-600">
          <span className="font-medium">
            {currentStep > 0 ? PROGRESS_STEPS[currentStep] : 'Initializing...'}
          </span>
          <span>{getProgressPercentage()}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-ntu-blue h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${getProgressPercentage()}%` }}
          />
        </div>
      </div>

      {/* Terminal-style message box */}
      <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm overflow-hidden">
        <div className="h-96 overflow-y-auto space-y-1">
          {progressMessages.length === 0 && (
            <div className="text-gray-500">Waiting for messages...</div>
          )}

          {progressMessages.map((msg, index) => (
            <div key={index} className="text-green-400">
              <span className="text-gray-500">
                [{formatTime(msg.timestamp)}]
              </span>
              <span className="ml-2 text-yellow-400">
                [Step {msg.step}]
              </span>
              <span className="ml-2">{msg.message}</span>
              {msg.details && (
                <div className="ml-16 text-gray-400 text-xs mt-1">
                  └─ {JSON.stringify(msg.details, null, 2)}
                </div>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {isSearching && (
            <div className="text-green-400 animate-pulse">
              <span className="text-gray-500">
                [{formatTime(new Date())}]
              </span>
              <span className="ml-2">Processing...</span>
            </div>
          )}

          {/* Auto-scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Message count */}
      <div className="text-sm text-gray-600 text-right">
        {progressMessages.length} message{progressMessages.length !== 1 ? 's' : ''} received
      </div>
    </div>
  );
};

export default ProgressDisplay;
