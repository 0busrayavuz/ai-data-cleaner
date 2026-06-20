import os
import html
from pathlib import Path

import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


PDF_FONT_REGULAR = "PrepWiseSans"
PDF_FONT_BOLD = "PrepWiseSans-Bold"


def _register_pdf_fonts() -> tuple[str, str]:
    """Register a Unicode font family that includes Turkish glyphs."""
    if PDF_FONT_REGULAR in pdfmetrics.getRegisteredFontNames():
        return PDF_FONT_REGULAR, PDF_FONT_BOLD

    backend_dir = Path(__file__).resolve().parents[1]
    candidates = [
        (
            backend_dir / "assets" / "fonts" / "DejaVuSans.ttf",
            backend_dir / "assets" / "fonts" / "DejaVuSans-Bold.ttf",
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
    ]

    for regular_path, bold_path in candidates:
        if regular_path.is_file() and bold_path.is_file():
            pdfmetrics.registerFont(TTFont(PDF_FONT_REGULAR, str(regular_path)))
            pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, str(bold_path)))
            pdfmetrics.registerFontFamily(
                PDF_FONT_REGULAR,
                normal=PDF_FONT_REGULAR,
                bold=PDF_FONT_BOLD,
                italic=PDF_FONT_REGULAR,
                boldItalic=PDF_FONT_BOLD,
            )
            return PDF_FONT_REGULAR, PDF_FONT_BOLD

    raise RuntimeError(
        "PDF raporu için Türkçe karakter destekli bir font bulunamadı."
    )

