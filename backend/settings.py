from sqlalchemy.orm import Session
from database import User, UserSettings

# Default game thresholds
DEFAULT_THRESHOLDS = {
    "valorant": {"ping": 60, "jitter": 10, "loss": 1.0},
    "cs2": {"ping": 70, "jitter": 15, "loss": 1.5},
    "dota2": {"ping": 90, "jitter": 20, "loss": 2.0},
    "fortnite": {"ping": 80, "jitter": 18, "loss": 2.0},
    "discord": {"ping": 50, "jitter": 8, "loss": 0.5},
}

def get_or_create_user_settings(db: Session, user_id: int) -> UserSettings:
    """Get user settings or create defaults"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings

def get_user_thresholds(db: Session, user_id: int) -> dict:
    """Get all game thresholds for a user"""
    settings = get_or_create_user_settings(db, user_id)
    
    return {
        "valorant": {"ping": settings.valorant_ping, "jitter": settings.valorant_jitter, "loss": settings.valorant_loss},
        "cs2": {"ping": settings.cs2_ping, "jitter": settings.cs2_jitter, "loss": settings.cs2_loss},
        "dota2": {"ping": settings.dota2_ping, "jitter": settings.dota2_jitter, "loss": settings.dota2_loss},
        "fortnite": {"ping": settings.fortnite_ping, "jitter": settings.fortnite_jitter, "loss": settings.fortnite_loss},
        "discord": {"ping": settings.discord_ping, "jitter": settings.discord_jitter, "loss": settings.discord_loss},
    }

def get_game_threshold(db: Session, user_id: int, game: str) -> dict:
    """Get threshold for specific game"""
    thresholds = get_user_thresholds(db, user_id)
    return thresholds.get(game, DEFAULT_THRESHOLDS.get(game, {"ping": 100, "jitter": 20, "loss": 5}))

def update_game_threshold(db: Session, user_id: int, game: str, ping: float, jitter: float, loss: float) -> bool:
    """Update threshold for specific game"""
    settings = get_or_create_user_settings(db, user_id)
    
    game_key = game.lower()
    
    if game_key == "valorant":
        settings.valorant_ping = ping
        settings.valorant_jitter = jitter
        settings.valorant_loss = loss
    elif game_key == "cs2":
        settings.cs2_ping = ping
        settings.cs2_jitter = jitter
        settings.cs2_loss = loss
    elif game_key == "dota2":
        settings.dota2_ping = ping
        settings.dota2_jitter = jitter
        settings.dota2_loss = loss
    elif game_key == "fortnite":
        settings.fortnite_ping = ping
        settings.fortnite_jitter = jitter
        settings.fortnite_loss = loss
    elif game_key == "discord":
        settings.discord_ping = ping
        settings.discord_jitter = jitter
        settings.discord_loss = loss
    else:
        return False
    
    db.commit()
    return True

def update_notification_settings(db: Session, user_id: int, 
                                notify_ping: bool = None,
                                notify_jitter: bool = None,
                                notify_loss: bool = None,
                                alert_threshold: float = None) -> bool:
    """Update notification preferences"""
    settings = get_or_create_user_settings(db, user_id)
    
    if notify_ping is not None:
        settings.notify_on_ping_spike = notify_ping
    if notify_jitter is not None:
        settings.notify_on_jitter_high = notify_jitter
    if notify_loss is not None:
        settings.notify_on_packet_loss = notify_loss
    if alert_threshold is not None:
        settings.ping_alert_threshold = alert_threshold
    
    db.commit()
    return True

def get_notification_settings(db: Session, user_id: int) -> dict:
    """Get notification settings for user"""
    settings = get_or_create_user_settings(db, user_id)
    
    return {
        "notify_on_ping_spike": settings.notify_on_ping_spike,
        "notify_on_jitter_high": settings.notify_on_jitter_high,
        "notify_on_packet_loss": settings.notify_on_packet_loss,
        "ping_alert_threshold": settings.ping_alert_threshold,
    }