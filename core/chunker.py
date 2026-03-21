#!/usr/bin/env python3
"""
My-Digirain 文本分块模块
将文档分割成适合检索的小块
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
import hashlib

# 配置
CONFIG_FILE = Path(__file__).parent / "config.yaml"


@dataclass
class TextChunk:
    """文本块"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self.generate_id()
    
    def generate_id(self) -> str:
        """生成唯一 ID"""
        return hashlib.md5(self.content.encode()).hexdigest()[:12]


class TextChunker:
    """智能文本分块器"""
    
    MIN_CHUNK_SIZE = 50  # 最小块大小
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        # 加载配置
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                config = yaml.safe_load(f)
                self.chunk_size = config.get("rag", {}).get("chunk_size", chunk_size)
                self.chunk_overlap = config.get("rag", {}).get("chunk_overlap", chunk_overlap)
        else:
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, source: str = "unknown") -> List[TextChunk]:
        """
        将文本分割成块
        
        Args:
            text: 输入文本
            source: 来源标识
            
        Returns:
            文本块列表
        """
        chunks = []
        
        # 先按段落分割
        paragraphs = self._split_into_paragraphs(text)
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            # 如果当前段落加上当前块超过限制
            if len(current_chunk) + len(para) > self.chunk_size:
                # 保存当前块（如果非空）
                if current_chunk.strip():
                    chunk = TextChunk(
                        id=f"{source}_{chunk_index}",
                        content=current_chunk.strip(),
                        metadata={
                            "source": source,
                            "chunk_index": chunk_index,
                            "char_count": len(current_chunk)
                        }
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # 开始新块，保留重叠部分
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + para
                else:
                    current_chunk = para
            else:
                current_chunk += "\n" + para if current_chunk else para
        
        # 保存最后一个块
        if current_chunk.strip():
            chunk = TextChunk(
                id=f"{source}_{chunk_index}",
                content=current_chunk.strip(),
                metadata={
                    "source": source,
                    "chunk_index": chunk_index,
                    "char_count": len(current_chunk)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """按段落分割"""
        # 清理多余空白
        text = re.sub(r'\n\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # 按换行分割
        paragraphs = text.split('\n\n')
        
        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def chunk_document(self, text: str, source: str = "document", 
                       title: str = "", author: str = "") -> List[TextChunk]:
        """
        分块文档（带元数据）
        
        Args:
            text: 文档文本
            source: 来源标识
            title: 文档标题
            author: 作者
            
        Returns:
            文本块列表
        """
        chunks = self.chunk_text(text, source)
        
        # 添加元数据
        for chunk in chunks:
            chunk.metadata.update({
                "title": title,
                "author": author,
                "source": source
            })
        
        return chunks


def main():
    """测试分块功能"""
    print("🧪 测试分块功能...")
    
    chunker = TextChunker()
    
    test_text = """
这是第一段内容。这里包含了关于某个主题的详细介绍。

这是第二段内容。包含更多的信息和细节。

这是第三段内容。进一步阐述了这个主题的各个方面。

这是第四段。提供了更多的背景知识。

这是第五段。最终总结了这个主题。
    """.strip()
    
    chunks = chunker.chunk_text(test_text, "test")
    
    print(f"✅ 分块完成！共 {len(chunks)} 个块")
    for i, chunk in enumerate(chunks):
        print(f"\n--- 块 {i+1} ---")
        print(f"ID: {chunk.id}")
        print(f"内容: {chunk.content[:100]}...")
        print(f"字符数: {chunk.metadata.get('char_count', 0)}")


if __name__ == "__main__":
    main()
