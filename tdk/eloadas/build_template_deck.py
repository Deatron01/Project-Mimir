"""TDK-előadás az Óbudai Egyetem TDK-prezentációs sablonjára (sablon/oe_tdk_sablon_2023.pptx).

Futtatás a tdk/eloadas mappából:  python build_template_deck.py  ->  mimir_tdk_eloadas.pptx
A számok forrása: tdk/elemzes/szamok.md (a dolgozat táblázataival egyezően kerekítve).
A sablon diáiból másoljuk a bal oldali navigációs sávot és a címdobozt, a mintadiákat a végén töröljük.
"""
import copy
import os

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'sablon', 'oe_tdk_sablon_2023.pptx')
OUT = os.environ.get('DECK_OUT') or os.path.join(HERE, 'mimir_tdk_eloadas.pptx')

NAVY = RGBColor(0x15, 0x1F, 0x39)
NAVY2 = RGBColor(0x00, 0x20, 0x60)
BLUE = RGBColor(0x00, 0x6C, 0xA9)
LIGHT = RGBColor(0x00, 0x9E, 0xE0)
ORANGE = RGBColor(0xC2, 0x4E, 0x1F)
GRAY = RGBColor(0x59, 0x59, 0x59)
LGRAY = RGBColor(0xA5, 0xA5, 0xA5)
TINT = RGBColor(0xEE, 0xF2, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HEAD = 'Franklin Gothic Demi'
BODY = 'Franklin Gothic Book'

prs = Presentation(TEMPLATE)
T = list(prs.slides)                       # the 16 template slides
NAV_SOURCE = {0: T[2], 1: T[3], 2: T[4], 3: T[6], 4: T[12]}   # active nav box -> template slide
TITLE_SOURCE = T[6]                        # its "Text Placeholder 1" text box is the slide title
LAYOUT = T[2].slide_layout                 # "Comparison" – carries the ÓE logo

X0, X1 = 3.3, 12.85                        # content area (right of the navigation column)


# ---------------------------------------------------------------- helpers
def clone_shape(src_shape, slide):
    el = copy.deepcopy(src_shape._element)
    slide.shapes._spTree.insert_element_before(el, 'p:extLst')
    return el


def new_slide(title, nav):
    s = prs.slides.add_slide(LAYOUT)
    for ph in list(s.placeholders):        # the layout's empty placeholders are not used
        ph._element.getparent().remove(ph._element)
    src = NAV_SOURCE[nav]
    for sh in src.shapes:
        if sh.name.startswith('Lekerekített téglalap'):
            clone_shape(sh, s)
    for sh in TITLE_SOURCE.shapes:
        if sh.name == 'Text Placeholder 1':
            el = clone_shape(sh, s)
    title_shape = s.shapes[-1]
    title_shape.width = Inches(X1 - 2.9)
    set_text(title_shape.text_frame, title)
    return s


def set_text(tf, text):
    """Replace the text of a frame, keeping the first run's formatting."""
    p0 = tf.paragraphs[0]
    runs = p0.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
    else:
        p0.text = text
    for p in tf.paragraphs[1:]:
        p._p.getparent().remove(p._p)


def box(slide, x, y, w, h, paras, size=16, anchor=MSO_ANCHOR.TOP, fill=None, line=None, align=PP_ALIGN.LEFT,
        shape=MSO_SHAPE.RECTANGLE, margin=0.08):
    """paras: list of paragraphs; each paragraph is a list of (text, {bold, color, size, italic, font}) runs."""
    if fill is None and line is None:
        sh = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    else:
        sh = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            sh.adjustments[0] = 0.08
        if fill is None:
            sh.fill.background()
        else:
            sh.fill.solid(); sh.fill.fore_color.rgb = fill
        if line is None:
            sh.line.fill.background()
        else:
            sh.line.color.rgb = line; sh.line.width = Pt(1)
        sh.shadow.inherit = False
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ('left', 'right', 'top', 'bottom'):
        setattr(tf, f'margin_{side}', Inches(margin))
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        if isinstance(para, str):
            para = [(para, {})]
        for text, o in para:
            r = p.add_run()
            r.text = text
            f = r.font
            f.name = o.get('font', BODY)
            f.size = Pt(o.get('size', size))
            f.bold = o.get('bold', False)
            f.italic = o.get('italic', False)
            f.color.rgb = o.get('color', NAVY)
    return sh


def bullets(slide, x, y, w, h, items, size=16):
    """items: list of (label, text) – label in bold blue."""
    paras = []
    for label, text in items:
        runs = []
        if label:
            runs.append((label + ' ', {'bold': True, 'color': BLUE, 'font': HEAD}))
        runs.append((text, {}))
        paras.append(runs)
    sh = box(slide, x, y, w, h, paras, size=size)
    for p in sh.text_frame.paragraphs:
        p.space_after = Pt(10)
    return sh


def source(slide, text='Forrás: saját szerkesztés'):
    box(slide, 9.6, 6.92, 3.25, 0.35, [[(text, {'size': 10, 'color': GRAY})]], align=PP_ALIGN.RIGHT)


def stat(slide, x, y, w, number, label, note=None, color=BLUE):
    box(slide, x, y, w, 0.75, [[(number, {'font': HEAD, 'size': 36, 'color': color})]], margin=0)
    box(slide, x, y + 0.75, w, 0.4, [[(label, {'font': HEAD, 'size': 15})]], margin=0)
    if note:
        box(slide, x, y + 1.12, w, 0.8, [[(note, {'size': 13, 'color': GRAY})]], margin=0)


def bar_chart(slide, x, y, w, h, categories, series, colors, title, scale=100, fmt='0","00', vmax=100, unit=20,
              horizontal=False, legend=True, label_fmt=None):
    cd = CategoryChartData()
    cd.categories = categories
    for name, values in series:
        cd.add_series(name, [round(v * scale) for v in values])
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    ch.font.name = BODY
    ch.font.size = Pt(12)
    ch.font.color.rgb = NAVY
    ch.has_title = True
    ch.chart_title.text_frame.text = title
    tp = ch.chart_title.text_frame.paragraphs[0]
    tp.runs[0].font.size = Pt(13); tp.runs[0].font.bold = False; tp.runs[0].font.color.rgb = GRAY
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(12)
    va = ch.value_axis
    va.minimum_scale = 0; va.maximum_scale = vmax; va.major_unit = unit
    va.tick_labels.number_format = fmt; va.tick_labels.number_format_is_linked = False
    va.major_gridlines.format.line.color.rgb = RGBColor(0xD9, 0xD9, 0xD9)
    va.format.line.fill.background()
    ca = ch.category_axis
    ca.format.line.color.rgb = LGRAY
    if horizontal:
        ca.reverse_order = True
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.overlap = 0
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = label_fmt or fmt; dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(11)
    for s, c in zip(plot.series, colors):
        s.format.fill.solid(); s.format.fill.fore_color.rgb = c
    return gf


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def flow_row(slide, y, label, color, steps, fill):
    box(slide, X0, y - 0.45, 9, 0.35, [[(label, {'font': HEAD, 'size': 14, 'color': color})]], margin=0)
    gap = 0.28
    w = ((X1 - X0) - gap * (len(steps) - 1)) / len(steps)
    for i, t in enumerate(steps):
        x = X0 + i * (w + gap)
        box(slide, x, y, w, 1.0, [[(t, {'size': 13})]], fill=fill, line=color, anchor=MSO_ANCHOR.MIDDLE,
            align=PP_ALIGN.CENTER, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        if i < len(steps) - 1:
            a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + w + 0.04), Inches(y + 0.4),
                                       Inches(0.2), Inches(0.2))
            a.fill.solid(); a.fill.fore_color.rgb = color; a.line.fill.background(); a.shadow.inherit = False


