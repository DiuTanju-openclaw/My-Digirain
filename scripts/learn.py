#!/usr/bin/env python3
"""
My-Digirain 学习模块 - 优化版
支持按章节拆分处理大文件
"""

import sys
import os
import re
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.chunker import TextChunker
from core.embedder import Embedder
from core.vector_store import VectorStore

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
    elif ext in [".mobi", ".azw3", ".azw"]:
        return extract_mobi(path)
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
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        
        book = epub.read_epub(str(path))
        text = ''
        for item in book.get_items():
            if item.get_type() == 9:  # HTML
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text() + '\n'
        return text
    except Exception as e:
        raise Exception(f"EPUB 解析失败: {e}")


def extract_mobi(path: Path) -> str:
    """提取 MOBI/AZW3 文本"""
    try:
        import mobi
        from bs4 import BeautifulSoup
        
        # 检查文件头，识别真实格式
        with open(path, 'rb') as f:
            header = f.read(10)
        
        # 如果实际是 EPUB（文件头包含 PK），用 epub 解析器
        if header[:2] == b'PK':
            print(f"     ℹ️ 检测到真实格式为 EPUB，自动使用 EPUB 解析器")
            return extract_epub(path)
        
        # 使用 mobi 库提取
        extracted = mobi.extract(str(path))
        
        if extracted:
            # 读取提取的 HTML 文件
            html_file = Path(extracted)
            if html_file.exists():
                with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                
                # 解析 HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n')
                
                # 清理临时文件
                try:
                    html_file.unlink()
                except:
                    pass
                    
                return text
        
        raise Exception("未能从 MOBI 文件中提取文本")
    except ImportError:
        raise Exception("请安装 mobi 库: pip install mobi")
    except Exception as e:
        raise Exception(f"MOBI 解析失败: {e}")


def split_by_chapters(text: str) -> list:
    """按章节拆分文本（跳过目录，直接解析正文）"""
    import re
    # 匹配章节标题
    chapter_pattern = r'^\s*(第[一二三四五六七八九十\d]+章.*|引言.*|前言.*|附录.*|结论.*|后记.*|推荐序.*|致谢.*)'
    lines = text.split('\n')
    
    # 找到正文开始位置：寻找"推荐序"后面跟着段落内容
    start_idx = 0
    preface_count = 0
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if '推荐序' in line_stripped and not line_stripped.startswith('第') and len(line_stripped) < 20:
            preface_count += 1
            if preface_count == 2:
                # 第二个"推荐序"后面几行就是正文开始
                start_idx = i + 2
                # 跳过空行
                while start_idx < len(lines) and not lines[start_idx].strip():
                    start_idx += 1
                break
    
    # 如果没找到，使用经验值
    if start_idx == 0:
        start_idx = 389  # 已知正文开始位置
    
    # 从找到的位置开始解析
    chapters = []
    current_chapter = {'title': '前言', 'content': ''}
    
    i = 0
    line_list = lines[start_idx:]
    while i < len(line_list):
        line_stripped = line_list[i].strip()
        if re.match(chapter_pattern, line_stripped):
            # 保存上一章
            if current_chapter['content'].strip():
                chapters.append(current_chapter)
            
            # 合并多行标题（章节标题可能分成多行）
            full_title = line_stripped
            # 检查后续行是否也是标题的一部分
            j = i + 1
            while j < len(line_list):
                next_line = line_list[j].strip()
                # 如果下一行是非空短行（<60字符），可能是标题的一部分
                if next_line and len(next_line) < 60 and len(next_line) > 2:
                    # 跳过空行
                    if not next_line:
                        j += 1
                        continue
                    # 如果不以句号/逗号/感叹号结尾，认为可能是标题
                    if not any(next_line.endswith(c) for c in '。！？.,!?'):
                        # 跳过已知非标题内容
                        if next_line in ['Unknown', ' ', '']:
                            break
                        full_title += ' ' + next_line
                        j += 1
                    else:
                        break
                else:
                    break
            
            current_chapter = {'title': full_title, 'content': ''}
            i = j
        else:
            current_chapter['content'] += line_stripped + '\n'
            i += 1
    
    # 保存最后一章
    if current_chapter['content'].strip():
        chapters.append(current_chapter)
    
    return chapters


