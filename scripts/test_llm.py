"""Make one direct LLM request to check provider configuration and connectivity."""

from src.qa import _response_to_text, get_llm


if __name__ == "__main__":
    try:
        response = get_llm().invoke("Say hello in one word")
        print(_response_to_text(response))
    except Exception as exc:
        print(f"[LLM ERROR] {exc}")
