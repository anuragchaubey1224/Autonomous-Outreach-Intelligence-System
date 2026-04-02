"""Decision Agent: classify reply text into POSITIVE, NEUTRAL, or NEGATIVE."""

from app.agents.message_agent import generate_text


VALID_INTENTS = {"POSITIVE", "NEUTRAL", "NEGATIVE"}


def classify_reply(reply_text: str) -> str:
    """
    Classify an email reply into POSITIVE, NEUTRAL, or NEGATIVE.

    Defaults to NEUTRAL if model output is invalid.
    """
    prompt = (
        "Classify this reply into one of three categories:\n"
        "POSITIVE, NEUTRAL, NEGATIVE\n\n"
        f"Reply:\n{reply_text}\n\n"
        "Only return one word."
    )

    print("Classifying reply...")

    try:
        raw_output = generate_text(prompt)
    except Exception:
        return "NEUTRAL"

    intent = (raw_output or "").strip().upper()
    if intent not in VALID_INTENTS:
        intent = "NEUTRAL"

    print(f"Intent detected: {intent}")
    return intent
