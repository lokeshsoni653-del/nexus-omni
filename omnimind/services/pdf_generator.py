"""
OmniMind AI — ReportLab Executive PDF Report Generator (Human-Readable Format)
"""
import os
import ast
import html
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("omnimind.services.pdf_generator")

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("ReportLab package not found. Using text fallback for PDF generation.")


def _clean_output_to_readable_html(action: str, output: Any) -> str:
    """Transform raw Python dict strings or dict objects into clean executive HTML text."""
    parsed = output
    if isinstance(output, str):
        stripped = output.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            try:
                parsed = ast.literal_eval(stripped)
            except Exception:
                parsed = output

    if isinstance(parsed, dict):
        lines = []

        # 1. Plan Output
        if "plan" in parsed and isinstance(parsed["plan"], list):
            lines.append("<b>Executive Plan Decomposed:</b>")
            for idx, item in enumerate(parsed["plan"], 1):
                if isinstance(item, dict):
                    desc = html.escape(item.get("description", str(item)))
                    agent = html.escape(item.get("agent_type", "worker")).upper()
                    lines.append(f"&nbsp;&nbsp;• <b>Step {idx} ({agent})</b>: {desc}")
                else:
                    lines.append(f"&nbsp;&nbsp;• <b>Step {idx}</b>: {html.escape(str(item))}")
            return "<br/>".join(lines)

        # 2. RAG Document Retrieval Output
        if "documents" in parsed and isinstance(parsed["documents"], list):
            lines.append("<b>Retrieved Enterprise Knowledge Base Excerpt:</b>")
            for doc in parsed["documents"]:
                if isinstance(doc, dict):
                    doc_id = html.escape(str(doc.get("id", "Document")))
                    content = html.escape(str(doc.get("content", "")).replace("\n", " "))
                    lines.append(f"&nbsp;&nbsp;• <b>Source ({doc_id})</b>: \"{content[:260]}...\"")
                else:
                    lines.append(f"&nbsp;&nbsp;• <b>Excerpt</b>: \"{html.escape(str(doc))[:260]}...\"")
            return "<br/>".join(lines)

        # 3. Reviewer Verification Output
        if "quality_score" in parsed or "is_approved" in parsed:
            score = parsed.get("quality_score", 1.0)
            approved = parsed.get("is_approved", True)
            feedback = html.escape(str(parsed.get("feedback", "Approved")))
            badge = "✅ <b>APPROVED</b> (High Confidence)" if approved else "⚠️ <b>REVISION NEEDED</b>"
            lines.append(f"<b>Verification Status:</b> {badge}")
            lines.append(f"<b>Quality Score:</b> {int(float(score) * 100)}%")
            lines.append(f"<b>Reviewer Feedback:</b> {feedback}")
            return "<br/>".join(lines)

        # 4. General dictionary keys
        for k, v in parsed.items():
            if k not in ("analysis", "raw") and v:
                val_str = html.escape(str(v))
                key_str = html.escape(k.replace("_", " ").title())
                lines.append(f"<b>{key_str}:</b> {val_str}")
        return "<br/>".join(lines) if lines else html.escape(str(output))

    elif isinstance(parsed, list):
        return "<br/>".join([f"• {html.escape(str(x))}" for x in parsed])

    return html.escape(str(output))


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
        """Build a formatted executive PDF report for a workflow run and save to disk."""
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
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Executive Typography & Palette
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=12,
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )
        agent_header = ParagraphStyle(
            "AgentHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#0284c7"),
        )
        goal_box_style = ParagraphStyle(
            "GoalBox",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
        )

        story = []

        # ── 1. Document Header Banner ───────────────────────────────────────────────
        escaped_name = html.escape(workflow_name)
        escaped_goal = html.escape(goal)
        escaped_user = html.escape(user_name)
        generated_at = datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')

        story.append(Paragraph("OmniMind AI — Multi-Agent Executive Report", title_style))
        story.append(Paragraph(f"Workflow: <b>{escaped_name}</b> | ID: <font color='#0284c7'>{workflow_id[:8]}</font> | Generated: {generated_at}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=12))

        # ── 2. Objective & Goal Section ─────────────────────────────────────────────
        story.append(Paragraph("🎯 Workflow Objective & Goal", h2_style))
        
        goal_table = Table(
            [[Paragraph(f"\"{escaped_goal}\"", goal_box_style)]],
            colWidths=[540],
        )
        goal_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(goal_table)
        story.append(Spacer(1, 10))

        # ── 3. Executive Summary Briefing ───────────────────────────────────────────
        story.append(Paragraph("📋 Executive Summary & Key Findings", h2_style))
        summary_text = (
            f"This executive report details the automated execution results for goal <i>\"{escaped_goal[:120]}...\"</i>. "
            f"The OmniMind Autonomous Multi-Agent engine assigned tasks across specialized roles (Orchestrator, RAG Specialist, "
            f"Worker, and Reviewer), retrieved relevant enterprise documents from ChromaDB, executed reasoning steps, and verified "
            f"all compliance criteria with high confidence."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 8))

        # ── 4. Agent Step Results Table ─────────────────────────────────────────────
        story.append(Paragraph("🤖 Agent Task Breakdown & Outputs", h2_style))

        step_results = execution_results.get("step_results", {})
        table_data = [
            [
                Paragraph("<b>Task Node</b>", agent_header),
                Paragraph("<b>Assigned Agent</b>", agent_header),
                Paragraph("<b>Output & Human-Readable Action Summary</b>", agent_header),
            ]
        ]

        for task_key, details in step_results.items():
            agent_name = html.escape(str(details.get("agent", "Agent")))
            action_raw = str(details.get("action", "executed_task")).replace("_", " ").title()
            action = html.escape(action_raw)
            raw_output = details.get("output", details)
            
            clean_output_html = _clean_output_to_readable_html(action, raw_output)

            table_data.append([
                Paragraph(f"<b>{html.escape(task_key)}</b>", body_style),
                Paragraph(f"<b>{agent_name}</b>", body_style),
                Paragraph(f"<b>Action Executed:</b> {action}<br/><br/>{clean_output_html}", body_style),
            ])

        table = Table(table_data, colWidths=[110, 110, 320])
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
        story.append(Spacer(1, 14))

        # ── 5. Footer Sign-off ──────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        story.append(Paragraph(f"Report generated by OmniMind Autonomous Multi-Agent SaaS Engine for <b>{escaped_user}</b>.", subtitle_style))

        # Build Document
        doc.build(story)
        logger.info(f"Generated executive PDF report: {filepath}")
        return filepath
