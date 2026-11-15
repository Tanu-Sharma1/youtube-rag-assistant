import re

from src.loader import fetch_transcript, TranscriptError
from src.utils import format_time


def clean_text(text: str) -> str:
    """[Music], [Applause] jaise tags hatao, newlines aur extra spaces saaf karo."""
    text = re.sub(r"\[[^\]]*\]", "", text)   # [Music] -> ""
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_transcript(transcript: dict, chunk_seconds: int = 60, overlap_seconds: int = 10) -> list[dict]:
    """
    Transcript ko time-based chunks me todta hai.
    chunk_seconds   = ek chunk kitne second ka (window size)
    overlap_seconds = agle chunk ke saath kitna common
    """
    if overlap_seconds >= chunk_seconds:
        raise ValueError("overlap, chunk size se chhota hona chahiye")

    video_id = transcript["video_id"]

    # 1) Segments saaf karo, khaali text wale hata do
    segs = []
    for s in transcript["segments"]:
        text = clean_text(s["text"])
        if text:
            segs.append({
                "text": text,
                "start": s["start"],
                "end": s["start"] + s["duration"],
            })

    if not segs:
        return []

    step = chunk_seconds - overlap_seconds   # window har baar itna aage khiskega
    window_start = segs[0]["start"]
    last_start = segs[-1]["start"]

    chunks = []
    prev_last_idx = -1   # pichhle chunk ka aakhri segment index

    # 2) Sliding window: [window_start, window_start + chunk_seconds)
    while window_start <= last_start:
        window_end = window_start + chunk_seconds

        # Is window me jin segments ka start aata hai, unke index
        idxs = [i for i, s in enumerate(segs) if window_start <= s["start"] < window_end]

        # Agar idxs khaali hai (lambi silence) ya last segment wahi hai jo pichhle chunk ka tha,
        # to ye chunk pichhle ka hi chhota hissa hoga -> skip
        if idxs and idxs[-1] != prev_last_idx:
            chunk_segs = [segs[i] for i in idxs]
            chunks.append({
                "chunk_id": f"{video_id}_{len(chunks)}",
                "video_id": video_id,
                "start": int(chunk_segs[0]["start"]),
                "end": int(max(s["end"] for s in chunk_segs)),
                "text": " ".join(s["text"] for s in chunk_segs),
            })
            prev_last_idx = idxs[-1]

        window_start += step

    return chunks


# Test: python -m src.chunker
if __name__ == "__main__":
    link = input("YouTube link daalo: ")
    try:
        data = fetch_transcript(link)
    except TranscriptError as e:
        print(f"Error: {e}")
        raise SystemExit

    chunks = chunk_transcript(data, chunk_seconds=60, overlap_seconds=10)
    print(f"\nTotal chunks: {len(chunks)}")
    avg_words = sum(len(c["text"].split()) for c in chunks) / len(chunks)
    print(f"Average words per chunk: {avg_words:.0f}")

    for c in chunks[:2]:
        print(f"\n[{format_time(c['start'])} - {format_time(c['end'])}] ({c['chunk_id']})")
        print(c["text"][:300], "...")