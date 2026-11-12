import { ChildProcess, spawn } from "node:child_process";
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
    const venvPython = path.join(this.runtimeDir, ".venv", "Scripts", "python.exe");
    if (fs.existsSync(venvPython)) {
      return venvPython;
    }
    return process.env.JAVO_PYTHON_PATH || "python";
  }

  public async start(preferredPort = 8000): Promise<BackendStatus> {
    if (this.proc && this.proc.exitCode === null) {
      return this.getStatus();
    }

    this.stopping = false;
    this.lastError = null;
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

    this.proc = spawn(pythonExe, args, {
      cwd: this.runtimeDir,
      env: {
        ...process.env,
        JAVO_HOST: "127.0.0.1",
        JAVO_PORT: String(this.port),
        PYTHONUNBUFFERED: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
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

    this.lastError = `Health check timed out at ${healthUrl}`;
    return false;
  }

  public async callControlEndpoint(endpoint: string, body?: Record<string, unknown>): Promise<boolean> {
    try {
      const res = await fetch(`http://127.0.0.1:${this.port}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(4000),
      });
      return res.ok;
    } catch {
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
