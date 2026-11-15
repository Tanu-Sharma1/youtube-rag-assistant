from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from src.loader import fetch_transcript, TranscriptError
from src.chunker import chunk_transcript
from src.utils import format_time

CHROMA_DIR = str(Path(__file__).resolve().parent.parent / "data" / "chroma_db")
COLLECTION_NAME = "youtube_videos"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings = None  # model ek hi baar load hoga (slow hai)
_vectorstore = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embeddings


def get_vectorstore() -> Chroma:
    """Chroma DB open karta hai (nahi hai to banata hai). Data disk pe save rehta hai."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_DIR,
        )
    return _vectorstore


def is_video_indexed(video_id: str) -> bool:
    store = get_vectorstore()
    found = store.get(where={"video_id": video_id}, limit=1)
    return len(found["ids"]) > 0


def index_video(chunks: list[dict]) -> int:
    """Chunks ko embeddings banake Chroma me store karta hai. Kitne chunks daale wo return karta hai."""
    if not chunks:
        return 0

    video_id = chunks[0]["video_id"]
    if is_video_indexed(video_id):
        print(f"[chroma] {video_id} pehle se indexed hai, skip")
        return 0

    docs = [
        Document(
            page_content=c["text"],
            metadata={
                "chunk_id": c["chunk_id"],
                "video_id": c["video_id"],
                "start": c["start"],   # Chroma metadata me sirf str/int/float/bool allowed
                "end": c["end"],
            },
        )
        for c in chunks
    ]
    ids = [c["chunk_id"] for c in chunks]

    store = get_vectorstore()
    store.add_documents(docs, ids=ids)
    print(f"[chroma] {len(docs)} chunks index hue")
    return len(docs)


def search(query: str, k: int = 4, video_id: str | None = None):
    """Sawaal ke sabse similar top-k chunks. Return: [(Document, score), ...]"""
    store = get_vectorstore()
    flt = {"video_id": video_id} if video_id else None
    return store.similarity_search_with_score(query, k=k, filter=flt)


# Test: python -m src.vectorstore
if __name__ == "__main__":
    link = input("YouTube link daalo: ")
    try:
        data = fetch_transcript(link)
    except TranscriptError as e:
        print(f"Error: {e}")
        raise SystemExit

    chunks = chunk_transcript(data, chunk_seconds=60, overlap_seconds=10)
    index_video(chunks)

    print("\nAb sawaal poocho (khatam karne ke liye 'q' likho)")
    while True:
        q = input("\nSawaal: ").strip()
        if q.lower() == "q":
            break
        for doc, score in search(q, k=3, video_id=data["video_id"]):
            m = doc.metadata
            print(f"\n[{format_time(m['start'])} - {format_time(m['end'])}] score={score:.3f}")
            print(doc.page_content[:250], "...")
