#!/usr/bin/env python3
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from data.get_legal_text import LegalTextParser, get_legal_text


class TestLegalTextParser(unittest.TestCase):
    def test_empty_html(self):
        parser = LegalTextParser()
        parser.feed("")
        self.assertEqual(parser.get_formatted_text(), "")

    def test_header_parsing_full(self):
        html = """
        <div class="jnheader">
            <h1>
                <span class="jnenbez">§ 19</span>
                <span class="jnentitel">Erteilung und Wirksamkeit der Betriebserlaubnis</span>
                Straßenverkehrs-Zulassungs-Ordnung (StVZO)
            </h1>
        </div>
        """
        parser = LegalTextParser()
        parser.feed(html)
        expected = "§ 19 Erteilung und Wirksamkeit der Betriebserlaubnis (Straßenverkehrs-Zulassungs-Ordnung (StVZO))"
        self.assertEqual(parser.get_formatted_text(), expected)

    def test_header_parsing_no_law_name(self):
        html = """
        <div class="jnheader">
            <h1>
                <span class="jnenbez">§ 19</span>
                <span class="jnentitel">Erteilung und Wirksamkeit</span>
            </h1>
        </div>
        """
        parser = LegalTextParser()
        parser.feed(html)
        expected = "§ 19 Erteilung und Wirksamkeit"
        self.assertEqual(parser.get_formatted_text(), expected)

    def test_header_parsing_only_law_name(self):
        html = """
        <div class="jnheader">
            <h1>Straßenverkehrs-Zulassungs-Ordnung</h1>
        </h1>
        """
        parser = LegalTextParser()
        parser.feed(html)
        expected = "Straßenverkehrs-Zulassungs-Ordnung"
        self.assertEqual(parser.get_formatted_text(), expected)

    def test_paragraphs_and_body_content(self):
        html = """
        <div class="jnhtml">
            <div class="jurAbsatz">Absatz 1 text with some spaces.</div>
            <div class="jurAbsatz">Absatz 2 text with&nbsp;non-breaking&nbsp;spaces.</div>
        </div>
        """
        parser = LegalTextParser()
        parser.feed(html)
        # Note: Non-breaking spaces should be replaced with regular spaces
        expected = "\n\nAbsatz 1 text with some spaces.\n\nAbsatz 2 text with non-breaking spaces."
        self.assertEqual(parser.get_formatted_text().strip(), expected.strip())

    def test_lists_and_br_tags(self):
        html = """
        <div class="jnhtml">
            <div class="jurAbsatz">
                Normal paragraph introduction.
                <dl>
                    <dt>1.</dt>
                    <dd>First list item content.</dd>
                    <dt>2.</dt>
                    <dd>Second list item content with <br/>a line break inside.</dd>
                </dl>
            </div>
        </div>
        """
        parser = LegalTextParser()
        parser.feed(html)
        expected = (
            "Normal paragraph introduction.\n"
            "  1. First list item content.\n"
            "  2. Second list item content with\n"
            "a line break inside."
        )
        self.assertEqual(parser.get_formatted_text().strip(), expected.strip())

    def test_div_nesting_stack(self):
        html = """
        <div class="jnheader">
            <h1><span class="jnenbez">§ 1</span> Title</h1>
            <div class="other">This should be ignored since we are not in_body or in_header tags we care about.</div>
        </div>
        <div class="jnhtml">
            <div class="jurAbsatz">Inside body</div>
        </div>
        """
        parser = LegalTextParser()
        parser.feed(html)
        expected = "§ 1 (Title)\n\nInside body"
        self.assertEqual(parser.get_formatted_text().strip(), expected.strip())


class TestGetLegalText(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_get_legal_text_utf8(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_response.read.return_value = (
            b'<div class="jnheader"><h1><span class="jnenbez">\xc2\xa7 19</span> Title</h1></div>'
            b'<div class="jnhtml"><div class="jurAbsatz">UTF-8 Umlaut: \xc3\xa4\xc3\xb6\xc3\xbc</div></div>'
        )
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = get_legal_text("http://example.com/law.html")
        expected = "§ 19 (Title)\n\nUTF-8 Umlaut: äöü"
        self.assertEqual(res, expected)

    @patch("urllib.request.urlopen")
    def test_get_legal_text_iso8859(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html; charset=iso-8859-1"}
        mock_response.read.return_value = (
            b'<div class="jnheader"><h1><span class="jnenbez">\xa7 19</span> Title</h1></div>'
            b'<div class="jnhtml"><div class="jurAbsatz">ISO Umlaut: \xe4\xf6\xfc</div></div>'
        )
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = get_legal_text("http://example.com/law.html")
        expected = "§ 19 (Title)\n\nISO Umlaut: äöü"
        self.assertEqual(res, expected)

    @patch("urllib.request.urlopen")
    def test_get_legal_text_default_encoding(self, mock_urlopen):
        # Setup mock response with no explicit charset in Content-Type (defaults to iso-8859-1)
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.read.return_value = (
            b'<div class="jnheader"><h1><span class="jnenbez">\xa7 19</span> Title</h1></div>'
            b'<div class="jnhtml"><div class="jurAbsatz">Default Umlaut: \xe4</div></div>'
        )
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = get_legal_text("http://example.com/law.html")
        expected = "§ 19 (Title)\n\nDefault Umlaut: ä"
        self.assertEqual(res, expected)

    @patch("urllib.request.urlopen")
    def test_get_legal_text_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        with self.assertRaises(RuntimeError) as ctx:
            get_legal_text("http://example.com/law.html")

        self.assertIn("Failed to fetch legal URL", str(ctx.exception))
        self.assertIn("Connection refused", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
