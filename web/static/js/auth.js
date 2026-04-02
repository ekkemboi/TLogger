/**
 * AuthManager - Handles authentication state, token refresh, and user session
 */
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.refreshTimer = null;
        this.tokenRefreshInterval = null;
        this.refreshThreshold = 2 * 60 * 1000; // Refresh 2 minutes before expiry
    }

    /**
     * Initialize auth manager - call on page load
     */
    async init() {
        await this.checkAuthStatus();
        this.setupTokenRefresh();
        this.updateUI();
    }

    /**
     * Check current authentication status
     */
    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/status', {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.authenticated) {
                    this.currentUser = data.user;
                    return true;
                }
            }

            this.currentUser = null;
            return false;
        } catch (error) {
            console.error('Auth check failed:', error);
            this.currentUser = null;
            return false;
        }
    }

    /**
     * Get current user info
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.currentUser !== null;
    }

    /**
     * Refresh the access token using refresh token
     */
    async refreshToken() {
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                credentials: 'include'
            });

            if (response.ok) {
                console.log('Token refreshed successfully');
                return true;
            } else {
                // Refresh failed, user needs to login again
                console.warn('Token refresh failed');
                this.redirectToLogin();
                return false;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }

    /**
     * Setup automatic token refresh
     */
    setupTokenRefresh() {
        // Clear any existing timer
        if (this.tokenRefreshInterval) {
            clearInterval(this.tokenRefreshInterval);
        }

        // Refresh token every 13 minutes (access tokens expire in 15 minutes)
        this.tokenRefreshInterval = setInterval(() => {
            if (this.isAuthenticated()) {
                this.refreshToken();
            }
        }, 13 * 60 * 1000);
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.currentUser = null;
            if (this.tokenRefreshInterval) {
                clearInterval(this.tokenRefreshInterval);
            }
            this.redirectToLogin();
        }
    }

    /**
     * Redirect to login page
     */
    redirectToLogin() {
        const currentPath = window.location.pathname;
        if (currentPath !== '/login') {
            window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
        }
    }

    /**
     * Update UI based on auth state
     */
    updateUI() {
        const userNavSection = document.getElementById('user-nav-section');
        if (!userNavSection) return;

        if (this.currentUser) {
            userNavSection.innerHTML = `
                <div class="flex items-center gap-3">
                    ${this.currentUser.profile_picture ? `
                        <img src="${this.currentUser.profile_picture}" alt="Profile" 
                             class="w-8 h-8 rounded-full border border-border-default">
                    ` : `
                        <div class="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-white font-bold text-sm">
                            ${this.getInitials(this.currentUser.name)}
                        </div>
                    `}
                    <span class="text-sm font-medium text-text-primary hidden md:block">${this.currentUser.name}</span>
                    <button onclick="authManager.logout()" 
                            class="flex items-center justify-center w-8 h-8 text-text-secondary hover:text-error transition-colors"
                            title="Logout">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                            <polyline points="16 17 21 12 16 7"></polyline>
                            <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg>
                    </button>
                </div>
            `;
        } else {
            userNavSection.innerHTML = `
                <a href="/login" class="text-sm font-medium text-accent-primary hover:text-accent-primary-hover">
                    Sign In
                </a>
            `;
        }
    }

    /**
     * Get user initials from name
     */
    getInitials(name) {
        if (!name) return '?';
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }

    /**
     * Make authenticated API request
     * Automatically handles token refresh on 401
     */
    async apiRequest(url, options = {}) {
        // Ensure credentials are included
        options.credentials = 'include';

        let response = await fetch(url, options);

        // If 401, try to refresh token and retry
        if (response.status === 401) {
            const refreshed = await this.refreshToken();
            if (refreshed) {
                response = await fetch(url, options);
            } else {
                this.redirectToLogin();
                throw new Error('Authentication required');
            }
        }

        return response;
    }
}

// Create global instance
const authManager = new AuthManager();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => authManager.init());
} else {
    authManager.init();
}

// Expose to window for debugging
window.authManager = authManager;
