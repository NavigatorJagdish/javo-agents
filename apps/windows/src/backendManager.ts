import { ChildProcess, spawn } from "node:child_process";
import fs from "node:fs";
import { randomBytes } from "node:crypto";
import net from "node:net";
import path from "node:path";

export interface BackendStatus {
  running: boolean;
  port: number;
  baseUrl: string;
  pid: number | null;
  lastError: string | null;
}

export class LocalRuntimeManager {
  private proc: ChildProcess | null = null;
  private port = 8000;
  private lastError: string | null = null;
  private stopping = false;
  private ready = false;
  private starting: Promise<BackendStatus> | null = null;
  private stoppingProcess: Promise<void> | null = null;
  private accessToken = randomBytes(32).toString("hex");

  public authorizationHeader(): string {
    return `Bearer ${this.accessToken}`;
  }

  constructor(private readonly runtimeDir: string, private readonly dataDir: string) {}

  public getStatus(): BackendStatus {
    return {
      running: this.ready && this.proc !== null && this.proc.exitCode === null,
      port: this.port,
      baseUrl: `http://127.0.0.1:${this.port}`,
      pid: this.proc?.pid ?? null,
      lastError: this.lastError,
    };
  }

  private async findAvailablePort(preferredPort: number): Promise<number> {
    const canBind = (port: number): Promise<boolean> =>
      new Promise((resolve) => {
        const srv = net.createServer();
        srv.once("error", () => resolve(false));
        srv.once("listening", () => {
          srv.close(() => resolve(true));
        });
        srv.listen(port, "127.0.0.1");
      });

    if (await canBind(preferredPort)) {
      return preferredPort;
    }

    return new Promise((resolve, reject) => {
      const srv = net.createServer();
      srv.once("error", reject);
      srv.listen(0, "127.0.0.1", () => {
        const addr = srv.address();
        if (addr && typeof addr === "object") {
          const chosen = addr.port;
          srv.close(() => resolve(chosen));
        } else {
          srv.close(() => reject(new Error("Failed to allocate local port")));
        }
      });
    });
  }

  private resolvePythonExecutable(): string {
    if (process.env.JAVO_PYTHON_PATH) return process.env.JAVO_PYTHON_PATH;
    const venvPython = path.join(this.runtimeDir, ".venv", "Scripts", "python.exe");
    if (fs.existsSync(venvPython)) {
      return venvPython;
    }
    return "python";
  }

  public async start(preferredPort = 8000): Promise<BackendStatus> {
    if (this.stoppingProcess) await this.stoppingProcess;
    if (this.starting) return this.starting;
    this.starting = this.startProcess(preferredPort);
    try { return await this.starting; }
    finally { this.starting = null; }
  }

