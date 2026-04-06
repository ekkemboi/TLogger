const { app, BrowserWindow, ipcMain, screen, shell, safeStorage } = require("electron");
const path = require("path");
const fs = require("fs");
const { promisify } = require("util");
const express = require("express");
const http = require("http");
const crypto = require("crypto");
const writeFile = promisify(fs.writeFile);
const readFile = promisify(fs.readFile);
const unlink = promisify(fs.unlink);
const mkdir = promisify(fs.mkdir);

// Token storage path
const TOKEN_FILE = path.join(app.getPath('userData'), 'auth_tokens.enc');

// OAuth flow state
let oauthCallbackServer = null;
let oauthCallbackPort = null;
let pendingOAuthCallback = null;
let oauthRedirectUri = null; // Track which redirect_uri was used

// Register tradelogger:// protocol
if (process.platform === 'linux') {
  // On Linux, setAsDefaultProtocolClient needs the app to be installed
  // For development, we use xdg-mime or check if already registered
  const protocolRegistered = app.setAsDefaultProtocolClient('tradelogger');
  console.log('Protocol registered (Linux):', protocolRegistered);
  
  // Linux passes protocol URL in argv when app is launched
  const protocolUrl = process.argv.find(arg => arg.startsWith('tradelogger://'));
  if (protocolUrl) {
    console.log('Linux: Found protocol URL in argv:', protocolUrl);
    process.env.PENDING_AUTH_URL = protocolUrl;
  }
} else {
  const protocolRegistered = app.setAsDefaultProtocolClient('tradelogger');
  console.log('Protocol registered:', protocolRegistered);
}

console.log('=== TradeLogger Widget Starting ===');
console.log('Process argv:', process.argv);
console.log('Platform:', process.platform);

// Hot reload in development
if (process.argv.includes("--dev")) {
  require("electron-reload")(__dirname, {
    electron: path.join(__dirname, "node_modules", ".bin", "electron"),
    hardResetMethod: "loadFile",
  });
}

let mainWindow;
let pendingAuthUrl = null;
let pendingTokens = null; // Store tokens temporarily until renderer is ready

/**
 * Store encrypted tokens to disk
 * @param {string} accessToken - JWT access token
 * @param {string} refreshToken - JWT refresh token
 * @param {boolean} rememberMe - Whether to persist tokens
 */
async function storeTokens(accessToken, refreshToken, rememberMe) {
  try {
    // Ensure userData directory exists
    const userDataPath = app.getPath('userData');
    await mkdir(userDataPath, { recursive: true });

    const tokenData = {
      accessToken,
      refreshToken,
      rememberMe,
      storedAt: new Date().toISOString(),
    };

    const jsonString = JSON.stringify(tokenData);

    // Encrypt the token data
    if (safeStorage.isEncryptionAvailable()) {
      const encrypted = safeStorage.encryptString(jsonString);
      await writeFile(TOKEN_FILE, encrypted);
      console.log('Tokens stored securely');
      return true;
    } else {
      console.warn('safeStorage not available, tokens not stored');
      return false;
    }
  } catch (error) {
    console.error('Failed to store tokens:', error);
    return false;
  }
}

/**
 * Retrieve and decrypt tokens from disk
 * @returns {Object|null} Token data or null if not found
 */
async function getTokens() {
  try {
    if (!fs.existsSync(TOKEN_FILE)) {
      return null;
    }

    const encrypted = await readFile(TOKEN_FILE);

    if (safeStorage.isEncryptionAvailable()) {
      const decrypted = safeStorage.decryptString(encrypted);
      return JSON.parse(decrypted);
    } else {
      console.warn('safeStorage not available, cannot decrypt tokens');
      return null;
    }
  } catch (error) {
    console.error('Failed to retrieve tokens:', error);
    return null;
  }
}

/**
 * Clear stored tokens from disk
 */
async function clearTokens() {
  try {
    if (fs.existsSync(TOKEN_FILE)) {
      await unlink(TOKEN_FILE);
      console.log('Tokens cleared');
    }
    return true;
  } catch (error) {
    console.error('Failed to clear tokens:', error);
    return false;
  }
}

