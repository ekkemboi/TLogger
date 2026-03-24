const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    captureScreenshot: () => ipcRenderer.invoke('capture-screenshot'),
    getWindowBounds: () => ipcRenderer.invoke('get-window-bounds')
});