  private async startProcess(preferredPort: number): Promise<BackendStatus> {
    if (this.proc && this.proc.exitCode === null) {
      return this.getStatus();
    }

    this.stopping = false;
    this.lastError = null;
    this.ready = false;
    fs.mkdirSync(this.dataDir, { recursive: true });
    this.port = await this.findAvailablePort(preferredPort);

    const pythonExe = this.resolvePythonExecutable();
    const args = [
      "-m",
      "uvicorn",
      "app.main:app",
      "--host",
      "127.0.0.1",
      "--port",
      String(this.port),
    ];

    const child = spawn(pythonExe, args, {
      cwd: this.dataDir,
      env: {
        ...process.env,
        PYTHONPATH: [this.runtimeDir, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
        JAVO_DATABASE_URL: `sqlite+aiosqlite:///${path.join(this.dataDir, "runtime.db").replaceAll("\\", "/")}`,
        JAVO_SCHEDULER_DB_URL: `sqlite:///${path.join(this.dataDir, "scheduler.db").replaceAll("\\", "/")}`,
        JAVO_CONTROL_STATE_PATH: path.join(this.dataDir, "runtime-control.json"),
        JAVO_CONTENT_ROOT: path.join(this.dataDir, "content"),
        JAVO_UPLOAD_DIR: path.join(this.dataDir, "uploads"),
        JAVO_BACKUP_DIR: path.join(this.dataDir, "backups"),
        JAVO_THUMBNAIL_DIR: path.join(this.dataDir, "thumbnails"),
        JAVO_OWNER_ACCESS_TOKEN: this.accessToken,
        JAVO_HOST: "127.0.0.1",
        JAVO_PORT: String(this.port),
        PYTHONUNBUFFERED: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
    this.proc = child;
    // Drain both pipes to prevent a verbose child blocking on a full stdout buffer.
    child.stdout?.resume();
    child.once("error", (error) => {
      if (this.proc !== child) return;
      this.lastError = `Could not start local runtime (${(error as NodeJS.ErrnoException).code || "spawn error"}). Check Python and runtime dependencies.`;
      this.ready = false;
      this.proc = null;
    });

    child.stderr?.on("data", (chunk: Buffer) => {
      const msg = chunk.toString("utf-8").trim();
      if (msg) {
        this.lastError = msg.slice(-400);
      }
    });

    child.on("exit", (code) => {
      if (this.proc !== child) return;
      if (!this.stopping && code !== 0) {
        this.lastError = `Backend exited with code ${code}`;
      }
      this.proc = null;
      this.ready = false;
    });

    if (!await this.waitForHealth(20000) && this.proc === child) {
      await this.stop();
    }
    return this.getStatus();
  }

  public async waitForHealth(timeoutMs = 20000): Promise<boolean> {
    const deadline = Date.now() + timeoutMs;
    const healthUrl = `http://127.0.0.1:${this.port}/health/`;

    while (Date.now() < deadline) {
      if (!this.proc || this.proc.exitCode !== null) return false;
      try {
        const res = await fetch(healthUrl, { headers: { Authorization: this.authorizationHeader() }, signal: AbortSignal.timeout(1500) });
        if (res.ok) {
          this.lastError = null;
          this.ready = true;
          return true;
        }
      } catch {
        // Backend is still starting up
      }
      await new Promise((r) => setTimeout(r, 400));
    }

    this.lastError = `Health check timed out at ${healthUrl}`;
    return false;
  }

  public async getControlState(): Promise<{ paused: boolean; emergency_stopped: boolean } | null> {
    try {
      const res = await fetch(`http://127.0.0.1:${this.port}/security/autopilot-status`, {
        headers: { Authorization: this.authorizationHeader() }, signal: AbortSignal.timeout(2000),
      });
      if (!res.ok) return null;
      const state = await res.json() as { paused?: unknown; emergency_stopped?: unknown };
      if (typeof state.paused !== "boolean" || typeof state.emergency_stopped !== "boolean") return null;
      return { paused: state.paused, emergency_stopped: state.emergency_stopped };
    } catch { return null; }
  }

  public async callControlEndpoint(endpoint: string, body?: Record<string, unknown>): Promise<boolean> {
    try {
      const res = await fetch(`http://127.0.0.1:${this.port}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: this.authorizationHeader() },
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(4000),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async stop(): Promise<void> {
    if (this.stoppingProcess) return this.stoppingProcess;
    this.stoppingProcess = this.stopProcess();
    try { await this.stoppingProcess; }
    finally { this.stoppingProcess = null; }
  }

  private async stopProcess(): Promise<void> {
    this.stopping = true;
    this.ready = false;
    if (!this.proc || this.proc.exitCode !== null) {
      this.proc = null;
      return;
    }

    const child = this.proc;
    await new Promise<void>((resolve, reject) => {
      const hardDeadline = setTimeout(() => {
        this.lastError = "Local runtime shutdown could not be confirmed.";
        reject(new Error(this.lastError));
      }, 6000);
      const timer = setTimeout(() => {
        if (child.exitCode === null) child.kill("SIGKILL");
      }, 4000);
      child.once("exit", () => { clearTimeout(timer); clearTimeout(hardDeadline); resolve(); });
      child.kill("SIGTERM");
    });
    if (this.proc === child) this.proc = null;
  }
}
