---
name: my-digirain
description: My-Digirain 是你的私人 AI 知识库。用于用户上传文档学习、智能问答、基于个人知识库的对话。当用户提到"学习文档"、"上传知识"、"我的知识库"、"关于这个文档"、或发送 PDF/EPUB/TXT 文件时触发此 Skill。
---

# My-Digirain - 私有知识库 Skill

你的个人 AI 知识库助手，让 OpenClaw 学习你提供的文档，并基于这些知识回答问题。

## 概述

My-Digirain 是一个深度集成 OpenClaw 的私有知识库 Skill：
- 用户可通过聊天窗口上传文档
- 自动分块、向量化、存储到独立知识库
- 基于学习的知识进行问答和建议
- 面向零技术基础用户设计

## 核心功能

### 1. 文档学习
- 支持 PDF、EPUB、TXT 格式
- 自动文本提取和分块
- 向量化后存入 ChromaDB
- 独立的知识库（不与现有系统共享）

### 2. 智能问答
- 基于用户上传的文档进行语义检索
- 返回相关内容 + 引用来源
- 支持多文档联合查询

### 3. 知识管理
- 列出已学习的文档
- 删除指定文档
- 清空知识库

## 使用场景

### 场景 1：首次学习文档

**用户**："我想学习这个文档"（上传 PDF 文件）

**My-Digirain**：
```
📚 正在学习文档...

✅ 学习完成！
- 文档名：xxx.pdf
- 提取内容：XXX 个段落
- 知识块：XXX 个

现在你可以问我关于这份文档的问题了！
```

### 场景 2：基于知识问答

**用户**："关于这份文档，xxx 是怎么说的？"

**My-Digirain**：
```
📖 根据你学习的文档，回答如下：

[AI 生成的回答]

📚 参考来源：
1. xxx.pdf (相关性: 0.85)
2. xxx.pdf (相关性: 0.72)
```

### 场景 3：查看知识库

**用户**："我的知识库有哪些？"

**My-Digirain**：
```
📚 你的知识库包含：

1. 产品手册.pdf (2026-01-15 学习)
2. 技术文档.pdf (2026-01-16 学习)
3. 笔记.txt (2026-01-17 学习)

共计 3 个文档，XXX 个知识块
```

## 命令触发

### 自动触发
- 用户上传 PDF/EPUB/TXT 文件
- 用户提到："学习"、"上传知识"、"我的知识库"

### 手动命令
| 命令 | 说明 |
|------|------|
| `学习 <文件>` | 学习指定文档 |
| `我的知识库` | 查看已学习文档 |
| `查询 <问题>` | 基于知识库提问 |
| `删除 <文档>` | 删除指定文档 |
| `清空知识库` | 清空所有知识 |

## 技术实现

### 依赖项
- Python 3.8+
- ChromaDB（向量存储）
- Ollama + BGE-M3（嵌入模型）
- pypdf / epublib（文档解析）

### 知识库位置
- 路径：`{skill_path}/knowledge_base/chroma_db/`
- **独立于现有系统**，不影响现有数据

### 核心模块

```python
# core/chunker.py - 文本分块
class TextChunker:
    def chunk_document(self, text: str) -> List[TextChunk]:
        """将文档分割成小块"""
        
# core/vector_store.py - 向量存储  
class VectorStore:
    def add_chunks(self, chunks: List[TextChunk]):
        """添加知识块到向量库"""
        
    def search(self, query: str, top_k: int) -> List[SearchResult]:
        """语义搜索"""
        
# core/embedder.py - 嵌入模型
class Embedder:
    def embed_text(self, text: str) -> List[float]:
        """将文本转为向量"""
```

### 脚本接口

```bash
# 学习文档
python scripts/learn.py /path/to/document.pdf

# 查询
python scripts/query.py "你的问题"

# 管理
python scripts/manage.py list
python scripts/manage.py delete <doc_name>
python scripts/manage.py clear
```

## 环境检测

首次使用时，Skill 会自动检测：

1. **Ollama 是否运行**
   - 未运行 → 提示启动命令
   
2. **BGE-M3 模型是否已安装**
   - 未安装 → 提示下载命令

3. **Python 依赖是否完整**
   - 缺失 → 提示安装命令

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| Ollama 未运行 | 服务未启动 | 运行 `ollama serve` |
| 模型未找到 | 未下载模型 | 运行 `ollama pull bge-m3` |
| 文件格式不支持 | 不支持的格式 | 使用 PDF/EPUB/TXT |
| 知识库为空 | 未学习任何文档 | 先上传文档学习 |

## 配置文件

```yaml
# config.yaml
rag:
  chunk_size: 500          # 分块大小
  chunk_overlap: 100       # 重叠大小
  top_k: 5                 # 返回结果数
  embedding_model: bge-m3  # 嵌入模型
  
storage:
  knowledge_base_path: ./knowledge_base/chroma_db
  
supported_formats:
  - pdf
  - epub
  - txt
```

## 更新日志

### v0.1.0 (2026-03-21)
- ✅ 初始版本
- ✅ 文档学习功能
- ✅ 语义问答功能
- ✅ 知识库管理
- ✅ 环境自动检测

## 注意事项

1. **数据独立**：知识库存储在 Skill 目录下，不影响现有系统
2. **隐私安全**：所有数据本地存储，不上传云端
3. **首次使用**：需要安装 Ollama 和 BGE-M3 模型
4. **文件大小**：建议单文件不超过 50MB

---

**让 AI 更懂你，从 My-Digirain 开始！** 🧠
