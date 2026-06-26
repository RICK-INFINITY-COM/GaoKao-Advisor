#!/usr/bin/env python3
"""
AI 对话助手 — 本地自用版
带轻量知识库（学校/专业/省控线）支撑的 AI 对话服务。
填入 DeepSeek API Key 即可使用，无数据库、无次数限制。
"""
import os
import json
import urllib.request
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, FileResponse
from pydantic import BaseModel

HERE = os.path.dirname(os.path.abspath(__file__))

# 读取 .env（可选）
_env_path = os.path.join(HERE, ".env")
if os.path.exists(_env_path):
    for line in open(_env_path, encoding="utf-8"):
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k.strip()] = v.strip()

app = FastAPI(title="AI Chat")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 默认锁定 DeepSeek（也可在 .env 改成其他兼容接口）
DEFAULT_LLM_URL = os.getenv("LLM_URL", "https://api.deepseek.com/chat/completions")
DEFAULT_LLM_KEY = os.getenv("LLM_API_KEY", "")
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# ===== 加载前端与提示词 =====
INDEX_HTML = open(os.path.join(HERE, "index.html"), encoding="utf-8").read() if os.path.exists(os.path.join(HERE, "index.html")) else ""
SYSTEM_PROMPT = open(os.path.join(HERE, "system_prompt.md"), encoding="utf-8").read() if os.path.exists(os.path.join(HERE, "system_prompt.md")) else ""

# ===== 加载轻量知识库 =====
KB = {"schools": [], "majors": [], "batch_lines": []}
_data_dir = os.path.join(HERE, "data")
for _name, _key in [("schools.json", "schools"), ("majors.json", "majors"), ("batch_lines.json", "batch_lines")]:
    _p = os.path.join(_data_dir, _name)
    if os.path.exists(_p):
        try:
            KB[_key] = json.load(open(_p, encoding="utf-8"))
        except Exception:
            pass

# 省份列表（用于省控线匹配）
PROVINCES = ["北京","天津","河北","山西","内蒙古","辽宁","吉林","黑龙江","上海","江苏",
             "浙江","安徽","福建","江西","山东","河南","湖北","湖南","广东","广西","海南",
             "重庆","四川","贵州","云南","西藏","陕西","甘肃","青海","宁夏","新疆"]

sessions = {}


def search_kb(msg):
    """根据用户提问，从知识库匹配相关数据作为上下文。返回拼接的文本（可为空）。"""
    ctx = []

    # 1. 学校匹配：提问中包含学校名
    matched_schools = [s for s in KB["schools"] if s.get("name") and s["name"] in msg]
    if matched_schools:
        lines = []
        for s in matched_schools[:15]:
            tag = []
            if s.get("f985") == "是": tag.append("985")
            if s.get("f211") == "是": tag.append("211")
            lines.append(f"  · {s['name']}：{s.get('province','')} {s.get('type','')} {s.get('nature','')} {' '.join(tag)}".strip())
        ctx.append("【相关学校信息】\n" + "\n".join(lines))

    # 2. 985/211 筛选提问："有哪些985大学" "XX省的211"
    if ("985" in msg or "二一一" in msg or "211" in msg) and any(w in msg for w in ["有哪些","哪些","名单","大学","院校","学校"]):
        prov = next((p for p in PROVINCES if p in msg), None)
        pool = [s for s in KB["schools"] if s.get("f985")=="是" and ("985" in msg)] if "985" in msg else \
               [s for s in KB["schools"] if s.get("f211")=="是" and ("211" in msg or "二一一" in msg)]
        if prov:
            pool = [s for s in pool if s.get("province")==prov]
        if pool:
            names = "、".join(s["name"] for s in pool[:30])
            ctx.append(f"【{'985' if '985' in msg else '211'}院校{'('+prov+')' if prov else ''}共{len(pool)}所】{names}")

    # 3. 专业匹配：提问包含专业名或专业类
    matched_majors = [m for m in KB["majors"] if m.get("name") and m["name"] in msg]
    if not matched_majors:
        matched_majors = [m for m in KB["majors"] if m.get("class") and m["class"] in msg]
    if matched_majors:
        lines = [f"  · {m['name']}（{m.get('category','')}/{m.get('class','')}，代码{m.get('code','')}）" for m in matched_majors[:15]]
        ctx.append("【相关专业目录】\n" + "\n".join(lines))

    # 4. 省控线匹配：提问包含省份 + 线/批次相关词
    prov = next((p for p in PROVINCES if p in msg), None)
    if prov and any(w in msg for w in ["线","批次","本科","专科","多少分","控制线","省控"]):
        lines = KB["batch_lines"]
        rel = [b for b in lines if b.get("province")==prov and any(w in str(b.get("batch","")) for w in ["本科","专科"])]
        if rel:
            txt = "\n".join(f"  · {b['year']} {b.get('category','')} {b.get('batch','')}：{b.get('score_line')}分" for b in rel[:20])
            ctx.append(f"【{prov}近年省控线】\n{txt}")

    return "\n\n".join(ctx)


