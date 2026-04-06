const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Existing APIs
    captureScreenshot: () => ipcRenderer.invoke('capture-screenshot'),
    getWindowBounds: () => ipcRenderer.invoke('get-window-bounds'),
    resizeWindow: (height) => ipcRenderer.invoke('resize-window', { height }),
    closeWindow: () => ipcRenderer.invoke('close-window'),
    minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
    setAlwaysOnTop: (enabled) => ipcRenderer.invoke('set-always-on-top', enabled),
    openExternal: (url) => ipcRenderer.invoke('open-external', url),

    // Auth APIs - OAuth 2.0 with PKCE
    openBrowserLogin: () => ipcRenderer.invoke('open-browser-login'),
    startOAuthFlow: () => ipcRenderer.invoke('start-oauth-flow'),
    onAuthCallback: (callback) => ipcRenderer.on('auth-callback', (event, ...args) => callback(event, ...args)),
    removeAuthCallback: (callback) => ipcRenderer.removeListener('auth-callback', callback),

    // Token storage APIs (for secure encrypted token management)
    getStoredTokens: () => ipcRenderer.invoke('get-stored-tokens'),
    storeTokens: (accessToken, refreshToken, rememberMe) => ipcRenderer.invoke('store-tokens', { accessToken, refreshToken, rememberMe }),
    clearStoredTokens: () => ipcRenderer.invoke('clear-stored-tokens'),
});
