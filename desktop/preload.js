const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    captureScreenshot: () => ipcRenderer.invoke('capture-screenshot'),
    getWindowBounds: () => ipcRenderer.invoke('get-window-bounds'),
    resizeWindow: (height) => ipcRenderer.invoke('resize-window', { height }),
    closeWindow: () => ipcRenderer.invoke('close-window'),
    minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
    setAlwaysOnTop: (enabled) => ipcRenderer.invoke('set-always-on-top', enabled),
    openExternal: (url) => ipcRenderer.invoke('open-external', url)
});
