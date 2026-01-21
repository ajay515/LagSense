const API = "http://127.0.0.1:8000";
const userId = localStorage.getItem("user_id") || 1;
const userEmail = localStorage.getItem("user_email") || "";

const defaultThresholds = {
  valorant: { ping: 60, jitter: 10, loss: 1 },
  cs2: { ping: 70, jitter: 15, loss: 1.5 },
  dota2: { ping: 90, jitter: 20, loss: 2 },
  fortnite: { ping: 80, jitter: 18, loss: 2 },
  discord: { ping: 50, jitter: 8, loss: 0.5 }
};

let currentSettings = {};

// ---------- LOAD SETTINGS ON PAGE LOAD ----------------
async function loadSettings() {
  try {
    const res = await fetch(`${API}/settings/${userId}`);
    const data = await res.json();

    currentSettings = data;

    // Populate profile
    document.getElementById("email").value = userEmail;
    
    // Populate game thresholds
    const container = document.getElementById("gameThresholds");
    container.innerHTML = "";

    Object.keys(defaultThresholds).forEach(game => {
      const threshold = data.thresholds[game] || defaultThresholds[game];
      
      const gameBox = document.createElement("div");
      gameBox.className = "game-threshold-box";
      gameBox.innerHTML = `
        <h4>${game.toUpperCase()}</h4>
        <div class="threshold-grid">
          <div class="threshold-input">
            <label>Ping (ms)</label>
            <input type="number" class="ping-${game}" value="${threshold.ping}" min="10" max="500">
          </div>
          <div class="threshold-input">
            <label>Jitter (ms)</label>
            <input type="number" class="jitter-${game}" value="${threshold.jitter}" min="1" max="100">
          </div>
          <div class="threshold-input">
            <label>Loss (%)</label>
            <input type="number" class="loss-${game}" value="${threshold.loss}" min="0" max="100" step="0.1">
          </div>
        </div>
      `;
      container.appendChild(gameBox);
    });

    // Populate notifications
    const notif = data.notifications || {};
    document.getElementById("notifyPingSpihe").checked = notif.notify_on_ping_spike !== false;
    document.getElementById("notifyJitter").checked = notif.notify_on_jitter_high !== false;
    document.getElementById("notifyLoss").checked = notif.notify_on_packet_loss !== false;
    document.getElementById("pingAlertThreshold").value = notif.ping_alert_threshold || 150;

  } catch (err) {
    console.error("Failed to load settings:", err);
    showMessage("Error loading settings", "error");
  }
}

// ---------- SAVE SETTINGS ----------------
async function saveSettings() {
  try {
    const thresholds = {};
    
    Object.keys(defaultThresholds).forEach(game => {
      thresholds[game] = {
        ping: parseFloat(document.querySelector(`.ping-${game}`).value),
        jitter: parseFloat(document.querySelector(`.jitter-${game}`).value),
        loss: parseFloat(document.querySelector(`.loss-${game}`).value)
      };
    });

    const settings = {
      thresholds,
      notifications: {
        notify_on_ping_spike: document.getElementById("notifyPingSpihe").checked,
        notify_on_jitter_high: document.getElementById("notifyJitter").checked,
        notify_on_packet_loss: document.getElementById("notifyLoss").checked,
        ping_alert_threshold: parseFloat(document.getElementById("pingAlertThreshold").value)
      }
    };

    const res = await fetch(`${API}/settings/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings)
    });

    const data = await res.json();

    if (data.success) {
      showMessage("Settings saved successfully!", "success");
    } else {
      showMessage(data.message || "Failed to save settings", "error");
    }
  } catch (err) {
    console.error("Save settings error:", err);
    showMessage("Error saving settings", "error");
  }
}

// ---------- SAVE PROFILE ----------------
async function saveProfile() {
  try {
    const displayName = document.getElementById("displayName").value;
    const newPassword = document.getElementById("newPassword").value;

    if (!displayName) {
      showMessage("Display name cannot be empty", "error");
      return;
    }

    const profileData = {
      display_name: displayName,
      password: newPassword || null
    };

    const res = await fetch(`${API}/profile/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profileData)
    });

    const data = await res.json();

    if (data.success) {
      showMessage("Profile updated successfully!", "success");
      document.getElementById("newPassword").value = "";
    } else {
      showMessage(data.message || "Failed to update profile", "error");
    }
  } catch (err) {
    console.error("Save profile error:", err);
    showMessage("Error updating profile", "error");
  }
}

// ---------- RESET TO DEFAULTS ----------------
async function resetToDefaults() {
  if (!confirm("Reset all thresholds to defaults? This cannot be undone.")) {
    return;
  }

  try {
    const settings = {
      thresholds: defaultThresholds,
      notifications: {
        notify_on_ping_spike: true,
        notify_on_jitter_high: true,
        notify_on_packet_loss: true,
        ping_alert_threshold: 150
      }
    };

    const res = await fetch(`${API}/settings/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings)
    });

    const data = await res.json();

    if (data.success) {
      showMessage("Reset to defaults!", "success");
      loadSettings(); // Reload to show defaults
    } else {
      showMessage("Failed to reset settings", "error");
    }
  } catch (err) {
    console.error("Reset error:", err);
    showMessage("Error resetting settings", "error");
  }
}

// ---------- SHOW MESSAGE ----------------
function showMessage(text, type) {
  const msg = document.getElementById("message");
  msg.innerText = text;
  msg.style.color = type === "success" ? "#10b981" : "#ef4444";
  
  setTimeout(() => {
    msg.innerText = "";
  }, 5000);
}

// ---------- LOGOUT ----------------
function logout() {
  localStorage.removeItem("user_id");
  localStorage.removeItem("user_email");
  window.location.href = "welcome.html";
}

// Load settings on page load
loadSettings();