# ======================================================================== 1. címdia (sablon 1. dia)
s1 = T[0]
for sh in s1.shapes:
    if sh.has_text_frame and 'Tudományos Diákköri Konferencia' in sh.text_frame.text:
        set_text(sh.text_frame, '64. Tudományos Diákköri Konferencia az Óbudai Egyetemen')
    elif sh.is_placeholder and sh.placeholder_format.idx == 0:
        set_text(sh.text_frame, 'Vizsgakérdés-generálás helyben futtatható nyelvi modellekkel')
        sh.top = Inches(2.1)
        sh.height = Inches(1.35)
    elif sh.name == 'Téglalap 14':
        tf = sh.text_frame
        lines = ['[Hallgató 1 neve] · [Neptun kód]', '[Hallgató 2 neve] · [Neptun kód]',
                 '[Hallgató 3 neve] · [Neptun kód]', '', 'Konzulens: [konzulens neve, beosztása]']
        first = tf.paragraphs[0]
        fmt_run = copy.deepcopy(first.runs[0]._r) if first.runs else None
        for p in tf.paragraphs[1:]:
            p._p.getparent().remove(p._p)
        set_text(tf, lines[0])
        for ln in lines[1:]:
            p = tf.add_paragraph()
            if fmt_run is not None and ln:
                r = copy.deepcopy(fmt_run); p._p.append(r); p.runs[0].text = ln
        sh.top = Inches(4.45); sh.height = Inches(1.9)
    elif sh.has_text_frame and sh.text_frame.text.startswith('Hallgató neve'):
        set_text(sh.text_frame, '')        # duplicate of the block above in the template
    elif sh.has_text_frame and sh.text_frame.text.startswith('Budapest'):
        set_text(sh.text_frame, 'Budapest, 2026. november 18.')
for sh in list(s1.shapes):                 # white KGK logo of the template: invisible, but overlaps the title
    if sh.shape_type == 13 and sh.name == 'Kép 10':
        sh._element.getparent().remove(sh._element)
box(s1, 1.34, 3.6, 10.5, 0.6, [[('A Mimir tervezésvezérelt, forráshivatkozásos RAG-módszere és kísérleti kiértékelése',
                                  {'size': 18, 'color': BLUE})]], margin=0)
notes(s1, '1. ELŐADÓ (kb. 30 mp). Köszöntjük a Bizottságot. Bemutatkozás: a három előadó és a konzulens. '
          'A dolgozat azt vizsgálja, hogyan lehet fogyasztói GPU-n, helyben futó kis nyelvi modellel megbízható '
          'feleletválasztós vizsgát generálni, és mitől függ az eredmény.')

# ======================================================================== 2. felépítés (sablon 2. dia)
s2 = T[1]
for sh in list(s2.shapes):
    if sh.has_text_frame and sh.text_frame.text.strip().startswith('Forrás'):
        sh._element.getparent().remove(sh._element)
    elif sh.name == 'Téglalap 9':
        sh._element.getparent().remove(sh._element)
who = {'Célkitűzések': '[1. előadó]', 'Elméleti háttér': '[1. előadó]', 'Anyag és módszer': '[1–2. előadó]',
       'Elemzés és eredmények': '[2–3. előadó]', 'Következtetések, javaslatok': '[3. előadó]'}
for sh in s2.shapes:
    if sh.has_text_frame and sh.text_frame.text.strip() in who:
        box(s2, 8.1, sh.top / 914400, 3.5, sh.height / 914400,
            [[(who[sh.text_frame.text.strip()], {'size': 15, 'color': GRAY})]], anchor=MSO_ANCHOR.MIDDLE)
notes(s2, '1. ELŐADÓ (kb. 15 mp). Az előadás a dolgozat szerkezetét követi: célkitűzések és elméleti háttér, '
          'a módszer, az eredmények, végül a következtetések és javaslatok. Hárman adjuk elő, a jobb oldalon '
          'látható beosztásban.')

