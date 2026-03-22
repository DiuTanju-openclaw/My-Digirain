#!/usr/bin/env python3
"""
RAG 问答模块
集成向量检索 + LLM 生成回答
"""

import os
import json
from typing import List, Dict, Any, Optional
from core.embedder import Embedder
from core.vector_store import VectorStore


class RAGQuery:
    """RAG 问答系统"""
    
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()
    
    def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        检索 + 生成回答
        
        Args:
            question: 用户问题
            top_k: 检索的段落数
            
        Returns:
            {
                "answer": "LLM生成的回答",
                "sources": [{"content": "...", "score": ...}],
                "context_len": 上下文字符数
            }
        """
        # 1. 向量检索
        query_emb = self.embedder.embed_text(question)
        results = self.store.search(query_emb, top_k=top_k)
        
        # 2. 构建上下文
        context = "\n\n".join([r['content'] for r in results])
        
        # 3. 构建 prompt
        prompt = self._build_prompt(question, context)
        
        # 4. 调用 LLM 生成回答
        answer = self._generate(prompt)
        
        return {
            "answer": answer,
            "sources": results,
            "context_len": len(context)
        }
    
    def _build_prompt(self, question: str, context: str) -> str:
        """构建 prompt"""
        return f"""你是一个专业的问答助手。请基于以下参考资料，用中文回答用户的问题。

要求：
1. 只基于参考内容回答，不要添加额外知识
2. 如果参考内容不足以回答，请如实说明
3. 回答要简洁、有条理

参考资料：
{context}

用户问题：{question}

回答："""
    
    def _generate(self, prompt: str) -> str:
        """调用 OpenClaw 模型的 API 生成回答"""
        # 使用 OpenClaw 配置的模型
        # 通过环境变量或配置文件获取 API 配置
        
        api_base = os.environ.get("OPENCLAW_API_BASE", "https://qianfan.baidubce.com/v2")
        api_key = os.environ.get("OPENCLAW_API_KEY", "")
        
        # 尝试读取 OpenClaw 配置
        config_path = os.path.expanduser("~/.config/openclaw/models.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                # 使用当前配置的模型
                model = config.get("current_model", "baiduqianfancodingplan/qianfan-code-latest")
        
        # 如果没有配置，使用简单方式（通过 curl 调用）
        # 这里我们返回 prompt，让上层处理实际的 LLM 调用
        # 实际使用中，可以通过 API 调用
        
        # 由于无法直接调用百度千帆 API，这里返回提示
        # 实际集成时可以使用 openai SDK 或 requests
        return None  # 需要外部调用 LLM


def rag_query(question: str, top_k: int = 3) -> Dict[str, Any]:
    """
    便捷函数：RAG 问答
    
    返回格式：
    {
        "question": "用户问题",
        "answer": "回答", 
        "sources": [{"content": "...", "score": ...}],
        "retrieval_time": 0.1,
        "llm_time": 0.0
    }
    """
    import time
    
    start = time.time()
    
    # 检索
    embedder = Embedder()
    store = VectorStore()
    
    query_emb = embedder.embed_text(question)
    results = store.search(query_emb, top_k=top_k)
    
    retrieval_time = time.time() - start
    
    # 构建上下文
    context = "\n\n".join([r['content'] for r in results])
    
    return {
        "question": question,
        "answer": None,  # 需要 LLM 生成
        "sources": results,
        "context": context,
        "retrieval_time": retrieval_time,
        "llm_time": 0.0
    }


# 测试
if __name__ == "__main__":
    # 测试检索
    result = rag_query("什么是优质问题？")
    print(f"检索到 {len(result['sources'])} 条相关内容")
    print(f"上下文长度: {result['context_len']} 字符")
    print("\n请使用 LLM 生成最终回答")
