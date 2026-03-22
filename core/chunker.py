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
    
    # 64K 上下文模型优化配置
    CONTEXT_OPTIMIZED = {
        "large": {"chunk_size": 8000, "chunk_overlap": 500},   # 大章节 - 适合 64k 上下文
        "medium": {"chunk_size": 4000, "chunk_overlap": 300},  # 中等章节
        "small": {"chunk_size": 2000, "chunk_overlap": 200},    # 小章节
        "default": {"chunk_size": 500, "chunk_overlap": 100},   # 默认配置
    }
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100, 
                 context_mode: str = None):
        # 加载配置
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                config = yaml.safe_load(f)
                self.chunk_size = config.get("rag", {}).get("chunk_size", chunk_size)
                self.chunk_overlap = config.get("rag", {}).get("chunk_overlap", chunk_overlap)
        else:
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
        
        # 根据上下文模式调整
        if context_mode and context_mode in self.CONTEXT_OPTIMIZED:
            opt = self.CONTEXT_OPTIMIZED[context_mode]
            self.chunk_size = opt["chunk_size"]
            self.chunk_overlap = opt["chunk_overlap"]
    
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
                        id=None,  # 让 TextChunk 自动生成 hash ID
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
                id=None,  # 让 TextChunk 自动生成 hash ID
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
    
    def smart_chunk_text(self, text: str, source: str = "unknown", 
                          max_chunk_size: int = None) -> List[TextChunk]:
        """
        智能分块 - 根据文本大小自动选择最佳分块策略
        
        策略：
        1. 超大文本 (>100K字符): 先按子章节拆分，再分块
        2. 大文本 (50K-100K字符): 使用大块模式 (8000字符/块)
        3. 中等文本 (10K-50K字符): 使用中块模式 (4000字符/块)
        4. 小文本 (<10K字符): 使用默认模式 (500字符/块)
        
        Args:
            text: 输入文本
            source: 来源标识
            max_chunk_size: 最大块大小限制
            
        Returns:
            文本块列表
        """
        text_len = len(text)
        
        # 保存原始配置
        original_size = self.chunk_size
        original_overlap = self.chunk_overlap
        
        try:
            if text_len > 100000:
                # 超大文本：使用最大块 + 递归拆分
                print(f"     📐 超大文本 ({text_len} 字符)，使用分阶段分块...")
                return self._chunk_ultra_large(text, source)
            elif text_len > 50000:
                # 大文本：使用大块模式
                print(f"     📐 大文本 ({text_len} 字符)，使用大块模式...")
                self.chunk_size = 8000
                self.chunk_overlap = 500
            elif text_len > 10000:
                # 中等文本：使用中块模式
                print(f"     📐 中等文本 ({text_len} 字符)，使用中块模式...")
                self.chunk_size = 4000
                self.chunk_overlap = 300
            else:
                # 小文本：使用默认模式
                self.chunk_size = max_chunk_size or 500
                self.chunk_overlap = 100
            
            # 执行分块
            return self.chunk_text(text, source)
            
        finally:
            # 恢复原始配置
            self.chunk_size = original_size
            self.chunk_overlap = original_overlap
    
    def _chunk_ultra_large(self, text: str, source: str) -> List[TextChunk]:
        """处理超大文本 - 分阶段分块"""
        # 第一阶段：按子章节/大段落拆分
        sections = self._split_into_sections(text)
        
        all_chunks = []
        for i, section in enumerate(sections):
            section_chunks = self.chunk_text(section["content"], 
                                              f"{source}_s{i}")
            # 添加节标题到元数据
            for chunk in section_chunks:
                chunk.metadata["section_title"] = section.get("title", "")
            all_chunks.extend(section_chunks)
        
        return all_chunks
    
    def _split_into_sections(self, text: str) -> List[Dict]:
        """将文本拆分成更大的节（用于超大文本处理）"""
        # 按较粗的边界拆分（章节、Part、大节等）
        section_pattern = r'^(第[一二三四五六七八九十\d]+[章节部篇]|Part\s+\d+|第[一二三四五六七八九十\d]+部分|引言|前言|结论|附录|后记)'
        
        lines = text.split('\n')
        sections = []
        current_section = {"title": "全文", "content": ""}
        
        for line in lines:
            line = line.strip()
            if re.match(section_pattern, line, re.IGNORECASE):
                # 保存上一节
                if current_section["content"].strip():
                    sections.append(current_section)
                # 开始新节
                current_section = {"title": line, "content": ""}
            else:
                current_section["content"] += line + "\n"
        
        # 保存最后一节
        if current_section["content"].strip():
            sections.append(current_section)
        
        # 如果没有找到分节符，整个文本作为一个节
        if len(sections) == 0:
            sections = [{"title": "全文", "content": text}]
        
        return sections
    
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
