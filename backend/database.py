from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./lagsense.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    display_name = Column(String, default="Gamer")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game = Column(String, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    verdict = Column(String, default="Unknown")
    avg_ping = Column(Float, default=0)
    avg_jitter = Column(Float, default=0)
    avg_loss = Column(Float, default=0)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    stats = relationship("NetworkStat", back_populates="session", cascade="all, delete-orphan")

class NetworkStat(Base):
    __tablename__ = "network_stats"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ping = Column(Float, default=0)
    jitter = Column(Float, default=0)
    packet_loss = Column(Float, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="stats")

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Game thresholds
    valorant_ping = Column(Float, default=60)
    valorant_jitter = Column(Float, default=10)
    valorant_loss = Column(Float, default=1.0)
    
    cs2_ping = Column(Float, default=70)
    cs2_jitter = Column(Float, default=15)
    cs2_loss = Column(Float, default=1.5)
    
    dota2_ping = Column(Float, default=90)
    dota2_jitter = Column(Float, default=20)
    dota2_loss = Column(Float, default=2.0)
    
    fortnite_ping = Column(Float, default=80)
    fortnite_jitter = Column(Float, default=18)
    fortnite_loss = Column(Float, default=2.0)
    
    discord_ping = Column(Float, default=50)
    discord_jitter = Column(Float, default=8)
    discord_loss = Column(Float, default=0.5)
    
    # Notification settings
    notify_on_ping_spike = Column(Boolean, default=True)
    notify_on_jitter_high = Column(Boolean, default=True)
    notify_on_packet_loss = Column(Boolean, default=True)
    ping_alert_threshold = Column(Float, default=150)
    
    # Relationships
    user = relationship("User", back_populates="settings")

def init_db():
    Base.metadata.create_all(bind=engine)