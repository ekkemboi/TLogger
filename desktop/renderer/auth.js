/**
 * WidgetAuthManager - Handles authentication for TradeLogger desktop widget
 * Uses browser-based login with protocol handler callback and secure token storage
 */
class WidgetAuthManager {
  constructor() {
    this.isAuthenticated = false;
    this.user = null;
    this.isCheckingAuth = false;
    this.tokens = null; // In-memory token cache
    this.loginButton = null;
    this.logoutButton = null;
    this.loadingSpinner = null;
    this.loginView = null;
    this.tradeView = null;
    this.userBar = null;
    this.authPollInterval = null;
  }

  /**
   * Initialize auth manager - call on page load
   */
  async init() {
    console.log('WidgetAuthManager initializing...');
    console.log('electronAPI available:', !!window.electronAPI);

    this.cacheElements();
    this.bindEvents();
    this.listenForAuthCallbacks();

    // Auto-check auth on startup (will use stored tokens if available)
    await this.checkAuthStatus();
  }

  cacheElements() {
    this.loginView = document.getElementById('login-view');
    this.tradeView = document.getElementById('trade-view');
    this.loadingSpinner = document.getElementById('loading-spinner');
    this.loginButton = document.getElementById('browser-login-btn');
    this.logoutButton = document.getElementById('logout-btn');
    this.userBar = document.getElementById('user-bar');
    this.userName = document.getElementById('user-name');
  }

  bindEvents() {
    console.log('Binding events...');

    if (this.loginButton) {
      this.loginButton.addEventListener('click', () => {
        console.log('Login button clicked!');
        this.startBrowserLogin();
      });
    }

    if (this.logoutButton) {
      this.logoutButton.addEventListener('click', () => {
        console.log('Logout button clicked!');
        this.logout();
      });
    }
  }

  /**
   * Listen for auth callbacks from main process via deep links
   */
  listenForAuthCallbacks() {
    if (window.electronAPI && window.electronAPI.onAuthCallback) {
      window.electronAPI.onAuthCallback(async (event, data) => {
        console.log('Auth callback received:', data);

        if (data.status === 'success') {
          console.log('Auth success via protocol callback');
          this.hideLoading();

          // If tokens were passed in the callback, use them
          if (data.tokens) {
            console.log('Received tokens from callback');
            this.tokens = data.tokens;
            // Store in main process for persistence
            await window.electronAPI.storeTokens(
              data.tokens.accessToken,
              data.tokens.refreshToken,
              data.tokens.rememberMe
            );
          }

          // Check auth status with the new tokens
          await this.checkAuthStatus();
        } else {
          this.hideLoading();
          let errorMessage = 'Authentication failed. Please try again.';
          if (data.status === 'expired') {
            errorMessage = 'Session expired. Please log in again.';
          } else if (data.status === 'invalid') {
            errorMessage = 'Invalid session. Please log in again.';
          } else if (data.status === 'unauthenticated') {
            errorMessage = 'Not logged in. Please log in via browser first.';
          }
          this.showError(errorMessage);
        }
      });
    } else {
      console.error('electronAPI.onAuthCallback not available');
    }
  }

  /**
   * Get tokens from main process
   * @returns {Object|null} Tokens object or null
   */
  async getStoredTokens() {
    if (this.tokens) {
      return this.tokens;
    }

    if (window.electronAPI && window.electronAPI.getStoredTokens) {
      try {
        this.tokens = await window.electronAPI.getStoredTokens();
        return this.tokens;
      } catch (error) {
        console.error('Failed to get stored tokens:', error);
        return null;
      }
    }

    return null;
  }

  /**
   * Check current authentication status via API
   * Uses stored tokens via Authorization header
   */
  async checkAuthStatus() {
    if (this.isCheckingAuth) {
      console.log('Already checking auth, skipping...');
      return this.isAuthenticated;
    }

    this.isCheckingAuth = true;
    console.log('Checking auth status...');

    try {
      // Get stored tokens
      const tokens = await this.getStoredTokens();

      const headers = {
        'Accept': 'application/json',
      };

      // Add Authorization header if we have tokens
      if (tokens && tokens.accessToken) {
        headers['Authorization'] = `Bearer ${tokens.accessToken}`;
      }

      const response = await fetch('http://localhost:5000/api/auth/status', {
        credentials: 'include',
        headers,
      });

      console.log('Auth status response:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Auth data:', JSON.stringify(data));

        if (data.authenticated) {
          this.isAuthenticated = true;
          this.user = data.user || null;
        } else {
          // If we have tokens but they're invalid/expired, try refreshing
          if (tokens && tokens.refreshToken) {
            console.log('Token invalid, attempting refresh...');
            const refreshed = await this.refreshAccessToken(tokens.refreshToken);
            if (refreshed) {
              // Retry check with new token
              this.isCheckingAuth = false;
              return this.checkAuthStatus();
            }
          }

          this.isAuthenticated = false;
          this.user = null;
        }
      } else if (response.status === 401) {
        // Unauthorized - try to refresh token
        if (tokens && tokens.refreshToken) {
          console.log('Got 401, attempting token refresh...');
          const refreshed = await this.refreshAccessToken(tokens.refreshToken);
          if (refreshed) {
            // Retry check with new token
            this.isCheckingAuth = false;
            return this.checkAuthStatus();
          }
        }

        // Refresh failed or no refresh token
        this.isAuthenticated = false;
        this.user = null;
        this.tokens = null;
      } else {
        console.log('Auth check failed with status:', response.status);
        this.isAuthenticated = false;
        this.user = null;
      }
    } catch (error) {
      console.error('Auth check failed with error:', error.message);
      this.isAuthenticated = false;
      this.user = null;
    } finally {
      this.isCheckingAuth = false;
      this.updateUI();
    }

