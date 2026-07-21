import { contextBridge, ipcRenderer } from 'electron'
import type { CheckResult } from '../main/checker'

const api = {
  /** Check a single Steam Workshop item by numeric ID. */
  check: (workshopId: string): Promise<CheckResult> =>
    ipcRenderer.invoke('steam:check', workshopId),
  /** Open a URL in the user's default browser. */
  openExternal: (url: string): Promise<void> =>
    ipcRenderer.invoke('shell:openExternal', url),
}

contextBridge.exposeInMainWorld('api', api)

export type Api = typeof api
