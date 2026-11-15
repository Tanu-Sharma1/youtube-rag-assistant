import json
import re
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked,
    IpBlocked,
)

# Cache folder: data/cache/ (project root ke relative)
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class TranscriptError(Exception):
    """Hamara apna error, jisme user ko dikhane layak message hota hai."""
    pass


def extract_video_id(url_or_id: str) -> str:
    """
    Alag-alag link formats se 11-character video ID nikalta hai.
    Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ -> dQw4w9WgXcQ
             https://youtu.be/dQw4w9WgXcQ?t=10            -> dQw4w9WgXcQ
    """
    text = url_or_id.strip()

    # Agar user ne seedha ID hi daal di
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", text):
        return text

    # watch?v=ID, youtu.be/ID, shorts/ID, embed/ID, live/ID
    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", text)
    if match:
        return match.group(1)

    raise TranscriptError("Ye valid YouTube link nahi lag raha. Link dobara check karo.")


def _cache_path(video_id: str) -> Path:
    return CACHE_DIR / f"{video_id}.json"


def fetch_transcript(url_or_id: str, languages=("en", "hi")) -> dict:
    """
    Transcript laata hai. Return format:
    {
      "video_id": "...",
      "language": "en",
      "segments": [{"text": "...", "start": 12.3, "duration": 4.1}, ...]
    }
    """
    video_id = extract_video_id(url_or_id)

    # 1) Pehle cache check karo
    cache_file = _cache_path(video_id)
    if cache_file.exists():
        print(f"[cache] {video_id} cache se load hua")
        return json.loads(cache_file.read_text(encoding="utf-8"))

    # 2) Cache me nahi hai, to YouTube se lao
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)  # is video ke saare available transcripts

        try:
            # Manual ya auto-generated, jo bhi hamari languages me mile
            transcript = transcript_list.find_transcript(list(languages))
        except NoTranscriptFound:
            # Hamari languages nahi mili -> jo pehla available hai wo le lo
            transcript = next(iter(transcript_list))

        fetched = transcript.fetch()
        segments = fetched.to_raw_data()  # list of {"text", "start", "duration"}
        language = transcript.language_code

    except TranscriptsDisabled:
        raise TranscriptError("Is video me captions band hain (disabled). Koi aur video try karo.")
    except NoTranscriptFound:
        raise TranscriptError("Is video ka koi transcript nahi mila.")
    except VideoUnavailable:
        raise TranscriptError("Video unavailable hai (private / deleted / region-locked).")
    except (RequestBlocked, IpBlocked):
        raise TranscriptError(
            "YouTube ne request block kar di (cloud/IP block). "
            "Local machine pe chalao, ya pehle se cached demo video use karo."
        )
    except StopIteration:
        raise TranscriptError("Is video ke liye koi caption track available nahi hai.")

    result = {"video_id": video_id, "language": language, "segments": segments}

    # 3) Cache me save karo
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[youtube] {video_id} fetch hua aur cache me save hua")
    return result


# Sirf test ke liye: python -m src.loader
if __name__ == "__main__":
    link = input("YouTube link daalo: ")
    try:
        data = fetch_transcript(link)
        print(f"\nVideo ID : {data['video_id']}")
        print(f"Language : {data['language']}")
        print(f"Segments : {len(data['segments'])}")
        print("\nPehle 3 segments:")
        for seg in data["segments"][:3]:
            print(f"  [{seg['start']:.1f}s] {seg['text']}")
    except TranscriptError as e:
        print(f"\nError: {e}")