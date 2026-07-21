import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { checkWorkshopItem } from './checker'

function createWindow(): void {
  const win = new BrowserWindow({
    width: 760,
    height: 900,
    minWidth: 560,
    minHeight: 640,
    show: false,
    backgroundColor: '#0a0a0c',
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 14, y: 18 },
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
    },
  })

  win.on('ready-to-show', () => win.show())

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  if (process.env['ELECTRON_RENDERER_URL']) {
    win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// One Workshop item per call — the renderer drives the loop + throttling so it
// can stream results and render live progress (mirrors the Python
// check_many_iter generator).
ipcMain.handle('steam:check', async (_e, workshopId: string) => {
  return checkWorkshopItem(String(workshopId))
})

ipcMain.handle('shell:openExternal', async (_e, url: string) => {
  if (typeof url === 'string' && /^https?:\/\//i.test(url)) await shell.openExternal(url)
})

app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
