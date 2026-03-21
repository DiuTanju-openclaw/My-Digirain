#!/usr/bin/env python3
"""
My-Digirain 学习模块
从文档中提取内容并学习
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.chunker import TextChunker
from core.embedder import Embedder
from core.vector_store import VectorStore
import hashlib

# 文档解析器
def extract_text_from_file(file_path: str) -> str:
    """从文件中提取文本"""
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext == ".pdf":
        return extract_pdf(path)
    elif ext == ".txt":
        return extract_txt(path)
    elif ext == ".epub":
        return extract_epub(path)
    else:
        raise ValueError(f"不支持的格式: {ext}")


def extract_pdf(path: Path) -> str:
    """提取 PDF 文本"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"PDF 解析失败: {e}")


def extract_txt(path: Path) -> str:
    """提取 TXT 文本"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_epub(path: Path) -> str:
    """提取 EPUB 文本"""
    try:
        from epublib.core import parse_epub
        book = parse_epub(str(path))
        text = ""
        for item in book.spine:
            if item.href in book.resources:
                content = book.resources[item.href].get_content()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                text += content + "\n"
        return text
    except Exception as e:
        raise Exception(f"EPUB 解析失败: {e}")


def learn_document(file_path: str, verbose: bool = True) -> dict:
    """
    学习文档
    
    Args:
        file_path: 文档路径
        verbose: 是否输出详细信息
        
    Returns:
        学习结果
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 生成文档名
    doc_name = file_path.stem  # 文件名（不含扩展名）
    
    if verbose:
        print(f"📚 正在学习: {file_path.name}")
    
    # 1. 提取文本
    if verbose:
        print("   [1/4] 提取文本内容...")
    try:
        text = extract_text_from_file(file_path)
        char_count = len(text)
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    if verbose:
        print(f"   提取到 {char_count} 个字符")
    
    # 2. 分块
    if verbose:
        print("   [2/4] 分割知识块...")
    chunker = TextChunker()
    chunks = chunker.chunk_document(text, source=doc_name, title=doc_name)
    
    if verbose:
        print(f"   分割成 {len(chunks)} 个知识块")
    
    # 3. 向量化
    if verbose:
        print("   [3/4] 向量化处理...")
    embedder = Embedder()
    
    if not embedder.is_available():
        return {"success": False, "error": "Ollama 服务未运行，请先运行 ollama serve"}
    
    # 批量向量化
    texts = [chunk.content for chunk in chunks]
    embeddings = embedder.embed_batch(texts)
    
    if verbose:
        print(f"   完成 {len(embeddings)} 个向量的计算")
    
    # 4. 存入向量库
    if verbose:
        print("   [4/4] 存入知识库...")
    store = VectorStore()
    count = store.add_chunks(chunks, embeddings, doc_name)
    
    if verbose:
        print(f"   ✅ 已存入 {count} 个知识块")
    
    return {
        "success": True,
        "document": doc_name,
        "char_count": char_count,
        "chunk_count": count,
        "file_path": str(file_path)
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python learn.py <文件路径>")
        print("示例: python learn.py ./documents/book.pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        result = learn_document(file_path)
        
        if result["success"]:
            print(f"\n✅ 学习完成！")
            print(f"   文档: {result['document']}")
            print(f"   字符数: {result['char_count']}")
            print(f"   知识块: {result['chunk_count']}")
        else:
            print(f"\n❌ 学习失败: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
