const API = "https://lagsense-api.onrender.com";
const userId = localStorage.getItem("user_id") || 1;

// Game thresholds (will be overridden by user settings)
const defaultThresholds = {
  valorant: { ping: 60, jitter: 10, loss: 1 },
  cs2: { ping: 70, jitter: 15, loss: 1.5 },
  dota2: { ping: 90, jitter: 20, loss: 2 },
  fortnite: { ping: 80, jitter: 18, loss: 2 },
  discord: { ping: 50, jitter: 8, loss: 0.5 },
  demo_game: { ping: 80, jitter: 15, loss: 2 }
};

let userThresholds = defaultThresholds;
let chart = null;

// ---------- LOAD USER SETTINGS ----------------
async function loadUserSettings() {
  try {
    const res = await fetch(`${API}/settings/${userId}`);
    const data = await res.json();
    
    if (data.thresholds) {
      userThresholds = data.thresholds;
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
    userThresholds = defaultThresholds;
  }
}

// ---------- POPULATE GAME DROPDOWN ----------------
function populateGames() {
  const select = document.getElementById("gameSelect");
  if (!select || select.options.length > 0) return;

  Object.keys(defaultThresholds).forEach(game => {
    const opt = document.createElement("option");
    opt.value = game;
    opt.textContent = game.toUpperCase();
    select.appendChild(opt);
  });
}

// ---------- CALCULATE HEALTH SCORE ----------------
function calculateHealthScore(ping, jitter, loss, thresholds) {
  let score = 100;
  
  if (ping > thresholds.ping) score -= 20;
  if (jitter > thresholds.jitter) score -= 20;
  if (loss > thresholds.loss) score -= 20;
  
  if (ping > thresholds.ping * 1.5) score -= 10;
  if (jitter > thresholds.jitter * 1.5) score -= 10;
  if (loss > thresholds.loss * 1.5) score -= 10;
  
  return Math.max(0, Math.min(100, score));
}

// ---------- HEALTH COLOR ----------------
function healthClass(val, limit) {
  if (val <= limit) return "good";
  if (val <= limit * 1.5) return "avg";
  return "bad";
}

// ---------- LOAD USERNAME ----------------
function loadUsername() {
  const userEmail = localStorage.getItem("user_email");
  
  if (userEmail) {
    document.getElementById("username").innerText = userEmail.split("@")[0];
  }
}

// ---------- LOAD STATISTICS ----------------
async function loadStatistics() {
  try {
    const res = await fetch(`${API}/statistics/${userId}`);
    const data = await res.json();

    document.getElementById("totalSessions").innerText = data.total_sessions || 0;
    document.getElementById("bestGame").innerText = (data.best_game || "N/A").toUpperCase();
    document.getElementById("worstGame").innerText = (data.worst_game || "N/A").toUpperCase();
    document.getElementById("totalPlaytime").innerText = (data.total_play_time || 0).toFixed(1) + "h";
  } catch (err) {
    console.error("Failed to load statistics:", err);
  }
}

// ---------- LIVE AUTO-DETECT ----------------
async function pollLive() {
  populateGames();

  for (const game of Object.keys(defaultThresholds)) {
    try {
      const res = await fetch(`${API}/live/${userId}/${game}`);
      const data = await res.json();

      if (data && data.ping !== undefined) {
        document.getElementById("gameSelect").value = game;

        const ping = parseFloat(data.ping);
        const jitter = parseFloat(data.jitter);
        const loss = parseFloat(data.loss);
        const thresholds = userThresholds[game] || defaultThresholds[game];

        document.getElementById("ping").innerText = ping.toFixed(1);
        document.getElementById("jitter").innerText = jitter.toFixed(1);
        document.getElementById("packetLoss").innerText = loss.toFixed(2);

        const healthScore = calculateHealthScore(ping, jitter, loss, thresholds);
        document.getElementById("healthScore").innerText = healthScore.toFixed(0);

        document.getElementById("ping").className =
          "metric-value " + healthClass(ping, thresholds.ping);
        document.getElementById("jitter").className =
          "metric-value " + healthClass(jitter, thresholds.jitter);
        document.getElementById("packetLoss").className =
          "metric-value " + healthClass(loss, thresholds.loss);
        document.getElementById("healthScore").className =
          "metric-value " + (healthScore >= 80 ? "good" : healthScore >= 50 ? "avg" : "bad");

        // Check for notifications
        checkNotifications(ping, jitter, loss, game, thresholds);

        return;
      }
    } catch (err) {
      console.error("Live polling error:", err);
    }
  }
}

// ---------- CHECK NOTIFICATIONS ----------------
async function checkNotifications(ping, jitter, loss, game, thresholds) {
  try {
    const res = await fetch(`${API}/settings/${userId}`);
    const settings = await res.json();
    const notif = settings.notifications || {};

    if (notif.notify_on_ping_spike && ping > notif.ping_alert_threshold) {
      showNotification(`⚠️ High Ping`, `${game.toUpperCase()}: ${ping.toFixed(1)}ms`);
    }
    if (notif.notify_on_jitter_high && jitter > thresholds.jitter) {
      showNotification(`⚠️ High Jitter`, `${game.toUpperCase()}: ${jitter.toFixed(2)}ms`);
    }
    if (notif.notify_on_packet_loss && loss > thresholds.loss) {
      showNotification(`⚠️ Packet Loss`, `${game.toUpperCase()}: ${loss.toFixed(2)}%`);
    }
  } catch (err) {
    console.error("Notification check error:", err);
  }
}

// ---------- SHOW NOTIFICATION ----------------
function showNotification(title, message) {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(title, {
      body: message,
      icon: 'logo.svg',
      tag: 'lagsense'
    });
  }
}

