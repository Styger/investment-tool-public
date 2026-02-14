"""
PDF Report Generator for Backtesting Results
Uses ReportLab - pure Python, no system dependencies required
"""

from datetime import datetime
from typing import Dict, List
from io import BytesIO
import tempfile
import os

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  ReportLab not available. Install with: pip install reportlab")


class BacktestPDFExporter:
    """Generate professional PDF reports from backtest results"""

    @staticmethod
    def generate_report(
        results: Dict,
        charts: Dict,
        universe_name: str = "Unknown",
        parameters: Dict = None,
    ) -> bytes:
        """
        Generate PDF report from backtest results

        Args:
            results: Backtest results dictionary
            charts: Dictionary of Plotly chart objects
            universe_name: Name of tested universe
            parameters: Strategy parameters used

        Returns:
            PDF file as bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "ReportLab is required for PDF generation. "
                "Install with: pip install reportlab"
            )

        # Create PDF buffer
        buffer = BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Container for the 'Flowable' objects
        elements = []

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1f77b4"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#1f77b4"),
            spaceAfter=12,
            spaceBefore=12,
        )

        # Extract data
        metrics = results.get("metrics", {})
        benchmark = results.get("benchmark", {})
        trades = results.get("trades", [])
        valuation_methods = results.get("valuation_methods", [])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Cover Page
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph("📊 ValueKit Backtest Report", title_style))
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("Consensus Valuation Strategy", styles["Heading2"]))
        elements.append(Spacer(1, 1 * inch))

        cover_info = [
            f"<b>Universe:</b> {universe_name}",
            f"<b>Period:</b> {results.get('dates', [''])[0] if results.get('dates') else 'N/A'} - {results.get('dates', [''])[-1] if results.get('dates') else 'N/A'}",
            f"<b>Valuation Methods:</b> {', '.join(valuation_methods) if valuation_methods else 'N/A'}",
            f"<b>Generated:</b> {timestamp}",
        ]

        for info in cover_info:
            elements.append(Paragraph(info, styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))

        elements.append(PageBreak())

        # Executive Summary
        elements.append(Paragraph("📋 Executive Summary", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        summary_data = [
            ["Metric", "Value"],
            ["Final Value", f"${results.get('final_value', 0):,.2f}"],
            ["Profit", f"${results.get('profit', 0):+,.2f}"],
            ["Total Return", f"{results.get('return_pct', 0):.2f}%"],
            ["CAGR", f"{results.get('cagr', 0):.2f}%"],
            ["Period", f"{metrics.get('years', 0):.1f} years"],
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5 * inch))

        # Strategy Parameters
        elements.append(Paragraph("🎯 Strategy Parameters", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        if parameters:
            params_data = [
                ["Parameter", "Value"],
                [
                    "Valuation Methods",
                    ", ".join(valuation_methods) if valuation_methods else "N/A",
                ],
                ["MOS Threshold", f"{parameters.get('mos_threshold', 'N/A')}%"],
                ["Moat Threshold", f"{parameters.get('moat_threshold', 'N/A')}/50"],
                [
                    "Sell MOS Threshold",
                    f"{parameters.get('sell_mos_threshold', 'N/A')}%",
                ],
                [
                    "Sell Moat Threshold",
                    f"{parameters.get('sell_moat_threshold', 'N/A')}/50",
                ],
                ["Max Positions", str(parameters.get("max_positions", "N/A"))],
                [
                    "Rebalance Frequency",
                    f"Every {parameters.get('rebalance_days', 'N/A')} days",
                ],
            ]

            params_table = Table(params_data, colWidths=[3 * inch, 3 * inch])
            params_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(params_table)

        elements.append(PageBreak())

        # Performance Metrics
        elements.append(Paragraph("📊 Performance Metrics", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        metrics_data = [
            ["Metric", "Value", "Description"],
            [
                "Sharpe Ratio",
                f"{metrics.get('sharpe_ratio', 0):.2f}",
                "Risk-adjusted return",
            ],
            [
                "Sortino Ratio",
                f"{metrics.get('sortino_ratio', 0):.2f}",
                "Downside risk-adjusted",
            ],
            [
                "Max Drawdown",
                f"{metrics.get('max_drawdown', 0):.2f}%",
                "Largest decline",
            ],
            [
                "Calmar Ratio",
                f"{metrics.get('calmar_ratio', 0):.2f}",
                "Return / Max DD",
            ],
        ]

        metrics_table = Table(metrics_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        metrics_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.5 * inch))

        # Benchmark Comparison
        if benchmark.get("benchmark_available"):
            elements.append(
                Paragraph("🎯 Benchmark Comparison (S&P 500)", heading_style)
            )
            elements.append(Spacer(1, 0.2 * inch))

            benchmark_data = [
                ["Metric", "Strategy", "S&P 500", "Difference"],
                [
                    "Total Return",
                    f"{benchmark.get('strategy_return', 0):.2f}%",
                    f"{benchmark.get('benchmark_return', 0):.2f}%",
                    f"{benchmark.get('outperformance', 0):+.2f}%",
                ],
                [
                    "CAGR",
                    f"{benchmark.get('strategy_cagr', 0):.2f}%",
                    f"{benchmark.get('benchmark_cagr', 0):.2f}%",
                    f"{(benchmark.get('strategy_cagr', 0) - benchmark.get('benchmark_cagr', 0)):+.2f}%",
                ],
                ["Alpha", "-", "-", f"{benchmark.get('alpha', 0):+.2f}%"],
                [
                    "Beta",
                    f"{benchmark.get('beta', 0):.2f}",
                    "1.00",
                    "Market correlation",
                ],
            ]

            benchmark_table = Table(
                benchmark_data,
                colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch],
            )
            benchmark_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(benchmark_table)

        elements.append(PageBreak())

        # Trade Statistics
        elements.append(Paragraph("📝 Trade Statistics", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        trade_stats_data = [
            ["Metric", "Value"],
            ["Total Trades", str(metrics.get("total_trades", 0))],
            ["Win Rate", f"{metrics.get('win_rate', 0):.1f}%"],
            ["Avg Hold Time", f"{metrics.get('avg_hold_time_days', 0):.0f} days"],
            ["Profit Factor", f"{metrics.get('profit_factor', 0):.2f}"],
            ["Average Win", f"${metrics.get('avg_win', 0):,.2f}"],
            ["Average Loss", f"${metrics.get('avg_loss', 0):,.2f}"],
        ]

        trade_stats_table = Table(trade_stats_data, colWidths=[3 * inch, 3 * inch])
        trade_stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(trade_stats_table)
        elements.append(Spacer(1, 0.5 * inch))

        # Charts
        elements.append(PageBreak())
        elements.append(Paragraph("📈 Performance Charts", heading_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Convert and add charts (using Matplotlib - no browser needed!)
        chart_images = BacktestPDFExporter._save_charts_as_images(results)

        charts_added = 0
        for chart_name, chart_path in chart_images.items():
            if chart_path and os.path.exists(chart_path):
                try:
                    img = Image(chart_path, width=6 * inch, height=3 * inch)
                    elements.append(img)
                    elements.append(Spacer(1, 0.3 * inch))
                    charts_added += 1
                except Exception as e:
                    print(f"Warning: Could not add chart {chart_name}: {e}")

        # If no charts were added, show message
        if charts_added == 0:
            note_style = ParagraphStyle(
                "Note",
                parent=styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#666666"),
                alignment=TA_CENTER,
            )
            elements.append(
                Paragraph(
                    "⚠️ Charts could not be embedded in PDF. "
                    "Charts are available in the web interface and HTML exports.",
                    note_style,
                )
            )
            elements.append(Spacer(1, 0.5 * inch))

        # Trade Log Summary
        if trades:
            elements.append(PageBreak())
            elements.append(Paragraph("📋 Top Trades", heading_style))
            elements.append(Spacer(1, 0.2 * inch))

            # Top 10 winners
            sorted_trades = sorted(trades, key=lambda x: x.get("pnl", 0), reverse=True)
            top_winners = sorted_trades[:10]

            elements.append(Paragraph("Top 10 Winners", styles["Heading3"]))
            elements.append(Spacer(1, 0.1 * inch))

            winners_data = [["Ticker", "Buy Date", "Sell Date", "P&L", "Hold Days"]]
            for trade in top_winners:
                buy_date = trade.get("buy_date", "N/A")
                sell_date = trade.get("sell_date", "N/A")

                if hasattr(buy_date, "strftime"):
                    buy_date = buy_date.strftime("%Y-%m-%d")
                if hasattr(sell_date, "strftime"):
                    sell_date = sell_date.strftime("%Y-%m-%d")

                winners_data.append(
                    [
                        str(trade.get("ticker", "N/A")),
                        str(buy_date),
                        str(sell_date),
                        f"${trade.get('pnl', 0):,.2f}",
                        str(trade.get("hold_days", 0)),
                    ]
                )

            winners_table = Table(
                winners_data,
                colWidths=[1 * inch, 1.2 * inch, 1.2 * inch, 1.3 * inch, 1 * inch],
            )
            winners_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.green),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.lightgreen),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(winners_table)
            elements.append(Spacer(1, 0.5 * inch))

            # Top 10 losers
            top_losers = sorted_trades[-10:][::-1]
            elements.append(Paragraph("Top 10 Losers", styles["Heading3"]))
            elements.append(Spacer(1, 0.1 * inch))

            losers_data = [["Ticker", "Buy Date", "Sell Date", "P&L", "Hold Days"]]
            for trade in top_losers:
                buy_date = trade.get("buy_date", "N/A")
                sell_date = trade.get("sell_date", "N/A")

                if hasattr(buy_date, "strftime"):
                    buy_date = buy_date.strftime("%Y-%m-%d")
                if hasattr(sell_date, "strftime"):
                    sell_date = sell_date.strftime("%Y-%m-%d")

                losers_data.append(
                    [
                        str(trade.get("ticker", "N/A")),
                        str(buy_date),
                        str(sell_date),
                        f"${trade.get('pnl', 0):,.2f}",
                        str(trade.get("hold_days", 0)),
                    ]
                )

            losers_table = Table(
                losers_data,
                colWidths=[1 * inch, 1.2 * inch, 1.2 * inch, 1.3 * inch, 1 * inch],
            )
            losers_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.red),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.lightcoral),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(losers_table)

        # Footer
        elements.append(Spacer(1, 1 * inch))
        footer_text = (
            f"Generated by ValueKit • {timestamp} • Consensus Valuation Strategy"
        )
        elements.append(Paragraph(footer_text, styles["Normal"]))

        # Build PDF
        doc.build(elements)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Cleanup temp chart files
        for chart_path in chart_images.values():
            if chart_path and os.path.exists(chart_path):
                try:
                    os.remove(chart_path)
                except:
                    pass

        return pdf_bytes

    @staticmethod
    def _save_charts_as_images(results: Dict) -> Dict:
        """
        Generate charts using Matplotlib (browser-independent)

        Args:
            results: Backtest results dictionary (not Plotly charts!)

        Returns:
            Dict mapping chart names to PNG file paths
        """
        from backend.backtesting.analytics.matplotlib_charts import (
            MatplotlibChartGenerator,
        )

        print("📊 Generating charts with Matplotlib for PDF (browser-independent)...")

        # Generate all charts using Matplotlib
        chart_images = MatplotlibChartGenerator.generate_all_charts(results)

        return chart_images