    return this.isAuthenticated;
  }

  /**
   * Refresh access token using refresh token
   * @param {string} refreshToken - The refresh token
   * @returns {boolean} Success status
   */
  async refreshAccessToken(refreshToken) {
    try {
      console.log('Refreshing access token...');

      const response = await fetch('http://localhost:5000/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshToken}`,
          'Accept': 'application/json',
        },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Token refresh successful');

        // Update stored tokens
        this.tokens = {
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          rememberMe: this.tokens ? this.tokens.rememberMe : true,
        };

        // Store in main process
        if (window.electronAPI && window.electronAPI.storeTokens) {
          await window.electronAPI.storeTokens(
            data.access_token,
            data.refresh_token,
            this.tokens.rememberMe
          );
        }

        return true;
      } else {
        console.error('Token refresh failed:', response.status);
        return false;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  }

  /**
   * Start browser login flow
   */
  startBrowserLogin() {
    this.clearError();

    if (window.electronAPI && window.electronAPI.openBrowserLogin) {
      console.log('Opening browser login...');
      window.electronAPI.openBrowserLogin();
      this.showError('Browser opened! Complete login in browser, then return here.');
    } else {
      console.error('electronAPI not available');
      this.showError('Unable to open browser. Please visit http://localhost:5000/login?source=desktop');
    }
  }

  /**
   * Logout - clears widget tokens only (doesn't affect browser)
   */
  async logout() {
    console.log('Logging out...');

    try {
      // Clear stored tokens in main process
      if (window.electronAPI && window.electronAPI.clearStoredTokens) {
        await window.electronAPI.clearStoredTokens();
      }

      // Clear in-memory tokens
      this.tokens = null;
      this.isAuthenticated = false;
      this.user = null;

      this.updateUI();
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  /**
   * Get authorization headers for API calls
   * @returns {Object} Headers object with Authorization if available
   */
  async getAuthHeaders() {
    const tokens = await this.getStoredTokens();
    const headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };

    if (tokens && tokens.accessToken) {
      headers['Authorization'] = `Bearer ${tokens.accessToken}`;
    }

    return headers;
  }

  /**
   * Make authenticated API request with automatic token refresh
   * @param {string} url - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise<Response>} Fetch response
   */
  async apiRequest(url, options = {}) {
    const tokens = await this.getStoredTokens();

    const config = {
      ...options,
      headers: {
        ...options.headers,
        'Accept': 'application/json',
      },
    };

    if (tokens && tokens.accessToken) {
      config.headers['Authorization'] = `Bearer ${tokens.accessToken}`;
    }

    let response = await fetch(url, config);

    // Handle 401 by refreshing token
    if (response.status === 401 && tokens && tokens.refreshToken) {
      console.log('API request got 401, refreshing token...');
      const refreshed = await this.refreshAccessToken(tokens.refreshToken);

      if (refreshed) {
        // Retry with new token
        const newTokens = await this.getStoredTokens();
        config.headers['Authorization'] = `Bearer ${newTokens.accessToken}`;
        response = await fetch(url, config);
      } else {
        // Refresh failed, logout
        this.logout();
      }
    }

    return response;
  }

  /**
   * Show loading spinner with message
   */
  showLoading(message = 'Loading...') {
    if (this.loadingSpinner) {
      const textEl = this.loadingSpinner.querySelector('.loading-text');
      if (textEl) textEl.textContent = message;
      this.loadingSpinner.classList.remove('hidden');
    }
    if (this.loginView) this.loginView.classList.add('hidden');
    if (this.tradeView) this.tradeView.classList.add('hidden');
  }

  /**
   * Hide loading spinner
   */
  hideLoading() {
    if (this.loadingSpinner) {
      this.loadingSpinner.classList.add('hidden');
    }
    this.updateUI();
  }

  /**
   * Update UI based on auth state
   */
  updateUI() {
    console.log('updateUI called, isAuthenticated:', this.isAuthenticated);

    if (!this.loginView || !this.tradeView) {
      console.error('Missing loginView or tradeView!');
      return;
    }

    if (this.isAuthenticated) {
      console.log('Showing trade view, hiding login view');

      this.loginView.classList.add('hidden');
      this.tradeView.classList.remove('hidden');

      if (this.user && this.userName) {
        const displayName = this.user.name || this.user.email;
        this.userName.textContent = displayName;
      }

      if (this.userBar) {
        this.userBar.classList.remove('hidden');
      }

      window.dispatchEvent(new CustomEvent('authStateChanged', {
        detail: { authenticated: true, user: this.user }
      }));
    } else {
      console.log('Showing login view, hiding trade view');

      this.loginView.classList.remove('hidden');
      this.tradeView.classList.add('hidden');

      if (this.userBar) {
        this.userBar.classList.add('hidden');
      }

      window.dispatchEvent(new CustomEvent('authStateChanged', {
        detail: { authenticated: false }
      }));
    }
  }

  /**
   * Show error message in login view
   */
  showError(message) {
    const errorEl = document.getElementById('login-error');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.remove('hidden');
    }
  }

  /**
   * Clear error message
   */
  clearError() {
    const errorEl = document.getElementById('login-error');
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.classList.add('hidden');
    }
  }

  /**
   * Get auth state for API calls
   */
  getAuthState() {
    return {
      isAuthenticated: this.isAuthenticated,
      user: this.user
    };
  }
}

// Create global instance
const widgetAuth = new WidgetAuthManager();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => widgetAuth.init());
} else {
  widgetAuth.init();
}

// Expose to window for debugging and use by widget.js
window.widgetAuth = widgetAuth;
