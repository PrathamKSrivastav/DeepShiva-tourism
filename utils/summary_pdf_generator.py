"""
Summary PDF Generator
Creates professional PDF documents from AI-generated summaries
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
import logging
import os
import re

logger = logging.getLogger(__name__)


class SummaryPDFGenerator:
    """Generate professional PDF from chat summary"""
    
    # Color scheme
    COLOR_PRIMARY = colors.HexColor("#10b981")      # Green (summary theme)
    COLOR_ACCENT = colors.HexColor("#3b82f6")       # Blue
    COLOR_TEXT = colors.HexColor("#1f2937")         # Dark gray
    COLOR_LIGHT_BG = colors.HexColor("#f0fdf4")     # Light green
    COLOR_BORDER = colors.HexColor("#d1d5db")       # Gray
    
    @staticmethod
    def create_summary_pdf(
        summary_data: dict,
        output_path: str
    ) -> bool:
        """
        Create PDF from summary data
        
        Args:
            summary_data: Dict containing summary_content, session_title, etc.
            output_path: Full file path to save PDF
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"📄 Generating summary PDF: {summary_data.get('session_title')}")
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
                title=f"Summary: {summary_data.get('session_title')}"
            )
            
            # Container for PDF elements
            elements = []
            
            # Create styles
            styles = getSampleStyleSheet()
            
            # Title style
            title_style = ParagraphStyle(
                'SummaryTitle',
                parent=styles['Heading1'],
                fontSize=22,
                textColor=SummaryPDFGenerator.COLOR_PRIMARY,
                spaceAfter=8,
                spaceBefore=0,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            )
            
            # Subtitle style
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=SummaryPDFGenerator.COLOR_TEXT,
                spaceAfter=20,
                fontName='Helvetica',
                alignment=TA_CENTER
            )
            
            # Section header style
            section_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=SummaryPDFGenerator.COLOR_ACCENT,
                spaceAfter=8,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            )
            
            # Content style
            content_style = ParagraphStyle(
                'Content',
                parent=styles['Normal'],
                fontSize=10,
                textColor=SummaryPDFGenerator.COLOR_TEXT,
                leftIndent=10,
                rightIndent=10,
                spaceAfter=6,
                fontName='Helvetica',
                alignment=TA_JUSTIFY
            )
            
            # Bullet style
            bullet_style = ParagraphStyle(
                'Bullet',
                parent=styles['Normal'],
                fontSize=10,
                textColor=SummaryPDFGenerator.COLOR_TEXT,
                leftIndent=25,
                bulletIndent=15,
                spaceAfter=4,
                fontName='Helvetica'
            )
            
            # Add header box
            header_data = [[
                Paragraph(
                    f"<b>🤖 AI-Generated Travel Summary</b><br/>"
                    f"<font size='9'>Intelligent analysis powered by Groq AI</font>",
                    subtitle_style
                )
            ]]
            
            header_table = Table(header_data, colWidths=[6.5*inch])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), SummaryPDFGenerator.COLOR_LIGHT_BG),
                ('BORDER', (0, 0), (-1, -1), 1, SummaryPDFGenerator.COLOR_PRIMARY),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            elements.append(header_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Add title
            title = Paragraph(summary_data.get('session_title', 'Travel Summary'), title_style)
            elements.append(title)
            
            # Add metadata
            metadata = summary_data.get('metadata', {})
            message_count = summary_data.get('message_count', 0)
            generated_at = summary_data.get('generated_at', datetime.utcnow().isoformat())
            
            try:
                gen_time = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                time_str = gen_time.strftime('%B %d, %Y at %I:%M %p')
            except:
                time_str = "Recent"
            
            meta_text = (
                f"<font size='9' color='#6b7280'>"
                f"Generated: {time_str} | "
                f"Messages Analyzed: {message_count} | "
                f"Conversation Length: {metadata.get('user_messages', 0)} exchanges"
                f"</font>"
            )
            
            elements.append(Paragraph(meta_text, subtitle_style))
            elements.append(Spacer(1, 0.15*inch))
            
            # Parse and add summary content
            summary_content = summary_data.get('summary_content', '')
            
            # Split by markdown headers and process
            sections = SummaryPDFGenerator._parse_markdown_sections(summary_content)
            
            for section_title, section_content in sections:
                if section_title:
                    # Add section header
                    elements.append(Paragraph(section_title, section_style))
                
                # Add section content
                if section_content:
                    # Check if it's a list
                    if section_content.strip().startswith('-') or section_content.strip().startswith('•'):
                        # Process as bullet list
                        items = [item.strip('- •').strip() for item in section_content.split('\n') if item.strip()]
                        for item in items:
                            if item:
                                bullet_para = Paragraph(f"• {item}", bullet_style)
                                elements.append(bullet_para)
                    else:
                        # Process as paragraph
                        para = Paragraph(section_content.strip(), content_style)
                        elements.append(para)
                
                elements.append(Spacer(1, 0.1*inch))
            
            # Add footer
            elements.append(Spacer(1, 0.3*inch))
            footer_text = (
                f"<font size='8' color='#9ca3af'>"
                f"This summary was generated using AI analysis. "
                f"Please verify critical information before making travel decisions.<br/>"
                f"© {datetime.now().year} Deep Shiva Tourism - Powered by Groq AI"
                f"</font>"
            )
            elements.append(Paragraph(footer_text, subtitle_style))
            
            # Build PDF
            doc.build(elements)
            logger.info(f"✅ Summary PDF generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Summary PDF generation failed: {str(e)}")
            logger.exception("Full traceback:")
            return False
    
    @staticmethod
    def _parse_markdown_sections(markdown_text: str):
        """Parse markdown into sections"""
        sections = []
        
        # Split by ## headers
        parts = re.split(r'\n##\s+', markdown_text)
        
        # First part (before any header)
        if parts[0].strip():
            sections.append(("", parts[0].strip()))
        
        # Process remaining sections
        for part in parts[1:]:
            lines = part.split('\n', 1)
            section_title = lines[0].strip()
            section_content = lines[1].strip() if len(lines) > 1 else ""
            
            # Remove emoji from title for cleaner PDF
            section_title = re.sub(r'[^\w\s&,-]', '', section_title).strip()
            
            sections.append((section_title, section_content))
        
        return sections
