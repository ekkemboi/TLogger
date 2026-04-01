const { app, BrowserWindow, ipcMain, screen, shell } = require("electron");
const path = require("path");

// Hot reload in development
if (process.argv.includes("--dev")) {
  require("electron-reload")(__dirname, {
    electron: path.join(__dirname, "node_modules", ".bin", "electron"),
    hardResetMethod: "loadFile",
  });
}

let mainWindow;

function createWindow() {
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
      nodeIntegration: true,
      contextIsolation: false,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));

  // Keep on top even when other apps are focused
  mainWindow.setAlwaysOnTop(true, "floating");
  mainWindow.setVisibleOnAllWorkspaces(true);
}

app.whenReady().then(createWindow);

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