def learn_chapter(chapter: dict, source: str, batch_size: int = 30, 
                  smart_chunk: bool = True) -> int:
    """
    学习单个章节
    
    Args:
        chapter: 章节 dict，包含 title 和 content
        source: 文档来源标识
        batch_size: 向量化批大小
        smart_chunk: 是否使用智能分块（根据内容大小自动调整）
    
    Returns:
        导入的知识块数量
    """
    title = chapter['title']
    text = chapter['content']
    
    char_count = len(text)
    print(f"  📖 处理章节: {title} ({char_count} 字符)")
    
    # 分块 - 使用智能分块
    chunker = TextChunker()
    
    if smart_chunk:
        # 智能分块：自动根据内容大小选择最佳分块策略
        # 先不分 title，因为 smart_chunk_text 会自动处理
        chunks = chunker.smart_chunk_text(text, source=source)
    else:
        chunks = chunker.chunk_document(text, source=source, title=title)
    
    print(f"     分块: {len(chunks)} 个")
    
    # 向量化 - 串行处理，每条显示进度
    embedder = Embedder()
    texts = [chunk.content for chunk in chunks]
    
    all_embeddings = []
    total = len(texts)
    
    for i, text in enumerate(texts):
        try:
            print(f"     [{i+1}/{total}] 嵌入中...", end="\r", flush=True)
            emb = embedder.embed_text(text)
            all_embeddings.append(emb)
        except Exception as e:
            print(f"     ⚠️ 嵌入失败: {e}", flush=True)
            all_embeddings.append(None)  # 占位
    
    print(f"     完成 {total} 个嵌入", flush=True)
    
    # 存入向量库
    store = VectorStore()
    # 过滤掉 None 的嵌入
    valid_chunks = []
    valid_embeddings = []
    for c, e in zip(chunks, all_embeddings):
        if e is not None:
            valid_chunks.append(c)
            valid_embeddings.append(e)
    
    if valid_chunks:
        count = store.add_chunks(valid_chunks, valid_embeddings, source)
    else:
        count = 0
    
    return count


def learn_document(file_path: str, verbose: bool = True) -> dict:
    """
    学习文档 (支持大文件按章节拆分)
    
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
    
    # 2. 按章节拆分
    if verbose:
        print("   [2/4] 按章节拆分...")
    chapters = split_by_chapters(text)
    print(f"   发现 {len(chapters)} 个章节")
    
    # 3. 逐章学习
    if verbose:
        print("   [3/4] 逐章向量化...")
    total_chunks = 0
    for i, chapter in enumerate(chapters):
        print(f"   [{i+1}/{len(chapters)}]", end=" ")
        count = learn_chapter(chapter, doc_name)
        total_chunks += count
        
        # 写入进度文件
        with open("/tmp/learn_progress.txt", "w") as f:
            f.write(f"{i+1}/{len(chapters)}|{chapter['title']}|{total_chunks}")
    
    # 完成后写入完成标记
    with open("/tmp/learn_progress.txt", "w") as f:
        f.write(f"done|{len(chapters)} chapters|{total_chunks} chunks")
    
    if verbose:
        print(f"   向量化的总知识块: {total_chunks}")
    
    if verbose:
        print("   [4/4] 完成!")
    
    return {
        "success": True,
        "document": doc_name,
        "char_count": char_count,
        "chapter_count": len(chapters),
        "chunk_count": total_chunks,
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
            print(f"   章节数: {result['chapter_count']}")
            print(f"   知识块: {result['chunk_count']}")
        else:
            print(f"\n❌ 学习失败: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