# ======================================================================== 3. problémafelvetés, célkitűzések
s = new_slide('Problémafelvetés, célkitűzések', 0)
box(s, X0, 1.5, X1 - X0, 0.75, [[('A mai gyakorlat: az oktató feltölti a jegyzetét egy felhős csevegő asszisztensbe, '
                                  'és „tíz feleletválasztós kérdést” kér. Ennek négy gyengesége van:', {'size': 16})]],
    margin=0)
P = [('P1', 'A helyesség nincs ellenőrizve – a forrás nem feltétlenül igazolja a kulcsot.'),
     ('P2', 'A szerkezet és a lefedettség nincs kontrollálva – darabszám, nehézség csak kérés.'),
     ('P3', 'Adatvédelem – a tananyag harmadik félhez kerül (GDPR).'),
     ('P4', 'Nagy, távoli modell kell – a teljes dokumentum hosszú kontextust igényel.')]
for i, (k, t) in enumerate(P):
    col, row = i % 2, i // 2
    box(s, X0 + col * 4.85, 2.35 + row * 1.0, 4.65, 0.85, [[(k + '  ', {'font': HEAD, 'color': BLUE}), (t, {'size': 14})]],
        fill=TINT, anchor=MSO_ANCHOR.MIDDLE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.15)
box(s, X0, 4.5, X1 - X0, 0.45, [[('Célkitűzések (kutatási kérdések)', {'font': HEAD, 'size': 17})]], margin=0)
bullets(s, X0, 4.95, X1 - X0, 2.0, [
    ('RQ1:', 'Jobb-e a lépésekre bontott, forráshoz kötött és ellenőrzött generálás, mint egyetlen prompt?'),
    ('RQ2:', 'Mennyit ér és mennyibe kerül az egyes komponens (terv, ellenőrző, gráf, keresés, darabolás)?'),
    ('RQ3:', 'Mennyire közelíti meg egy 8–12 GB-os kártyán futó, 4 bites modell a nagy szervermodellt?')], size=15)
notes(s, '1. ELŐADÓ (kb. 1 perc). A kiinduló gyakorlat egyszerű, de négy ponton gyenge: P1 a kulcs helyessége, '
         'P2 a szerkezet és lefedettség, P3 az adatvédelem, P4 a nagy modell igénye. A P3 és a P4 egymást erősíti: '
         'helyi futtatással megoldódna az adatvédelem, de a kis modellek éppen az ilyen hosszú, egylépéses '
         'feladatban gyengék. Három kutatási kérdést tettünk fel (RQ1–RQ3).')

# ======================================================================== 4. elméleti háttér
s = new_slide('Elméleti háttér rövid bemutatása', 1)
bullets(s, X0, 1.5, 6.1, 5.3, [
    ('Kérdésgenerálás:', 'a szabályalapú és neurális rendszerektől a nagy nyelvi modellekig; a gépi kérdések egy része '
                         'hibás kulcsú (GPT-4: 4,9 %-ban több helyes válasz).'),
    ('RAG és darabolás:', 'naiv, fejlett és moduláris RAG; a szemantikus darabolás előnye adatkészletfüggő.'),
    ('Felbontás és ellenőrzés:', 'tervezés, majd végrehajtás; az önellenőrzés külső információ nélkül keveset ér.'),
    ('Mérés:', 'nyelvi modell mint bíró; a dokumentum mint statisztikai egység, Holm-korrekció.'),
    ('Jogi keret:', 'GDPR (adattakarékosság), MI-rendelet: a tanár által ellenőrzött kérdésgenerálás nem magas kockázatú.')],
    size=15)
box(s, 9.65, 1.5, 3.2, 5.3, [
    [('101', {'font': HEAD, 'size': 40, 'color': BLUE})],
    [('hivatkozott forrás', {'font': HEAD, 'size': 15})],
    [('hazai (PULI-modellek, HuLU, MILQA, NAIH) és nemzetközi szakirodalom', {'size': 13, 'color': GRAY})],
    [('', {'size': 8})],
    [('Kutatási rés', {'font': HEAD, 'size': 15})],
    [('Tudomásunk szerint nincs nyílt rendszer, amely terv, kérdésenkénti forrás és ellenőrzés mellett fogyasztói '
      'GPU-n generál vizsgát, és a magyar nyelvű kiértékelés is feltáratlan.', {'size': 13, 'color': GRAY})]],
    fill=TINT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.2)
notes(s, '1. ELŐADÓ (kb. 1 perc). A szakirodalmat öt területen dolgoztuk fel, 101 forrással, hazai és nemzetközi '
         'munkák alapján. A legfontosabb tanulságok: a nagy modellek kérdései között is van hibás kulcsú; a RAG '
         'minőségét a lekérdezés és a darabolás erősen befolyásolja; az önellenőrzés külső információ nélkül keveset '
         'ér. A kutatási rés: nincs olyan nyílt rendszer, amely mindezt fogyasztói GPU-n, ellenőrizhetően végezné.')

# ======================================================================== 5. anyag és módszer I – a módszer
s = new_slide('Anyag és módszer: a javasolt generálási módszer', 2)
flow_row(s, 2.0, 'Alapvonal – naiv RAG (E0): egyetlen modellhívás', GRAY,
         ['Dokumentum', 'Szemantikus darabok', 'Lekérdezés: „10 feleletválasztós kérdés…”', 'A 3 legközelebbi darab',
          '1 hívás: a teljes vizsga'], WHITE)
flow_row(s, 3.85, 'Javasolt módszer (E1–E3): kérdéshelyenként', BLUE,
         ['Vizsgaterv: fogalom, típus, Bloom-szint', 'Keresés a tervezett fogalommal', '1 kérdés forráshivatkozással',
          'Ellenőrző lánc (hiba esetén új kísérlet)', 'Oktatói jóváhagyás'], TINT)