// ---------- REQUEST NOTIFICATION PERMISSION ----------------
function requestNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

// ---------- LOAD SESSIONS ----------------
async function loadSessions() {
  const game = document.getElementById("gameSelect").value;
  if (!game) return;

  try {
    const res = await fetch(`${API}/sessions/${userId}/${game}`);
    const sessions = await res.json();

    const select = document.getElementById("sessionSelect");
    select.innerHTML = "";

    if (sessions.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "No sessions found";
      select.appendChild(opt);
      return;
    }

    sessions.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = new Date(s).toLocaleString();
      select.appendChild(opt);
    });
  } catch (err) {
    console.error("Load sessions error:", err);
    alert("Failed to load sessions");
  }
}

// ---------- ANALYZE SESSION ----------------
async function analyzeSession() {
  const game = document.getElementById("gameSelect").value;
  const session = document.getElementById("sessionSelect").value;
  
  if (!session) {
    alert("Please select a session first");
    return;
  }

  try {
    const res = await fetch(`${API}/session/${userId}/${game}/${session}`);
    const data = await res.json();

    if (data.error) {
      alert("Error analyzing session: " + data.error);
      return;
    }

    document.getElementById("verdict").innerText = data.verdict || "No data";
    document.getElementById("optimizer").innerText =
      data.optimizer
        ? "✓ Routing optimizer likely to help"
        : "✗ Routing optimizer not required";

    const causes = document.getElementById("causes");
    causes.innerHTML = "";
    
    if (data.reasons && data.reasons.length > 0) {
      data.reasons.forEach(r => {
        const li = document.createElement("li");
        li.textContent = r;
        causes.appendChild(li);
      });
    } else {
      const li = document.createElement("li");
      li.textContent = "No issues detected";
      causes.appendChild(li);
    }

    // Display stats
    if (data.avg_ping !== undefined) {
      const statsHtml = `
        <strong>Average Stats:</strong><br>
        Ping: ${data.avg_ping.toFixed(1)}ms | 
        Jitter: ${data.avg_jitter.toFixed(2)}ms | 
        Loss: ${data.avg_loss.toFixed(2)}%
      `;
      document.getElementById("optimizer").innerHTML += `<br><br>${statsHtml}`;
    }

    if (data.timeline && data.timeline.length > 0) {
      renderChart(data.timeline);
    }
  } catch (err) {
    console.error("Analyze session error:", err);
    alert("Error analyzing session");
  }
}

// ---------- TIMELINE CHART ----------------
function renderChart(timeline) {
  const ctx = document.getElementById("timelineChart").getContext("2d");
  const labels = timeline.map(p =>
    new Date(p.time).toLocaleTimeString()
  );
  const pingValues = timeline.map(p => p.ping);
  const jitterValues = timeline.map(p => p.jitter);
  const lossValues = timeline.map(p => p.loss * 10); // Scale for visibility

  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Ping (ms)",
          data: pingValues,
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56,189,248,0.1)",
          tension: 0.3,
          fill: true,
          yAxisID: "y"
        },
        {
          label: "Jitter (ms)",
          data: jitterValues,
          borderColor: "#fbbf24",
          backgroundColor: "rgba(251,191,36,0.1)",
          tension: 0.3,
          fill: false,
          yAxisID: "y1"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: { color: "#e5e7eb" }
        }
      },
      scales: {
        y: {
          type: 'linear',
          position: 'left',
          ticks: { color: "#94a3b8" },
          grid: { color: "rgba(56,189,248,0.1)" },
          title: { display: true, text: "Ping/Jitter (ms)", color: "#e5e7eb" }
        },
        y1: {
          type: 'linear',
          position: 'right',
          ticks: { color: "#94a3b8" },
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Loss (%)", color: "#e5e7eb" }
        },
        x: {
          ticks: { color: "#94a3b8" },
          grid: { color: "rgba(56,189,248,0.1)" }
        }
      }
    }
  });
}

// ---------- LOGOUT ----------------
function logout() {
  localStorage.removeItem("user_id");
  localStorage.removeItem("user_email");
  window.location.href = "welcome.html";
}

// ---------- START EVERYTHING ----------------
requestNotificationPermission();
loadUsername();
loadUserSettings();
loadStatistics();
populateGames();
setInterval(pollLive, 2000);
setInterval(loadStatistics, 60000); // Update stats every minute