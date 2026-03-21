# My-Digirain - OpenClaw 私有知识库 Skill

你的个人 AI 知识库助手，让 OpenClaw 学习你提供的文档，并基于这些知识回答问题。

## 什么是 My-Digirain？

My-Digirain 是一个 OpenClaw Skill，让你可以：
- 📚 **上传文档学习** - 将 PDF、EPUB、TXT 等文档上传给 AI 学习
- 💬 **智能问答** - 基于已学习的文档回答问题
- 🧠 **构建个人知识库** - 持续添加文档，打造专属知识体系

## 安装前提

在安装 My-Digirain 之前，你需要准备：

### 1. 安装 Ollama（嵌入模型服务）

**macOS / Linux:**
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载 BGE-M3 嵌入模型（用于语义理解）
ollama pull bge-m3
```

**Windows:**
1. 下载 Ollama: https://ollama.com/download/windows
2. 安装后打开终端，运行：`ollama pull bge-m3`

### 2. 安装 Python 依赖

```bash
# 确保有 Python 3.8+
python3 --version

# 安装依赖
pip install chromadb pypdf epublib python-multipart
```

## 安装步骤

### 方式一：OpenClaw 用户（推荐）

```bash
# 安装 Skill
clawhub install my-digirain

# 重启 OpenClaw
openclaw restart
```

### 方式二：手动安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/My-Digirain.git
cd My-Digirain

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 1. 首次使用

安装完成后，对 OpenClaw 说：
```
你好，我想学习这个文档
```
或上传一个文件，My-Digirain 会引导你完成学习。

### 2. 学习文档

方式一：直接上传文件到聊天窗口

方式二：使用命令
```
学习 /path/to/your/document.pdf
```

### 3. 提问

学习完成后，直接提问：
```
关于这个文档的内容，xxx 是怎么说的？
```

## 命令列表

| 命令 | 说明 |
|------|------|
| `学习 <文件>` | 上传并学习文档 |
| `我的知识库` | 查看已学习的文档列表 |
| `查询 <问题>` | 基于知识库提问 |
| `删除 <文档名>` | 从知识库移除文档 |
| `清空知识库` | 删除所有学习的内容 |

## 支持的格式

- PDF (.pdf)
- EPUB (.epub)
- 文本 (.txt)
- Word (.docx) - 即将支持

## 常见问题

### Q: 第一次使用需要做什么？
A: 确保 Ollama 已安装并运行了 `ollama pull bge-m3`

### Q: 知识库数据存储在哪里？
A: `knowledge_base/chroma_db/` 目录下

### Q: 可以同时学习多本书吗？
A: 可以，My-Digirain 支持多个文档，会自动整合知识

### Q: 学习后的文档可以删除吗？
A: 可以，使用 `删除 <文档名>` 命令

## 技术架构

```
My-Digirain/
├── SKILL.md           # Skill 定义
├── core/              # 核心引擎
│   ├── chunker.py     # 文本分块
│   ├── vector_store.py # 向量存储
│   └── embedder.py    # 嵌入模型
├── scripts/           # 命令脚本
│   ├── learn.py       # 学习文档
│   └── query.py       # 问答
└── knowledge_base/    # 用户知识库
```

## 更新日志

### v0.1.0 (2026-03-21)
- ✅ 初始版本
- ✅ 支持 PDF/EPUB/TXT 文档学习
- ✅ 基于 BGE-M3 的语义检索
- ✅ ChromaDB 向量存储

## 获取帮助

- 问题反馈：https://github.com/your-repo/My-Digirain/issues
- 文档更新：请查看 README.md

---

**让 AI 更懂你，从 My-Digirain 开始！** 🧠
