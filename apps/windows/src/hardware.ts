import { execFile } from "node:child_process";
import os from "node:os";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export interface HardwareProfile {
  cpuModel: string;
  cpuCores: number;
  totalRamGb: number;
  freeRamGb: number;
  hasNvidiaGpu: boolean;
  gpuName: string | null;
  gpuVramGb: number | null;
  recommendedTier: "8gb_cpu" | "16gb_hybrid" | "32gb_gpu";
  recommendedOllamaModel: string;
  maxConcurrentAgents: number;
}

async function detectNvidiaGpu(): Promise<{ name: string; vramGb: number } | null> {
  try {
    const { stdout } = await execFileAsync(
      "nvidia-smi",
      ["--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
      { timeout: 3000 }
    );
    const firstLine = stdout.trim().split(/\r?\n/)[0];
    if (!firstLine) return null;
    const [name, memMbRaw] = firstLine.split(",").map((s) => s.trim());
    const memMb = Number(memMbRaw);
    return {
      name: name || "NVIDIA GPU",
      vramGb: Number.isFinite(memMb) ? Math.round((memMb / 1024) * 10) / 10 : 0,
    };
  } catch {
    return null;
  }
}

export async function detectHardwareProfile(): Promise<HardwareProfile> {
  const cpus = os.cpus();
  const totalRamGb = Math.round((os.totalmem() / 1024 ** 3) * 10) / 10;
  const freeRamGb = Math.round((os.freemem() / 1024 ** 3) * 10) / 10;
  const gpu = await detectNvidiaGpu();

  let recommendedTier: HardwareProfile["recommendedTier"] = "8gb_cpu";
  let recommendedOllamaModel = "qwen2.5:3b-instruct-q4_K_M";
  let maxConcurrentAgents = 2;

  if (totalRamGb >= 24 && gpu && gpu.vramGb >= 8) {
    recommendedTier = "32gb_gpu";
    recommendedOllamaModel = "qwen2.5:14b-instruct-q4_K_M";
    maxConcurrentAgents = 5;
  } else if (totalRamGb >= 14 || (gpu && gpu.vramGb >= 6)) {
    recommendedTier = "16gb_hybrid";
    recommendedOllamaModel = "qwen2.5:7b-instruct-q4_K_M";
    maxConcurrentAgents = 3;
  }

  return {
    cpuModel: cpus[0]?.model ?? "Unknown CPU",
    cpuCores: cpus.length,
    totalRamGb,
    freeRamGb,
    hasNvidiaGpu: Boolean(gpu),
    gpuName: gpu?.name ?? null,
    gpuVramGb: gpu?.vramGb ?? null,
    recommendedTier,
    recommendedOllamaModel,
    maxConcurrentAgents,
  };
}
