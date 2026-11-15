import streamlit as st

from src.chunker import chunk_transcript
from src.loader import TranscriptError, fetch_transcript
from src.qa import answer_question, get_llm
from src.vectorstore import get_embeddings, index_video


st.set_page_config(page_title="YouTube Video Q&A", page_icon="🎥")
st.title("YouTube Video Q&A Assistant")
st.write("Add a video, index its transcript, then ask questions about it.")


@st.cache_resource
def cached_embeddings():
    """Load the embedding model once; Streamlit reuses it between reruns."""
    return get_embeddings()


@st.cache_resource
def cached_llm():
    """Reuse one configured Gemini or Ollama model for all chat turns."""
    return get_llm()


if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

video_url = st.text_input("YouTube video link", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Index video", type="primary"):
    if not video_url.strip():
        st.warning("Paste a YouTube video link first.")
    else:
        try:
            with st.spinner("Loading transcript and indexing the video..."):
                transcript = fetch_transcript(video_url.strip())
                chunks = chunk_transcript(transcript, chunk_seconds=60, overlap_seconds=10)
                if not chunks:
                    st.error("This video transcript has no usable caption text.")
                else:
                    # Warm the cached embedding model before the vector store uses it.
                    cached_embeddings()
                    count = index_video(chunks)
                    st.session_state.video_id = transcript["video_id"]
                    st.session_state.messages = []
                    if count:
                        st.success(f"Indexed {count} transcript chunks for {transcript['video_id']}.")
                    else:
                        st.success(f"Video {transcript['video_id']} is already indexed and ready.")
        except TranscriptError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not index this video: {exc}")

if st.session_state.video_id:
    st.caption(f"Current video: {st.session_state.video_id}")

# Replay saved messages after each Streamlit rerun.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        for source in message.get("sources", []):
            st.markdown(f"[Source: {source['label']}]({source['url']})")

question = st.chat_input("Ask a question about the indexed video")
if question:
    if not st.session_state.video_id:
        st.warning("Index a video before asking a question.")
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            answer_placeholder = st.empty()
            partial_answer = [""]

            def show_token(token):
                partial_answer[0] += token
                answer_placeholder.markdown(partial_answer[0])

            with st.spinner("Searching the transcript and writing an answer..."):
                try:
                    cached_embeddings()
                    result = answer_question(
                        question,
                        video_id=st.session_state.video_id,
                        llm=cached_llm(),
                        on_token=show_token,
                    )
                except Exception as exc:
                    result = {"answer": f"[APP ERROR] {exc}", "sources": []}

            # Replace streamed text with the final answer or a clear error message.
            if result["answer"].startswith("[LLM ERROR]"):
                answer_placeholder.empty()
                st.error(result["answer"])
            else:
                answer_placeholder.markdown(result["answer"])
            # answer_question returns no sources for missing answers and LLM errors.
            for source in result["sources"]:
                st.markdown(f"[Source: {source['label']}]({source['url']})")
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
            })
