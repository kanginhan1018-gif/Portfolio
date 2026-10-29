"""Small builder that reuses the look of milp-acceleration-v2.pptx (cards, fonts, theme colors)."""
import copy, math, os, re
from lxml import etree
from pptx import Presentation

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
A_NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
FONT = ('<a:latin typeface="Apple SD Gothic Neo" pitchFamily="34" charset="0"/>'
        '<a:ea typeface="Apple SD Gothic Neo" pitchFamily="34" charset="-122"/>'
        '<a:cs typeface="Apple SD Gothic Neo" pitchFamily="34" charset="-120"/>')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TEMPLATE = os.path.join(HERE, 'template.pptx')   # slide 1 = cover, slide 2 = any content slide (title + page number)


def out(name):
    """Output path: $PPT_OUT/name, default public/papers/name."""
    return os.path.join(os.environ.get('PPT_OUT', os.path.join(ROOT, 'public', 'papers')), name)


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def runs_xml(text, size, color='tx1', bold=False):
    """'**x**' -> bold accent1 run, '``x``' -> bold tx2 run."""
    out = []
    for part in re.split(r'(\*\*.+?\*\*|``.+?``)', text):
        if not part:
            continue
        b, c, t = bold, color, part
        if part.startswith('**'):
            b, c, t = True, 'accent1', part[2:-2]
        elif part.startswith('``'):
            b, c, t = True, 'tx2', part[2:-2]
        out.append(f'<a:r><a:rPr lang="en-US" sz="{int(size*100)}" b="{1 if b else 0}" dirty="0">'
                   f'<a:solidFill><a:schemeClr val="{c}"/></a:solidFill>{FONT}</a:rPr>'
                   f'<a:t>{esc(t)}</a:t></a:r>')
    return ''.join(out)


def para_xml(text, size, color='tx1', bold=False, bullet=True, algn=None, after=6):
    al = f' algn="{algn}"' if algn else ''
    if bullet:
        ppr = (f'<a:pPr marL="228600" indent="-228600"{al}><a:spcAft><a:spcPts val="{int(after*100)}"/></a:spcAft>'
               '<a:buSzPct val="100000"/><a:buChar char="&#8226;"/></a:pPr>')
    else:
        ppr = (f'<a:pPr marL="0" indent="0"{al}><a:spcAft><a:spcPts val="{int(after*100)}"/></a:spcAft><a:buNone/></a:pPr>')
    return f'<a:p>{ppr}{runs_xml(text, size, color, bold)}</a:p>'


def visual_len(t):
    t = re.sub(r'\*\*|``', '', t)
    n = 0.0
    for ch in t:
        o = ord(ch)
        if o > 0x2E80 or 0xAC00 <= o <= 0xD7A3 or ch in '→←⇒≤≥≠≈×·∈∞':
            n += 1.0
        elif ch == ' ':
            n += 0.35
        elif ch.isdigit() or ch.isalpha():
            n += 0.56
        else:
            n += 0.5
    return n


def est_height(items, width, size, after=6, indent=228600):
    tot = 0
    for text, bullet in items:
        avail = (width - (indent if bullet else 0)) / 12700 / size
        lines = max(1, math.ceil(visual_len(text) / avail * 1.04))
        tot += lines * size * 1.32 + after
    return tot * 12700


def parse_items(items):
    return [(it[1:].lstrip(), False) if it.startswith('~') else (it, True) for it in items]


def fit_size(items, width, height, start=16, lo=10.5):
    sz = start
    while sz > lo:
        if est_height(items, width, sz) <= height:
            return sz
        sz -= 0.5
    return lo


def sp_xml(idn, name, x, y, w, h, body, anchor='t'):
    return (f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="{idn}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" rtlCol="0" anchor="{anchor}"/>'
            f'<a:lstStyle/>{body}</p:txBody></p:sp>')


def card_xml(idn, name, x, y, w, h, adj=2264, fill='bg2'):
    return (f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="{idn}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst></a:prstGeom>'
            f'<a:solidFill><a:schemeClr val="{fill}"/></a:solidFill>'
            f'<a:ln w="12700"><a:solidFill><a:schemeClr val="{fill}"/></a:solidFill><a:prstDash val="solid"/></a:ln></p:spPr></p:sp>')


