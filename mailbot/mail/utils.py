from email import message_from_string
from email.message import Message
import html2text

from email import message_from_string
from email.message import Message
import html2text

def extract_best_body(raw_email: str) -> str:
    try:
        if raw_email.lstrip().lower().startswith('<!doctype') or raw_email.lstrip().lower().startswith('<html'):
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.bypass_tables = False
            h.body_width = 0
            return h.handle(raw_email).strip()

        msg: Message = message_from_string(raw_email)

        if msg.is_multipart():
            plain = html = None

            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    continue

                ctype = part.get_content_type()
                charset = part.get_content_charset() or 'utf-8'
                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                try:
                    content = payload.decode(charset, errors='replace')
                except Exception:
                    content = payload.decode('utf-8', errors='replace')

                if ctype == 'text/plain' and not plain:
                    plain = content
                elif ctype == 'text/html' and not html:
                    html = content

            if plain:
                return plain.strip()
            elif html:
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                h.bypass_tables = False
                h.body_width = 0
                return h.handle(html).strip()
        else:
            ctype = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if not payload:
                return raw_email.strip()

            charset = msg.get_content_charset() or 'utf-8'
            try:
                content = payload.decode(charset, errors='replace')
            except Exception:
                content = payload.decode('utf-8', errors='replace')

            if ctype == 'text/plain':
                return content.strip()
            elif ctype == 'text/html':
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                h.bypass_tables = False
                h.body_width = 0
                return h.handle(content).strip()
    except Exception:
        pass

    # Fallback: return raw if all else fails
    return raw_email.strip()
