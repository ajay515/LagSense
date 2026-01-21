import time
import socket
import requests
from datetime import datetime, timedelta
import psutil
import win32gui
import win32process
import subprocess
import re
from collections import deque
import numpy as np
import json
import os
from pathlib import Path

API = "http://127.0.0.1:8000"
USER_ID = 1

# Notification tracking (don't spam)
NOTIFICATION_LOG_FILE = Path.home() / ".lagsense" / "notifications.json"
NOTIFICATION_DELAY_MINUTES = 20

GAME_PROCESSES = {
    "valorant": ["valorant.exe"],
    "cs2": ["cs2.exe"],
    "dota2": ["dota2.exe"],
    "fortnite": ["fortniteclient-win64-shipping.exe"],
    "discord": ["discord.exe"]
}

last_game = None
session_active = False
ping_history = deque(maxlen=10)

# Create logs directory
NOTIFICATION_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ---------- NOTIFICATION TRACKING ----------
def load_notification_log():
    """Load previous notifications"""
    try:
        if NOTIFICATION_LOG_FILE.exists():
            with open(NOTIFICATION_LOG_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_notification_log(log):
    """Save notification log"""
    try:
        with open(NOTIFICATION_LOG_FILE, 'w') as f:
            json.dump(log, f)
    except Exception:
        pass

def can_notify(notification_type, game):
    """Check if enough time has passed since last notification"""
    log = load_notification_log()
    key = f"{notification_type}_{game}"
    
    if key not in log:
        return True
    
    last_time = datetime.fromisoformat(log[key])
    if datetime.now() - last_time > timedelta(minutes=NOTIFICATION_DELAY_MINUTES):
        return True
    
    return False

def record_notification(notification_type, game):
    """Record that we sent a notification"""
    log = load_notification_log()
    key = f"{notification_type}_{game}"
    log[key] = datetime.now().isoformat()
    save_notification_log(log)

# ---------- SHOW WINDOWS NOTIFICATION ----------
def show_windows_notification(title, message, icon_path=None):
    """Show Windows 10/11 notification"""
    try:
        # Use Windows notification
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=10, threaded=True)
    except Exception:
        try:
            # Fallback: use PowerShell
            ps_command = f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null; $APP_ID = "LagSense"; $template = @" <toast><visual><binding template="ToastText02"><text id="1">{title}</text><text id="2">{message}</text></binding></visual></toast> "@; $xml = New-Object Windows.Data.Xml.Dom.XmlDocument; $xml.LoadXml($template); $toast = New-Object Windows.UI.Notifications.ToastNotification $xml; [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast) "@'
            subprocess.run(['powershell', '-Command', ps_command], capture_output=True)
        except Exception as e:
            print(f"Notification failed: {e}")

# ---------- TCP LATENCY ----------
def tcp_latency(host="1.1.1.1", port=443, timeout=1):
    """Measure TCP latency in milliseconds"""
    try:
        start = time.time()
        socket.create_connection((host, port), timeout=timeout).close()
        return round((time.time() - start) * 1000, 2)
    except Exception:
        return None

# ---------- CALCULATE JITTER ----------
def calculate_jitter():
    """Calculate jitter from ping history"""
    if len(ping_history) < 2:
        return 0
    
    try:
        pings = list(ping_history)
        differences = [abs(pings[i] - pings[i-1]) for i in range(1, len(pings))]
        return round(np.mean(differences), 2) if differences else 0
    except Exception:
        return 0

# ---------- DETECT PACKET LOSS ----------
def detect_packet_loss(host="1.1.1.1", count=10, timeout=1):
    """Detect packet loss using ping"""
    try:
        cmd = f"ping -n {count} -w {timeout*1000} {host}"
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if "Received = " in result.stdout:
            match = re.search(r'Received = (\d+)', result.stdout)
            if match:
                received = int(match.group(1))
                loss_percentage = ((count - received) / count) * 100
                return round(loss_percentage, 2)
    except Exception:
        pass
    
    return 0

