"""
PDF Generator for Chat Sessions
Converts chat history to professional PDF documents
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChatPDFGenerator:
    """Generate professional PDF from chat session"""
    
    # Color scheme
    COLOR_PRIMARY = colors.HexColor("#208084")      # Teal
    COLOR_USER_BG = colors.HexColor("#E8F4F8")      # Light teal
    COLOR_ASSISTANT_BG = colors.HexColor("#FFF9E6") # Light yellow
    COLOR_TEXT = colors.HexColor("#1F2121")         # Dark
    COLOR_BORDER = colors.HexColor("#D0D0D0")       # Gray
    
    @staticmethod
    def create_pdf(
        session_title: str,
        persona: str,
        messages: list,
        output_path: str
    ) -> bool:
        """
        Create PDF from chat messages
        
        Args:
            session_title: Title of the chat session
            persona: Persona used in the session
            messages: List of message dicts with role, content, timestamp
            output_path: Full file path to save PDF
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"📄 Generating PDF: {session_title}")
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
                title=session_title
            )
            
            # Container for PDF elements
            elements = []
            
            # Create styles
            styles = getSampleStyleSheet()
            
            # Title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=ChatPDFGenerator.COLOR_PRIMARY,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
            
            # Subtitle style
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=ChatPDFGenerator.COLOR_TEXT,
                spaceAfter=12,
                fontName='Helvetica'
            )
            
            # Message styles
            user_style = ParagraphStyle(
                'UserMessage',
                parent=styles['Normal'],
                fontSize=10,
                textColor=ChatPDFGenerator.COLOR_TEXT,
                leftIndent=10,
                rightIndent=10,
                spaceAfter=6,
                fontName='Helvetica'
            )
            
            assistant_style = ParagraphStyle(
                'AssistantMessage',
                parent=styles['Normal'],
                fontSize=10,
                textColor=ChatPDFGenerator.COLOR_TEXT,
                leftIndent=10,
                rightIndent=10,
                spaceAfter=6,
                fontName='Helvetica'
            )
            
            timestamp_style = ParagraphStyle(
                'Timestamp',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor("#808080"),
                alignment=TA_RIGHT,
                spaceAfter=4,
                fontName='Helvetica-Oblique'
            )
            
            # Add title
            title = Paragraph(session_title, title_style)
            elements.append(title)
            
            # Add metadata
            metadata = f"<b>Persona:</b> {persona} | <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elements.append(Paragraph(metadata, subtitle_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Add messages
            for i, msg in enumerate(messages):
                if msg.get('role') == 'user':
                    # User message
                    content = msg.get('content', '')
                    timestamp = msg.get('timestamp', '')
                    
                    # Timestamp
                    if timestamp:
                        try:
                            ts_str = ChatPDFGenerator._format_timestamp(timestamp)
                            elements.append(Paragraph(ts_str, timestamp_style))
                        except:
                            pass
                    
                    # Message box table
                    table_data = [[Paragraph(f"<b>You:</b> {content}", user_style)]]
                    
                    table = Table(
                        table_data,
                        colWidths=[6*inch],
                        rowHeights=[None]
                    )
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), ChatPDFGenerator.COLOR_USER_BG),
                        ('BORDER', (0, 0), (-1, -1), 1, ChatPDFGenerator.COLOR_BORDER),
                        ('BORDERRADIUS', (0, 0), (-1, -1), 5),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        ('TOPPADDING', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    
                    elements.append(table)
                    elements.append(Spacer(1, 0.15*inch))
                    
                elif msg.get('role') == 'assistant':
                    # Assistant message
                    content = msg.get('content', '')
                    timestamp = msg.get('timestamp', '')
                    
                    # Timestamp
                    if timestamp:
                        try:
                            ts_str = ChatPDFGenerator._format_timestamp(timestamp)
                            elements.append(Paragraph(ts_str, timestamp_style))
                        except:
                            pass
                    
                    # Message box table
                    table_data = [[Paragraph(f"<b>Assistant:</b> {content}", assistant_style)]]
                    
                    table = Table(
                        table_data,
                        colWidths=[6*inch],
                        rowHeights=[None]
                    )
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), ChatPDFGenerator.COLOR_ASSISTANT_BG),
                        ('BORDER', (0, 0), (-1, -1), 1, ChatPDFGenerator.COLOR_BORDER),
                        ('BORDERRADIUS', (0, 0), (-1, -1), 5),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        ('TOPPADDING', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    
                    elements.append(table)
                    elements.append(Spacer(1, 0.15*inch))
                
                # Page break every 8 messages
                if (i + 1) % 8 == 0:
                    elements.append(PageBreak())
            
            # Build PDF
            doc.build(elements)
            logger.info(f"✅ PDF generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ PDF generation failed: {str(e)}")
            return False
    
    @staticmethod
    def _format_timestamp(timestamp) -> str:
        """Convert timestamp to readable format"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            return dt.strftime('%I:%M %p')
        except:
            return ""
