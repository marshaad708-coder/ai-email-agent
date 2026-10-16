"""IMAP inbox agent: fetch unread mail, classify, draft/archive."""

import email
import imaplib
from email.header import decode_header
from email.message import EmailMessage

from .classifier import classify


def _decode(value):
    if value is None:
        return ""
    parts = decode_header(value)
    out = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            out += text.decode(enc or "utf-8", errors="ignore")
        else:
            out += text
    return out


def _snippet(msg: EmailMessage, limit: int = 300) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_content()[:limit]
                except Exception:
                    continue
        return ""
    try:
        return msg.get_content()[:limit]
    except Exception:
        return ""


class InboxAgent:
    def __init__(self, host, email_addr, password, use_llm=False, llm_model="llama3.1"):
        self.host = host
        self.email_addr = email_addr
        self.password = password
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.imap = None

    def connect(self):
        self.imap = imaplib.IMAP4_SSL(self.host)
        self.imap.login(self.email_addr, self.password)
        self.imap.select("INBOX")

    def close(self):
        try:
            self.imap.close()
        except Exception:
            pass
        try:
            self.imap.logout()
        except Exception:
            pass

    def fetch_unread(self, limit=20):
        _typ, data = self.imap.search(None, "UNSEEN")
        ids = data[0].split()[:limit]
        messages = []
        for num in ids:
            _typ, data = self.imap.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1], policy=email.policy.default)
            messages.append((num, {
                "from": _decode(msg["From"]),
                "subject": _decode(msg["Subject"]),
                "snippet": _snippet(msg),
                "date": _decode(msg["Date"]),
            }))
        return messages

    def draft_reply(self, original, draft_text: str, dry_run: bool):
        """File a reply draft. In dry-run mode, just report it."""
        if dry_run:
            return f"[dry-run] would draft reply to '{original['subject']}'"
        reply = EmailMessage()
        reply["From"] = self.email_addr
        reply["To"] = original["from"]
        reply["Subject"] = "Re: " + original["subject"]
        reply.set_content(draft_text)
        self.imap.append("[Gmail]/Drafts", None, None, reply.as_bytes())
        return f"draft filed for '{original['subject']}'"

    def archive(self, num: bytes, dry_run: bool):
        if dry_run:
            return "[dry-run] would archive message"
        self.imap.store(num, "+X-GM-LABELS", "\\Trash")
        return "archived"

    def run(self, limit=20, dry_run=True):
        """Process unread mail. Returns a list of (subject, label, action) tuples."""
        self.connect()
        try:
            report = []
            for num, meta in self.fetch_unread(limit):
                label = classify(meta["subject"], meta["from"], meta["snippet"],
                                 use_llm=self.use_llm, model=self.llm_model)
                if label == "urgent":
                    draft = (
                        f"Hi,\n\nThanks for your email about "
                        f"\"{meta['subject']}\". I'll review this and get back "
                        f"to you shortly.\n\nBest regards"
                    )
                    action = self.draft_reply(meta, draft, dry_run)
                elif label == "spam":
                    action = self.archive(num, dry_run)
                else:
                    action = "left in inbox"
                report.append((meta["subject"][:60], label, action))
            return report
        finally:
            self.close()
