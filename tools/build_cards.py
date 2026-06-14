#!/usr/bin/env python3
"""把 topics/**/*.md 里的面试问答卡解析出来，生成一个 Anki 风格的 cards.html 抽认卡查看器。

数据源永远是 markdown；本脚本只生成"视图"。改完笔记重跑即可：
    python3 tools/build_cards.py

输出：仓库根目录的 cards.html（零依赖，双击用浏览器打开）。
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
:root{--bg:#0f1115;--panel:#181b22;--card:#1f232c;--line:#2b303b;--fg:#e6e8ec;--mut:#9aa3b2;--acc:#4f8cff;
--again:#ff6b6b;--hard:#f0a43a;--good:#2ecc71;--easy:#4f8cff;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 -apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--panel);border-bottom:1px solid var(--line);padding:12px 16px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.bar>strong{font-size:16px;margin-right:4px}
select,button{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:7px 10px;font-size:13px;cursor:pointer}
.seg{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{border:0;border-right:1px solid var(--line);border-radius:0}
.seg button:last-child{border-right:0}
.seg button.on{background:var(--acc);color:#fff}
.stats{margin-left:auto;color:var(--mut);font-size:13px}.stats b{color:var(--fg)}
.hidden{display:none}
#study{max-width:680px;margin:34px auto;padding:0 16px}
.scard{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:24px;box-shadow:0 6px 24px rgba(0,0,0,.25)}
.badges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.badge{font-size:11px;color:var(--mut);background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:2px 9px}
.q{font-size:19px;font-weight:600;line-height:1.5}
.q .zh{display:block;color:var(--mut);font-weight:500;font-size:16px;margin-top:6px}
.ans{border-top:1px dashed var(--line);margin-top:16px;padding-top:14px}
.ans h4{margin:14px 0 4px;font-size:12px;color:var(--acc);text-transform:uppercase;letter-spacing:.04em}
.ans h4:first-child{margin-top:0}
.ans ul{margin:4px 0;padding-left:18px}.ans p{margin:4px 0}
.ans code{background:var(--panel);padding:1px 5px;border-radius:4px;font-size:12px}
.actions{margin-top:20px}
.reveal{width:100%;padding:13px;font-size:15px;background:var(--acc);color:#fff;border-color:var(--acc)}
.reveal small{opacity:.8;font-size:11px;margin-left:6px}
.grades{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.grades button{display:flex;flex-direction:column;gap:2px;padding:11px 4px;font-size:14px;font-weight:600}
.grades small{font-weight:500;font-size:11px;opacity:.85}
.g-again{background:var(--again);border-color:var(--again);color:#2a0606}
.g-hard{background:var(--hard);border-color:var(--hard);color:#2a1c06}
.g-good{background:var(--good);border-color:var(--good);color:#06210f}
.g-easy{background:var(--easy);border-color:var(--easy);color:#fff}
.done{text-align:center;color:var(--mut);padding:50px 10px}
.done .big{font-size:22px;color:var(--fg);margin-bottom:18px}
.done button{padding:11px 18px;background:var(--acc);color:#fff;border-color:var(--acc)}
#browse{max-width:1100px;margin:20px auto;padding:0 16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
#browse .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
#browse .q{font-size:15px}#browse .q .zh{font-size:14px}
#browse details{margin-top:10px}
#browse summary{cursor:pointer;color:var(--acc);font-size:13px}
#browse .ans{margin-top:10px}
.empty{grid-column:1/-1;text-align:center;color:var(--mut);padding:40px}
.lang-en .zh,.lang-en .ans-zh{display:none}
.lang-zh .en,.lang-zh .ans-en{display:none}
</style>
</head>
<body>
<header><div class="bar">
<strong>AIE 抽认卡</strong>
<div class="seg" id="mode"><button data-m="study" class="on">学习</button><button data-m="browse">浏览</button></div>
<select id="fDomain"><option value="">全部领域</option></select>
<select id="fTopic"><option value="">全部主题</option></select>
<select id="fDiff"><option value="">全部难度</option></select>
<div class="seg" id="lang"><button data-l="both" class="on">中英</button><button data-l="en">EN</button><button data-l="zh">中</button></div>
<span class="stats" id="stats"></span>
<button id="reset">重置进度</button>
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
    wrap.innerHTML = `<div class="done"><div class="big">🎉 ${studyAll?'全部过完了':'这组今天复习完了'}</div>`
      + (any?`<button id="againAll">${studyAll?'再过一遍':'无视进度 · 全部再学一遍'}</button>`:'<p>没有卡片，换个筛选试试。</p>')
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
