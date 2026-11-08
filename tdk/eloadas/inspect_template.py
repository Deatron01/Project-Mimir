"""Print the shapes of selected template slides and the theme fonts/colors."""
import re, sys, zipfile
from pptx import Presentation
from pptx.util import Emu

T = sys.argv[1]
p = Presentation(T)
EMU = 914400
print('slide size', p.slide_width / EMU, p.slide_height / EMU)
for idx in [0, 1, 2, 6, 10, 14, 15]:
    s = p.slides[idx]
    print(f'\n=== slide {idx + 1} layout={s.slide_layout.name}')
    for sh in s.shapes:
        ph = sh.placeholder_format.idx if sh.is_placeholder else '-'
        txt = sh.text_frame.text[:40].replace('\n', ' | ') if sh.has_text_frame else ''
        fill = ''
        try:
            if sh.fill.type is not None and sh.fill.type == 1:
                fill = str(sh.fill.fore_color.rgb)
        except Exception:
            pass
        print(f'  {sh.shape_type!s:22} ph={ph!s:3} name={sh.name[:28]:28} '
              f'x={sh.left / EMU:.2f} y={sh.top / EMU:.2f} w={sh.width / EMU:.2f} h={sh.height / EMU:.2f} fill={fill} "{txt}"')
z = zipfile.ZipFile(T)
theme = [n for n in z.namelist() if n.startswith('ppt/theme/theme')][0]
x = z.read(theme).decode('utf8')
print('\nfonts:', re.findall(r'<a:(?:major|minor)Font><a:latin typeface="([^"]+)"', x))
print('colors:', re.findall(r'<a:(dk1|lt1|dk2|lt2|accent\d)>.*?val="([0-9A-Fa-f]{6}|\w+)"', x))
# fonts used in slide 3 runs
s3 = z.read('ppt/slides/slide3.xml').decode('utf8')
print('slide3 fonts:', set(re.findall(r'typeface="([^"]+)"', s3)), 'colors:', set(re.findall(r'srgbClr val="([0-9A-F]{6})"', s3)))
