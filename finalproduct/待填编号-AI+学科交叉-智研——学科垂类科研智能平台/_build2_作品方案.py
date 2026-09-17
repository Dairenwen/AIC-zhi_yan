# -*- coding: utf-8 -*-
"""
Build the 2026AIC AI+学科交叉 作品方案 (技术报告) by copying content verbatim
from the source 技术报告.docx into the official template skeleton.
NO new prose is generated. Only structure/format/typesetting is applied.
"""
import copy
import docx
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, Emu
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = "/Users/drw/Downloads/比赛/AIC-zhi_yan/srcproduct/武汉理工大学—学科垂类大模型与创新应用开发—智研——面向人工智能学科科研全流程赋能的垂类大模型应用系统/05—作品代码/技术报告.docx"
OUT = "/Users/drw/Downloads/比赛/AIC-zhi_yan/finalproduct/待填编号-AI+学科交叉-智研——学科垂类科研智能平台/AIC-2026-待填编号-AI+学科交叉-作品方案.docx"

R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_V = "{urn:schemas-microsoft-com:vml}"
NS_MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
RELATTRS = [qn("r:embed"), qn("r:id"), qn("r:link"), qn("r:pict"), qn("r:dm"),
            qn("r:lo"), qn("r:qs"), qn("r:cs"),
            "{urn:schemas-microsoft-com:office:office}relid"]

EA = "宋体"
LATIN = "Times New Roman"
MAX_IMG_W = Emu(int(Cm(14.8).emu))

# ---------------------------------------------------------------- source index
src = Document(SRC)


def iter_blocks(doc):
    out = []
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            out.append(Paragraph(child, doc))
        elif child.tag == qn("w:tbl"):
            out.append(Table(child, doc))
        else:
            out.append(None)
    return out


# Index ONLY w:p / w:tbl children, in document order (other body-level
# children such as w:bookmarkEnd / w:sectPr must not consume an index).
SBLOCKS = {}
i = 0
for child in src.element.body.iterchildren():
    if child.tag in (qn("w:p"), qn("w:tbl")):
        i += 1
        SBLOCKS[i] = child

# ---------------------------------------------------------------- new document
doc = Document()

# purge the default empty paragraph later; set up base style
st = doc.styles["Normal"]
st.font.name = LATIN
st.font.size = Pt(12)
st._element.rPr.rFonts.set(qn("w:eastAsia"), EA)
st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
st.paragraph_format.space_before = Pt(0)
st.paragraph_format.space_after = Pt(0)


def page_setup(section, a4=True):
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(3)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)
    section.gutter = Cm(0)


def set_run(run, size=12, bold=False, ea=EA, latin=LATIN):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    rf.set(qn("w:ascii"), latin)
    rf.set(qn("w:hAnsi"), latin)
    rf.set(qn("w:eastAsia"), ea)


def fmt_para(p, size=12, bold=False, align=None, indent_chars=0,
             before=0, after=0, keep_next=False):
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if align is not None:
        p.alignment = align
    ppr = p._p.get_or_add_pPr()
    ind = ppr.find(qn("w:ind"))
    if ind is None:
        ind = OxmlElement("w:ind")
        ppr.append(ind)
    for a in ("w:firstLine", "w:firstLineChars", "w:left", "w:leftChars",
              "w:hanging", "w:hangingChars"):
        if ind.get(qn(a)) is not None:
            del ind.attrib[qn(a)]
    if indent_chars:
        ind.set(qn("w:firstLineChars"), str(int(indent_chars * 100)))
        ind.set(qn("w:firstLine"), str(int(size * 20 * indent_chars)))
    if keep_next:
        kn = OxmlElement("w:keepNext")
        ppr.append(kn)
    for r in p.runs:
        set_run(r, size=size, bold=bold)
    return p


def add_para(text="", size=12, bold=False, align=None, indent_chars=0,
             before=0, after=0, keep_next=False):
    p = doc.add_paragraph()
    if text:
        p.add_run(text)
    return fmt_para(p, size, bold, align, indent_chars, before, after, keep_next)