def ai_call(messages, user_key=""):
    key = user_key or DEFAULT_LLM_KEY
    if not key:
        return "⚠️ 还没配置 API Key。请点击右上角设置图标，填入你的 DeepSeek API Key。"
    payload = json.dumps({
        "model": DEFAULT_LLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4000,
        "stream": False
    }).encode()
    req = urllib.request.Request(
        DEFAULT_LLM_URL, payload,
        {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = ""
        try: body = e.read().decode()[:200]
        except Exception: pass
        return f"⚠️ AI 接口返回错误 {e.code}。{body}"
    except Exception as e:
        return f"⚠️ AI 调用失败：{str(e)[:150]}"


class ChatRequest(BaseModel):
    message: str = ""
    session_id: str = "default"
    user_api_key: str = ""


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML or "<h1>AI Chat</h1>"


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": DEFAULT_LLM_MODEL,
        "has_default_key": bool(DEFAULT_LLM_KEY),
        "kb": {k: len(v) for k, v in KB.items()}
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    msg = req.message.strip()
    if not msg:
        return {"reply": "请输入你的问题~"}

    sid = req.session_id or "default"
    if sid not in sessions:
        sessions[sid] = []
        if SYSTEM_PROMPT:
            sessions[sid].append({"role": "system", "content": SYSTEM_PROMPT})

    # 知识库检索：把命中数据作为一条 system 上下文注入本轮
    kb_ctx = search_kb(msg)
    turn_messages = list(sessions[sid])
    turn_messages.append({"role": "user", "content": msg})
    if kb_ctx:
        turn_messages.append({"role": "system", "content": "以下是知识库检索到的参考数据，回答时可参考：\n\n" + kb_ctx})

    reply = ai_call(turn_messages[-20:], req.user_api_key)
    sessions[sid].append({"role": "user", "content": msg})
    sessions[sid].append({"role": "assistant", "content": reply})

    return {"reply": reply, "kb_hit": bool(kb_ctx)}


@app.delete("/api/session/{sid}")
def clear_session(sid: str):
    if sid in sessions:
        del sessions[sid]
    return {"ok": True}


# 静态资源（仅放行图片）
_IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".svg"}
@app.get("/{filename}")
def static_file(filename: str):
    name = os.path.basename(filename)
    if os.path.splitext(name)[1].lower() not in _IMG_EXT:
        return Response("Not Found", status_code=404)
    fp = os.path.join(HERE, name)
    if not os.path.isfile(fp):
        return Response("Not Found", status_code=404)
    return FileResponse(fp)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8766"))
    print(f"AI Chat 启动: http://0.0.0.0:{port}")
    print(f"模型: {DEFAULT_LLM_MODEL}  默认Key: {'已配' if DEFAULT_LLM_KEY else '未配(前端填)'}")
    print(f"知识库: 学校{len(KB['schools'])} 专业{len(KB['majors'])} 省控线{len(KB['batch_lines'])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
