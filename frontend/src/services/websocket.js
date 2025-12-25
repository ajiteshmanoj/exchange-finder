/**
 * WebSocket Client for NTU Exchange Finder
 * Handles real-time communication with the backend during university search
 */

import { WS_SEARCH_ENDPOINT } from '../utils/constants';

export class WebSocketSearchClient {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.messageHandlers = {
      progress: [],
      complete: [],
      error: []
    };
  }

  /**
   * Connect to WebSocket and start search
   * @param {Object} searchRequest - Search request payload
   * @returns {Promise} Resolves when connection is established
   */
  connect(searchRequest) {
    return new Promise((resolve, reject) => {
      try {
        // Create WebSocket connection
        this.ws = new WebSocket(WS_SEARCH_ENDPOINT);

        // Connection opened
        this.ws.onopen = () => {
          console.log('[WebSocket] Connected to server');
          this.isConnected = true;

          // Send search request
          this.ws.send(JSON.stringify(searchRequest));
          console.log('[WebSocket] Search request sent');

          resolve();
        };

        // Listen for messages
        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this._handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        // Connection closed
        this.ws.onclose = () => {
          console.log('[WebSocket] Connection closed');
          this.isConnected = false;
        };

        // Connection error
        this.ws.onerror = (error) => {
          console.error('[WebSocket] Connection error:', error);
          this.isConnected = false;
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Route incoming messages to appropriate handlers
   * @param {Object} message - Parsed message object
   */
  _handleMessage(message) {
    const { type } = message;

    if (!type) {
      console.warn('[WebSocket] Received message without type:', message);
      return;
    }

    // Call registered handlers for this message type
    const handlers = this.messageHandlers[type] || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error(`[WebSocket] Handler error for type "${type}":`, error);
      }
    });

    // Auto-disconnect on complete or error
    if (type === 'complete' || type === 'error') {
      setTimeout(() => this.disconnect(), 100);
    }
  }

  /**
   * Register a message handler
   * @param {string} type - Message type ('progress', 'complete', 'error')
   * @param {Function} handler - Handler function(message)
   */
  on(type, handler) {
    if (!this.messageHandlers[type]) {
      this.messageHandlers[type] = [];
    }
    this.messageHandlers[type].push(handler);
  }

  /**
   * Remove a message handler
   * @param {string} type - Message type
   * @param {Function} handler - Handler function to remove
   */
  off(type, handler) {
    if (!this.messageHandlers[type]) return;
    this.messageHandlers[type] = this.messageHandlers[type].filter(h => h !== handler);
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
      console.log('[WebSocket] Disconnected');
    }
  }

  /**
   * Check if currently connected
   * @returns {boolean}
   */
  isActive() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}