// Single instance lock for deep link handling
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  console.log('Another instance is running, quitting...');
  app.quit();
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    console.log('Second instance detected');
    console.log('Command line:', commandLine);
    
    // Focus existing window
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();

      // Handle protocol URL from second instance
      // The URL might be the last argument on some platforms
      const protocolUrl = commandLine.find(arg => {
        const cleanArg = arg.replace(/^["']|["']$/g, ''); // Remove quotes
        return cleanArg.startsWith('tradelogger://');
      });
      
      if (protocolUrl) {
        console.log('Found protocol URL in second-instance:', protocolUrl);
        handleDeepLink(protocolUrl.replace(/^["']|["']$/g, ''));
      }
    }
  });
}

// macOS deep link handler
app.on('open-url', (event, url) => {
  console.log('macOS open-url event:', url);
  event.preventDefault();
  handleDeepLink(url);
});

/**
 * Handle deep link from protocol URL
 * @param {string} url - The protocol URL (e.g., tradelogger://auth?code=abc123&state=xyz789)
 */
async function handleDeepLink(url) {
  console.log('=== Handling deep link ===');
  console.log('URL:', url);

  try {
    const urlObj = new URL(url);
    console.log('Parsed URL:', urlObj.pathname, urlObj.searchParams.toString());

    if (urlObj.pathname === '/auth') {
      const code = urlObj.searchParams.get('code');
      const state = urlObj.searchParams.get('state');
      const error = urlObj.searchParams.get('error');
      
      console.log('OAuth callback received:', { hasCode: !!code, hasState: !!state, hasError: !!error });

      if (error) {
        console.error('OAuth error from protocol:', error);
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { status: 'error', error });
        }
        return;
      }

      if (!code) {
        console.error('No authorization code in callback');
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { status: 'error', error: 'No authorization code' });
        }
        return;
      }

      // Close localhost callback server if it's still running (protocol won the race)
      if (oauthCallbackServer) {
        console.log('Protocol callback received, closing localhost server');
        oauthCallbackServer.close();
        oauthCallbackServer = null;
      }

      // Verify state parameter (CSRF protection)
      if (state && state !== global.oauthState) {
        console.error('State mismatch - possible CSRF attack');
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { 
            status: 'error', 
            error: 'Security validation failed' 
          });
        }
        return;
      }

      try {
        // Exchange code for tokens
        const tokenData = await exchangeCodeForTokens(code, global.oauthCodeVerifier);
        
        // Store tokens
        await storeTokens(tokenData.access_token, tokenData.refresh_token, true);
        
        // Create token data for renderer
        const rendererTokenData = {
          accessToken: tokenData.access_token,
          refreshToken: tokenData.refresh_token,
          rememberMe: true
        };

        // If window isn't ready yet, store the tokens for later
        if (!mainWindow || !mainWindow.webContents) {
          console.log('Window not ready, storing pending tokens');
          pendingTokens = rendererTokenData;
          return;
        }

        // Notify renderer process
        console.log('Sending auth-callback to renderer');
        mainWindow.webContents.send('auth-callback', { 
          status: 'success',
          tokens: rendererTokenData
        });
        
        // Clear temporary PKCE parameters
        global.oauthCodeVerifier = null;
        global.oauthState = null;
        
      } catch (error) {
        console.error('Token exchange failed:', error);
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { 
            status: 'error', 
            error: error.message 
          });
        }
      }
    }
  } catch (error) {
    console.error('Failed to handle deep link:', error);
  }
}

