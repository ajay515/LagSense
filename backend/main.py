from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import statistics
import os
from typing import List

from database import SessionLocal, init_db, User, Session as DBSession, NetworkStat, UserSettings
from auth import register_user, login_user, hash_password
from models import (
    AuthRequest, UserUpdate, NetworkStatCreate, VerdictResponse,
    SessionResponse, UserSettingsResponse, UserSettingsUpdate,
    GameThresholds, StatisticsResponse
)
import settings

app = FastAPI(title="LagSense API")

# ================= CORS MIDDLEWARE =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ================= DATABASE =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= AUTHENTICATION =================
@app.post("/register")
def register(data: AuthRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, data.email, data.password)
        if not user:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "User already exists"}
            )
        return JSONResponse(
            status_code=200,
            content={"success": True, "user_id": user.id}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Registration error: {str(e)}"}
        )

@app.post("/login")
def login(data: AuthRequest, db: Session = Depends(get_db)):
    try:
        user = login_user(db, data.email, data.password)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Invalid credentials"}
            )
        return JSONResponse(
            status_code=200,
            content={"success": True, "user_id": user.id}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Login error: {str(e)}"}
        )

# ================= USER MANAGEMENT =================
@app.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return JSONResponse(status_code=404, content={"error": "User not found"})
        
        return JSONResponse(
            status_code=200,
            content={
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "created_at": user.created_at.isoformat()
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.put("/profile/{user_id}")
def update_profile(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return JSONResponse(status_code=404, content={"success": False, "message": "User not found"})
        
        if data.display_name:
            user.display_name = data.display_name
        if data.password:
            user.password = hash_password(data.password)
        
        db.commit()
        return JSONResponse(status_code=200, content={"success": True, "message": "Profile updated"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@app.get("/stats/users")
def total_users(db: Session = Depends(get_db)):
    try:
        count = db.query(User).count()
        return JSONResponse(status_code=200, content={"users": count or 0})
    except Exception as e:
        return JSONResponse(status_code=500, content={"users": 0, "error": str(e)})

# ================= NETWORK STATS - RECEIVE DATA =================
@app.post("/stat")
def receive_stat(stat: NetworkStatCreate, db: Session = Depends(get_db)):
    try:
        thresholds = settings.get_user_thresholds(db, stat.user_id)
        
        if stat.game not in thresholds:
            return JSONResponse(status_code=200, content={"status": "ignored"})

        # Get or create current session
        db_session = db.query(DBSession).filter(
            DBSession.user_id == stat.user_id,
            DBSession.game == stat.game,
            DBSession.end_time == None
        ).first()

        if not db_session:
            db_session = DBSession(
                user_id=stat.user_id,
                game=stat.game,
                start_time=datetime.utcnow()
            )
            db.add(db_session)
            db.commit()
            db.refresh(db_session)

        # Store network stat
        network_stat = NetworkStat(
            session_id=db_session.id,
            user_id=stat.user_id,
            ping=stat.ping,
            jitter=stat.jitter,
            packet_loss=stat.loss,
            timestamp=stat.timestamp
        )
        db.add(network_stat)
        db.commit()

        # Update session averages
        all_stats = db.query(NetworkStat).filter(NetworkStat.session_id == db_session.id).all()
        pings = [s.ping for s in all_stats]
        jitters = [s.jitter for s in all_stats]
        losses = [s.packet_loss for s in all_stats]

        db_session.avg_ping = statistics.mean(pings) if pings else 0
        db_session.avg_jitter = statistics.mean(jitters) if jitters else 0
        db_session.avg_loss = statistics.mean(losses) if losses else 0
        db.commit()

        return JSONResponse(status_code=200, content={"status": "ok", "session_id": db_session.id})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# ================= SESSION MANAGEMENT =================
@app.post("/end-session/{user_id}/{game}")
def end_session(user_id: int, game: str, db: Session = Depends(get_db)):
    try:
        db_session = db.query(DBSession).filter(
            DBSession.user_id == user_id,
            DBSession.game == game,
            DBSession.end_time == None
        ).first()

        if db_session:
            db_session.end_time = datetime.utcnow()
            db.commit()

        return JSONResponse(status_code=200, content={"status": "ended"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/live/{user_id}/{game}")
def live_metrics(user_id: int, game: str, db: Session = Depends(get_db)):
    try:
        db_session = db.query(DBSession).filter(
            DBSession.user_id == user_id,
            DBSession.game == game,
            DBSession.end_time == None
        ).first()

        if not db_session:
            return JSONResponse(status_code=200, content={})

        latest_stat = db.query(NetworkStat).filter(
            NetworkStat.session_id == db_session.id
        ).order_by(NetworkStat.timestamp.desc()).first()

        if not latest_stat:
            return JSONResponse(status_code=200, content={})

        return JSONResponse(
            status_code=200,
            content={
                "ping": latest_stat.ping,
                "jitter": latest_stat.jitter,
                "loss": latest_stat.packet_loss,
                "timestamp": latest_stat.timestamp.isoformat()
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/sessions/{user_id}/{game}")
def list_sessions(user_id: int, game: str, db: Session = Depends(get_db)):
    try:
        db_sessions = db.query(DBSession).filter(
            DBSession.user_id == user_id,
            DBSession.game == game
        ).order_by(DBSession.start_time.desc()).all()

        return JSONResponse(
            status_code=200,
            content=[s.start_time.isoformat() for s in db_sessions]
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ================= SESSION ANALYSIS =================
@app.get("/session/{user_id}/{game}/{session_id}")
def analyze_session(user_id: int, game: str, session_id: str, db: Session = Depends(get_db)):
    try:
        db_session = db.query(DBSession).filter(
            DBSession.user_id == user_id,
            DBSession.game == game,
            DBSession.start_time == session_id
        ).first()

        if not db_session:
            return JSONResponse(status_code=404, content={"error": "Session not found"})

        all_stats = db.query(NetworkStat).filter(NetworkStat.session_id == db_session.id).all()

        if not all_stats:
            return JSONResponse(status_code=200, content={"error": "No data in session"})

        pings = [s.ping for s in all_stats]
        jitters = [s.jitter for s in all_stats]
        losses = [s.packet_loss for s in all_stats]

        avg_ping = statistics.mean(pings)
        avg_jitter = statistics.mean(jitters)
        avg_loss = statistics.mean(losses)

        thresholds = settings.get_game_threshold(db, user_id, game)

        score = sum([
            avg_ping > thresholds["ping"],
            avg_jitter > thresholds["jitter"],
            avg_loss > thresholds["loss"]
        ])

        verdict = ["Good", "Average", "Bad"][min(score, 2)]
        optimizer = avg_jitter > thresholds["jitter"] or avg_loss > thresholds["loss"]

        reasons = []
        if avg_ping > thresholds["ping"] and avg_jitter <= thresholds["jitter"]:
            reasons.append("High base latency – distant servers or inefficient ISP routing")
        if avg_jitter > thresholds["jitter"]:
            reasons.append("High jitter – unstable routing or Wi-Fi interference")
        if avg_loss > thresholds["loss"]:
            reasons.append("Packet loss detected – ISP congestion or poor routing")
        if max(pings) - min(pings) > thresholds["ping"]:
            reasons.append("Ping spikes – background downloads or wireless drops")
        if not reasons:
            reasons.append("No major network issues detected")

        db_session.verdict = verdict
        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "verdict": verdict,
                "optimizer": optimizer,
                "reasons": reasons,
                "avg_ping": round(avg_ping, 2),
                "avg_jitter": round(avg_jitter, 2),
                "avg_loss": round(avg_loss, 2),
                "timeline": [
                    {"time": s.timestamp.isoformat(), "ping": s.ping, "jitter": s.jitter, "loss": s.packet_loss}
                    for s in all_stats
                ]
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ================= USER STATISTICS =================
@app.get("/statistics/{user_id}")
def get_statistics(user_id: int, db: Session = Depends(get_db)):
    try:
        all_sessions = db.query(DBSession).filter(DBSession.user_id == user_id).all()

        if not all_sessions:
            return JSONResponse(
                status_code=200,
                content={
                    "total_sessions": 0,
                    "avg_ping": 0,
                    "avg_jitter": 0,
                    "avg_loss": 0,
                    "best_game": "N/A",
                    "worst_game": "N/A",
                    "total_play_time": 0
                }
            )

        all_pings = [s.avg_ping for s in all_sessions if s.avg_ping > 0]
        all_jitters = [s.avg_jitter for s in all_sessions if s.avg_jitter > 0]
        all_losses = [s.avg_loss for s in all_sessions if s.avg_loss > 0]

        total_play_time = sum([
            (s.end_time - s.start_time).total_seconds() / 3600
            for s in all_sessions if s.end_time
        ])

        games = {}
        for sess in all_sessions:
            if sess.game not in games:
                games[sess.game] = []
            games[sess.game].append(sess.avg_ping)

        best_game = min(games.items(), key=lambda x: statistics.mean(x[1]))[0] if games else "N/A"
        worst_game = max(games.items(), key=lambda x: statistics.mean(x[1]))[0] if games else "N/A"

        return JSONResponse(
            status_code=200,
            content={
                "total_sessions": len(all_sessions),
                "avg_ping": round(statistics.mean(all_pings), 2) if all_pings else 0,
                "avg_jitter": round(statistics.mean(all_jitters), 2) if all_jitters else 0,
                "avg_loss": round(statistics.mean(all_losses), 2) if all_losses else 0,
                "best_game": best_game,
                "worst_game": worst_game,
                "total_play_time": round(total_play_time, 2)
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ================= USER SETTINGS =================
@app.get("/settings/{user_id}")
def get_settings(user_id: int, db: Session = Depends(get_db)):
    try:
        thresholds = settings.get_user_thresholds(db, user_id)
        notifications = settings.get_notification_settings(db, user_id)

        return JSONResponse(
            status_code=200,
            content={
                "thresholds": thresholds,
                "notifications": notifications
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.put("/settings/{user_id}")
def update_settings(user_id: int, data: dict, db: Session = Depends(get_db)):
    try:
        if "thresholds" in data:
            for game, threshold in data["thresholds"].items():
                settings.update_game_threshold(
                    db, user_id, game,
                    threshold.get("ping", 100),
                    threshold.get("jitter", 20),
                    threshold.get("loss", 5)
                )

        if "notifications" in data:
            notif = data["notifications"]
            settings.update_notification_settings(
                db, user_id,
                notif.get("notify_on_ping_spike"),
                notif.get("notify_on_jitter_high"),
                notif.get("notify_on_packet_loss"),
                notif.get("ping_alert_threshold")
            )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Settings updated"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

# ================= HEALTH CHECK =================
@app.get("/")
def root():
    return JSONResponse(
        status_code=200,
        content={"status": "LagSense backend running"}
    )

@app.get("/health")
def health():
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"}
    )