from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# ================= USER MODELS =================
class UserBase(BaseModel):
    email: str
    display_name: Optional[str] = "Gamer"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ================= AUTH MODELS =================
class AuthRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    user_id: Optional[int] = None
    message: Optional[str] = None

# ================= NETWORK STAT MODELS =================
class NetworkStatCreate(BaseModel):
    user_id: int
    game: str
    ping: float
    jitter: float
    loss: float
    timestamp: datetime

class NetworkStatResponse(BaseModel):
    id: int
    session_id: int
    ping: float
    jitter: float
    packet_loss: float
    timestamp: datetime

    class Config:
        from_attributes = True

# ================= SESSION MODELS =================
class SessionCreate(BaseModel):
    user_id: int
    game: str

class SessionUpdate(BaseModel):
    verdict: Optional[str] = None
    end_time: Optional[datetime] = None

class SessionResponse(BaseModel):
    id: int
    user_id: int
    game: str
    start_time: datetime
    end_time: Optional[datetime] = None
    verdict: Optional[str] = None
    avg_ping: float
    avg_jitter: float
    avg_loss: float

    class Config:
        from_attributes = True

class SessionDetailResponse(SessionResponse):
    stats: List[NetworkStatResponse]

# ================= SETTINGS MODELS =================
class GameThresholds(BaseModel):
    ping: float
    jitter: float
    loss: float

class UserSettingsResponse(BaseModel):
    valorant: GameThresholds
    cs2: GameThresholds
    dota2: GameThresholds
    fortnite: GameThresholds
    discord: GameThresholds
    notify_on_ping_spike: bool
    notify_on_jitter_high: bool
    notify_on_packet_loss: bool
    ping_alert_threshold: float

class UserSettingsUpdate(BaseModel):
    valorant: Optional[GameThresholds] = None
    cs2: Optional[GameThresholds] = None
    dota2: Optional[GameThresholds] = None
    fortnite: Optional[GameThresholds] = None
    discord: Optional[GameThresholds] = None
    notify_on_ping_spike: Optional[bool] = None
    notify_on_jitter_high: Optional[bool] = None
    notify_on_packet_loss: Optional[bool] = None
    ping_alert_threshold: Optional[float] = None

# ================= STATS MODELS =================
class StatisticsResponse(BaseModel):
    total_sessions: int
    avg_ping: float
    avg_jitter: float
    avg_loss: float
    best_game: str
    worst_game: str
    total_play_time: float  # in hours

class GameStatistics(BaseModel):
    game: str
    sessions_count: int
    avg_ping: float
    avg_jitter: float
    avg_loss: float
    worst_ping: float
    best_ping: float
    verdict_good: int
    verdict_average: int
    verdict_bad: int

# ================= VERDICT MODELS =================
class VerdictResponse(BaseModel):
    verdict: str
    optimizer: bool
    reasons: List[str]
    timeline: List[dict]
    avg_ping: float
    avg_jitter: float
    avg_loss: float

# ================= NOTIFICATION MODELS =================
class NotificationEvent(BaseModel):
    type: str  # "ping_spike", "jitter_high", "packet_loss"
    game: str
    value: float
    threshold: float
    timestamp: datetime
    message: str