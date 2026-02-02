const { app, Tray, Menu, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const isDev = require("electron-is-dev");

let tray = null;
let mainWindow = null;
let agentProcess = null;
let backendProcess = null;

// ---------- START PYTHON AGENT ----------
function startAgent() {
  if (agentProcess) return;

  try {
    const agentPath = path.join(__dirname, "..", "agent", "lagsense_background_agent.py");
    const pythonPath = path.join(__dirname, "..", "agent", "venv", "Scripts", "python.exe");
    
    agentProcess = spawn(pythonPath, [agentPath], {
      windowsHide: true,
      detached: false
    });

    console.log("✓ LagSense Agent started");

    agentProcess.stdout.on("data", (data) => {
      console.log(`[Agent] ${data}`);
    });

    agentProcess.stderr.on("data", (data) => {
      console.error(`[Agent Error] ${data}`);
    });

    agentProcess.on("exit", (code) => {
      console.log(`✗ Agent exited with code ${code}`);
      agentProcess = null;
    });
  } catch (err) {
    console.error("Failed to start agent:", err);
  }
}

// ---------- START BACKEND - FIXED ----------
function startBackend() {
  try {
    const backendPath = path.join(__dirname, "..", "backend");
    const pythonPath = path.join(backendPath, "venv", "Scripts", "python.exe");
    
    backendProcess = spawn(pythonPath, [
      "-m", "uvicorn", 
      "main:app", 
      "--host", "127.0.0.1", 
      "--port", "8000"
    ], {
      windowsHide: true,
      cwd: backendPath
    });

    console.log("✓ LagSense Backend started");

    backendProcess.stdout.on("data", (data) => {
      console.log(`[Backend] ${data}`);
    });

    backendProcess.stderr.on("data", (data) => {
      console.error(`[Backend Error] ${data}`);
    });

    backendProcess.on("exit", (code) => {
      console.log(`Backend exited with code ${code}`);
      backendProcess = null;
    });
  } catch (err) {
    console.error("Failed to start backend:", err);
  }
}

// ---------- CREATE APP WINDOW - FIXED TO LOAD WELCOME PAGE ----------
function createWindow() {
  if (mainWindow) {
    mainWindow.show();
    return;
  }

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    icon: path.join(__dirname, "icon.ico"),
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Load welcome page (landing page) - FIXED
  const frontendPath = path.join(__dirname, "..", "frontend", "welcome.html");
  mainWindow.loadFile(frontendPath);

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.on("close", (e) => {
    e.preventDefault();
    mainWindow.hide();
  });

  // Open dev tools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
}

// ---------- CREATE TRAY ----------
function createTray() {
  tray = new Tray(path.join(__dirname, "icon.ico"));

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "📊 Open Dashboard",
      click: () => {
        if (mainWindow) {
          mainWindow.loadFile(path.join(__dirname, "..", "frontend", "dashboard.html"));
          mainWindow.show();
        }
      }
    },
    {
      label: "🏠 Home",
      click: () => {
        if (mainWindow) {
          mainWindow.loadFile(path.join(__dirname, "..", "frontend", "welcome.html"));
          mainWindow.show();
        }
      }
    },
    {
      label: "⚙️ Settings",
      click: () => {
        if (mainWindow) {
          mainWindow.loadFile(path.join(__dirname, "..", "frontend", "settings.html"));
          mainWindow.show();
        }
      }
    },
    { type: "separator" },
    {
      label: "🔄 Status",
      submenu: [
        {
          label: agentProcess ? "Agent: Running ✓" : "Agent: Stopped ✗",
          enabled: false
        },
        {
          label: backendProcess ? "Backend: Running ✓" : "Backend: Stopped ✗",
          enabled: false
        }
      ]
    },
    { type: "separator" },
    {
      label: "❌ Exit LagSense",
      click: () => {
        if (agentProcess) agentProcess.kill();
        if (backendProcess) backendProcess.kill();
        app.quit();
      }
    }
  ]);

  tray.setToolTip("LagSense - Network Monitor Running");
  tray.setContextMenu(contextMenu);

  tray.on("click", () => {
    if (mainWindow) {
      mainWindow.loadFile(path.join(__dirname, "..", "frontend", "welcome.html"));
      mainWindow.show();
    }
  });
}

// ---------- APP READY ----------
app.whenReady().then(() => {
  startBackend();
  startAgent();
  createTray();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// ---------- PREVENT APP QUIT ----------
app.on("window-all-closed", (e) => {
  e.preventDefault();
});

// ---------- IPC HANDLERS ----------
ipcMain.handle("get-agent-status", async () => {
  return agentProcess !== null;
});

ipcMain.handle("get-backend-status", async () => {
  return backendProcess !== null;
});

ipcMain.handle("get-version", async () => {
  return "1.0.0";
});

// ---------- GRACEFUL SHUTDOWN ----------
process.on("exit", () => {
  if (agentProcess) agentProcess.kill();
  if (backendProcess) backendProcess.kill();
});
