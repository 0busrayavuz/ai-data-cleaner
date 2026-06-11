from reportlab.pdfbase import pdfmetrics

from backend.reporting.report_generator import _register_pdf_fonts


def test_pdf_font_supports_turkish_characters():
    regular_font, bold_font = _register_pdf_fonts()
    turkish_characters = "çğıöşüÇĞİÖŞÜ"

    for font_name in (regular_font, bold_font):
        widths = pdfmetrics.getFont(font_name).face.charWidths
        assert all(ord(character) in widths for character in turkish_characters)
