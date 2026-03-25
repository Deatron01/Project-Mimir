import re
import ast
import os
from pdf_handler import PDFProcessor

class AgenticRouter:
    def __init__(self):
        print("Agentic Router inicializálva.")
        self.pdf_processor = PDFProcessor()

    def route_document(self, content_or_path, file_extension):
        """
        Útválasztás. PDF esetén fájlelérési utat vár, szöveges fájloknál a nyers szöveget.
        """
        ext = file_extension.lower().strip('.')
        
        if ext == 'pdf':
            print(f"-> Útvonal: PDF Elemzés ({content_or_path})")
            if not os.path.exists(content_or_path):
                return [{"type": "error", "content": "A PDF fájl nem található!"}]
            
            extracted_text, used_route = self.pdf_processor.process_pdf(content_or_path)
            print(f"   [PDF Motor] Használt metódus: {used_route}")
            
            return self._parse_markdown(extracted_text)
            
        elif ext in ['md', 'markdown', 'txt']:
            print(f"-> Útvonal: Strukturált ({ext.upper()})")
            return self._parse_markdown(content_or_path)
            
        elif ext in ['py', 'python']:
            print("-> Útvonal: Programkód (Python AST)")
            return self._parse_python_ast(content_or_path)
            
        else:
            print("-> Útvonal: Narratív szöveg (Nyers)")
            return [{"type": "narrative", "content": content_or_path}]

    def _parse_markdown(self, text):
        chunks = []
        # Szétválasztjuk a szöveget a Markdown kódblokkok (```) mentén
        parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
        
        for part in parts:
            clean_part = part.strip()
            if not clean_part:
                continue
                
            if clean_part.startswith('```') and clean_part.endswith('```'):
                code_content = clean_part.strip('`').strip()
                if '\n' in code_content:
                    lines = code_content.split('\n')
                    # Ha az első sor csak egy szó, az valószínűleg a nyelv neve
                    if len(lines[0].split()) == 1:
                        code_content = '\n'.join(lines[1:]).strip()
                        
                chunks.append({
                    "type": "code_block",
                    "content": code_content
                })
            else:
                # OKOS VÁGÁS: Markdown headerek (#) VAGY Számozott fejezetek (pl. 1. 2. 1. )
                # Csak akkor vág, ha a szám után nagybetű jön (hogy ne vágja szét a listákat a mondat közepén)
                sections = re.split(r'(?m)^(?:#{1,3}\s+|\d+(?:\.\s*\d+)*\.\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ]))', clean_part)
                
                for sec in sections:
                    clean_sec = sec.strip()
                    if clean_sec:
                        chunks.append({
                            "type": "markdown_section",
                            "content": clean_sec
                        })
        return chunks

    def _parse_python_ast(self, code):
        chunks = []
        try:
            tree = ast.parse(code)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    chunks.append({
                        "type": "code_block",
                        "content": ast.unparse(node),
                        "name": node.name
                    })
                else:
                    chunks.append({
                        "type": "code_snippet",
                        "content": ast.unparse(node)
                    })
            return chunks
        except SyntaxError:
            return [{"type": "code_error", "content": code}]