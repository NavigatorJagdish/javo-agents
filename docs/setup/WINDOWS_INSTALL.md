# Windows Installation Guide (Beginner-Friendly + Hinglish Tips)

Welcome to **Javo Agents**! This guide helps you get your local AI creator team running on Windows 10/11 — even on an 8 GB RAM laptop.

> **Hinglish Quick Tip:** Agar aapke laptop mein 8 GB RAM hai, toh chinta mat karo! Javo automatically lightweight `qwen2.5:3b` model recommend karta hai taaki PC slow na ho aur $0 cost pe sab locally chale.

---

## 1. Prerequisites

1. **Windows 10 or Windows 11 (64-bit)**
2. **Python 3.11+** — Download from [python.org](https://www.python.org/downloads/) (*Check "Add Python to PATH"* during installation!)
3. **Node.js 20+ & pnpm** — Download LTS from [nodejs.org](https://nodejs.org/), then run `npm install -g pnpm`
4. **Ollama** *(Recommended for free local AI)* — Download from [ollama.com](https://ollama.com/download/windows)
5. **FFmpeg** *(Optional, for video/audio processing)* — `winget install Gyan.FFmpeg`

---

## 2. One-Command Setup

Open **PowerShell** in the `javo-agents` folder and run:

```powershell
.\scripts\setup-windows.ps1
```

This script:
- Creates a clean Python `.venv` inside `services/local-runtime/.venv`
- Installs FastAPI, SQLAlchemy, and backend dependencies
- Generates `.ico` and `.png` app icons (when Pillow is installed)
- Installs workspace JavaScript packages

---

## 3. Start Javo Agents

Run:

```powershell
.\scripts\start-windows.ps1
```

What happens:
1. Starts the local Python backend on `http://127.0.0.1:8000` and waits for `/health/`.
2. Launches the Electron Desktop Shell (or Vite Dashboard if running in dev mode).
3. Adds the **Javo Agents System Tray Icon** with quick controls:
   - **Open Dashboard**
   - **Pause / Resume Autopilot**
   - **Emergency Stop (Kill Switch)**

> **Hinglish Tip:** Agar kabhi lage ki agent galat post schedule kar raha hai, System Tray icon pe right-click karke **"Emergency Stop"** dabao — turant sab ruk jayega!

---

## 4. Building a Windows Installer (`.exe`)

To build the NSIS installer and Portable `.exe`:

```powershell
.\scripts\package-release.ps1
```

Installers will appear in `apps/windows/release/`.
