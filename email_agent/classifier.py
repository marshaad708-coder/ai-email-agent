"""Email classifier: fast rule-based pass, optional Ollama LLM for the hard ones."""

import re

URGENT_KEYWORDS = [
    "urgent", "asap", "immediately", "deadline", "action required",
    "payment due", "invoice", "contract", "interview", "offer letter",
    "server down", "outage", "security alert", "account locked",
]

SPAM_KEYWORDS = [
    "unsubscribe", "limited time offer", "act now", "congratulations you won",
    "crypto giveaway", "double your", "risk-free", "no cost",
    "viagra", "lottery", "inheritance",
]

NEWSLETTER_HINTS = ["newsletter", "digest", "weekly roundup", "no-reply", "noreply"]


def classify_rulebased(subject: str, sender: str, snippet: str) -> str:
    """Return 'urgent', 'spam', or 'personal'."""
    text = f"{subject} {snippet}".lower()
    if any(k in text for k in SPAM_KEYWORDS):
        return "spam"
    if any(k in text for k in URGENT_KEYWORDS):
        return "urgent"
    if any(h in sender.lower() for h in NEWSLETTER_HINTS):
        return "spam"
    return "personal"


def classify_llm(subject: str, sender: str, snippet: str,
                 model: str = "llama3.1", timeout: int = 30) -> str:
    """Ask a local Ollama model. Falls back to rule-based on any failure."""
    try:
        import ollama
        prompt = (
            "Classify this email as exactly one word: urgent, spam, or personal.\n"
            f"From: {sender}\nSubject: {subject}\nPreview: {snippet}\n"
            "Answer with only the word."
        )
        resp = ollama.generate(model=model, prompt=prompt,
                               options={"temperature": 0})
        word = re.search(r"(urgent|spam|personal)",
                         resp["response"].lower())
        return word.group(1) if word else classify_rulebased(subject, sender, snippet)
    except Exception:
        return classify_rulebased(subject, sender, snippet)


def classify(subject: str, sender: str, snippet: str, use_llm: bool = False,
             model: str = "llama3.1") -> str:
    label = classify_rulebased(subject, sender, snippet)
    # Only spend LLM time on the ambiguous ones.
    if use_llm and label == "personal":
        return classify_llm(subject, sender, snippet, model=model)
    return label
