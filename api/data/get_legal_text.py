#!/usr/bin/env python3
"""
Utility to retrieve and parse legal text from links on www.gesetze-im-internet.de.
Example link: https://www.gesetze-im-internet.de/stvzo_2012/__19.html
"""

import urllib.request
import urllib.error
from html.parser import HTMLParser


class LegalTextParser(HTMLParser):
    """
    HTMLParser subclass optimized for parsing single section pages (Einzelnorm)
    from www.gesetze-im-internet.de.
    """
    def __init__(self):
        super().__init__()
        self.in_header = False
        self.in_body = False
        self.in_h1 = False
        self.in_jnenbez = False
        self.in_jnentitel = False
        
        self.law_name_parts = []
        self.jnenbez_parts = []
        self.jnentitel_parts = []
        
        self.paragraphs = []
        self.current_paragraph = []
        
        self.div_stack = []

    def ensure_spacing(self, newline=False):
        if not self.current_paragraph:
            return
        last = self.current_paragraph[-1]
        if newline:
            if not last.endswith("\n"):
                self.current_paragraph.append("\n")
        else:
            if last and not last[-1].isspace():
                self.current_paragraph.append(" ")

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "div":
            classes = attrs_dict.get("class", "").split()
            self.div_stack.append(classes)
            if "jnheader" in classes:
                self.in_header = True
            if "jnhtml" in classes:
                self.in_body = True
            if "jurAbsatz" in classes:
                self.flush_paragraph()
                
        elif tag == "h1" and self.in_header:
            self.in_h1 = True
            
        elif tag == "span" and self.in_h1:
            classes = attrs_dict.get("class", "").split()
            if "jnenbez" in classes:
                self.in_jnenbez = True
            elif "jnentitel" in classes:
                self.in_jnentitel = True
                
        elif tag in ("dl", "ol", "ul") and self.in_body:
            self.ensure_spacing(newline=True)
        elif tag == "dt" and self.in_body:
            self.ensure_spacing(newline=True)
            self.current_paragraph.append("  ")
        elif tag == "dd" and self.in_body:
            self.ensure_spacing(newline=False)
        elif tag == "br" and self.in_body:
            self.ensure_spacing(newline=True)

    def handle_endtag(self, tag):
        if tag == "div":
            if self.div_stack:
                classes = self.div_stack.pop()
                if "jnheader" in classes:
                    self.in_header = False
                if "jnhtml" in classes:
                    self.in_body = False
                if "jurAbsatz" in classes:
                    self.flush_paragraph()
                    
        elif tag == "h1":
            self.in_h1 = False
        elif tag == "span":
            self.in_jnenbez = False
            self.in_jnentitel = False
            
        elif tag in ("dl", "ol", "ul", "dd", "dt") and self.in_body:
            self.ensure_spacing(newline=False)

    def handle_data(self, data):
        # Normalize non-breaking spaces
        data_norm = data.replace('\xa0', ' ')
        
        if self.in_header and self.in_h1:
            if self.in_jnenbez:
                self.jnenbez_parts.append(data_norm)
            elif self.in_jnentitel:
                self.jnentitel_parts.append(data_norm)
            else:
                self.law_name_parts.append(data_norm)
                
        elif self.in_body:
            if self.current_paragraph:
                last = self.current_paragraph[-1]
                if last.endswith("\n") or last.endswith(" "):
                    data_norm = data_norm.lstrip()
            if data_norm:
                self.current_paragraph.append(data_norm)

    def flush_paragraph(self):
        if self.current_paragraph:
            text = "".join(self.current_paragraph)
            lines = []
            for line in text.split("\n"):
                cleaned = " ".join(line.split())
                if cleaned:
                    indent = ""
                    if line.startswith(" "):
                        indent = "  "
                    lines.append(indent + cleaned)
            paragraph_text = "\n".join(lines)
            if paragraph_text:
                self.paragraphs.append(paragraph_text)
            self.current_paragraph = []

    def get_formatted_text(self) -> str:
        self.flush_paragraph()
        
        law_name = " ".join(self.law_name_parts).strip()
        jnenbez = " ".join(self.jnenbez_parts).strip()
        jnentitel = " ".join(self.jnentitel_parts).strip()
        
        title_lines = []
        if jnenbez or jnentitel:
            full_sec = f"{jnenbez} {jnentitel}".strip()
            if law_name:
                title_lines.append(f"{full_sec} ({law_name})")
            else:
                title_lines.append(full_sec)
        elif law_name:
            title_lines.append(law_name)
            
        body_text = "\n\n".join(self.paragraphs)
        
        full_text = "\n".join(title_lines) + "\n\n" + body_text
        return full_text.strip()


def get_legal_text(url: str) -> str:
    """
    Retrieves and parses the legal text from the given gesetze-im-internet.de URL.
    
    Args:
        url: The URL to the legal text page (e.g. a .html page).
        
    Returns:
        The formatted plain text/markdown version of the section.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            # Detect encoding from headers (usually 'iso-8859-1')
            content_type = response.headers.get("Content-Type", "")
            encoding = "iso-8859-1"
            if "charset=" in content_type:
                for part in content_type.split(";"):
                    if "charset=" in part:
                        encoding = part.split("=")[-1].strip()
                        break
            
            raw_html = response.read()
            html_content = raw_html.decode(encoding, errors="replace")
            
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to fetch legal URL {url}: {e}")
        
    parser = LegalTextParser()
    parser.feed(html_content)
    return parser.get_formatted_text()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python get_legal_text.py <url>")
        sys.exit(1)
        
    url_to_fetch = sys.argv[1]
    try:
        result = get_legal_text(url_to_fetch)
        print(result)
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)
