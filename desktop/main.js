const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;

    mainWindow = new BrowserWindow({
        width: 350,
        height: 500,
        x: width - 370,
        y: 50,
        frame: false,
        alwaysOnTop: true,
        resizable: false,
        transparent: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

    // Keep on top even when other apps are focused
    mainWindow.setAlwaysOnTop(true, 'floating');
    mainWindow.setVisibleOnAllWorkspaces(true);

    // Prevent window from being minimized
    mainWindow.on('minimize', (event) => {
        event.preventDefault();
        mainWindow.show();
    });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// IPC handlers
ipcMain.handle('capture-screenshot', async () => {
    // Capture the screen region behind the widget
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;
    const bounds = mainWindow.getBounds();

    // Capture area to the left of the widget (where TradingView would be)
    const captureBounds = {
        x: 0,
        y: 0,
        width: bounds.x - 20,
        height: height
    };

    try {
        const screenshot = await mainWindow.webContents.capturePage(captureBounds);
        return screenshot.toDataURL();
    } catch (error) {
        console.error('Screenshot capture failed:', error);
        return null;
    }
});

ipcMain.handle('get-window-bounds', () => {
    return mainWindow.getBounds();
});
