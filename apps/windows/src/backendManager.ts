import { ChildProcess, spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
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
  private authToken: string | null = null;

  constructor(private readonly runtimeDir: string) {}

  public getStatus(): BackendStatus {
    return {
      running: this.proc !== null && this.proc.exitCode === null,
      port: this.port,
      baseUrl: `http://127.0.0.1:${this.port}`,
      pid: this.proc?.pid ?? null,
      lastError: this.lastError,
    };
  }

  public getAuthToken(): string | null {
    return this.authToken;
  }

  public setAuthToken(token: string): void {
    this.authToken = token;
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

  public resolvePythonExecutable(): string {
    // 1. Explicit environment override
    const envPython = process.env.JAVO_PYTHON_PATH;
    if (envPython && fs.existsSync(envPython)) {
      return envPython;
    }

    // 2. Bundled python runtime paths (packaged app)
    const bundledCandidates = [
      path.join(process.resourcesPath || "", "python", "python.exe"),
      path.join(this.runtimeDir, "python", "python.exe"),
      path.join(this.runtimeDir, ".venv", "Scripts", "python.exe"),
      path.join(this.runtimeDir, "venv", "Scripts", "python.exe"),
      path.join(this.runtimeDir, "..", "..", ".venv", "Scripts", "python.exe"),
    ];
    for (const cand of bundledCandidates) {
      if (cand && fs.existsSync(cand)) {
        return cand;
      }
    }

    // 3. Common Windows Python installations
    const localAppData = process.env.LOCALAPPDATA || "";
    const systemCandidates = [
      path.join(localAppData, "Programs", "Python", "Python311", "python.exe"),
      path.join(localAppData, "Programs", "Python", "Python312", "python.exe"),
      path.join(localAppData, "Programs", "Python", "Python310", "python.exe"),
      "C:\\Program Files\\Python311\\python.exe",
      "C:\\Program Files\\Python312\\python.exe",
      "C:\\Python311\\python.exe",
      "C:\\Python312\\python.exe",
      "C:\\Python310\\python.exe",
    ];
    for (const cand of systemCandidates) {
      if (fs.existsSync(cand)) {
        return cand;
      }
    }

    // 4. Default to system PATH lookup
    return "python";
  }

  public async start(preferredPort = 8000): Promise<BackendStatus> {
    if (this.proc && this.proc.exitCode === null) {
      return this.getStatus();
    }

    this.stopping = false;
    this.lastError = null;
    this.port = await this.findAvailablePort(preferredPort);

    // Ensure durable or securely provisioned local owner token
    if (!this.authToken) {
      this.authToken = process.env.JAVO_OWNER_TOKEN || crypto.randomBytes(32).toString("base64url");
    }

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

    try {
      this.proc = spawn(pythonExe, args, {
        cwd: this.runtimeDir,
        env: {
          ...process.env,
          JAVO_HOST: "127.0.0.1",
          JAVO_PORT: String(this.port),
          JAVO_OWNER_TOKEN: this.authToken,
          PYTHONUNBUFFERED: "1",
        },
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true,
      });
    } catch (spawnErr: unknown) {
      const msg = spawnErr instanceof Error ? spawnErr.message : String(spawnErr);
      this.lastError = `Failed to spawn Python process (${pythonExe}): ${msg}`;
      return this.getStatus();
    }

    this.proc.on("error", (err: NodeJS.ErrnoException) => {
      if (err.code === "ENOENT") {
        this.lastError = `Python runtime not found at '${pythonExe}'. Please install Python 3.10+ from https://www.python.org or set JAVO_PYTHON_PATH.`;
      } else {
        this.lastError = `Backend process error: ${err.message}`;
      }
      this.proc = null;
    });

    this.proc.stderr?.on("data", (chunk: Buffer) => {
      const msg = chunk.toString("utf-8").trim();
      if (msg) {
        this.lastError = msg.slice(-400);
      }
    });

    this.proc.on("exit", (code) => {
      if (!this.stopping && code !== 0) {
        this.lastError = `Backend exited with code ${code}`;
      }
      this.proc = null;
    });

    await this.waitForHealth(20000);
    return this.getStatus();
  }

  public async waitForHealth(timeoutMs = 20000): Promise<boolean> {
    const deadline = Date.now() + timeoutMs;
    const healthUrl = `http://127.0.0.1:${this.port}/health/`;

    while (Date.now() < deadline) {
      try {
        const res = await fetch(healthUrl, { signal: AbortSignal.timeout(1500) });
        if (res.ok) {
          this.lastError = null;
          return true;
        }
      } catch {
        // Backend is still starting up
      }
      await new Promise((r) => setTimeout(r, 400));
    }

    if (!this.lastError) {
      this.lastError = `Health check timed out at ${healthUrl}`;
    }
    return false;
  }

  public async callControlEndpoint(endpoint: string, body?: Record<string, unknown>): Promise<boolean> {
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (this.authToken) {
        headers["Authorization"] = `Bearer ${this.authToken}`;
      }
      const res = await fetch(`http://127.0.0.1:${this.port}${endpoint}`, {
        method: "POST",
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(4000),
      });
      if (!res.ok) {
        const errText = await res.text().catch(() => "");
        this.lastError = `Control endpoint ${endpoint} failed (${res.status}): ${errText.slice(0, 150)}`;
        return false;
      }
      this.lastError = null;
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this.lastError = `Control endpoint ${endpoint} error: ${msg}`;
      return false;
    }
  }

  public async stop(): Promise<void> {
    this.stopping = true;
    if (!this.proc || this.proc.exitCode !== null) {
      this.proc = null;
      return;
    }

    const child = this.proc;
    child.kill("SIGTERM");

    await Promise.race([
      new Promise<void>((resolve) => child.once("exit", () => resolve())),
      new Promise<void>((resolve) =>
        setTimeout(() => {
          if (child.exitCode === null) {
            child.kill("SIGKILL");
          }
          resolve();
        }, 4000)
      ),
    ]);
    this.proc = null;
  }
}
