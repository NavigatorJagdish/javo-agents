import { contextBridge, ipcRenderer } from "electron";

export interface JavoDesktopBridge {
  getRuntimeStatus: () => Promise<{
    running: boolean;
    port: number;
    baseUrl: string;
    pid: number | null;
    lastError: string | null;
    paused: boolean | null;
    emergencyStopped: boolean | null;
  }>;
  getHardwareProfile: () => Promise<Record<string, unknown>>;
  pauseAgents: () => Promise<boolean>;
  resumeAgents: () => Promise<boolean>;
  emergencyStop: () => Promise<boolean>;
  openDashboard: () => Promise<void>;
  notify: (title: string, body: string) => Promise<void>;
}

const bridge: JavoDesktopBridge = {
  getRuntimeStatus: () => ipcRenderer.invoke("javo:runtime-status"),
  getHardwareProfile: () => ipcRenderer.invoke("javo:hardware-profile"),
  pauseAgents: () => ipcRenderer.invoke("javo:pause-agents"),
  resumeAgents: () => ipcRenderer.invoke("javo:resume-agents"),
  emergencyStop: () => ipcRenderer.invoke("javo:emergency-stop"),
  openDashboard: () => ipcRenderer.invoke("javo:open-dashboard"),
  notify: (title: string, body: string) => ipcRenderer.invoke("javo:notify", { title, body }),
};

contextBridge.exposeInMainWorld("javoDesktop", bridge);
