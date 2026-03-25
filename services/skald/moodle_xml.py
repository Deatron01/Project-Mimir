import html

class MoodleXMLExporter:
    def __init__(self):
        self.header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
        self.footer = '</quiz>'

    def _cdata(self, text):
        """Biztonságos CDATA blokk generálása."""
        return f"<![CDATA[{text}]]>"

    def generate_mcq(self, question: dict) -> str:
        """Feleletválasztós (Multiple Choice) kérdés XML blokkja."""
        q_text = self._cdata(question.get('text', ''))
        xml = f"""
    <question type="multichoice">
        <name>
            <text>{html.escape(question.get('title', 'Kérdés'))}</text>
        </name>
        <questiontext format="html">
            <text>{q_text}</text>
        </questiontext>
        <defaultgrade>1.0000000</defaultgrade>
        <single>true</single>
        <shuffleanswers>true</shuffleanswers>
"""
        for ans in question.get('answers', []):
            fraction = "100" if ans.get('is_correct') else "0"
            xml += f"""
        <answer fraction="{fraction}" format="html">
            <text>{self._cdata(ans.get('text', ''))}</text>
            <feedback format="html">
                <text>{self._cdata(ans.get('feedback', ''))}</text>
            </feedback>
        </answer>"""
        
        xml += "\n    </question>\n"
        return xml

    def export_test(self, questions: list) -> str:
        """Teljes teszt összefűzése."""
        body = ""
        for q in questions:
            if q.get('type') == 'mcq':
                body += self.generate_mcq(q)
            # Ide jöhet később a true/false és esszé logika
        return self.header + body + self.footer