#!/usr/bin/env python3
"""
My-Digirain 嵌入模块
使用 Ollama BGE-M3 模型进行文本向量化
"""

import requests
import numpy as np
from typing import List, Optional
import yaml
from pathlib import Path
import sys

# 配置
CONFIG_FILE = Path(__file__).parent / "config.yaml"


class Embedder:
    """文本嵌入器，使用 Ollama BGE-M3"""
    
    def __init__(self, model: str = "bge-m3", ollama_url: str = "http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url
        
        # 加载配置
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                config = yaml.safe_load(f)
                self.model = config.get("rag", {}).get("embedding_model", self.model)
        
    def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def embed_text(self, text: str, max_retries: int = 2) -> List[float]:
        """
        将单个文本转为向量
        
        Args:
            text: 输入文本
            max_retries: 最大重试次数
            
        Returns:
            向量列表
        """
        # 截断过长文本
        if len(text) > 8000:
            text = text[:8000]
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    },
                    timeout=300  # 5分钟超时，处理大文本
                )
                
                if response.status_code == 200:
                    return response.json().get("embedding", [])
                elif response.status_code == 404:
                    raise Exception(f"模型 {self.model} 未找到")
                else:
                    raise Exception(f"Ollama error: {response.text}")
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"     ⚠️ 超时，重试 {attempt+1}/{max_retries}...", flush=True)
                    continue
                print(f"     ❌ 嵌入超时: {text[:50]}...", flush=True)
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"     ⚠️ 嵌入失败: {e}，重试中...", flush=True)
                    continue
                print(f"     ❌ 嵌入错误: {e}", flush=True)
        
        # 返回零向量作为后备
        return [0.0] * self.get_embedding_dimension()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        embeddings = []
        for text in texts:
            embedding = self.embed_text(text)
            embeddings.append(embedding)
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        # BGE-M3 是 1024 维
        return 1024


def main():
    """测试嵌入功能"""
    print("🧪 测试嵌入功能...")
    
    embedder = Embedder()
    
    # 检查服务
    if not embedder.is_available():
        print("❌ Ollama 服务未运行，请先运行: ollama serve")
        return
    
    print("✅ Ollama 服务正常")
    
    # 测试嵌入
    test_text = "This is a test document about artificial intelligence."
    embedding = embedder.embed_text(test_text)
    
    print(f"✅ 嵌入成功！向量维度: {len(embedding)}")
    print(f"   前5个值: {embedding[:5]}")


if __name__ == "__main__":
    main()