box(s, X0, 5.3, X1 - X0, 1.4, [
    [('Ellenőrző lánc (az olcsótól a drágáig): ', {'font': HEAD, 'size': 14}),
     ('forma · meta-hivatkozás · szivárgás és kérdésforma · hivatkozás · alátámasztottság és disztraktorok (nyelvi '
      'modell) · vak megoldás (nyelvi modell) · duplikátum', {'size': 14})],
    [('A szerkezetről determinisztikus program dönt; a modell egyszerre egy rövid kérdést ír a saját kontextusából.',
      {'size': 14, 'color': GRAY, 'italic': True})]],
    line=LGRAY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.18, anchor=MSO_ANCHOR.MIDDLE)
notes(s, '1. ELŐADÓ (kb. 1,5 perc). Fent az alapvonal: a lekérdezés maga a feladatleírás, a három legközelebbi '
         'darabból egyetlen hívás írja a vizsgát. Lent a javasolt módszer: a vizsgaterv rögzíti, melyik fogalomból, '
         'milyen típusú és Bloom-szintű kérdés készül; minden kérdéshelyre külön keresünk a tervezett fogalommal; a '
         'modell egy kérdést ír, és megnevezi a forrásdarabot; az ellenőrző lánc előbb olcsó szabályokat, majd nyelvi '
         'modellt futtat, hiba esetén visszajelzéssel újrapróbál. A végső döntés az oktatóé. '
         'ÁTADÁS a 2. előadónak: a kísérleti tervről és az eredményekről ő beszél.')

# ======================================================================== 6. anyag és módszer II – kísérleti terv
s = new_slide('Anyag és módszer II.: kísérleti terv és hipotézisek', 2)
for i, (n, l, d) in enumerate([('30', 'dokumentum', '27 magyar, 3 angol'), ('14', 'konfiguráció', 'egyszerre egy tényező'),
                               ('3', 'helyi modell', 'Qwen2.5-7B, PULI-LlumiX 8B, Gemma 3 12B'),
                               ('11 100+', 'pontozott kérdés', 'három vizsgálatban')]):
    stat(s, X0 + i * 2.42, 1.45, 2.25, n, l, d)
MW = 5.25                                  # width of the "how we measure" box
measure = [
    ('Minőségi index (Q, 0–1):', 'négy arány átlaga – hibátlan formájú-e a vizsga (F), igazolja-e a forrás a '
                                 'helyes választ (G), eltalálja-e a bíró a választ a kulcs ismerete nélkül (A), és '
                                 'valóban rosszak-e a rossz válaszok (V).'),
    ('Bíró:', 'egy független, más modellcsaládba tartozó nagy nyelvi modell pontozza a kérdéseket; öt oktató '
              'vakon ellenőrizte.'),
    ('Statisztika:', 'a konfigurációkat dokumentumonként, párosan vetjük össze (Wilcoxon-próba). Sok összevetésnél '
                     'a véletlen is adhat „szignifikáns” eredményt, ezért a p-értékeket Holm-korrekcióval '
                     'szigorítjuk (p̃).'),
    ('Egyezés:', 'κ és α – 0: csak véletlenszerű, 1: teljes egyezés; ρ – mennyire azonos két rangsor.')]
paras = [[('Hogyan mérünk?', {'font': HEAD, 'size': 15})]]
for label, text in measure:
    paras.append([(label + ' ', {'font': HEAD, 'size': 12, 'color': BLUE}), (text, {'size': 12})])
box(s, X0, 3.45, MW, 3.4, paras, fill=TINT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.16)
hx = X0 + MW + 0.3
box(s, hx, 3.45, X1 - hx, 0.4, [[('Hipotézisek', {'font': HEAD, 'size': 15})]], margin=0)
bullets(s, hx, 3.9, X1 - hx, 2.95, [
    ('H1:', 'A vizsgaterv a naiv RAG-hoz képest növeli az alátámasztottságot (G) és a lefedettséget.'),
    ('H2:', 'Az ellenőrző lánc tovább javít, és ítélete egyezik a bíróéval.'),
    ('H3:', 'A teljes dokumentumot kapó alapvonal lefedettsége alacsonyabb.'),
    ('H4:', 'A helyi kis modell megközelíti a szervermodell naiv változatát (Q-különbség < 0,1).'),
    ('H5:', 'A bíró megbízhatóan egyezik az oktatókkal (α ≥ 0,667).')], size=13)
notes(s, '2. ELŐADÓ (kb. 1,5 perc). Saját, nyílt kiértékelő keretrendszert építettünk: 30 dokumentum, 14 '
         'konfiguráció, amelyek mindegyike egyetlen tényezőben tér el a referenciájától, három helyi modell, több '
         'mint 11 100 pontozott kérdés. Hogyan mérünk: a minőségi index négy arány átlaga – formailag hibátlan-e a '
         'vizsga, a forrás igazolja-e a helyes választ, kitalálható-e a helyes válasz a kulcs nélkül, és valóban '
         'rosszak-e a rossz válaszok. A pontozást egy független, más modellcsaládba tartozó nyelvi modell, a bíró '
         'végzi; ezt öt oktató vak értékelésével ellenőriztük. A konfigurációkat dokumentumonként, párosan '
         'hasonlítjuk össze; mivel sok összevetést végzünk, a p-értékeket Holm-korrekcióval szigorítjuk, hogy a '
         'véletlen ne tűnjön hatásnak. Az egyezést κ-val és α-val mérjük: 0 a véletlen, 1 a teljes egyezés. Öt '
         'hipotézist vizsgáltunk.')

# ======================================================================== 7. eredmények I – fő eredmény
s = new_slide('Főbb kutatási eredmények I.: a vizsgaterv hatása', 3)
cats = ['Naiv RAG (E0)', 'Vizsgaterv (E1)', '+ Ellenőrzés (E2)', 'Teljes dokumentum']
bar_chart(s, X0, 1.4, 6.3, 5.45, cats, [('PULI-LlumiX 8B', [0.28, 0.54, 0.67, 0.41]), ('Gemma 3 12B', [0.72, 0.95, 0.95, 0.96])],
          [ORANGE, NAVY], 'Minőségi index (Q), fő vizsgálat, 30 dokumentum')