# heading levels: 1 -> 三号16pt bold, 2 -> 四号14pt bold, 3/4 -> 小四12pt bold
HSPEC = {1: (16, 6, 6), 2: (14, 6, 3), 3: (12, 6, 3), 4: (12, 3, 3)}


def add_heading(text, level):
    size, before, after = HSPEC[level]
    p = doc.add_paragraph()
    p.add_run(text)
    fmt_para(p, size=size, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
             indent_chars=0, before=before, after=after, keep_next=True)
    # register as a Word outline level so the TOC field picks it up
    ppr = p._p.get_or_add_pPr()
    ol = OxmlElement("w:outlineLvl")
    ol.set(qn("w:val"), str(level - 1))
    ppr.append(ol)
    return p


def add_blank(n=1):
    for _ in range(n):
        add_para("")


def add_body_lines(lines):
    """Add verbatim body paragraphs (copied from reference-project files)."""
    for ln in lines:
        add_para(ln, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent_chars=2)


def add_arch_figure():
    """Insert the existing 分层架构图 (rendered from 作品方案.pptx slide 2.1)."""
    from docx.opc.packuri import PackURI
    shape = doc.add_picture(ARCH_IMG, width=Cm(14.8))
    # the copied source images already occupy media/image1..image45; force a
    # unique partname so the arch image does not collide with media/image1.png
    rId = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
    part = doc.part.rels[rId].target_part
    existing = {p.partname for p in doc.part.package.iter_parts()}
    n = 46
    while PackURI("/word/media/image%d.png" % n) in existing:
        n += 1
    part.partname = PackURI("/word/media/image%d.png" % n)
    lp = doc.paragraphs[-1]
    fmt_para(lp, 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, 0, before=6, after=0,
             keep_next=True)
    cp = doc.add_paragraph()
    cp.add_run("图0 系统架构")
    fmt_para(cp, 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, 0, before=0, after=6)


def renumber(doc):
    """Renumber figures/tables continuously and fix in-text references."""
    import re
    cap_re = re.compile(r'^(图|表)\s*(\d+)(?:-(\d+))?\s*(.*)$')
    fig = tbl = 0
    mapping = {}
    for p in doc.paragraphs:
        t = p.text.strip()
        m = cap_re.match(t)
        if not m:
            continue
        kind, a, b, title = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        old = "%s%s" % (kind, a) if b is None else "%s%s-%s" % (kind, a, b)
        if kind == "图":
            fig += 1
            new = "图%d" % fig
        else:
            tbl += 1
            new = "表%d" % tbl
        mapping[old] = new
        # rewrite caption with canonical spacing
        for r in list(p.runs):
            r._element.getparent().remove(r._element)
        run = p.add_run("%s %s" % (new, title))
        fmt_para(p, 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, 0, before=0, after=6)

    # replace old references everywhere. The source splits references across runs
    # (e.g. "如图" + "2-1" + "所示"), so replace on the concatenated paragraph text
    # and rewrite the whole paragraph run when anything changed.
    olds = sorted(mapping, key=lambda k: (-len(k), k))
    space_pat = re.compile(r'([图表])\s+(\d+\s*-\s*\d+)')

    def _norm(s):
        return space_pat.sub(r'\1\2', s)

    all_paras = list(doc.paragraphs)
    for tb in doc.tables:
        for row in tb.rows:
            for cell in row.cells:
                all_paras.extend(cell.paragraphs)
    for p in all_paras:
        full = p.text
        if not full:
            continue
        newfull = _norm(full)
        for old in olds:
            newfull = newfull.replace(old, mapping[old])
        if newfull != full:
            # determine whether this paragraph lives inside a table
            in_table = False
            anc = p._p.getparent()
            while anc is not None:
                if anc.tag == qn("w:tbl"):
                    in_table = True
                    break
                anc = anc.getparent()
            size = 10.5 if in_table else 12
            for r in list(p.runs):
                r._element.getparent().remove(r._element)
            run = p.add_run(newfull)
            set_run(run, size=size)
    return mapping


