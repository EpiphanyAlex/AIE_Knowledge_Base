#!/usr/bin/env python3
"""把 topics/**/*.md 里的面试问答卡解析出来，生成一个 Apple 风格的 cards.html 抽认卡查看器。

数据源永远是 markdown；本脚本只生成"视图"。改完笔记重跑即可：
    python3 tools/build_cards.py

输出：仓库根目录的 cards.html（零依赖，双击用浏览器打开）。
设计：Apple Web 风格 + design token 体系，详见 docs/cards-redesign-prd.md。
学习模式：一次一张卡 → 显示答案 → 重来/难/良/简单 评分，带间隔重复(SRS)，进度存浏览器 localStorage。
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = ROOT / "topics"
OUT = ROOT / "cards.html"

LABEL = re.compile(r"^\*\*(.+?)[:：]\*\*\s*(.*)$")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4:]
    fm: dict = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip()
    return fm, body


def slice_qa_section(body: str) -> str:
    lines = body.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("## ") and "问答卡" in ln:
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end])


def field_for(label: str) -> str | None:
    label = label.strip()
    if label.startswith("Answer"):
        return "answer_en"
    if "核心答案" in label:
        return "answer_zh"
    if "追问" in label or "深入" in label:
        return "followup"
    if "误区" in label:
        return "pitfall"
    if "难度" in label:
        return "difficulty"
    return None


def parse_cards(qa: str) -> list[dict]:
    cards: list[dict] = []
    chunks = re.split(r"^###\s+", qa, flags=re.MULTILINE)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        head = re.sub(r"^Q?\d*\.?\s*", "", lines[0]).strip()
        if " / " in head:                       # 第一个带空格的 / 即中英分隔
            q_en, q_zh = head.split(" / ", 1)
            q_en, q_zh = q_en.strip(), q_zh.strip()
        else:
            q_en, q_zh = head, ""
        card = {"q_en": q_en, "q_zh": q_zh, "difficulty": "",
                "answer_en": "", "answer_zh": "", "followup": "", "pitfall": ""}
        cur = None
        buf: list[str] = []

        def flush():
            nonlocal buf, cur
            if cur and buf:
                joined = "\n".join(buf).strip()
                card[cur] = (card[cur] + "\n" + joined).strip() if card[cur] else joined
            buf = []

        for ln in lines[1:]:
            m = LABEL.match(ln.strip())
            if m:
                flush()
                fld = field_for(m.group(1))
                cur = fld
                rest = m.group(2).strip()
                if fld == "difficulty":
                    card["difficulty"] = rest
                    cur = None
                elif rest:
                    buf.append(rest)
            else:
                if cur:
                    buf.append(ln)
        flush()
        if card["q_en"] or card["q_zh"]:
            cards.append(card)
    return cards


def md_to_html(text: str) -> str:
    if not text.strip():
        return ""
    out: list[str] = []
    in_ul = False
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        bullet = s.startswith("- ")
        content = s[2:] if bullet else s
        content = html.escape(content)
        content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"`(.+?)`", r"<code>\1</code>", content)
        if bullet:
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{content}</li>")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<p>{content}</p>")
    if in_ul:
        out.append("</ul>")
    return "".join(out)


def collect() -> list[dict]:
    cards: list[dict] = []
    for md in sorted(TOPICS_DIR.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        topic = fm.get("topic", md.stem)
        domain = fm.get("domain", md.parent.name)
        topic_diff = fm.get("difficulty", "")
        status = fm.get("status", "")
        rel = str(md.relative_to(ROOT))
        for idx, c in enumerate(parse_cards(slice_qa_section(body)), 1):
            cards.append({
                "id": f"{rel}#q{idx}",
                "topic": topic,
                "domain": domain,
                "file": rel,
                "status": status,
                "difficulty": c["difficulty"] or topic_diff,
                "q_en": c["q_en"],
                "q_zh": c["q_zh"],
                "answer_en": md_to_html(c["answer_en"]),
                "answer_zh": md_to_html(c["answer_zh"]),
                "followup": md_to_html(c["followup"]),
                "pitfall": md_to_html(c["pitfall"]),
            })
    return cards


HTML_HEAD = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AIE 抽认卡</title>
<style>
:root{
--bg:#f5f5f7;--surface:#fff;--surface-2:#e8e8ed;--surface-3:#f5f5f7;
--text:#1d1d1f;--text-secondary:#6e6e73;--separator:#d2d2d7;
--accent:#0071e3;--accent-hover:#0077ed;--on-accent:#fff;
--again:#d70015;--again-bg:rgba(255,59,48,.12);--again-bg-h:rgba(255,59,48,.20);
--hard:#9a5b00;--hard-bg:rgba(255,149,0,.14);--hard-bg-h:rgba(255,149,0,.22);
--good:#1d7a33;--good-bg:rgba(52,199,89,.15);--good-bg-h:rgba(52,199,89,.24);
--easy:#0058b0;--easy-bg:rgba(0,122,255,.12);--easy-bg-h:rgba(0,122,255,.20);
--font:-apple-system,"SF Pro Text","SF Pro Display","Helvetica Neue","PingFang SC","Microsoft YaHei",sans-serif;
--fs-xs:12px;--fs-sm:14px;--fs-base:17px;--fs-lg:21px;--fs-xl:28px;
--fw-regular:400;--fw-medium:500;--fw-semibold:600;--tracking-tight:-0.02em;
--space-1:4px;--space-2:8px;--space-3:12px;--space-4:16px;--space-5:24px;--space-6:32px;--space-8:48px;--space-10:64px;
--radius-sm:8px;--radius-md:12px;--radius-lg:18px;--radius-xl:24px;--radius-pill:980px;
--shadow-sm:0 1px 3px rgba(0,0,0,.06);--shadow-md:0 4px 20px rgba(0,0,0,.08);
--ease:cubic-bezier(.4,0,.2,1);--dur-fast:150ms;--dur:250ms;
}
@media (prefers-color-scheme:dark){:root{
--bg:#000;--surface:#1c1c1e;--surface-2:#2c2c2e;--surface-3:#2c2c2e;
--text:#f5f5f7;--text-secondary:#98989d;--separator:#38383a;
--accent:#2997ff;--accent-hover:#47a6ff;
--again:#ff6961;--hard:#ffb340;--good:#30d158;--easy:#64a8ff;
--shadow-sm:0 1px 3px rgba(0,0,0,.4);--shadow-md:0 4px 24px rgba(0,0,0,.5);
}}
*{box-sizing:border-box}
html{-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--font);font-size:var(--fs-base);line-height:1.55}
.hidden{display:none}
header{position:sticky;top:0;z-index:50;border-bottom:1px solid var(--separator);
background:var(--bg);background:color-mix(in srgb,var(--bg) 82%,transparent);
backdrop-filter:saturate(180%) blur(20px);-webkit-backdrop-filter:saturate(180%) blur(20px)}
.bar{display:flex;flex-wrap:wrap;gap:var(--space-3);align-items:center;max-width:1100px;margin:0 auto;padding:var(--space-3) var(--space-5)}
.brand{font-size:var(--fs-base);font-weight:var(--fw-semibold);letter-spacing:var(--tracking-tight)}
.stats{margin-left:auto;color:var(--text-secondary);font-size:var(--fs-sm)}
.stats b{color:var(--text);font-weight:var(--fw-medium)}
select{appearance:none;-webkit-appearance:none;background:var(--surface);color:var(--text);border:1px solid var(--separator);border-radius:var(--radius-sm);padding:6px 30px 6px 12px;font-size:var(--fs-sm);font-family:inherit;cursor:pointer;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236e6e73' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center}
button{font-family:inherit;cursor:pointer}
.seg{display:inline-flex;background:var(--surface-2);border-radius:var(--radius-sm);padding:2px;gap:2px}
.seg button{border:0;background:transparent;color:var(--text);border-radius:7px;padding:5px 13px;font-size:var(--fs-sm);font-weight:var(--fw-medium);transition:background var(--dur-fast) var(--ease)}
.seg button.on{background:var(--surface);box-shadow:var(--shadow-sm)}
.ghost{border:1px solid var(--separator);background:var(--surface);color:var(--text);border-radius:var(--radius-sm);padding:6px 13px;font-size:var(--fs-sm);transition:background var(--dur-fast) var(--ease)}
.ghost:hover{background:var(--surface-2)}
#study{max-width:600px;margin:var(--space-10) auto;padding:0 var(--space-5)}
.scard{background:var(--surface);border:1px solid var(--separator);border-radius:var(--radius-xl);padding:var(--space-8);box-shadow:var(--shadow-md)}
.badges{display:flex;gap:var(--space-2);flex-wrap:wrap;margin-bottom:var(--space-5)}
.badge{font-size:var(--fs-xs);color:var(--text-secondary);background:var(--surface-3);border-radius:var(--radius-pill);padding:3px 11px}
.q{font-size:var(--fs-xl);font-weight:var(--fw-semibold);letter-spacing:var(--tracking-tight);line-height:1.25}
.q .zh{display:block;font-size:var(--fs-lg);font-weight:var(--fw-regular);color:var(--text-secondary);letter-spacing:normal;margin-top:var(--space-2)}
.ans{border-top:1px solid var(--separator);margin-top:var(--space-5);padding-top:var(--space-5);font-size:var(--fs-base)}
.ans h4{margin:var(--space-5) 0 var(--space-2);font-size:var(--fs-sm);font-weight:var(--fw-semibold);color:var(--text-secondary)}
.ans h4:first-child{margin-top:0}
.ans ul{margin:var(--space-2) 0;padding-left:1.2em}.ans li{margin:3px 0}
.ans p{margin:var(--space-2) 0}
.ans code{background:var(--surface-3);padding:1px 6px;border-radius:6px;font-size:.9em}
.actions{margin-top:var(--space-6)}
.reveal{width:100%;background:var(--accent);color:var(--on-accent);border:0;border-radius:var(--radius-pill);padding:13px;font-size:var(--fs-base);font-weight:var(--fw-medium);transition:background var(--dur-fast) var(--ease)}
.reveal:hover{background:var(--accent-hover)}
.reveal small{opacity:.7;font-size:var(--fs-xs);margin-left:var(--space-2)}
.grades{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--space-2)}
.grades button{display:flex;flex-direction:column;gap:2px;border:0;border-radius:var(--radius-md);padding:12px 4px;font-size:var(--fs-sm);font-weight:var(--fw-semibold);transition:background var(--dur-fast) var(--ease)}
.grades small{font-weight:var(--fw-regular);font-size:var(--fs-xs);opacity:.85}
.g-again{background:var(--again-bg);color:var(--again)}.g-again:hover{background:var(--again-bg-h)}
.g-hard{background:var(--hard-bg);color:var(--hard)}.g-hard:hover{background:var(--hard-bg-h)}
.g-good{background:var(--good-bg);color:var(--good)}.g-good:hover{background:var(--good-bg-h)}
.g-easy{background:var(--easy-bg);color:var(--easy)}.g-easy:hover{background:var(--easy-bg-h)}
.done{text-align:center;color:var(--text-secondary);padding:var(--space-10) var(--space-4)}
.done svg{width:46px;height:46px;color:var(--good);margin-bottom:var(--space-4)}
.done .big{font-size:var(--fs-lg);font-weight:var(--fw-semibold);color:var(--text);margin-bottom:var(--space-5)}
.done .ghost{padding:10px 18px}
#browse{max-width:1100px;margin:var(--space-6) auto;padding:0 var(--space-5);display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:var(--space-4)}
#browse .card{background:var(--surface);border:1px solid var(--separator);border-radius:var(--radius-lg);padding:var(--space-5);box-shadow:var(--shadow-sm)}
#browse .q{font-size:var(--fs-base)}#browse .q .zh{font-size:var(--fs-sm)}
#browse details{margin-top:var(--space-3)}
#browse summary{cursor:pointer;color:var(--accent);font-size:var(--fs-sm);list-style:none}
#browse summary::-webkit-details-marker{display:none}
#browse .ans{margin-top:var(--space-3)}
.empty{grid-column:1/-1;text-align:center;color:var(--text-secondary);padding:var(--space-10)}
.lang-en .zh,.lang-en .ans-zh{display:none}
.lang-zh .en,.lang-zh .ans-en{display:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
</head>
<body>
<header><div class="bar">
<span class="brand">AIE 抽认卡</span>
<div class="seg" id="mode"><button data-m="study" class="on">学习</button><button data-m="browse">浏览</button></div>
<select id="fDomain" aria-label="按领域筛选"><option value="">全部领域</option></select>
<select id="fTopic" aria-label="按主题筛选"><option value="">全部主题</option></select>
<select id="fDiff" aria-label="按难度筛选"><option value="">全部难度</option></select>
<div class="seg" id="lang"><button data-l="both" class="on">中英</button><button data-l="en">EN</button><button data-l="zh">中</button></div>
<span class="stats" id="stats"></span>
<button id="reset" class="ghost">重置进度</button>
</div></header>
<main id="study"></main>
<main id="browse" class="hidden"></main>
<script>
const CARDS = """