for i, (n, l, d, c) in enumerate([('+0,26', 'PULI-LlumiX 8B', 'tervezés vs. naiv RAG; 27 dokumentumon jobb; Holm p < 0,001', ORANGE),
                                  ('+0,23', 'Gemma 3 12B', 'tervezés vs. naiv RAG; 22 dokumentumon jobb; Holm p = 0,002', NAVY)]):
    stat(s, 9.95, 1.55 + i * 2.05, 2.9, n, l, d, color=c)
box(s, 9.95, 5.7, 2.9, 1.1, [[('Qwen2.5-7B (6 dokumentum): ', {'font': HEAD, 'size': 13, 'color': BLUE}),
                              ('0,64 → 0,88 → 0,96; teljes dok. 0,83', {'size': 13})]], fill=TINT,
    shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.12, anchor=MSO_ANCHOR.MIDDLE)
source(s)
notes(s, '2. ELŐADÓ (kb. 1,5 perc). A dolgozat legerősebb eredménye: a vizsgaterv mindkét modellnél nagyot javít a '
         'naiv RAG-hoz képest, a PULI-nál +0,26, a Gemmánál +0,23, Holm-korrekció után is szignifikánsan; a Qwennél '
         'az előzetes vizsgálatban ugyanez az irány. A haszon modellfüggő: a gyenge PULI-nál a teljes módszer 0,67, a '
         'teljes dokumentumos prompt csak 0,41; az erős Gemmánál a teljes dokumentumos prompt is 0,96.')

# ======================================================================== 8. eredmények II – darabolás
s = new_slide('Főbb kutatási eredmények II.: a naiv RAG törékenysége', 3)
bar_chart(s, X0, 1.4, 5.6, 5.45, ['Qwen2.5-7B (6 dok.)', 'PULI-LlumiX 8B', 'Gemma 3 12B'],
          [('Szemantikus darabolás (E0)', [0.64, 0.28, 0.72]), ('Rögzített, 800 karakteres darabok (E5c)', [0.86, 0.25, 0.97])],
          [LGRAY, BLUE], 'Naiv RAG, minőségi index (Q)')
bullets(s, 9.15, 1.5, 3.7, 3.6, [
    ('1.', 'A lekérdezés feladatleírás: „10 feleletválasztós kérdés, könnyű”.'),
    ('2.', 'A szemantikus darabolás rövid, tartalom nélküli darabokat is vág.'),
    ('3.', 'A tartalom nélküli lekérdezés éppen ezekhez van a legközelebb.')], size=14)
box(s, 9.15, 5.0, 3.7, 1.75, [[('Példa (Gemma): ', {'font': HEAD, 'size': 13, 'color': ORANGE}),
                               ('„Mi a nehézségi szint a vizsgának?” – kulcs: „Kezdő (könnyű).”', {'size': 13, 'italic': True})],
                              [('Rögzített darabolással a 0,70 alatti dokumentumok száma 16-ról 0-ra csökkent.', {'size': 13})]],
    line=ORANGE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.14)
source(s)
notes(s, '2. ELŐADÓ (kb. 1 perc). A naiv RAG gyengesége nem a keresés: a referenciakérdésekkel a jó darab az esetek '
         '86 %-ában az első három találat között volt. A hiba a lekérdezés: feladatleírás, és a szemantikus darabolás '
         'rövid, tartalom nélküli darabjaihoz áll a legközelebb. Rögzített darabolással ugyanez a naiv RAG a Gemmánál '
         '0,72-ről 0,97-re javul. A gyenge PULI-nál ez sem segít: ott a formátumkövetés a szűk keresztmetszet.')

# ======================================================================== 9. eredmények III – komponensek
s = new_slide('Főbb kutatási eredmények III.: a komponensek hatása', 3)
rows = [('Összevetés', 'PULI Δ', 'PULI p̃', 'Gemma Δ', 'Gemma p̃', 'Értékelés'),
        ('Tervezés (E1–E0)', '+0,26', '< 0,001', '+0,23', '0,002', 'megéri'),
        ('Ellenőrzés (E2–E1)', '+0,13', '0,066', '+0,01', '1,00', 'modellfüggő'),
        ('Teljes módszer (E2–E0)', '+0,39', '< 0,001', '+0,23', '< 0,001', 'megéri'),
        ('Módszer vs. teljes dok. (E2–B-doc-L)', '+0,26', '< 0,001', '−0,01', '1,00', 'gyenge modellnél'),
        ('Csak szabályok (E2x–E2)', '0,00', '0,975', '−0,02', '1,00', 'a szabályok viszik'),
        ('Fogalomgráf (E3–E2)', '−0,10', '0,775', '−0,01', '1,00', 'nem éri meg')]
tbl = s.shapes.add_table(len(rows), len(rows[0]), Inches(X0), Inches(1.5), Inches(X1 - X0), Inches(4.4)).table
widths = [3.35, 1.05, 1.1, 1.05, 1.1, 1.9]
for j, wdt in enumerate(widths):
    tbl.columns[j].width = Inches(wdt)
for i, r in enumerate(rows):
    for j, val in enumerate(r):
        c = tbl.cell(i, j)
        c.text = val
        p = c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if j in (0, 5) else PP_ALIGN.CENTER
        f = p.runs[0].font
        f.size = Pt(13); f.name = HEAD if i == 0 else BODY
        f.color.rgb = WHITE if i == 0 else NAVY
        f.bold = i > 0 and j in (2, 4) and val.startswith('<')
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY if i == 0 else (TINT if i % 2 == 0 else WHITE)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
box(s, X0, 6.05, X1 - X0, 0.8, [[('Δ: a minőségi index változása; p̃: Holm-korrigált p-érték (páros Wilcoxon-próba, 30 dokumentum). '
                                  'A hibrid keresés (E2h) sem javított szignifikánsan.', {'size': 12, 'color': GRAY})]], margin=0)
