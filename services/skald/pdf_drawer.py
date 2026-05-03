from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer,HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os

class NativePDFDrawer:
    def __init__(self):
        # --- BETŰTÍPUS REGISZTRÁLÁSA ---
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', font_bold_path))
            self.font_regular = 'DejaVu'
            self.font_bold = 'DejaVu-Bold'
        except Exception as e:
            print(f"Figyelem: Fallback Helvetica-ra. Hiba: {e}")
            self.font_regular = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def draw_test(self, questions: list, title="Generált Vizsgateszt") -> bytes:
        buffer = io.BytesIO()
        
        # Dokumentum létrehozása margókkal
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
        )
        
        styles = getSampleStyleSheet()
        
        # --- EGYEDI STÍLUSOK DEFINIÁLÁSA ---
        title_style = ParagraphStyle(
            'TitleStyle',
            fontName=self.font_bold,
            fontSize=20,
            alignment=1, # Középre igazítva
            spaceAfter=30
        )
        
        question_style = ParagraphStyle(
            'QuestionStyle',
            fontName=self.font_bold,
            fontSize=12,
            leading=16, # Sorköz
            spaceBefore=15,
            spaceAfter=10
        )
        
        answer_style = ParagraphStyle(
            'AnswerStyle',
            fontName=self.font_regular,
            fontSize=11,
            leftIndent=20, # Behúzás a válaszoknak
            spaceAfter=6
        )

        elements = []

        # 1. Cím hozzáadása
        elements.append(Paragraph(title, title_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=20))

        # 2. Kérdések és válaszok feldolgozása
        for idx, q in enumerate(questions, 1):
            # Kérdés szövege (tisztítva a felesleges karakterektől)
            q_text = q.get('text', '').replace('$', '')
            elements.append(Paragraph(f"{idx}. {q_text}", question_style))
            
            # Válaszok kezelése
            if q.get('type') in ['mcq', 'tf']:
                labels = ['A)', 'B)', 'C)', 'D)', 'E)']
                for i, ans in enumerate(q.get('answers', [])):
                    label = labels[i] if i < len(labels) else "•"
                    ans_text = ans.get('text', '').replace('$', '')
                    
                    elements.append(Paragraph(f"{label} {ans_text}", answer_style))
            
            # Ha kifejtős kérdés, hagyunk helyet a válasznak (opcionális)
            elif q.get('type') == 'open':
                elements.append(Paragraph("_" * 80, answer_style))
                elements.append(Spacer(1, 10))

        # PDF felépítése
        doc.build(elements)
        
        pdf_value = buffer.getvalue()
        buffer.close()
        return pdf_value