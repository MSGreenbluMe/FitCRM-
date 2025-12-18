import email
import imaplib
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from email.header import decode_header
from email.message import Message
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ImapAccount:
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = True
    starttls: bool = False


def test_imap_connection(account: ImapAccount, mailbox: str = "INBOX") -> Tuple[bool, Optional[str]]:
    try:
        client = _connect(account)
        try:
            client.select(mailbox, readonly=True)
            return True, None
        finally:
            try:
                client.logout()
            except Exception:
                pass
    except Exception as e:
        return False, str(e)


def fetch_imap_messages(
    account: ImapAccount,
    mailbox: str = "INBOX",
    limit: int = 20,
) -> List[Dict[str, Any]]:
    client = _connect(account)
    try:
        status, _ = client.select(mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Failed to select mailbox: {mailbox}")

        status, data = client.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            return []

        msg_ids = data[0].split()
        msg_ids = msg_ids[-limit:]

        out: List[Dict[str, Any]] = []
        for msg_id in reversed(msg_ids):
            status, msg_data = client.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data:
                continue

            raw_bytes = None
            for part in msg_data:
                if isinstance(part, tuple) and len(part) >= 2:
                    raw_bytes = part[1]
                    break
            if not raw_bytes:
                continue

            parsed = email.message_from_bytes(raw_bytes)
            out.append(
                {
                    "uid": msg_id.decode("utf-8", errors="ignore"),
                    "subject": _decode_mime_header(parsed.get("Subject")),
                    "from": _decode_mime_header(parsed.get("From")),
                    "date": _parse_email_date(parsed.get("Date")),
                    "body": _extract_text_body(parsed),
                }
            )

        return out
    finally:
        try:
            client.logout()
        except Exception:
            pass


def _connect(account: ImapAccount):
    if account.use_ssl:
        client = imaplib.IMAP4_SSL(account.host, account.port)
        client.login(account.username, account.password)
        return client

    client = imaplib.IMAP4(account.host, account.port)
    if account.starttls:
        context = ssl.create_default_context()
        client.starttls(ssl_context=context)
    client.login(account.username, account.password)
    return client


def _decode_mime_header(value: Optional[str]) -> str:
    if not value:
        return ""

    decoded = decode_header(value)
    parts: List[str] = []
    for chunk, enc in decoded:
        if isinstance(chunk, bytes):
            try:
                parts.append(chunk.decode(enc or "utf-8", errors="replace"))
            except Exception:
                parts.append(chunk.decode("utf-8", errors="replace"))
        else:
            parts.append(str(chunk))

    return "".join(parts).strip()


def _parse_email_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    try:
        dt = email.utils.parsedate_to_datetime(value)
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _extract_text_body(msg: Message) -> str:
    if msg.is_multipart():
        text_parts: List[str] = []
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition", "")
            if content_type == "text/plain" and "attachment" not in content_disposition.lower():
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                try:
                    text_parts.append(payload.decode(charset, errors="replace"))
                except Exception:
                    text_parts.append(payload.decode("utf-8", errors="replace"))
        if text_parts:
            return "\n".join([p.strip() for p in text_parts if p and p.strip()]).strip()

    payload = msg.get_payload(decode=True)
    if not payload:
        return ""

    charset = msg.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace").strip()
    except Exception:
        return payload.decode("utf-8", errors="replace").strip()