class Deck:
    def __init__(self):
        self.prs = Presentation(TEMPLATE)
        s16 = self.prs.slides[1]
        by = {sh.shape_id: sh for sh in s16.shapes}
        self.title_el = copy.deepcopy(by[2]._element)
        self.num_el = copy.deepcopy(by[25]._element)
        self.layout = s16.slide_layout
        s1 = self.prs.slides[0]
        self.cover_layout = s1.slide_layout
        self.cover_els = [copy.deepcopy(sh._element) for sh in s1.shapes]
        lst = self.prs.slides._sldIdLst
        for sid in list(lst):
            self.prs.part.drop_rel(sid.rId)
            lst.remove(sid)
        self.n = 100
        self.sizes = []   # (slide_no, kind, font sizes) for review

    def _id(self):
        self.n += 1
        return self.n

    def _add(self, slide, xml):
        slide.shapes._spTree.append(etree.fromstring(xml))

    def _blank(self, layout):
        s = self.prs.slides.add_slide(layout)
        for sh in list(s.shapes):
            sh._element.getparent().remove(sh._element)
        return s

    def cover(self, topic, subtitle, refs, kicker='논문 리뷰 · 과외 노트'):
        s = self._blank(self.cover_layout)
        for el in self.cover_els:
            s.shapes._spTree.append(copy.deepcopy(el))
        S = {sh.shape_id: sh for sh in s.shapes}

        def setruns(sh, texts):
            for para, t in zip(sh.text_frame.paragraphs, texts):
                para.runs[0].text = t
                for r in para.runs[1:]:
                    r._r.getparent().remove(r._r)
        setruns(S[2], [kicker])
        setruns(S[3], [topic, subtitle])
        setruns(S[4], [refs])
        return s

    def _frame(self, title, footer):
        s = self._blank(self.layout)
        t = copy.deepcopy(self.title_el)
        t.xpath('.//a:t')[0].text = title
        s.shapes._spTree.append(t)
        s.shapes._spTree.append(copy.deepcopy(self.num_el))
        if footer:
            self._add(s, sp_xml(self._id(), 'footer', 548640, 6355080, 10607040, 274320,
                                para_xml(footer, 10, 'accent3', bullet=False, after=0), 'ctr'))
        return s

    def _card(self, s, x, y, w, h, head, items, start=18):
        self._add(s, card_xml(self._id(), 'card', x, y, w, h))
        pad = 228600
        self._add(s, sp_xml(self._id(), 'head', x + pad, y + 150000, w - 2 * pad, 365760,
                            para_xml(head, 16, 'accent1', bold=True, bullet=False, after=0), 'ctr'))
        parsed = parse_items(items)
        ty = y + 150000 + 365760 + 110000
        th = h - (ty - y) - 150000
        tw = w - 2 * pad
        sz = fit_size(parsed, tw, th, start=start)
        body = ''.join(para_xml(t, sz, bullet=b) for t, b in parsed)
        self._add(s, sp_xml(self._id(), 'body', x + pad, ty, tw, th, body))
        return sz

    def two(self, title, lhead, litems, rhead, ritems, footer='', split=0.56):
        s = self._frame(title, footer)
        x0, y0, tw, h = 548640, 1371600, 11064240, 4846320
        gap = 228600
        lw = int((tw - gap) * split)
        rw = tw - gap - lw
        a = self._card(s, x0, y0, lw, h, lhead, litems)
        b = self._card(s, x0 + lw + gap, y0, rw, h, rhead, ritems)
        self.sizes.append((len(self.prs.slides), title, a, b))

    def wide(self, title, head, items, footer=''):
        s = self._frame(title, footer)
        a = self._card(s, 548640, 1371600, 11064240, 4846320, head, items, start=19)
        self.sizes.append((len(self.prs.slides), title, a, None))

    def table(self, title, headers, rows, colw, footer='', note=None, aligns=None):
        s = self._frame(title, footer)
        x0, y = 548640, 1371600
        total = 11064240
        sw = sum(colw)
        ws = [int(total * c / sw) for c in colw]
        pad = 150000
        aligns = aligns or ['l'] * len(headers)
        cx = x0
        for hd, w, al in zip(headers, ws, aligns):
            self._add(s, sp_xml(self._id(), 'th', cx + pad, y, w - 2 * pad, 365760,
                                para_xml(hd, 13, 'accent3', bold=True, bullet=False,
                                         algn='ctr' if al == 'c' else None, after=0), 'ctr'))
            cx += w
        y += 400000
        avail = 6250000 - y - (700000 if note else 0)

        compact = len(rows) >= 8
        gap_r = 40000 if compact else 60000

        def row_h(r, sz):
            m = max(est_height([(c, False)], w - 2 * pad, sz, after=0) for c, w in zip(r, ws))
            return max(m + (110000 if compact else 160000), 330000 if compact else 400000)
        size = 15
        while size > 10.5 and sum(row_h(r, size) + gap_r for r in rows) > avail:
            size -= 0.5
        for r in rows:
            rh = row_h(r, size)
            self._add(s, card_xml(self._id(), 'row', x0, y, total, rh, adj=13793))
            cx = x0
            for c, w, al in zip(r, ws, aligns):
                self._add(s, sp_xml(self._id(), 'cell', cx + pad, y, w - 2 * pad, rh,
                                    para_xml(c, size, bullet=False, algn='ctr' if al == 'c' else None, after=0), 'ctr'))
                cx += w
            y += rh + gap_r
        if note:
            nsz = 15
            self._add(s, sp_xml(self._id(), 'note', x0, y + 40000, total, 650000,
                                para_xml(note, nsz, 'tx2', bullet=False, after=0), 't'))
        self.sizes.append((len(self.prs.slides), title, size, y))

    def save(self, path):
        self.prs.save(path)
        for rec in self.sizes:
            print(rec)