def generate_quality_report(
    dataset_id: int,
    filename: str,
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    result: dict,
    before_health: float,
    after_health: float,
    suffix: str = None
) -> tuple[str, str]:
    """
    Generates HTML and PDF quality reports and saves them to the outputs directory.
    Returns: (html_path, pdf_path)
    """
    os.makedirs("outputs", exist_ok=True)
    html_name = f"report_{dataset_id}_{suffix}.html" if suffix else f"report_{dataset_id}.html"
    pdf_name = f"report_{dataset_id}_{suffix}.pdf" if suffix else f"report_{dataset_id}.pdf"
    html_path = os.path.join("outputs", html_name)
    pdf_path = os.path.join("outputs", pdf_name)
    health_breakdown = result.get("health_breakdown") or {}
    health_before = health_breakdown.get("before") or {}
    health_after = health_breakdown.get("after") or {}

    # ── 1. Create HTML Report ──
    # Create logs HTML table rows
    logs_html = ""
    for log in result.get("logs", []):
        status_color = "#22c55e" if log.get("status") == "ok" else "#ef4444"
        logs_html += f"""
        <tr>
            <td><strong>{html.escape(str(log.get('column', '-')))}</strong></td>
            <td><span class="badge" style="background: {status_color}">{html.escape(str(log.get('status', 'unknown')))}</span></td>
            <td>{html.escape(str(log.get('category', '-')))}</td>
            <td><code>{html.escape(str(log.get('method', '-')))}</code></td>
            <td>{html.escape(str(log.get('detail', '-')))}</td>
            <td>{html.escape(str(log.get('timestamp', '-')))}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>PrepWise - Kalite ve Temizlik Raporu</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #0b0f19;
            color: #f3f4f6;
            margin: 0;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1f2937;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.2rem;
            color: #38bdf8;
            text-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
        }}
        .header .date {{
            color: #9ca3af;
            font-size: 0.95rem;
        }}
        .card {{
            background: rgba(17, 24, 39, 0.8);
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .card h3 {{
            margin-top: 0;
            color: #38bdf8;
            border-bottom: 1px solid #374151;
            padding-bottom: 8px;
            margin-bottom: 16px;
        }}
        .grid-metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .metric-label {{
            color: #9ca3af;
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 1.25rem;
            font-weight: bold;
            color: #f3f4f6;
        }}
        .health-scores {{
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
        }}
        .health-card {{
            flex: 1;
            min-width: 250px;
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #374151;
        }}
        .health-before {{
            background: rgba(239, 68, 68, 0.1);
            border-color: rgba(239, 68, 68, 0.3);
        }}
        .health-after {{
            background: rgba(34, 197, 94, 0.1);
            border-color: rgba(34, 197, 94, 0.3);
        }}
        .health-value {{
            font-size: 3.5rem;
            font-weight: 800;
            margin: 10px 0;
        }}
        .health-before .health-value {{
            color: #ef4444;
        }}
        .health-after .health-value {{
            color: #22c55e;
        }}
        .health-diff {{
            font-size: 1.1rem;
            font-weight: bold;
            color: #38bdf8;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #1f2937;
        }}
        th {{
            background-color: #111827;
            color: #9ca3af;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        td {{
            font-size: 0.9rem;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
        }}
        code {{
            background: #1e293b;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>PrepWise</h1>
                <div style="color: #9ca3af; font-size: 0.9rem;">Akıllı Veri Temizleme Kalite Raporu</div>
            </div>
            <div class="date">Oluşturma Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}</div>
        </div>

        <div class="card">
            <h3>Dosya Bilgileri</h3>
            <div class="grid-metadata">
                <div>
                    <div class="metric-label">Dosya Adı</div>
                    <div class="metric-value">{html.escape(str(filename))}</div>
                </div>
                <div>
                    <div class="metric-label">Satır Sayısı</div>
                    <div class="metric-value">{len(df_before)}</div>
                </div>
                <div>
                    <div class="metric-label">Sütun Sayısı</div>
                    <div class="metric-value">{len(df_before.columns)}</div>
                </div>
                <div>
                    <div class="metric-label">Veri Seti ID</div>
                    <div class="metric-value">#{dataset_id}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>Veri Sağlık Durumu (Health Score)</h3>
            <div class="health-scores">
                <div class="health-card health-before">
                    <div class="metric-label">Temizlik Öncesi Sağlık Skoru</div>
                    <div class="health-value">{before_health}%</div>
                    <div class="metric-label">Eksik Hücre Oranı: {result.get('before_missing_pct', 0)}%</div>
                </div>
                <div class="health-card health-after">
                    <div class="metric-label">Temizlik Sonrası Sağlık Skoru</div>
                    <div class="health-value">{after_health}%</div>
                    <div class="metric-label">Eksik Hücre Oranı: {result.get('after_missing_pct', 0)}%</div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <span class="health-diff">Gelişim Oranı: +{round(max(0.0, after_health - before_health), 2)}%</span>
            </div>
            <p style="color: #9ca3af; font-size: 0.82rem; margin: 18px 0 0;">
                Puanlama ağırlıkları: eksik hücre %100, format sorunu %50,
                IQR aykırısı %25. Aykırı değerler her zaman hata olmadığı için
                daha düşük ağırlıkla değerlendirilir. İşlem sonrası aykırılar,
                adil karşılaştırma için işlem öncesindeki IQR sınırlarıyla ölçülür.
                Bu puan, veri kalitesini özetleyen açıklanabilir bir göstergedir;
                alan uzmanı değerlendirmesinin yerine geçmez.
            </p>
            <table>
                <thead>
                    <tr>
                        <th>Sağlık Bileşeni</th>
                        <th>İşlem Öncesi</th>
                        <th>İşlem Sonrası</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Eksik Hücre</td>
                        <td>{health_before.get('missing', '-')}</td>
                        <td>{health_after.get('missing', '-')}</td>
                    </tr>
                    <tr>
                        <td>IQR Aykırısı</td>
                        <td>{health_before.get('outliers', '-')}</td>
                        <td>{health_after.get('outliers', '-')}</td>
                    </tr>
                    <tr>
                        <td>Format Sorunu</td>
                        <td>{health_before.get('format', '-')}</td>
                        <td>{health_after.get('format', '-')}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h3>Metrik Özetleri</h3>
            <div class="grid-metadata">
                <div>
                    <div class="metric-label">Giderilen Eksik Değerler</div>
                    <div class="metric-value">{(df_before.isnull().sum().sum() - df_after.isnull().sum().sum())} hücre</div>
                </div>
                <div>
                    <div class="metric-label">Temizlenen Aykırı Değerler</div>
                    <div class="metric-value">{result.get('outlier_count', 0)} hücre</div>
                </div>
                <div>
                    <div class="metric-label">Düzeltilen Format Sorunları</div>
                    <div class="metric-value">{result.get('format_errors', 0)} hücre</div>
                </div>
                <div>
                    <div class="metric-label">Uygulanan Başarılı Kural</div>
                    <div class="metric-value">{result.get('applied_count', 0)} / {len(result.get('logs', []))}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>Uygulanan Temizlik Logları</h3>
            <table>
                <thead>
                    <tr>
                        <th>Sütun</th>
                        <th>Durum</th>
                        <th>Kategori</th>
                        <th>Yöntem</th>
                        <th>Detay / Sonuç</th>
                        <th>Zaman</th>
                    </tr>
                </thead>
                <tbody>
                    {logs_html if logs_html else "<tr><td colspan='6' style='text-align:center;'>Uygulanmış işlem kaydı bulunmamaktadır.</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # ── 2. Create PDF Report using ReportLab ──
    try:
        regular_font, bold_font = _register_pdf_fonts()
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name='TitleStyle',
            parent=styles['Heading1'],
            fontName=bold_font,
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0284c7"),
            spaceAfter=15
        )
        subtitle_style = ParagraphStyle(
            name='SubTitleStyle',
            parent=styles['Normal'],
            fontName=regular_font,
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=20
        )
        section_style = ParagraphStyle(
            name='SectionStyle',
            parent=styles['Heading2'],
            fontName=bold_font,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0369a1"),
            spaceBefore=12,
            spaceAfter=8
        )
        normal_style = ParagraphStyle(
            name='NormalStyle',
            parent=styles['Normal'],
            fontName=regular_font,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1f2937")
        )
        bold_style = ParagraphStyle(
            name='BoldStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            fontName=bold_font,
            textColor=colors.HexColor("#111827")
        )

        elements = []

        # Header
        elements.append(Paragraph("PrepWise - Veri Kalite Raporu", title_style))
        elements.append(Paragraph(f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 10))

        # Meta Data Table
        elements.append(Paragraph("Dosya Metadata Bilgileri", section_style))
        meta_data = [
            [Paragraph("Dosya Adı", bold_style), Paragraph(html.escape(str(filename)), normal_style)],
            [Paragraph("Başlangıç Satır Sayısı", bold_style), Paragraph(str(len(df_before)), normal_style)],
            [Paragraph("Başlangıç Sütun Sayısı", bold_style), Paragraph(str(len(df_before.columns)), normal_style)],
            [Paragraph("Veri Seti Numarası", bold_style), Paragraph(f"#{dataset_id}", normal_style)]
        ]
        meta_table = Table(meta_data, colWidths=[150, 350])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 15))

        # Health Scores Table
        elements.append(Paragraph("Sağlık Durumu Analizi (Health Score)", section_style))
        health_data = [
            [Paragraph("İşlem Öncesi Sağlık Skoru", bold_style), Paragraph(f"{before_health}%", normal_style)],
            [Paragraph("İşlem Sonrası Sağlık Skoru", bold_style), Paragraph(f"{after_health}%", normal_style)],
            [Paragraph("Sağlık Gelişim Artışı", bold_style), Paragraph(f"+{round(max(0.0, after_health - before_health), 2)}%", normal_style)]
        ]
        health_table = Table(health_data, colWidths=[200, 300])
        health_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fee2e2")),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#dcfce7")),
            ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#e0f2fe")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(health_table)
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            "Puanlama ağırlıkları: eksik hücre %100, format sorunu %50, "
            "IQR aykırısı %25. Aykırı değerler her zaman hata olmadığı için "
            "daha düşük ağırlıkla değerlendirilir. İşlem sonrası aykırılar, "
            "işlem öncesindeki IQR sınırlarıyla ölçülür. Bu puan açıklanabilir "
            "bir kalite göstergesidir; alan uzmanı değerlendirmesinin yerine geçmez.",
            normal_style,
        ))
        breakdown_data = [
            [
                Paragraph("Sağlık Bileşeni", bold_style),
                Paragraph("İşlem Öncesi", bold_style),
                Paragraph("İşlem Sonrası", bold_style),
            ],
            [
                Paragraph("Eksik Hücre", normal_style),
                Paragraph(str(health_before.get("missing", "-")), normal_style),
                Paragraph(str(health_after.get("missing", "-")), normal_style),
            ],
            [
                Paragraph("IQR Aykırısı", normal_style),
                Paragraph(str(health_before.get("outliers", "-")), normal_style),
                Paragraph(str(health_after.get("outliers", "-")), normal_style),
            ],
            [
                Paragraph("Format Sorunu", normal_style),
                Paragraph(str(health_before.get("format", "-")), normal_style),
                Paragraph(str(health_after.get("format", "-")), normal_style),
            ],
        ]
        breakdown_table = Table(breakdown_data, colWidths=[200, 150, 150])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(Spacer(1, 6))
        elements.append(breakdown_table)
        elements.append(Spacer(1, 15))

        # Operations Table
        elements.append(Paragraph("Uygulanan Temizlik Log Kayıtları", section_style))
        op_header = [
            Paragraph("Sütun", bold_style),
            Paragraph("Durum", bold_style),
            Paragraph("Kategori", bold_style),
            Paragraph("Yöntem", bold_style),
            Paragraph("Sonuç Detayı", bold_style)
        ]
        table_rows = [op_header]
        for log in result.get("logs", []):
            table_rows.append([
                Paragraph(html.escape(str(log.get("column", "-"))), normal_style),
                Paragraph(html.escape(str(log.get("status", "ok"))), normal_style),
                Paragraph(html.escape(str(log.get("category", "-"))), normal_style),
                Paragraph(html.escape(str(log.get("method", "-"))), normal_style),
                Paragraph(html.escape(str(log.get("detail", "-"))), normal_style)
            ])

        op_table = Table(table_rows, colWidths=[80, 50, 70, 70, 230])
        op_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(op_table)

        doc.build(elements)
    except Exception as e:
        print(f"[PDF GENERATION ERROR] Could not build PDF: {str(e)}")
        raise e

    return html_path, pdf_path
