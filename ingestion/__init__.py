"""
Document Ingestion Module

Handles parsing of PDFs and other document types for IT diligence analysis.
"""
from .pdf_parser import PDFParser, ParsedDocument, parse_pdfs

__all__ = ['PDFParser', 'ParsedDocument', 'parse_pdfs']