function createWindow() {
  console.log('Creating window...');
  
  // Get the display where the cursor is currently
  const cursorPoint = screen.getCursorScreenPoint();
  const currentDisplay = screen.getPrimaryDisplay(cursorPoint);

  mainWindow = new BrowserWindow({
    width: 350,
    height: currentDisplay.workAreaSize.height,
    x: currentDisplay.workAreaSize.width - 370,
    y: currentDisplay.workAreaSize.y + 50,
    frame: false,
    alwaysOnTop: true,
    resizable: true,
    transparent: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));

  // Keep on top even when other apps are focused
  mainWindow.setAlwaysOnTop(true, "floating");
  mainWindow.setVisibleOnAllWorkspaces(true);

  // Handle pending auth URL if window was created after protocol call
  mainWindow.webContents.on('dom-ready', () => {
    console.log('Window DOM ready');
    
    // Check for protocol URL on Windows/Linux (passed via command line when app not running)
    if (process.platform === 'win32' || process.platform === 'linux') {
      // Check argv first
      const protocolUrl = process.argv.find(arg => arg.startsWith('tradelogger://'));
      if (protocolUrl) {
        console.log('Found protocol URL in argv:', protocolUrl);
        handleDeepLink(protocolUrl);
      }
      
      // Check environment variable (Linux fallback)
      if (process.env.PENDING_AUTH_URL) {
        console.log('Found protocol URL in env:', process.env.PENDING_AUTH_URL);
        handleDeepLink(process.env.PENDING_AUTH_URL);
        delete process.env.PENDING_AUTH_URL;
      }
    }
    
    // Handle any pending tokens from protocol callback
    if (pendingTokens) {
      console.log('Processing pending tokens');
      mainWindow.webContents.send('auth-callback', { 
        status: 'success',
        tokens: pendingTokens
      });
      pendingTokens = null;
    }
  });
  
  // Open DevTools in development
  if (process.argv.includes("--dev")) {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(() => {
  console.log('App ready, creating window...');
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers
ipcMain.handle("capture-screenshot", async () => {
  // Capture the screen region behind the widget
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  const bounds = mainWindow.getBounds();

  // Capture area to the left of the widget (where TradingView would be)
  const captureBounds = {
    x: 0,
    y: 0,
    width: bounds.x - 20,
    height: height,
  };

  try {
    const screenshot = await mainWindow.webContents.capturePage(captureBounds);
    return screenshot.toDataURL();
  } catch (error) {
    console.error("Screenshot capture failed:", error);
    return null;
  }
});

ipcMain.handle("get-window-bounds", () => {
  return mainWindow.getBounds();
});

ipcMain.handle("resize-window", (event, { height }) => {
  mainWindow.setSize(350, height);
  return { success: true };
});

ipcMain.handle("open-external", (event, url) => {
  shell.openExternal(url);
  return { success: true };
});

ipcMain.handle("set-always-on-top", (event, enabled) => {
  mainWindow.setAlwaysOnTop(enabled, "floating");
  return enabled;
});

ipcMain.handle("close-window", () => {
  mainWindow.close();
});

ipcMain.handle("minimize-window", () => {
  mainWindow.minimize();
  return { success: true };
});

// OAuth 2.0 with PKCE helpers
function generatePKCE() {
  // Generate PKCE code verifier and challenge.
  const codeVerifier = crypto.randomBytes(32).toString('base64url');
  const codeChallenge = crypto.createHash('sha256')
    .update(codeVerifier)
    .digest('base64url');
  return { codeVerifier, codeChallenge };
}

function generateState() {
  // Generate random state parameter for CSRF protection.
  return crypto.randomBytes(32).toString('base64url');
}

async function findAvailablePort(startPort = 45678) {
  // Find an available port for the callback server.
  return new Promise((resolve, reject) => {
    const server = http.createServer();
    server.listen(startPort, () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', () => {
      // Port in use, try next one
      resolve(findAvailablePort(startPort + 1));
    });
  });
}

function startOAuthCallbackServer(port, onCodeReceived) {
  // Start Express server to receive OAuth callback.
  const app = express();
  
  app.get('/callback', (req, res) => {
    const { code, state, error, status, access_token, refresh_token, remember_me } = req.query;
    
    console.log('=== Localhost callback received ===');
    console.log('Query params:', req.query);
    console.log('Full URL:', req.originalUrl);
    
    const htmlTemplate = (title, message, icon, color) => `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-900 flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-gray-800 rounded-2xl p-8 text-center shadow-2xl">
        <div class="w-20 h-20 ${color} rounded-full flex items-center justify-center mx-auto mb-6">
            <span class="text-4xl">${icon}</span>
        </div>
        <h1 class="text-2xl font-bold text-white mb-2">${title}</h1>
        <p class="text-gray-400 mb-6">${message}</p>
        <div class="text-sm text-gray-500">
            <p>You can close this window</p>
        </div>
    </div>
</body>
</html>`;
    
    // Handle OAuth code flow (normal OAuth)
    if (code) {
      console.log('OAuth callback received with code');
      res.send(htmlTemplate(
        'Authentication Successful',
        'You are now signed in to TradeLogger.',
        '✓',
        'bg-green-500'
      ));
      onCodeReceived(code, state, null);
    }
    // Handle direct token passing (development mode shortcut)
    else if (status === 'success' && access_token) {
      console.log('Direct token received (development mode)');
      res.send(htmlTemplate(
        'Authentication Successful',
        'You are now signed in to TradeLogger.',
        '✓',
        'bg-green-500'
      ));
      onCodeReceived(null, null, null, { access_token, refresh_token, remember_me });
    }
    else if (error) {
      console.error('OAuth callback error:', error);
      res.send(htmlTemplate(
        'Authentication Failed',
        error || 'An error occurred during authentication.',
        '✗',
        'bg-red-500'
      ));
      onCodeReceived(null, null, error);
    } else {
      console.log('OAuth callback - no code or error');
      res.send(htmlTemplate(
        'Invalid Request',
        'Missing authorization code.',
        '⚠',
        'bg-yellow-500'
      ));
      onCodeReceived(null, null, 'Missing authorization code');
    }
    
    // Close server after handling callback
    setTimeout(() => {
      if (oauthCallbackServer) {
        oauthCallbackServer.close();
        oauthCallbackServer = null;
        console.log('OAuth callback server closed');
      }
    }, 1000);
  });
  
  oauthCallbackServer = app.listen(port, () => {
    console.log(`OAuth callback server listening on port ${port}`);
    console.log(`Callback URL: http://127.0.0.1:${port}/callback`);
  });
  
  oauthCallbackPort = port;
  return port;
}

async function exchangeCodeForTokens(code, codeVerifier) {
  // Exchange authorization code for access and refresh tokens.
  // Use the redirect_uri that was used during authorization (stored in oauthRedirectUri)
  const redirectUri = oauthRedirectUri || `http://127.0.0.1:${oauthCallbackPort}/callback`;
  
  try {
    const response = await fetch('http://localhost:5000/api/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code,
        code_verifier: codeVerifier,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Token exchange failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Token exchange error:', error);
    throw error;
  }
}

// Auth IPC handlers
ipcMain.handle("open-browser-login", async () => {
  console.log('Opening browser for OAuth login...');
  
  try {
    // Generate PKCE parameters
    const { codeVerifier, codeChallenge } = generatePKCE();
    const state = generateState();
    
    // Start localhost callback server
    const port = await findAvailablePort();
    const localhostUrl = `http://127.0.0.1:${port}/callback`;
    
    // Store PKCE parameters temporarily
    global.oauthCodeVerifier = codeVerifier;
    global.oauthState = state;
    
    // Start callback server
    startOAuthCallbackServer(port, async (code, returnedState, error, directTokens) => {
      // Handle direct token passing (development mode shortcut)
      if (directTokens) {
        console.log('Direct tokens received:', directTokens);
        await storeTokens(directTokens.access_token, directTokens.refresh_token, directTokens.remember_me);
        
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { 
            status: 'success',
            tokens: {
              accessToken: directTokens.access_token,
              refreshToken: directTokens.refresh_token,
              rememberMe: directTokens.remember_me
            }
          });
        }
        return;
      }
      
      if (error) {
        console.error('OAuth callback error:', error);
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { 
            status: 'error', 
            error: error 
          });
        }
        return;
      }
      
      // Verify state parameter (CSRF protection)
      if (returnedState !== global.oauthState) {
        console.error('State mismatch - possible CSRF attack');
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { 
            status: 'error', 
            error: 'Security validation failed' 
          });
        }
        return;
      }
      
      try {
        // Exchange code for tokens
        const tokenData = await exchangeCodeForTokens(code, global.oauthCodeVerifier);
        
        // Store tokens
        await storeTokens(tokenData.access_token, tokenData.refresh_token, true);
        
        // Notify renderer
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { 
            status: 'success',
            tokens: {
              accessToken: tokenData.access_token,
              refreshToken: tokenData.refresh_token,
              rememberMe: true
            }
          });
        }
        
        // Clear temporary PKCE parameters
        global.oauthCodeVerifier = null;
        global.oauthState = null;
        
      } catch (error) {
        console.error('Token exchange failed:', error);
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('auth-callback', { 
            status: 'error', 
            error: error.message 
          });
        }
      }
    });
    
    // Build authorization URL
    // Use localhost callback for development, protocol for packaged app
    let redirectUri;
    console.log('app.isPackaged:', app.isPackaged);
    if (app.isPackaged) {
      redirectUri = 'tradelogger://auth';
    } else {
      redirectUri = localhostUrl;
    }

    // Store redirect URI for token exchange
    oauthRedirectUri = redirectUri;

    const authUrl = `http://localhost:5000/api/oauth/authorize?` +
      `redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&fallback_uri=${encodeURIComponent(localhostUrl)}` +
      `&code_challenge=${encodeURIComponent(codeChallenge)}` +
      `&state=${encodeURIComponent(state)}` +
      `&response_type=code`;
    
    console.log('Opening browser with OAuth URL');
    console.log('Development mode (localhost callback):', !app.isPackaged);
    console.log('Redirect URI:', redirectUri);
    await shell.openExternal(authUrl);
    
    return { success: true, port };
  } catch (error) {
    console.error('Failed to start OAuth flow:', error);
    return { success: false, error: error.message };
  }
});

// Legacy handler - kept for backward compatibility
ipcMain.handle("start-oauth-flow", async () => {
  // Start OAuth 2.0 flow with PKCE and dual callback support.
  return await ipcMain.handlers.get("open-browser-login")();
});

// Token storage IPC handlers
ipcMain.handle("get-stored-tokens", async () => {
  console.log('Getting stored tokens...');
  const tokens = await getTokens();
  return tokens;
});

ipcMain.handle("store-tokens", async (event, { accessToken, refreshToken, rememberMe }) => {
  console.log('Storing tokens...');
  const success = await storeTokens(accessToken, refreshToken, rememberMe);
  return { success };
});

ipcMain.handle("clear-stored-tokens", async () => {
  console.log('Clearing stored tokens...');
  const success = await clearTokens();
  return { success };
});
