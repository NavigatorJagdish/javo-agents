import { app, BrowserWindow, ipcMain, Menu, nativeImage, Notification, shell, Tray } from "electron";
import fs from "node:fs";
import path from "node:path";
import { LocalRuntimeManager } from "./backendManager";
import { detectHardwareProfile } from "./hardware";

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let isQuitting = false;
let isPaused = true;
let controlStateKnown = false;
let shutdownComplete = false;
let trayRefresh: ReturnType<typeof setInterval> | null = null;

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

const runtimeManager = new LocalRuntimeManager(
  resolveRuntimeDir(), path.join(app.getPath("userData"), "runtime")
);

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

  // Keep the owner credential in the main process. Only this window can receive
  // authorization, and only for its exact loopback backend origin.
  win.webContents.session.webRequest.onBeforeSendHeaders(
    { urls: [`${backendUrl}/*`] }, (details, callback) => {
      if (details.webContentsId === win.webContents.id && new URL(details.url).origin === backendUrl) {
        details.requestHeaders.Authorization = runtimeManager.authorizationHeader();
      }
      callback({ requestHeaders: details.requestHeaders });
    }
  );

  const devUrl = process.env.JAVO_DASHBOARD_URL;
  const root = resolveRepoRoot();
  const builtDashboard = app.isPackaged
    ? path.join(root, "dashboard", "index.html")
    : path.join(root, "apps", "dashboard", "dist", "index.html");

  if (devUrl && /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?\/?$/.test(devUrl)) {
    win.loadURL(`${devUrl}?apiBase=${encodeURIComponent(backendUrl)}`);
  } else if (fs.existsSync(builtDashboard)) {
    win.loadFile(builtDashboard, { query: { apiBase: backendUrl } });
  } else {
    win.loadFile(path.join(__dirname, "..", "public", "fallback.html"), {
      query: { apiBase: backendUrl },
    });
  }

  win.webContents.on("will-navigate", (event, url) => {
    const current = win.webContents.getURL();
    if (url.split("#")[0] !== current.split("#")[0]) event.preventDefault();
  });

  return win;
}

async function updateTrayMenu(): Promise<void> {
  if (!tray) return;
  const control = await runtimeManager.getControlState();
  controlStateKnown = control !== null;
  if (control) isPaused = control.paused || control.emergency_stopped;
  if (!tray || isQuitting) return;
  const status = runtimeManager.getStatus();
  const menu = Menu.buildFromTemplate([
    {
      label: `Javo Agents (${status.running ? `Port ${status.port}` : "Runtime unavailable"})`,
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
      label: !controlStateKnown ? "Autopilot status unavailable" : isPaused ? "Resume Autopilot" : "Pause Autopilot",
      enabled: controlStateKnown,
      click: async () => {
        if (isPaused) {
          if (!await runtimeManager.callControlEndpoint("/security/resume")) {
            showDesktopNotification("Resume failed", "Runtime did not confirm the action.");
            return;
          }
          isPaused = false;
          showDesktopNotification("Javo Agents", "Supervised Autopilot resumed.");
        } else {
          if (!await runtimeManager.callControlEndpoint("/security/pause")) {
            showDesktopNotification("Pause failed", "Runtime did not confirm the action.");
            return;
          }
          isPaused = true;
          showDesktopNotification("Javo Agents", "Autopilot paused. Pending jobs held.");
        }
        await updateTrayMenu();
      },
    },
    {
      label: "Emergency Stop (Kill Switch)",
      click: async () => {
        const ok = await runtimeManager.callControlEndpoint("/security/emergency-stop", {
          reason: "Triggered from Windows System Tray",
        });
        if (!ok) { showDesktopNotification("Emergency stop unconfirmed", "Runtime could not be reached. Check running jobs."); return; }
        isPaused = true;
        showDesktopNotification("EMERGENCY STOP REQUESTED", "Local cancellation requested. Verify any in-flight remote actions.");
        await updateTrayMenu();
      },
    },
    { type: "separator" },
    {
      label: "Quit Javo Agents",
      click: async () => {
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
  tray.on("right-click", () => { void updateTrayMenu(); });
  void updateTrayMenu();
  trayRefresh = setInterval(() => { void updateTrayMenu(); }, 3000);
}

function registerIpcHandlers(): void {
  ipcMain.handle("javo:runtime-status", async () => {
    const control = await runtimeManager.getControlState();
    return { ...runtimeManager.getStatus(), paused: control ? control.paused : null,
      emergencyStopped: control ? control.emergency_stopped : null };
  });

  ipcMain.handle("javo:hardware-profile", () => detectHardwareProfile());

  ipcMain.handle("javo:pause-agents", async () => {
    const ok = await runtimeManager.callControlEndpoint("/security/pause");
    if (ok) isPaused = true;
    await updateTrayMenu();
    return ok;
  });

  ipcMain.handle("javo:resume-agents", async () => {
    const ok = await runtimeManager.callControlEndpoint("/security/resume");
    if (ok) isPaused = false;
    await updateTrayMenu();
    return ok;
  });

  ipcMain.handle("javo:emergency-stop", async () => {
    const ok = await runtimeManager.callControlEndpoint("/security/emergency-stop", {
      reason: "Triggered from Desktop UI",
    });
    if (ok) isPaused = true;
    await updateTrayMenu();
    showDesktopNotification(ok ? "EMERGENCY STOP REQUESTED" : "STOP UNCONFIRMED", ok ? "Local cancellation requested; check in-flight remote actions." : "Runtime did not confirm cancellation.");
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
    void updateTrayMenu();
  });

  app.on("before-quit", (event) => {
    if (shutdownComplete) return;
    event.preventDefault();
    if (isQuitting) return;
    isQuitting = true;
    if (trayRefresh) clearInterval(trayRefresh);
    void runtimeManager.stop().catch(() => {
      showDesktopNotification("Shutdown unconfirmed", "Check that the local runtime has stopped before restarting.");
    }).finally(() => {
      shutdownComplete = true;
      app.quit();
    });
  });

  app.on("window-all-closed", () => {
    // Keep alive in system tray on Windows
  });
}