HTML_TAIL = """;
const $ = s => document.querySelector(s);
const CARDMAP = Object.fromEntries(CARDS.map(c => [c.id, c]));
const SKEY = 'aie-srs-v1';
const DAY = 86400000;
let srs = JSON.parse(localStorage.getItem(SKEY) || '{}');
let lang = 'both', mode = 'study', studyAll = false;
let session = [], revealed = false;

function saveSrs(){ localStorage.setItem(SKEY, JSON.stringify(srs)); }
function st(id){ return srs[id] || (srs[id] = {ease:2.5, ivl:0, due:0, reps:0}); }

function fillSelect(sel, vals){
  for(const v of [...new Set(vals)].filter(Boolean).sort())
    sel.insertAdjacentHTML('beforeend', `<option>${v}</option>`);
}
fillSelect($('#fDomain'), CARDS.map(c=>c.domain));
fillSelect($('#fDiff'), CARDS.map(c=>c.difficulty));
function refreshTopics(){
  const d = $('#fDomain').value, s = $('#fTopic');
  s.innerHTML = '<option value="">全部主题</option>';
  fillSelect(s, CARDS.filter(c=>!d||c.domain===d).map(c=>c.topic));
}
refreshTopics();

function filtered(){
  const d=$('#fDomain').value, t=$('#fTopic').value, f=$('#fDiff').value;
  return CARDS.filter(c=>(!d||c.domain===d)&&(!t||c.topic===t)&&(!f||c.difficulty===f));
}
function buildSession(){
  const now = Date.now();
  let pool = filtered();
  if(!studyAll) pool = pool.filter(c => st(c.id).due <= now);
  session = pool.map(c => c.id);
  revealed = false;
}

function nextIvl(s, g){
  if(g==='hard') return s.ivl ? Math.max(1, Math.round(s.ivl*1.2)) : 1;
  if(g==='good') return s.ivl ? Math.round(s.ivl*s.ease) : 1;
  return s.ivl ? Math.round(s.ivl*s.ease*1.3) : 3;          // easy
}
function ivlLabel(s, g){ return g==='again' ? '<10分' : nextIvl(s,g)+'天'; }

function grade(g){
  const id = session[0], s = st(id);
  s.reps++;
  if(g==='again'){ s.ease=Math.max(1.3,s.ease-0.2); s.ivl=0; s.due=Date.now(); }
  else { if(g==='hard') s.ease=Math.max(1.3,s.ease-0.15); if(g==='easy') s.ease+=0.15;
         s.ivl=nextIvl(s,g); s.due=Date.now()+s.ivl*DAY; }
  saveSrs();
  session.shift();
  if(g==='again') session.splice(Math.min(session.length,3),0,id);   // 稍后再出现
  revealed=false;
  renderStudy();
}

function answerHtml(c){
  return (c.answer_en?`<h4 class="ans-en">Answer (EN)</h4><div class="ans-en">${c.answer_en}</div>`:'')
    + (c.answer_zh?`<h4 class="ans-zh">核心答案</h4><div class="ans-zh">${c.answer_zh}</div>`:'')
    + (c.followup?`<h4>追问 / 深入</h4>${c.followup}`:'')
    + (c.pitfall?`<h4>常见误区</h4>${c.pitfall}`:'');
}

function renderStudy(){
  const wrap = $('#study'); wrap.className = 'lang-'+lang;
  updateStats();
  if(!session.length){
    const any = filtered().length;
    wrap.innerHTML = `<div class="done">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M8 12l3 3 5-6"></path></svg>
      <div class="big">${studyAll?'全部过完了':'这组今天复习完了'}</div>`
      + (any?`<button id="againAll" class="ghost">${studyAll?'再过一遍':'无视进度 · 全部再学一遍'}</button>`:'<p>没有卡片，换个筛选试试。</p>')
      + `</div>`;
    const b=$('#againAll'); if(b) b.onclick=()=>{ studyAll=true; buildSession(); renderStudy(); };
    return;
  }
  const c = CARDMAP[session[0]], s = st(c.id);
  wrap.innerHTML = `<div class="scard">
    <div class="badges"><span class="badge">${c.domain}</span><span class="badge">${c.topic}</span><span class="badge">${c.difficulty}</span></div>
    <div class="q"><span class="en">${c.q_en||''}</span><span class="zh">${c.q_zh||''}</span></div>
    <div class="ans ${revealed?'':'hidden'}">${answerHtml(c)}</div>
    <div class="actions">${revealed
      ? `<div class="grades">
          <button class="g-again" data-g="again">重来<small>${ivlLabel(s,'again')}</small></button>
          <button class="g-hard" data-g="hard">难<small>${ivlLabel(s,'hard')}</small></button>
          <button class="g-good" data-g="good">良<small>${ivlLabel(s,'good')}</small></button>
          <button class="g-easy" data-g="easy">简单<small>${ivlLabel(s,'easy')}</small></button></div>`
      : `<button class="reveal" id="reveal">显示答案<small>空格</small></button>`}</div>
  </div>`;
  if(!revealed) $('#reveal').onclick=()=>{ revealed=true; renderStudy(); };
  else wrap.querySelectorAll('[data-g]').forEach(b=> b.onclick=()=>grade(b.dataset.g));
}

function renderBrowse(){
  const wrap=$('#browse'); wrap.className='lang-'+lang;
  const list=filtered();
  wrap.innerHTML = list.length ? list.map(c=>`<div class="card">
    <div class="badges"><span class="badge">${c.domain}</span><span class="badge">${c.topic}</span><span class="badge">${c.difficulty}</span></div>
    <div class="q"><span class="en">${c.q_en||''}</span><span class="zh">${c.q_zh||''}</span></div>
    <details><summary>显示答案</summary><div class="ans">${answerHtml(c)}</div></details>
  </div>`).join('') : '<div class="empty">没有匹配的卡片</div>';
}

function updateStats(){
  const now=Date.now(), fil=filtered();
  const due=fil.filter(c=>st(c.id).due<=now).length;
  const learned=fil.filter(c=>st(c.id).reps>0).length;
  $('#stats').innerHTML = mode==='study'
    ? `待学 <b>${session.length}</b> · 到期 <b>${due}</b> · 共 <b>${fil.length}</b>`
    : `共 <b>${fil.length}</b> 卡 · 学过 <b>${learned}</b>`;
}

function rerender(){ mode==='study' ? renderStudy() : renderBrowse(); }
function refilter(){ if(mode==='study'){ studyAll=false; buildSession(); } rerender(); }

$('#fDomain').onchange=()=>{ refreshTopics(); refilter(); };
$('#fTopic').onchange=refilter;
$('#fDiff').onchange=refilter;
$('#lang').onclick=e=>{ if(e.target.dataset.l){ lang=e.target.dataset.l;
  [...e.target.parentNode.children].forEach(b=>b.classList.toggle('on',b===e.target)); rerender(); } };
$('#mode').onclick=e=>{ if(e.target.dataset.m){ mode=e.target.dataset.m;
  [...e.target.parentNode.children].forEach(b=>b.classList.toggle('on',b===e.target));
  $('#study').classList.toggle('hidden',mode!=='study');
  $('#browse').classList.toggle('hidden',mode!=='browse');
  if(mode==='study'){ studyAll=false; buildSession(); } rerender(); } };
$('#reset').onclick=()=>{ if(confirm('清空所有学习进度？')){ srs={}; saveSrs(); studyAll=false; buildSession(); rerender(); } };

document.addEventListener('keydown', e=>{
  if(mode!=='study' || !session.length) return;
  if((e.key===' '||e.key==='Enter') && !revealed){ e.preventDefault(); revealed=true; renderStudy(); }
  else if(revealed && ['1','2','3','4'].includes(e.key)){
    grade({'1':'again','2':'hard','3':'good','4':'easy'}[e.key]); }
});

buildSession(); rerender();
</script>
</body>
</html>
"""


def main():
    cards = collect()
    out = HTML_HEAD + json.dumps(cards, ensure_ascii=False) + HTML_TAIL
    OUT.write_text(out, encoding="utf-8")
    topics = len({c["file"] for c in cards})
    print(f"✓ 生成 {OUT.relative_to(ROOT)} — {len(cards)} 张卡，来自 {topics} 个主题")


if __name__ == "__main__":
    main()
