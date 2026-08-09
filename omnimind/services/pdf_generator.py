"""
OmniMind AI — ReportLab Executive PDF Report Generator
"""
import os
import html
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("omnimind.services.pdf_generator")

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("ReportLab package not found. Using text fallback for PDF generation.")


class WorkflowPdfReportGenerator:
    """Generates styled executive PDF reports from agent workflow execution outputs."""

    def __init__(self, output_dir: str = "./uploads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_workflow_pdf(
        self,
        workflow_id: str,
        workflow_name: str,
        goal: str,
        execution_results: Dict[str, Any],
        user_name: str = "OmniMind User",
    ) -> str:
        """
        Build a formatted executive PDF report for a workflow run and save to disk.

        Returns path to generated PDF file.
        """
        filename = f"report_wf_{workflow_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        if not HAS_REPORTLAB:
            with open(filepath, "wb") as f:
                content = f"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n{goal}\n"
                f.write(content.encode("utf-8"))
            return filepath

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # Custom Executive Typography & Palette
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15,
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8,
        )
        agent_header = ParagraphStyle(
            "AgentHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#0284c7"),
        )

        story = []

        # Title Header
        escaped_name = html.escape(workflow_name)
        escaped_goal = html.escape(goal)

        story.append(Paragraph("OmniMind AI — Multi-Agent Executive Report", title_style))
        story.append(Paragraph(f"Workflow: <b>{escaped_name}</b> | ID: {workflow_id[:8]}... | Generated: {datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=15))

        # Goal Summary Box
        story.append(Paragraph("Workflow Objective & Goal", h2_style))
        story.append(Paragraph(f"<i>\"{escaped_goal}\"</i>", body_style))
        story.append(Spacer(1, 10))

        # Agent Step Results Table
        story.append(Paragraph("Agent Execution Summary & Outputs", h2_style))

        step_results = execution_results.get("step_results", {})
        table_data = [
            [
                Paragraph("<b>Task Node</b>", agent_header),
                Paragraph("<b>Assigned Agent</b>", agent_header),
                Paragraph("<b>Output & Action Taken</b>", agent_header),
            ]
        ]

        for task_key, details in step_results.items():
            agent_name = html.escape(str(details.get("agent", "Agent")))
            action = html.escape(str(details.get("action", "executed_task")))
            raw_output = str(details.get("output", details))[:500]
            output_summary = html.escape(raw_output)

            table_data.append([
                Paragraph(f"<b>{html.escape(task_key)}</b>", body_style),
                Paragraph(agent_name, body_style),
                Paragraph(f"<b>Action:</b> {action}<br/>{output_summary}", body_style),
            ])

        table = Table(table_data, colWidths=[110, 110, 310])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))

        # Footer Sign-off
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
        story.append(Paragraph(f"Report generated by OmniMind Autonomous Multi-Agent SaaS Engine for {html.escape(user_name)}.", subtitle_style))

        # Build Document
        doc.build(story)
        logger.info(f"Generated executive PDF report: {filepath}")
        return filepath