# ---- verbatim content copied from reference-project files (no generation) ----
C_SAITI = [
    "一流学科建设持续推进，大模型加速高校科研范式变革。",
    "项目建设必要性：面向 AI 学科科研场景，构建赋能、增效、协同、创新的智能科研基础设施。",
    "三类一体化协同联动，形成 AI 学科科研完整业务闭环。",
    "从“多个科研 AI 工具”走向“一个完整科研智能系统”。",
]
C_XUEKE = [
    "试用对象：人工智能学科高校教师、本科/硕士/博士研究生（智研助手核心目标用户）。",
    "AI 领域知识更新快、论文密集、方法链复杂，对科研智能工具的专业性与可信性提出更高要求。",
]
C_AIXUQIU = [
    "从“通用问答工具”走向“专业科研智能体系系统”。",
    "通用能力 ≠ 专业科研可信能力。",
    "四类痛点共同制约 AI 科研场景中的专业化、可信化、协同化与自动化应用。",
    "需要构建面向 AI 学科科研全流程的垂类大模型 + 知识库 + 工具链 + 智能体工作流体系。",
]
C_XUANXING = [
    "系统采用前后端分离架构：Vue 3 + TypeScript + Vite 负责交互界面，Flask + SQLAlchemy 提供 API 与任务编排，PostgreSQL 保存用户、任务、项目和产物，内嵌知识库运行时提供切片、检索和问答。",
    "基于 Qwen3.6-27B 与科研领域监督数据，采用 4-bit QLoRA 参数高效微调，提升模型面向科研任务的专业能力与证据忠实性。",
    "融合稀疏 — 稠密混合检索与文献级证据绑定，构建精准召回、动态更新、上下文可控、结果可溯源的科研 RAG 链路。",
    "基于 LangGraph 状态图与统一任务服务，构建“动态编排 — 受控执行 — 协同交互 — 实时监测 — 异常降级”的多智能体科研工作流。",
]
C_KEXINGXING = [
    "平台已部署运行，科研能力、协作组织与任务状态统一管理。",
    "知识库（8530 篇论文）、11 个科研智能体、5 个科研工具、3 个科研智囊团。",
]
C_JIHUA = [
    "以用户反馈为驱动，围绕“稳定性—能力扩展—产品化—规模复制”持续迭代，与商业化推广节奏协同推进。",
    "①短期：稳定优化与效果验证",
    "——调度逻辑优化、条件路由优化、多 Agent 协作、降级策略完善；",
    "——证据约束强化、回答准确性优化、引用一致性检查、幻觉风险控制；",
    "——测试集完善、功能测试、对照实验、用户反馈。",
    "②中期：能力扩展与规模试用",
    "——增加科研数据读取、基础统计分析、数据可视化、实验结果辅助解读；",
    "——重点优化论文文本、图片、表格、公式、图文关联理解；",
    "——工作流可视化、任务状态展示、证据快速查看、结果管理。",
    "③长期：产品成熟与规模复制",
    "——面向高校科研场景形成标准化交付能力；",
    "——私有化部署、知识迁移、平台对接、规模复制；",
    "——实现从单学科试点向多学科、多院系、多高校规模复制。",
]
C_ZIYUAN = [
    "前端使用 Vue 3、TypeScript 和 Vite，后端使用 Flask、SQLAlchemy 和 PostgreSQL。",
    "PostgreSQL 16（主系统 zhiyan schema 与内嵌知识库 knowledge_base schema）、Agent 子进程（论文精读、专利、绘图、翻译等）、外部模型服务（OpenAI 兼容接口 / Ollama）。",
    "可选基础设施：Redis、Milvus Lite、Elasticsearch、GPU/CUDA、短信服务商。",
]
C_TUANDUI = [
    "构建“专家指导+技术互补”的研发团队，支撑“知识—模型—智能体—应用”全链路项目实施。",
    "团队成员分工：Agent 编排、大模型微调、RAG 检索、后端服务、前端平台、测试验证、产品运营。",
    "技术指导、学术把关。",
]
C_BUZU = [
    "主要改进方向集中在：面向本科生的解释通俗化、最新预印本收录时效、私有知识库与课题组建档、长文档生成稳定性、教学场景扩展五个方面，将作为下一版本迭代重点。",
    "——稳定性：项目问答卡顿、API 连接失败或超时、滚动异常；",
    "——记录留存：首页对话未保存到历史；",
    "——语言支持：希望页面支持中英文切换。",
]
C_ZHANWANG = [
    "以用户反馈为驱动，围绕“稳定性—能力扩展—产品化—规模复制”持续迭代，与商业化推广节奏协同推进。",
    "①短期：稳定优化与效果验证；②中期：能力扩展与规模试用；③长期：产品成熟与规模复制。",
    "单学科试点 → 多学科复制 → 多院系拓展 → 多高校推广。",
]
C_DAIMA = [
    "模型权重存放地址：Modelscope 社区；模型权重文件 id：lzx420/qwen3.6-27b-zhiyan；模型权重下载方式：modelscope download --model lzx420/qwen3.6-27b-zhiyan。",
]
ARCH_IMG = "/tmp/aic_work/arch-09.png"


