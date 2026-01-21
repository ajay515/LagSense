const { app, Tray, Menu, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const isDev = require("electron-is-dev");

let tray = null;
let mainWindow = null;
let agentProcess = null;

// ---------- START PYTHON AGENT ----------
function startAgent() {
  if (agentProcess) return;

  try {
    const agentPath = path.join(__dirname, "..", "agent", "lagsense_background_agent.py");
    
    agentProcess = spawn("python", [agentPath], {
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

// ---------- START BACKEND ----------
function startBackend() {
  try {
    const backendPath = path.join(__dirname, "..", "backend");
    
    const backendProcess = spawn("cmd", ["/c", "cd backend && venv\\Scripts\\activate && uvicorn main:app --reload"], {
      windowsHide: true,
      cwd: path.join(__dirname, "..")
    });

    backendProcess.on("exit", (code) => {
      console.log(`Backend exited with code ${code}`);
    });
  } catch (err) {
    console.error("Failed to start backend:", err);
  }
}

// ---------- CREATE APP WINDOW ----------
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

  // Load frontend
  const frontendPath = path.join(__dirname, "..", "frontend", "dashboard.html");
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
      click: createWindow
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
          label: "Agent: Running ✓",
          enabled: false
        },
        {
          label: "Backend: Running ✓",
          enabled: false
        }
      ]
    },
    { type: "separator" },
    {
      label: "❌ Exit LagSense",
      click: () => {
        if (agentProcess) agentProcess.kill();
        app.quit();
      }
    }
  ]);

  tray.setToolTip("LagSense - Network Monitor Running");
  tray.setContextMenu(contextMenu);

  tray.on("click", createWindow);
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

ipcMain.handle("get-version", async () => {
  return "1.0.0";
});

// ---------- GRACEFUL SHUTDOWN ----------
process.on("exit", () => {
  if (agentProcess) agentProcess.kill();
});