notes(s, '2. ELŐADÓ (kb. 1 perc). A tervezett összehasonlítások: a tervezés és a teljes módszer mindkét modellnél '
         'szignifikáns. Az ellenőrzés a PULI-nál +0,13, de Holm után nem szignifikáns, a Gemmánál nulla; a csak '
         'szabályalapú változat ugyanannyit ér, tehát a lánc haszna a szabályokból jön. A fogalomgráf és a hibrid '
         'keresés nem érte meg. ÁTADÁS a 3. előadónak: a modellek összevetése és a következtetések.')

# ======================================================================== 10. eredmények IV – modellek
s = new_slide('Főbb kutatási eredmények IV.: a generátormodellek', 3)
bar_chart(s, X0, 1.4, 6.0, 5.45, ['Naiv RAG (E0)', 'Teljes módszer (E2)', 'Teljes dok. (B-doc-L)'],
          [('Qwen2.5-7B', [0.64, 0.96, 0.83]), ('PULI-LlumiX 8B', [0.32, 0.72, 0.49]), ('Gemma 3 12B', [0.71, 0.97, 0.97])],
          [BLUE, ORANGE, NAVY], 'Minőségi index ugyanazon a hat dokumentumon')
box(s, 9.55, 1.5, 3.3, 0.5, [[('A PULI-LlumiX 8B kudarca', {'font': HEAD, 'size': 15})]], margin=0)
for i, (n, d) in enumerate([('1,8', 'kérdés hívásonként a kért 10 helyett'),
                            ('1–6 %', 'formai megfelelés egy hívásban'),
                            ('34 %', 'szivárgó kulcs ellenőrzés nélkül')]):
    box(s, 9.55, 2.05 + i * 0.85, 1.25, 0.7, [[(n, {'font': HEAD, 'size': 22, 'color': ORANGE})]], margin=0, anchor=MSO_ANCHOR.MIDDLE)
    box(s, 10.85, 2.05 + i * 0.85, 2.0, 0.7, [[(d, {'size': 12})]], margin=0, anchor=MSO_ANCHOR.MIDDLE)
box(s, 9.55, 4.7, 3.3, 2.1, [[('A Llama 3.1 8B Instruct magyar továbbelőtanítása, utólagos utasítás-hangolás nélkül. '
                               'Memória: Qwen 4,8 GiB, PULI 5,5 GiB (8 GB-os kártya), Gemma 7,8 GiB (12 GB-os kártya).',
                               {'size': 12, 'color': GRAY})]], fill=TINT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.14)
source(s)
notes(s, '3. ELŐADÓ (kb. 1,5 perc). Ugyanazon a hat dokumentumon a sorrend minden konfigurációban Gemma, Qwen, '
         'PULI. Ugyanaz a teljes módszer a PULI-val 0,72, a Gemmával 0,97: a modellválasztás többet számít bármely '
         'komponensnél. A magyarra továbbtanított PULI a magyar szövegeken is a leggyengébb, mert nem követi az '
         'utasítást: egy hívásban átlagosan 1,8 kérdést ír a kért tíz helyett. A következtetést erre a '
         'továbbelőtanított, utólag nem hangolt modellre szűkítjük.')

# ======================================================================== 10b. eredmények V – oktatói értékelés
s = new_slide('Főbb kutatási eredmények V.: a bíró és az oktatók', 3)
bar_chart(s, X0, 1.4, 6.0, 5.45, ['Gemma 3 12B', 'Qwen2.5-7B', 'PULI-LlumiX 8B'],
          [('Oktatók (5 fő)', [4.22, 3.94, 2.55]), ('Bíró (gpt-oss-120b)', [4.61, 4.44, 3.78])],
          [NAVY, LGRAY], 'Átlagpontszám (1–5), 60 vakon értékelt kérdés', vmax=500, unit=100)
box(s, 9.55, 1.5, 3.3, 0.5, [[('5 oktató · 60 kérdés · vak értékelés', {'font': HEAD, 'size': 15})]], margin=0)
for i, (n, d) in enumerate([('ρ = 0,77', 'a hat konfiguráció sorrendje egyezik a bíró és az oktatók szerint'),
                            ('α = 0,62', 'bíró–oktatók egyezése a helyességen (küszöb: 0,667)'),
                            ('70 % vs. 45 %', 'felhasználható kérdés a bíró, illetve az oktatói többség szerint')]):
    box(s, 9.55, 2.1 + i * 1.3, 3.3, 0.55, [[(n, {'font': HEAD, 'size': 24, 'color': ORANGE if i else BLUE})]], margin=0)
    box(s, 9.55, 2.65 + i * 1.3, 3.3, 0.65, [[(d, {'size': 12, 'color': GRAY})]], margin=0)
box(s, 9.55, 6.0, 3.3, 0.8, [[('A bíró rangsorolásra jó, abszolút szintre engedékeny – leginkább a gyenge modellnél.',
                              {'size': 12})]], fill=TINT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.12,
    anchor=MSO_ANCHOR.MIDDLE)
source(s)
notes(s, '3. ELŐADÓ (kb. 1 perc). A bírót öt oktató vak értékelésével ellenőriztük: hat konfigurációból 60 kérdést '
         'pontoztak ugyanazzal a rubrikával. A sorrend egyezik: az oktatók szerint is a Gemma a legjobb és a PULI a '
         'leggyengébb, a hat konfiguráció rangsora ρ = 0,77-tel egyezik. Az abszolút pontszámok viszont nem: a bíró '
         'minden szempontban engedékenyebb, a helyességen α = 0,62, a küszöb 0,667 alatt; a kérdések 70 %-át '
         'használná fel, az oktatók 45 %-át. A legnagyobb a különbség a PULI-nál, több mint egy pont. Ezért a bíró '
         'számait összevetésre használjuk, abszolút minőségként felső becslésnek tekintjük. Az oktatók egymás közt '
         'is csak a helyességen egyeztek erősen (α = 0,69).')