def body_add(el):
    """Append a block INSIDE the body, i.e. before the trailing w:sectPr.

    doc.add_paragraph() already does this, so appending copied elements
    straight onto the body would place them after the section break and
    detach them from the surrounding headings.
    """
    body = doc.element.body
    sect = body.find(qn("w:sectPr"))
    if sect is not None:
        sect.addprevious(el)
    else:
        body.append(el)


# ------------------------------------------------------------- copy machinery
def remap_rels(el):
    """Re-point every relationship reference in a copied element at this doc."""
    todo = []
    for node in el.iter():
        for attr in RELATTRS:
            rid = node.get(attr)
            if rid:
                todo.append((node, attr, rid))
    cache = {}
    for node, attr, rid in todo:
        if rid in cache:
            node.set(attr, cache[rid])
            continue
        rel = src.part.rels.get(rid)
        if rel is None:
            continue
        if rel.is_external:
            new = doc.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
        else:
            new = doc.part.relate_to(rel.target_part, rel.reltype)
        cache[rid] = new
        node.set(attr, new)


def clamp_images(el):
    for ext in el.iter(qn("wp:extent")):
        cx, cy = int(ext.get("cx")), int(ext.get("cy"))
        if cx > MAX_IMG_W:
            k = MAX_IMG_W / cx
            ext.set("cx", str(int(cx * k)))
            ext.set("cy", str(int(cy * k)))
            gp = ext.getparent()
            for x in gp.iter(qn("a:ext")):
                if x.get("cx") is None or x.get("cy") is None:
                    continue
                x.set("cx", str(int(int(x.get("cx")) * k)))
                x.set("cy", str(int(int(x.get("cy")) * k)))
    # VML (OLE object) images
    for sh in el.iter(NS_V + "shape"):
        style = sh.get("style") or ""
        parts = dict()
        for seg in style.split(";"):
            if ":" in seg:
                k, v = seg.split(":", 1)
                parts[k.strip()] = v.strip()
        w, h = parts.get("width"), parts.get("height")
        if w and h and w.endswith("pt") and h.endswith("pt"):
            wv, hv = float(w[:-2]), float(h[:-2])
            maxpt = 14.8 * 28.3465
            if wv > maxpt:
                k = maxpt / wv
                parts["width"] = "%.2fpt" % (wv * k)
                parts["height"] = "%.2fpt" % (hv * k)
                sh.set("style", ";".join("%s:%s" % kv for kv in parts.items()))


def norm_text(el):
    for t in el.iter(qn("w:t")):
        if t.text:
            t.text = t.text.replace("､", "、")


