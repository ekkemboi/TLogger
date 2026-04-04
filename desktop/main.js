const { app, BrowserWindow, ipcMain, screen, shell, safeStorage } = require("electron");
const path = require("path");
const fs = require("fs");
const { promisify } = require("util");
const writeFile = promisify(fs.writeFile);
const readFile = promisify(fs.readFile);
const unlink = promisify(fs.unlink);
const mkdir = promisify(fs.mkdir);

// Token storage path
const TOKEN_FILE = path.join(app.getPath('userData'), 'auth_tokens.enc');

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
 * @param {string} url - The protocol URL (e.g., tradelogger://auth?status=success)
 */
async function handleDeepLink(url) {
  console.log('=== Handling deep link ===');
  console.log('URL:', url);

  try {
    const urlObj = new URL(url);
    console.log('Parsed URL:', urlObj.pathname, urlObj.searchParams.toString());

    if (urlObj.pathname === '/auth') {
      const status = urlObj.searchParams.get('status');
      console.log('Auth callback status:', status);

      // Extract tokens from URL if status is success
      let tokenData = null;
      if (status === 'success') {
        const accessToken = urlObj.searchParams.get('access_token');
        const refreshToken = urlObj.searchParams.get('refresh_token');
        const rememberMe = urlObj.searchParams.get('remember_me') === 'true';

        if (accessToken && refreshToken) {
          console.log('Received tokens from auth callback');
          tokenData = {
            accessToken,
            refreshToken,
            rememberMe,
          };

          // Store tokens securely
          await storeTokens(accessToken, refreshToken, rememberMe);
        }
      }

      // If window isn't ready yet, store the URL and tokens for later
      if (!mainWindow || !mainWindow.webContents) {
        console.log('Window not ready, storing pending auth URL');
        pendingAuthUrl = url;
        pendingTokens = tokenData;
        return;
      }

      // Notify renderer process with full data
      console.log('Sending auth-callback to renderer');
      const messageData = { status };
      if (tokenData) {
        messageData.tokens = tokenData;
      }
      mainWindow.webContents.send('auth-callback', messageData);
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
    
    // Handle any pending auth URL from second-instance
    if (pendingAuthUrl) {
      console.log('Processing pending auth URL:', pendingAuthUrl);
      const urlObj = new URL(pendingAuthUrl);
      const status = urlObj.searchParams.get('status');
      
      const messageData = { status };
      if (pendingTokens && status === 'success') {
        messageData.tokens = pendingTokens;
      }
      
      mainWindow.webContents.send('auth-callback', messageData);
      pendingAuthUrl = null;
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

// Auth IPC handlers
ipcMain.handle("open-browser-login", async () => {
  console.log('Opening browser for login...');
  const loginUrl = 'http://localhost:5000/login?source=desktop';
  await shell.openExternal(loginUrl);
  return { success: true };
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
