# YouTube Video Q&A Assistant (RAG)

Paste a YouTube link, ask questions about the video, and get answers with clickable timestamp links that jump to the exact moment.

## Features
- Fetches the transcript with timestamps (cached locally to avoid repeated YouTube requests)
- Splits it into overlapping, time-based chunks (60s window, 10s overlap) with start/end metadata
- Stores embeddings in a Chroma vector database
- Answers only from the retrieved transcript; says "Not found in the video." when the answer is missing
- Shows clickable timestamp sources, built in code from chunk metadata (not written by the LLM)
- Streamlit UI with clear error messages for missing captions and API failures

## How it works
```
YouTube link -> transcript -> 60s overlapping chunks -> embeddings -> Chroma

Question -> top-k similar chunks -> Gemini (answer only from context)
         -> answer + timestamp links
```

## Tech stack
Python, youtube-transcript-api, LangChain, Chroma, sentence-transformers (all-MiniLM-L6-v2), Gemini, Streamlit

## Project structure
```
src/loader.py       fetch transcript + cache
src/chunker.py      time-based chunking with overlap
src/vectorstore.py  embeddings + Chroma
src/qa.py           prompt + LLM answer + timestamp sources
src/utils.py        helpers
app.py              Streamlit UI
eval/               retrieval evaluation script (experimental)
scripts/            LLM connectivity checks
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```
Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=your_model_name
```
Run:
```bash
streamlit run app.py
```

## Design decisions
- **Timestamp links come from metadata, not the LLM**, so they are never made up.
- **Strict prompt + temperature 0:** the model must answer only from context.
- **LLM errors are shown separately** from "Not found in the video."
- **Transcript cache** reduces YouTube requests and lets demo videos work offline.

## Known limitations
- Videos without captions are not supported.
- YouTube may block transcript requests from cloud IPs.
- Free Gemini tier has low daily limits and model names change over time.
- The small embedding model works best on English.

## Future work
Summary and key points, hybrid search (BM25 + vector), multi-video support, retrieval evaluation (Recall@k).