def run_has_graphic(r_el):
    for tag in (qn("w:drawing"), qn("w:pict"), qn("w:object"),
                NS_MC + "AlternateContent"):
        if r_el.find(tag) is not None:
            return True
    return False


def is_caption(text):
    t = text.strip()
    if not t:
        return False
    for pre in ("图", "表"):
        if t.startswith(pre):
            rest = t[1:].lstrip()
            return bool(rest) and (rest[0].isdigit() or rest[0] == " ")
    return False


def emit_paragraph(p_el):
    """Copy one source w:p, splitting graphics away from body text."""
    el = copy.deepcopy(p_el)
    remap_rels(el)
    clamp_images(el)
    norm_text(el)

    ppr = el.find(qn("w:pPr"))
    runs = [c for c in el.iterchildren() if c.tag == qn("w:r")]
    others = [c for c in el.iterchildren()
              if c.tag not in (qn("w:r"), qn("w:pPr"))]

    # group consecutive runs into graphic / text chunks
    groups = []
    for r in runs:
        g = "img" if run_has_graphic(r) else "txt"
        if groups and groups[-1][0] == g:
            groups[-1][1].append(r)
        else:
            groups.append([g, [r]])

    if not groups:
        # keep empty / field-only paragraphs as-is
        body_add(el)
        pg = Paragraph(el, doc)
        fmt_para(pg, 12, False, None, 0)
        return

    made = []
    for kind, rs in groups:
        np = OxmlElement("w:p")
        if ppr is not None:
            np.append(copy.deepcopy(ppr))
        for r in rs:
            np.append(r)
        if kind == "txt" and groups[-1][0] == kind:
            for o in others:
                np.append(o)
        body_add(np)
        made.append((kind, Paragraph(np, doc)))

    for kind, pg in made:
        txt = pg.text.strip()
        if kind == "img":
            fmt_para(pg, 12, False, WD_ALIGN_PARAGRAPH.CENTER, 0,
                     before=3, after=0, keep_next=True)
        elif is_caption(txt):
            fmt_para(pg, 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, 0,
                     before=0, after=6)
        elif not txt:
            fmt_para(pg, 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, 0)
        else:
            fmt_para(pg, 12, False, WD_ALIGN_PARAGRAPH.JUSTIFY, 2)


def emit_table(tbl_el):
    el = copy.deepcopy(tbl_el)
    remap_rels(el)
    clamp_images(el)
    norm_text(el)
    body_add(el)
    t = Table(el, doc)
    t.style = doc.styles["Table Grid"]
    t.autofit = True
    tblpr = el.find(qn("w:tblPr"))
    jc = tblpr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        tblpr.append(jc)
    jc.set(qn("w:val"), "center")
    # repeat header row
    if len(t.rows):
        trpr = t.rows[0]._tr.get_or_add_trPr()
        th = OxmlElement("w:tblHeader")
        trpr.append(th)
    for ri, row in enumerate(t.rows):
        for cell in row.cells:
            for p in cell.paragraphs:
                fmt_para(p, 10.5, bold=(ri == 0),
                         align=WD_ALIGN_PARAGRAPH.LEFT, indent_chars=0)
            cell.vertical_alignment = 1
    add_para("", size=6)


EMITTED = []


def emit(*indices):
    """Copy the given source block indices, in order."""
    for idx in indices:
        EMITTED.append(idx)
        el = SBLOCKS.get(idx)
        if el is None:
            continue
        if el.tag == qn("w:p"):
            emit_paragraph(el)
        else:
            emit_table(el)


def emit_range(a, b, skip=()):
    emit(*[i for i in range(a, b + 1) if i in SBLOCKS and i not in skip])


# ---------------------------------------------------------------- cover page
page_setup(doc.sections[0])
sec1 = doc.sections[0]

# drop the default empty first paragraph, if the base template has one
if doc.paragraphs:
    doc.element.body.remove(doc.paragraphs[0]._p)