# ======================================================================== 11. hipotézisvizsgálat
s = new_slide('A hipotézisvizsgálat eredményei', 3)
hyp = [('Hipotézis', 'Eredmény', 'Mit találtunk?'),
       ('H1 – vizsgaterv', 'Igazolást nyert',
        'A vizsgaterv mindkét modellnél jobb vizsgát adott, mint a naiv RAG (Q +0,26 és +0,23); a különbség a '
        'Holm-korrekció után is szignifikáns.'),
       ('H2 – ellenőrzés', 'Nem igazolódott',
        'Az ellenőrző lánc után nem lett több forrással igazolt kérdés, és az ellenőrző ítélete csak a véletlen '
        'szintjén egyezik a bíróéval (κ ≈ 0).'),
       ('H3 – lefedettség', 'Nem igazolódott',
        'A teljes dokumentumot kapó modell ugyanakkora részét fedi le a dokumentumnak, mint a tervezett módszer '
        '(43 % vs. 43 %).'),
       ('H4 – helyi vs. szerver', 'Igazolást nyert',
        'A 8 GB-os kártyán futó Qwen a módszerrel elérte a szervermodell egyszerű változatait (Q 0,96 vs. 0,95); '
        'a gyenge PULI-val nem.'),
       ('H5 – bíró vs. oktatók', 'Nem igazolódott',
        'A bíró ugyanúgy rangsorol, mint az oktatók (ρ = 0,77), de engedékenyebb: a helyességen α = 0,62, az '
        'elvárt 0,667 alatt.')]
tbl = s.shapes.add_table(len(hyp), 3, Inches(X0), Inches(1.5), Inches(X1 - X0), Inches(5.2)).table
for j, wdt in enumerate([2.2, 1.75, 5.6]):
    tbl.columns[j].width = Inches(wdt)
verdict_color = {'Igazolást nyert': RGBColor(0x2E, 0x7D, 0x4F), 'Nem igazolódott': ORANGE,
                 'Részben igazolódott': BLUE, 'Folyamatban': GRAY}
for i, r in enumerate(hyp):
    for j, val in enumerate(r):
        c = tbl.cell(i, j)
        c.text = val
        f = c.text_frame.paragraphs[0].runs[0].font
        f.size = Pt(13); f.name = HEAD if (i == 0 or j < 2) else BODY
        f.color.rgb = WHITE if i == 0 else (verdict_color.get(val, NAVY) if j == 1 else NAVY)
        c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else (TINT if i % 2 == 0 else WHITE)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
source(s, 'Forrás: saját szerkesztés')
notes(s, '3. ELŐADÓ (kb. 1 perc). A H1 igazolást nyert: a vizsgaterv mindkét modellnél jobb vizsgát ad, mint a '
         'naiv RAG, és ez a szigorított próbán is megáll. A H2 a fő vizsgálatban nem: az ellenőrzés után sem lett '
         'több forrással igazolt kérdés, és az ellenőrző ítélete csak véletlenszerűen egyezik a bíróéval. A H3 sem: '
         'a teljes dokumentumot kapó modell nem tömöríti a kérdéseit a dokumentum egy részére. A H4 leíró szinten '
         'igen: a Qwen a módszerrel eléri a szervermodell teljes dokumentumos promptjának és naiv RAG-jának '
         'szintjét, de ez a modellen múlik, a PULI-val nem teljesül. A H5 nem: a bíró ugyanúgy rangsorol, mint az '
         'oktatók, de magasabb pontot ad, így az egyezése az elvárt szint alatt marad.')

# ======================================================================== 12. új eredmények
s = new_slide('A tudományos munka új és újszerű eredményei', 4)
bullets(s, X0, 1.55, X1 - X0, 5.2, [
    ('(1)', 'Tervezésvezérelt, forráshivatkozásos generálási módszer, amely fogyasztói GPU-n (8–12 GB) futó, 4 bites '
            'modellel működik; a terv a darabszámot, a típust és a Bloom-szintet kikényszeríti.'),
    ('(2)', 'Nyílt, egytényezős kiértékelő keretrendszer forrásalapú mutatókkal, független bíróval és dokumentumszintű '
            'statisztikával – tudomásunk szerint az első rendszerszintű magyar nyelvű vizsgakérdés-generálási kiértékelés.'),
    ('(3)', 'Mechanizmus a naiv RAG kudarcára: a feladatleírás mint lekérdezés és a minimális méret nélküli szemantikus '
            'darabolás együtt tartalom nélküli kérdésekhez vezet; rögzített darabolással 0,72 → 0,97 (Gemma).'),
    ('(4)', 'A lépésekre bontás haszna a modell képességével csökken: gyenge modellnél nélkülözhetetlen, erősnél az '
            'ellenőrizhetőséget adja.')], size=18)
notes(s, '3. ELŐADÓ (kb. 1 perc). Négy újszerű eredményt emelünk ki: a módszert, a nyílt kiértékelő '
         'keretrendszert – tudomásunk szerint ez az első rendszerszintű magyar nyelvű kiértékelés a témában –, a naiv '
         'RAG kudarcának mechanizmusát, és azt, hogy a felbontás haszna a modell képességétől függ.')

