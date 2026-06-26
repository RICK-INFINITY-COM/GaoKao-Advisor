# 高考志愿填报AI助手 - 开源精简版

> 极简的本地 AI 对话工具，自带轻量升学知识库（院校 / 专业 / 省控线）支撑。填入你自己的 DeepSeek API Key 即可使用，无需数据库、无次数限制、不经第三方中转。

## 🌐 在线体验

商业版已上线：[**rickinf.top**](https://rickinf.top) — 425万录取数据 + DeepSeek 驱动，免费试用8次。

---

适合想在自己电脑或服务器上跑一个私人 AI 助手的人。所有对话直接走你自己的 API Key，提问涉及院校/专业/分数线时会自动检索本地知识库，让 AI 回答有据可依。

## ✨ 特点

- **极简**：一个 Python 后端 + 一个 HTML 前端，没有多余的东西
- **本地自用**：API Key 存浏览器本地，对话直连 DeepSeek，不经第三方
- **无限制**：没有次数限制、没有用户系统、没有数据库
- **知识库支撑**：内置院校（2991所）、专业目录（833个）、近年省控线，提问时自动检索注入
- **可定制**：改 `system_prompt.md` 变成任意角色助手；替换 `data/` 下的 JSON 即可更新知识库
- **一键部署**：支持 Docker，也支持纯 Python 直接跑

## 🚀 快速开始

### 方式一：Docker

```bash
git clone https://github.com/你的用户名/gaokao-advisor-lite.git
cd gaokao-advisor-lite
cp .env.example .env
docker-compose up -d
# 访问 http://localhost:8766
```

### 方式二：直接 Python 运行

```bash
git clone https://github.com/你的用户名/gaokao-advisor-lite.git
cd gaokao-advisor-lite
pip install -r requirements.txt
python server.py
# 浏览器打开 http://localhost:8766
```

打开页面后，点右上角 ⚙ 设置图标，填入 DeepSeek API Key（去 platform.deepseek.com 获取），即可开始对话。

## ⚙️ 配置

编辑 `.env`（可选，本地自用也可以完全不配，直接在前端填 Key）：

```ini
LLM_URL=https://api.deepseek.com/chat/completions
LLM_API_KEY=***
LLM_MODEL=deepseek-chat
PORT=8766
```

- `LLM_API_KEY` 留空 → 用户必须在前端设置页填自己的 Key
- `LLM_API_KEY` 填了 → 前端无需填 Key 直接可用（适合部署给家人共用）

## 📚 知识库

`data/` 目录下有三份轻量 JSON，启动时自动加载到内存：

| 文件 | 内容 | 条数 |
|------|------|------|
| `schools.json` | 全国院校（含 985/211 标签、公办/民办、类型、所在地） | 2991 |
| `majors.json` | 本科专业目录（代码、名称、学科门类、专业类） | 833 |
| `batch_lines.json` | 近年各省省控线（本科批/专科批） | 409 |

提问时，后端会按关键词自动检索：提到校名→注入该校信息；提到专业→注入专业目录；提到省份+分数线→注入该省省控线。命中时对话下方会显示"已参考本地知识库数据"。

**替换/扩充**：直接覆盖对应 JSON 文件，重启服务即可。格式见文件内容。知识库不含历年录取明细，如需更精准数据请自行补充。

## 📖 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/chat` | 对话（自动检索知识库） |
| `GET` | `/api/health` | 健康检查 + 知识库统计 |
| `DELETE` | `/api/session/{id}` | 清空会话上下文 |

```bash
curl -X POST http://localhost:8766/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"北京大学是985吗","session_id":"s1","user_api_key":"sk-xxx"}'
```

## 🎨 自定义助手

编辑 `system_prompt.md`，重启服务即可。示例：

```markdown
你是一位资深健身教练，专攻减脂和增肌。
1. 根据身高体重给出针对性建议
2. 推荐动作时标注目标肌群和组数
```

前端 `index.html` 的标题、欢迎语、配色也可自行修改。

## ❓ FAQ

**Q: API Key 安全吗？**
A: 前端填的 Key 只存浏览器 localStorage，请求时直连 DeepSeek 官方接口，不经本服务器存储。

**Q: 对话记录会保存吗？**
A: 不会。上下文只存在进程内存，重启即清空。

**Q: 知识库数据准确吗？**
A: 知识库为轻量版元数据，仅供参考。涉及具体录取分数等请以官方公布为准。

## 📋 项目结构

```
.
├── server.py              # 后端（FastAPI + 知识库检索）
├── index.html             # 前端（单文件 H5）
├── system_prompt.md       # AI 角色设定（可改）
├── data/                  # 轻量知识库
│   ├── schools.json       # 院校
│   ├── majors.json        # 专业目录
│   └── batch_lines.json   # 省控线
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── LICENSE                # CC BY-NC 4.0
```

## 📄 License

CC BY-NC 4.0 — 可自由使用、修改、分享，但**禁止商业用途**。商业授权请联系瑞克无限Rick。

在线体验：[rickinf.top](https://rickinf.top)
