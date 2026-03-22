# My-Digirain 🤖📚

> 基于 Ollama BGE-M3 的本地 RAG 知识库系统

![Python Version](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📖 简介

My-Digirain 是一个本地 RAG（检索增强生成）知识库系统，支持：
- 📚 多格式文档导入（PDF, EPUB, TXT, MOBI, AZW3）
- 🔍 向量语义搜索（BGE-M3 嵌入模型）
- 💾 ChromaDB 本地向量存储
- 🧠 RAG 问答（集成 OpenClaw LLM）

## 🏗️ 架构

```
My-Digirain/
├── core/                    # 核心模块
│   ├── chunker.py          # 智能文本分块
│   ├── embedder.py         # BGE-M3 向量化
│   ├── vector_store.py     # ChromaDB 存储
│   └── rag.py              # RAG 问答模块
├── scripts/
│   └── learn.py            # 文档导入脚本
├── knowledge_base/         # 知识库存储
│   └── chroma_db/          # ChromaDB 数据
├── downloads/              # 待处理文档
└── config.yaml              # 配置文件
```

## ⚡ 性能

| 指标 | 数据 |
|------|------|
| **向量维度** | 1024 (BGE-M3) |
| **知识库规模** | 87 知识块 |
| **平均检索延迟** | < 0.5s |
| **章节导入耗时** | ~3 分钟/章 |
| **嵌入生成速度** | ~40 秒/块 |

### 章节导入统计
| 章节 | 字符数 | 知识块 | 耗时 |
|------|--------|--------|------|
| 第1-9章 | ~157K | 46 | ~30min |
| 后记+致谢 | ~13K | 41 | ~1.5min |
| **总计** | ~170K | 87 | ~33min |

## 🚀 快速开始

### 1. 克隆与安装

```bash
# 克隆项目
git clone https://github.com/your-repo/My-Digirain.git
cd My-Digirain

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 Ollama

```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取 BGE-M3 嵌入模型
ollama pull bge-m3

# 验证
ollama list
```

### 3. 配置 config.yaml

```yaml
# config.yaml
ollama:
  base_url: "http://localhost:11434"
  embedding_model: "bge-m3"

chroma:
  persist_directory: "./knowledge_base/chroma_db"

chunker:
  min_chunk_size: 50
  max_chunk_size: 8000
  chunk_overlap: 200
```

### 4. 导入书籍

```bash
# 导入书籍（支持 PDF, EPUB, TXT, MOBI, AZW3）
python scripts/learn.py downloads/问题即答案.txt
```

### 5. RAG 问答

```python
import sys
sys.path.insert(0, '.')

from core.embedder import Embedder
from core.vector_store import VectorStore

# 检索
embedder = Embedder()
store = VectorStore()

query = "优质问题有哪些特征？"
query_emb = embedder.embed_text(query)
results = store.search(query_emb, top_k=3)

# 显示结果
for r in results:
    print(r['content'][:200])
```

## 📖 功能特性

### ✅ 已实现

1. **智能章节解析**
   - 自动跳过目录（TOC）
   - 多行标题合并
   - 支持副标题

2. **智能文本分块**
   - 小文本 (<10K): 500 字符/块
   - 中等文本 (10K-50K): 4000 字符/块
   - 大文本 (50K-100K): 8000 字符/块
   - 超大文本 (>100K): 递归分块

3. **多格式支持**
   - PDF (pypdf)
   - EPUB (epublib)
   - TXT (纯文本)
   - MOBI/AZW3 (mobi)

4. **RAG 问答**
   - 向量检索 + LLM 生成
   - 使用 OpenClaw LLM 整理总结

5. **唯一 ID 生成**
   - 基于内容哈希 (MD5)

### 🔄 待完成

- [ ] 安装聊天模型（qwen2.5）用于本地 LLM 生成
- [ ] Web UI 界面
- [ ] CLI 命令行工具

## 📝 使用示例

### 导入书籍

```bash
# 方式1: 命令行
python scripts/learn.py downloads/书籍.txt

# 方式2: Python API
from scripts.learn import extract_text_from_file, split_by_chapters, learn_chapter

text = extract_text_from_file('book.txt')
chapters = split_by_chapters(text)

for chapter in chapters:
    learn_chapter(chapter, '书名')
```

### 检索查询

```python
from core.embedder import Embedder
from core.vector_store import VectorStore

embedder = Embedder()
store = VectorStore()

# 语义搜索
results = store.search(
    embedder.embed_text("你的问题"),
    top_k=5
)

for r in results:
    print(f"相似度: {r['score']:.3f}")
    print(f"内容: {r['content'][:100]}...")
```

## 📦 依赖

```
chromadb>=0.4.0
ollama>=0.1.0
pypdf>=3.0.0
epublib>=0.0.0
mobi>=0.0.0
pyyaml>=6.0
requests>=2.28
```

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 PR！

---

*版本: 1.0.0 | 更新: 2026-03-22*