# ======================================================================== 13. következtetések
s = new_slide('Következtetések, kiemelt tanulságok', 4)
bullets(s, X0, 1.55, 5.9, 5.2, [
    ('K1:', 'A minőséget elsősorban a modell és a visszakeresés lekérdezése határozza meg, nem egy-egy komponens.'),
    ('K2:', 'Az ellenőrző lánc a vizsgát javítja (szűrő, második esély), de kérdésenkénti jelzése nem ítélet – csak '
            'figyelmeztetés az oktatónak.'),
    ('K3:', 'A mérés is eredmény: a csendes hibákat csak a nyers kimenetek kézi átnézése tárja fel.'),
    ('K4:', 'A bíró a konfigurációk rangsorolására alkalmas, abszolút minőségre nem: az oktatók szigorúbbak.')], size=18)
box(s, 9.45, 1.55, 3.4, 4.55, [
    [('Három csendes mérési hiba', {'font': HEAD, 'size': 15})],
    [('20 %', {'font': HEAD, 'size': 26, 'color': ORANGE})],
    [('válaszszivárgás a pilotban – a bíró mégis 5/5-öt adott', {'size': 12, 'color': GRAY})],
    [('κ ≈ 0', {'font': HEAD, 'size': 26, 'color': ORANGE})],
    [('az ellenőrző és a bíró kérdésenkénti egyezése', {'size': 12, 'color': GRAY})],
    [('42–55 %', {'font': HEAD, 'size': 26, 'color': ORANGE})],
    [('a Wikipédia-kérdések bírói ítéletaránya (az angol kérdéseknél szinte mind)', {'size': 12, 'color': GRAY})]],
    fill=TINT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.2)
notes(s, '3. ELŐADÓ (kb. 1 perc). Három következtetés: a modell és a lekérdezés számít a legtöbbet; az ellenőrzés a '
         'vizsgát javítja, de a jelzése kérdésenként nem megbízható ítélet; a mérést magát is ellenőrizni kell – '
         'három csendes hibát csak a nyers kimenetek átnézése tárt fel; és a bíró a konfigurációk összevetésére '
         'jó, de az oktatóknál engedékenyebb, ezért az abszolút arányai felső becslések.')

# ======================================================================== 14. javaslatok
s = new_slide('Javaslattétel és jövőbeni irányok', 4)
for i, (tier, conf, kpi, note, col) in enumerate([
        ('8 GB-os kártya', 'Qwen2.5-7B + teljes módszer (E2)', 'Q 0,96 · legrosszabb dokumentum 0,89 · ≈ 11× idő',
         'a szervermodell teljes dokumentumos promptjának szintje, kérdésenkénti forrással', BLUE),
        ('12 GB-os kártya', 'Gemma 3 12B + vizsgaterv (E1–E2)', 'Q 0,95 · ≈ 5–8,5× idő',
         'gyors vázlathoz a rögzített darabolású naiv RAG: Q 0,97, ≈ 1× – forrás és terv nélkül', NAVY)]):
    box(s, X0 + i * 4.85, 1.5, 4.65, 2.2, [
        [('J' + str(i + 1) + ': ' + tier, {'font': HEAD, 'size': 17, 'color': col})],
        [(conf, {'font': HEAD, 'size': 14})],
        [(kpi, {'size': 13})],
        [(note, {'size': 12, 'color': GRAY})]], fill=TINT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, margin=0.18)
bullets(s, X0, 4.0, X1 - X0, 2.8, [
    ('J3:', 'Nem ajánlott: fogalomgráf, hibrid keresés; az LLM-ellenőrző jelzése csak figyelmeztetésként.'),
    ('Jövő:', 'a bíró kalibrálása nagyobb oktatói mintán; a hiányzó bírói ítéletek újrapontozása; adaptív ellenőrzés; a darabolás hatása '
              'a tervezett folyamatra; tételelemzés valós hallgatói válaszokon.')], size=17)
notes(s, '3. ELŐADÓ (kb. 1 perc). A mérésekből ajánlás következik: 8 GB-os kártyán a Qwen2.5-7B a teljes módszerrel, '
         '12 GB-on a Gemma 3 12B a vizsgatervvel; gyors vázlathoz a rögzített darabolású naiv RAG is elég, de forrás és '
         'terv nélkül. A fogalomgráf és a hibrid keresés nem éri meg. A további munka legfontosabb lépése a bíró '
         'kalibrálása nagyobb oktatói mintán, hogy engedékenységét korrigálni lehessen.')

# ======================================================================== 15–16. köszönet, bírálói kérdések (sablon)
s15, s16 = T[14], T[15]
for sh in s15.shapes:
    if sh.has_text_frame and 'Köszönöm' in sh.text_frame.text:
        set_text(sh.text_frame, 'Köszönjük a megtisztelő figyelmüket!')
notes(s15, '3. ELŐADÓ. Megköszönjük a figyelmet, és átadjuk a szót a Bizottságnak.')
for sh in s16.shapes:
    if sh.has_text_frame and 'Vezesse fel' in sh.text_frame.text:
        for para in sh.text_frame.paragraphs:
            for r in para.runs:
                if 'Vezesse fel' in r.text:
                    r.text = '[A bírálói kérdés] – válasz: [rövid válasz]'
notes(s16, 'Tartalék dia: ide kerülnek a bírálatokban szereplő kérdések és a rövid válaszok, ha a bírálatok megérkeztek.')

# ---------------------------------------------------------------- order and cleanup
sld_ids = prs.slides._sldIdLst
items = list(sld_ids)
keep_first = [items[0], items[1]]
template_rest = items[2:16]
new = items[16:]
drop = [it for it in template_rest if it not in (items[14], items[15])]
for it in drop:
    prs.part.drop_rel(it.rId)
    sld_ids.remove(it)
# final order: title, agenda, new slides, thanks, questions
for it in new:
    sld_ids.remove(it)
thanks, questions = items[14], items[15]
sld_ids.remove(thanks); sld_ids.remove(questions)
for it in new + [thanks, questions]:
    sld_ids.append(it)

prs.save(OUT)
print('written', OUT, 'slides:', len(prs.slides))
