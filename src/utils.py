def format_time(seconds: float) -> str:
    """755 -> '12:35', 3725 -> '1:02:05'"""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def make_timestamp_url(video_id: str, start_seconds: float) -> str:
    """Video ID + second se clickable YouTube link banata hai."""
    return f"https://www.youtube.com/watch?v={video_id}&t={int(start_seconds)}s"