add_blank(2)
for t, sz in (("2026年第八届", 22), ("全球校园人工智能算法精英大赛", 22)):
    add_para(t, size=sz, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
add_blank(1)
add_para("算法创新赛", size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
add_para("赛题5：AI+学科交叉", size=18, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
add_para("技术报告", size=22, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
add_blank(4)
for line in ("团队名称：                            ",
             "参赛编号：AIC-2026-                   ",
             "作品名称：                            "):
    p = add_para(line, size=14, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER,
                 after=10)
add_blank(5)
add_para("日期：      年   月   日", size=14,
         align=WD_ALIGN_PARAGRAPH.CENTER)

# ---------------------------------------------------------------- TOC section
sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
page_setup(sec2)
sec2.footer.is_linked_to_previous = False
sec2.header.is_linked_to_previous = False

hp = sec2.header.paragraphs[0]
hp.text = "2026第八届全球校园人工智能算法精英大赛"
fmt_para(hp, 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, 0)
pbdr = hp._p.get_or_add_pPr()
bd = OxmlElement("w:pBdr")
bot = OxmlElement("w:bottom")
bot.set(qn("w:val"), "single")
bot.set(qn("w:sz"), "6")
bot.set(qn("w:space"), "1")
bot.set(qn("w:color"), "auto")
bd.append(bot)
pbdr.append(bd)

fp = sec2.footer.paragraphs[0]
fmt_para(fp, 10.5, False, WD_ALIGN_PARAGRAPH.CENTER, 0)
r = fp.add_run()
f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve")
it.text = " PAGE  \\* MERGEFORMAT "
f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
r._element.append(f1); r._element.append(it); r._element.append(f2)
set_run(r, 10.5)

# restart page numbering at 1 in the body
sp = sec2._sectPr
pgnum = OxmlElement("w:pgNumType")
pgnum.set(qn("w:start"), "1")
sp.append(pgnum)

add_para("目　　录", size=22, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
         after=12)
tp = doc.add_paragraph()
tr = tp.add_run()
b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin")
b.set(qn("w:dirty"), "true")
ins = OxmlElement("w:instrText"); ins.set(qn("xml:space"), "preserve")
ins.text = ' TOC \\o "1-3" \\h \\z \\u '
sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
plc = OxmlElement("w:r")
pt = OxmlElement("w:t")
pt.text = "【请在 Word 中右键此处 → 更新域 → 更新整个目录】"
plc.append(pt)
e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end")
for x in (b, ins, sep, plc, e):
    tr._element.append(x)
set_run(tr, 12)
fmt_para(tp, 12, False, None, 0)

doc.add_page_break()

# ================================================================== 作品简介
add_heading("作品简介", 1)
emit(143, 144)
add_blank(1)

# ================================================================ 一、项目概述
add_heading("一、项目概述", 1)
add_heading("（一）项目背景与意义", 2)
add_heading("1. 一流学科建设需求", 3)
emit_range(147, 149)
add_heading("2. 大模型助研新机遇", 3)
emit_range(151, 153)
add_heading("3. 人工智能科研特点", 3)
emit_range(155, 157)

add_heading("（二）核心目标", 2)
add_heading("1. 赋能：提升专业可信水平", 3)
emit_range(178, 180)
add_heading("2. 增效：改善科研任务衔接", 3)
emit_range(182, 183)
add_heading("3. 协同：促进知识积累复用", 3)
emit_range(185, 186)
add_heading("4. 创新：推动科研模式演进", 3)
emit_range(188, 189)

add_heading("（三）赛题方向定位", 2)
add_body_lines(C_SAITI)

# ================================================================ 二、需求分析
add_heading("二、需求分析", 1)
add_heading("（一）学科专业界定", 2)
add_body_lines(C_XUEKE)

add_heading("（二）核心痛点梳理", 2)
add_heading("1. 专业回答可信不足", 3)
emit_range(160, 162)
add_heading("2. 内容来源追溯困难", 3)
emit_range(164, 167)
add_heading("3. 工具与资料碎片化", 3)
emit_range(169, 171)
add_heading("4. 复杂任务编排不足", 3)
emit_range(173, 175)

add_heading("（三）AI赋能需求", 2)
add_body_lines(C_AIXUQIU)

# ============================================================ 三、解决方案设计
add_heading("三、解决方案设计", 1)
add_heading("（一）系统架构设计", 2)
add_arch_figure()
emit_range(449, 452)

add_heading("（二）技术选型依据", 2)
add_body_lines(C_XUANXING)

add_heading("（三）核心技术模块", 2)

add_heading("1. 学科专属知识库构建", 3)
emit_range(215, 219)
add_heading("① 数据采集与清洗", 4)
emit_range(221, 241)
add_heading("② 数据处理", 4)
emit_range(243, 258)
add_heading("③ 数据存储", 4)
emit_range(260, 270)

add_heading("2. 深度检索增强生成（RAG）架构设计", 3)
emit_range(272, 274)
add_heading("① 检索前增强：问题理解与检索准备", 4)
emit_range(276, 286)
add_heading("② 检索增强：混合召回与证据组织", 4)
emit_range(288, 298)
add_heading("③ 检索后增强：回答生成、核验与价值闭环", 4)
emit_range(300, 310)

add_heading("3. 垂类大模型微调与优化方案", 3)
emit_range(312, 316)
add_heading("① 基模选型", 4)
emit_range(318, 320)
add_heading("② 微调数据集构建", 4)
emit_range(322, 356)
add_heading("③ LoRA微调", 4)
emit_range(358, 362)
add_heading("④ DPO优化", 4)
emit_range(364, 367)
add_heading("⑤ 模型测试", 4)
emit_range(369, 378)

add_heading("4. 智能Agent工作流编排引擎", 3)
emit_range(380, 381)
add_heading("① 总体架构与任务调度", 4)
emit_range(383, 387)
add_heading("② 十一个智能体的分工与衔接", 4)
emit_range(389, 392)
add_heading("③ 面向科研场景的组合编排", 4)
emit_range(394, 407)
add_heading("④ 阶段成果与上下文交接", 4)
emit_range(409, 412)
add_heading("⑤ 执行控制与过程反馈", 4)
emit_range(414, 417)

add_heading("5. 多模态交互与跨格式处理", 3)
emit_range(419, 420)
add_heading("① 科研对象解析", 4)
emit_range(422, 425)
add_heading("② 图表与公式理解", 4)
emit_range(427, 431)
add_heading("③ 跨格式成果输出", 4)
emit_range(433, 439)
add_heading("④ 质量与安全校验", 4)
emit_range(441, 446)

# ---------------------------------------------------- （四）作品功能说明
#  name, 功能场景描述 a-b, 总体技术方案 a-b, 功能模块实现 a-b  (source heading
#  paragraphs themselves are excluded; only body content is copied)
AGENTS = [
    ("文献检索智能体", 455, 462, 464, 467, 469, 487),
    ("arXiv 每日学术速递智能体", 490, 495, 497, 499, 501, 519),
    ("论文精读智能体", 522, 527, 529, 535, 537, 555),
    ("绘图创作智能体", 558, 563, 565, 568, 570, 587),
    ("文稿辅助智能体", 590, 595, 597, 599, 601, 622),
    ("创新点生成智能体", 625, 632, 634, 638, 640, 657),
    ("专利撰写智能体", 660, 665, 667, 669, 671, 682),
    ("学术翻译智能体", 685, 690, 692, 694, 696, 713),
    ("审稿意见回复智能体", 716, 718, 720, 726, 728, 740),
    ("投稿推荐智能体", 743, 745, 747, 751, 753, 765),
    ("学术合规性校验智能体", 768, 775, 777, 779, 781, 803),
]

add_heading("（四）作品功能说明", 2)
for n, (name, a1, b1, a2, b2, a3, b3) in enumerate(AGENTS, 1):
    add_heading("%d. %s" % (n, name), 3)
    add_heading("① 功能场景描述", 4)
    emit_range(a1, b1)
    add_heading("② 总体技术方案", 4)
    emit_range(a2, b2)
    add_heading("③ 功能模块实现", 4)
    emit_range(a3, b3)

# ============================================================ 四、方案可行性
add_heading("四、方案可行性", 1)
emit(876)
add_heading("（一）技术可行性", 2)
add_body_lines(C_KEXINGXING)

add_heading("（二）经济可行性", 2)
emit(888)
add_heading("1. 轻量化 API 接入模式", 3)
emit_range(890, 894)
add_heading("2. 一体化平台 + 自研学科垂域“智研”模型套餐", 3)
emit_range(896, 902)
add_heading("3. 客户分层", 3)
emit_range(904, 906)
add_heading("4. 增值服务", 3)
emit_range(908, 910)
add_heading("5. 成本节约测算", 3)
emit_range(929, 931)

add_heading("（三）推广价值", 2)
add_heading("1. 行业痛点与需求基础", 3)
emit_range(913, 920)
add_heading("2. 竞品分析", 3)
emit_range(878, 886)
add_heading("3. 差异化商业优势", 3)
emit_range(922, 927)
add_heading("4. 市场空间与推广路径", 3)
emit_range(933, 935)
add_heading("5. 小结", 3)
emit(937)

# ============================================================== 五、项目实施
add_heading("五、项目实施", 1)
add_heading("（一）实施计划", 2)
add_body_lines(C_JIHUA)
add_heading("（二）资源保障", 2)
add_body_lines(C_ZIYUAN)
add_heading("（三）团队协作", 2)
add_body_lines(C_TUANDUI)

# ============================================================== 六、应用效果
add_heading("六、应用效果", 1)
add_heading("（一）应用效果预期", 2)
add_blank(4)

add_heading("（二）成果展示", 2)
emit_range(805, 806)
add_heading("1. 核心Agent测试", 3)
add_heading("① 测试设计", 4)
emit_range(809, 812)
add_heading("② 文稿辅助Agent", 4)
emit_range(814, 835)
add_heading("③ 审稿意见解析与引导回复Agent", 4)
emit_range(837, 852)
add_heading("④ 综合分析", 4)
emit(854)
add_heading("2. 真实用户使用效果", 3)
add_heading("① 试用设计", 4)
emit_range(857, 858)
add_heading("② 核心用户试用结果", 4)
emit_range(860, 864)
add_heading("③ 规模化试用结果", 4)
emit_range(866, 869)
add_heading("④ 用户反馈与效果结论", 4)
emit_range(871, 873)

# ============================================================ 七、总结与展望
add_heading("七、总结与展望", 1)
add_heading("（一）方案总结", 2)
emit(191)
add_heading("1. 证据约束的学科RAG", 3)
emit_range(193, 195)
add_heading("2. 混合检索与分层排序", 3)
emit_range(197, 199)
add_heading("3. 动态知识与上下文管理", 3)
emit_range(201, 203)
add_heading("4. 证据驱动的QLoRA适配", 3)
emit_range(205, 207)
add_heading("5. 状态感知的受控编排", 3)
emit_range(209, 211)
add_body_lines(C_BUZU)

add_heading("（二）未来展望", 2)
add_body_lines(C_ZHANWANG)

# ================================================================== 八、附录
add_heading("八、附录", 1)
add_heading("（一）代码与模型", 2)
add_body_lines(C_DAIMA)
add_heading("（二）参考文献", 2)
add_blank(4)
add_heading("（三）其他材料", 2)
add_blank(3)

import os, json
json.dump(EMITTED, open("/tmp/aic_work/emitted.json", "w"))
_mapping = renumber(doc)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc.save(OUT)
print("saved:", OUT)
print("size MB: %.2f" % (os.path.getsize(OUT) / 1024 / 1024))
print("paragraphs:", len(doc.paragraphs), "tables:", len(doc.tables))
print("renumber map (%d entries):" % len(_mapping))
for k in sorted(_mapping, key=lambda x: (-len(x), x)):
    print("   ", k, "->", _mapping[k])
