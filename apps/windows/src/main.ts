import { app, BrowserWindow, ipcMain, Menu, nativeImage, Notification, shell, Tray } from "electron";
import fs from "node:fs";
import path from "node:path";
import { LocalRuntimeManager } from "./backendManager";
import { detectHardwareProfile } from "./hardware";

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let isQuitting = false;
let isPaused = false;

function resolveRepoRoot(): string {
  if (app.isPackaged) {
    return process.resourcesPath;
  }
  return path.resolve(__dirname, "..", "..", "..");
}

function resolveRuntimeDir(): string {
  const root = resolveRepoRoot();
  const packagedPath = path.join(root, "local-runtime");
  if (fs.existsSync(packagedPath)) {
    return packagedPath;
  }
  return path.join(root, "services", "local-runtime");
}

function resolveIconPath(): string {
  const root = resolveRepoRoot();
  const candidates = [
    path.join(root, "icons", "dist", "javo-app.ico"),
    path.join(root, "packages", "brand-assets", "icons", "dist", "javo-app.ico"),
    path.join(root, "icons", "dist", "tray-icon.png"),
    path.join(root, "packages", "brand-assets", "icons", "dist", "tray-icon.png"),
  ];
  return candidates.find((p) => fs.existsSync(p)) ?? "";
}

const runtimeManager = new LocalRuntimeManager(resolveRuntimeDir());

function showDesktopNotification(title: string, body: string): void {
  if (Notification.isSupported()) {
    new Notification({ title, body }).show();
  }
}

function createMainWindow(backendUrl: string): BrowserWindow {
  const iconPath = resolveIconPath();
  const win = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 1024,
    minHeight: 680,
    backgroundColor: "#0B1026",
    title: "Javo Agents — Supervised AI Team",
    icon: iconPath || undefined,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://") || url.startsWith("http://localhost")) {
      shell.openExternal(url);
    }
    return { action: "deny" };
  });

  win.on("close", (event) => {
    if (!isQuitting) {
      event.preventDefault();
      win.hide();
      showDesktopNotification("Javo Agents", "Minimized to system tray. Agents continue running safely.");
    }
  });

  const devUrl = process.env.JAVO_DASHBOARD_URL;
  const root = resolveRepoRoot();
  const builtDashboard = app.isPackaged
    ? path.join(root, "dashboard", "index.html")
    : path.join(root, "apps", "dashboard", "dist", "index.html");

  if (devUrl) {
    win.loadURL(`${devUrl}?apiBase=${encodeURIComponent(backendUrl)}`);
  } else if (fs.existsSync(builtDashboard)) {
    win.loadFile(builtDashboard, { query: { apiBase: backendUrl } });
  } else {
    win.loadFile(path.join(__dirname, "..", "public", "fallback.html"), {
      query: { apiBase: backendUrl },
    });
  }

  return win;
}

function updateTrayMenu(): void {
  if (!tray) return;
  const status = runtimeManager.getStatus();
  const menu = Menu.buildFromTemplate([
    {
      label: `Javo Agents (${status.running ? `Port ${status.port}` : "Starting..."})`,
      enabled: false,
    },
    { type: "separator" },
    {
      label: "Open Dashboard",
      click: () => {
        if (!mainWindow) {
          mainWindow = createMainWindow(status.baseUrl);
        } else {
          mainWindow.show();
          mainWindow.focus();
        }
      },
    },
    {
      label: isPaused ? "Resume Autopilot" : "Pause Autopilot",
      click: async () => {
        if (isPaused) {
          await runtimeManager.callControlEndpoint("/security/resume");
          isPaused = false;
          showDesktopNotification("Javo Agents", "Supervised Autopilot resumed.");
        } else {
          await runtimeManager.callControlEndpoint("/security/pause");
          isPaused = true;
          showDesktopNotification("Javo Agents", "Autopilot paused. Pending jobs held.");
        }
        updateTrayMenu();
      },
    },
    {
      label: "Emergency Stop (Kill Switch)",
      click: async () => {
        await runtimeManager.callControlEndpoint("/security/emergency-stop", {
          reason: "Triggered from Windows System Tray",
        });
        isPaused = true;
        showDesktopNotification("EMERGENCY STOP ACTIVATED", "All agent actions and publishes halted.");
        updateTrayMenu();
      },
    },
    { type: "separator" },
    {
      label: "Quit Javo Agents",
      click: async () => {
        isQuitting = true;
        await runtimeManager.stop();
        app.quit();
      },
    },
  ]);
  tray.setContextMenu(menu);
}

function createTray(): void {
  const iconPath = resolveIconPath();
  const icon = iconPath ? nativeImage.createFromPath(iconPath) : nativeImage.createEmpty();
  tray = new Tray(icon);
  tray.setToolTip("Javo Agents — Local AI Runtime");
  tray.on("double-click", () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
  updateTrayMenu();
}

function registerIpcHandlers(): void {
  ipcMain.handle("javo:runtime-status", () => ({
    ...runtimeManager.getStatus(),
    paused: isPaused,
  }));

  ipcMain.handle("javo:hardware-profile", () => detectHardwareProfile());

  ipcMain.handle("javo:pause-agents", async () => {
    const ok = await runtimeManager.callControlEndpoint("/security/pause");
    if (ok) isPaused = true;
    updateTrayMenu();
    return ok;
  });

  ipcMain.handle("javo:resume-agents", async () => {
    const ok = await runtimeManager.callControlEndpoint("/security/resume");
    if (ok) isPaused = false;
    updateTrayMenu();
    return ok;
  });

  ipcMain.handle("javo:emergency-stop", async () => {
    const ok = await runtimeManager.callControlEndpoint("/security/emergency-stop", {
      reason: "Triggered from Desktop UI",
    });
    isPaused = true;
    updateTrayMenu();
    showDesktopNotification("EMERGENCY STOP", "All Javo Agents stopped immediately.");
    return ok;
  });

  ipcMain.handle("javo:open-dashboard", () => {
    mainWindow?.show();
    mainWindow?.focus();
  });

  ipcMain.handle("javo:notify", (_event, payload: { title: string; body: string }) => {
    showDesktopNotification(payload.title, payload.body);
  });
}

// Single-instance lock
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    registerIpcHandlers();
    const preferredPort = Number(process.env.JAVO_PORT || 8000);
    const status = await runtimeManager.start(preferredPort).catch(() => runtimeManager.getStatus());
    mainWindow = createMainWindow(status.baseUrl);
    createTray();
    updateTrayMenu();
  });

  app.on("before-quit", async () => {
    isQuitting = true;
    await runtimeManager.stop();
  });

  app.on("window-all-closed", () => {
    // Keep alive in system tray on Windows
  });
}
