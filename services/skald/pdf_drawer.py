from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

class NativePDFDrawer:
    def __init__(self):
        self.width, self.height = A4
        self.margin = 50

    def draw_test(self, questions: list, title="Generált Vizsgateszt") -> bytes:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setFont("Helvetica-Bold", 16)
        
        y_position = self.height - self.margin
        c.drawString(self.margin, y_position, title)
        y_position -= 40
        
        c.setFont("Helvetica", 12)
        
        for idx, q in enumerate(questions):
            # Egyszerű automatikus tördelés a lap alján
            if y_position < 100:
                c.showPage()
                c.setFont("Helvetica", 12)
                y_position = self.height - self.margin
            
            # Kérdés kiírása
            c.drawString(self.margin, y_position, f"{idx + 1}. {q.get('text', '')}")
            y_position -= 20
            
            # Válaszok kiírása
            if q.get('type') == 'mcq':
                labels = ['A)', 'B)', 'C)', 'D)']
                for i, ans in enumerate(q.get('answers', [])):
                    label = labels[i] if i < len(labels) else "•"
                    c.drawString(self.margin + 20, y_position, f"{label} {ans.get('text', '')}")
                    y_position -= 15
            
            y_position -= 10 # Térköz a következő kérdésig
            
        c.save()
        buffer.seek(0)
        return buffer.getvalue()