# ---------- DETECT GAME (BACKGROUND) ----------
def detect_game_process():
    """Detect game process even if in background"""
    try:
        for proc in psutil.process_iter(['name']):
            try:
                exe_name = proc.info['name'].lower()
                for game, names in GAME_PROCESSES.items():
                    if exe_name in names:
                        return game
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass
    
    return None

# ---------- SEND NOTIFICATION ----------------
def check_and_notify(ping, jitter, loss, game, thresholds):
    """Check if should notify and send notification"""
    issues = []
    
    # Check for issues
    if ping > thresholds["ping"] * 1.5:  # High threshold for notification
        if can_notify("high_ping", game):
            issues.append(f"⚠️ Critical Ping: {ping:.1f}ms")
            record_notification("high_ping", game)
    
    if jitter > thresholds["jitter"] * 1.5:
        if can_notify("high_jitter", game):
            issues.append(f"⚠️ High Jitter: {jitter:.2f}ms")
            record_notification("high_jitter", game)
    
    if loss > thresholds["loss"] * 1.5:
        if can_notify("packet_loss", game):
            issues.append(f"⚠️ Packet Loss: {loss:.2f}%")
            record_notification("packet_loss", game)
    
    # Send notification if issues found
    if issues:
        title = f"LagSense - {game.upper()}"
        message = "\n".join(issues)
        show_windows_notification(title, message)

# ---------- FOREGROUND GAME DETECTION ----------
def detect_foreground_game():
    """Detect which game is in foreground"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        exe = proc.name().lower()

        for game, names in GAME_PROCESSES.items():
            if exe in names:
                return game
    except Exception:
        pass
    
    return None

# ---------- SESSION END ----------
def end_session(game):
    """End current game session"""
    try:
        requests.post(f"{API}/end-session/{USER_ID}/{game}", timeout=2)
        print(f"✓ Session ended for {game}")
    except Exception as e:
        print(f"✗ Failed to end session: {e}")

# ---------- MAIN LOOP ----------
print("=" * 60)
print("LagSense Background Agent v2.1 - Production Ready")
print("=" * 60)
print("🎮 Monitoring: Valorant, CS2, Dota2, Fortnite, Discord")
print("📊 Measuring: Ping, Jitter, Packet Loss")
print("🔔 Notifications: Every 20 minutes max")
print("🔄 Background Monitoring: Always active")
print("=" * 60)

while True:
    try:
        # Detect game in background (not just foreground)
        game = detect_game_process()
        
        # Measure network quality
        latency = tcp_latency()
        jitter = calculate_jitter()
        packet_loss = detect_packet_loss()
        
        # Game closed
        if session_active and last_game and game != last_game:
            end_session(last_game)
            session_active = False
            ping_history.clear()

        if game and latency is not None:
            # Add to ping history for jitter calculation
            ping_history.append(latency)
            jitter = calculate_jitter()
            
            payload = {
                "user_id": USER_ID,
                "game": game,
                "ping": latency,
                "jitter": jitter,
                "loss": packet_loss,
                "timestamp": datetime.utcnow().isoformat()
            }

            try:
                response = requests.post(f"{API}/stat", json=payload, timeout=2)
                if response.status_code == 200:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {game.upper():8} | Ping: {latency:6.1f}ms | Jitter: {jitter:5.2f}ms | Loss: {packet_loss:5.2f}%")
                    session_active = True
                    last_game = game
                    
                    # Get thresholds from backend
                    try:
                        settings_res = requests.get(f"{API}/settings/{USER_ID}", timeout=2)
                        settings_data = settings_res.json()
                        thresholds = settings_data.get("thresholds", {}).get(game, {"ping": 100, "jitter": 20, "loss": 5})
                        check_and_notify(latency, jitter, packet_loss, game, thresholds)
                    except Exception:
                        pass
                else:
                    print(f"✗ API error: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"✗ Connection error: {e}")

        time.sleep(2)

    except KeyboardInterrupt:
        if session_active and last_game:
            end_session(last_game)
        print("\n✓ LagSense Agent stopped")
        break
    except Exception as e:
        print(f"✗ Error: {e}")
        time.sleep(2)