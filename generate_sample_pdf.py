import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_sample_pdf(filename: str = "sample_enterprise_policy.pdf") -> str:
    """Generate a sample private enterprise PDF for testing ChromaDB ingestion."""
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "OmniMind AI Private Enterprise Security & RAG Policy")
    
    c.setFont("Helvetica", 11)
    c.drawString(100, 720, "Document ID: POL-2026-X89 | Classification: CONFIDENTIAL")
    c.drawString(100, 700, "1. Executive Summary")
    c.drawString(100, 680, "OmniMind AI provides autonomous multi-agent execution with private document intelligence.")
    c.drawString(100, 665, "All private PDF files ingested into ChromaDB are stored with page-level metadata.")
    
    c.drawString(100, 630, "2. Security Controls & Data Isolation")
    c.drawString(100, 610, "Data isolation is enforced at the vector collection level using unique tenant identifiers.")
    c.drawString(100, 595, "Vector embeddings are generated using high density 1536-dimensional embedding models.")
    c.drawString(100, 580, "Agent tool calls querying ChromaDB must specify tenant context and query limit top_k.")
    
    c.showPage()
    
    # Page 2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "3. Multi-Agent Query Procedures")
    c.setFont("Helvetica", 11)
    c.drawString(100, 720, "When an agent executes the 'chroma_pdf_query' tool:")
    c.drawString(100, 700, "- It extracts exact matching passages from the ChromaDB vector database.")
    c.drawString(100, 685, "- It filters out irrelevant results with similarity distance thresholding.")
    c.drawString(100, 670, "- The RAG Specialist Agent synthesizes the exact PDF answer with page citations.")

    c.drawString(100, 630, "4. SLA & Performance Metrics")
    c.drawString(100, 610, "Target query response latency is < 45 milliseconds for vector retrieval.")
    c.drawString(100, 595, "Document ingestion throughput is benchmarked at 150 PDF pages per minute.")
    
    c.save()
    print(f"Sample PDF successfully generated: '{filename}'")
    return filename


if __name__ == "__main__":
    create_sample_pdf()
