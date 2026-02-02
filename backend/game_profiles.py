GAME_PROFILES = {
    "valorant": {
        "max_ping": 60,
        "max_jitter": 5,
        "loss_warning": 1.0,
        "desc": "Highly sensitive to jitter and packet loss"
    },
    "cs2": {
        "max_ping": 80,
        "max_jitter": 10,
        "loss_warning": 2.0,
        "desc": "Moderate tolerance, stable routing preferred"
    },
    "fortnite": {
        "max_ping": 100,
        "max_jitter": 15,
        "loss_warning": 3.0,
        "desc": "High tolerance, but spikes affect builds"
    },
    "dota2": {
        "max_ping": 90,
        "max_jitter": 8,
        "loss_warning": 1.5,
        "desc": "Stable latency critical for team fights"
    }
}
