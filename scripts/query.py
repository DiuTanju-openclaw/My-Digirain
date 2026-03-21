#!/usr/bin/env python3
"""
My-Digirain 查询模块
基于知识库进行问答
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embedder import Embedder
from core.vector_store import VectorStore
import yaml

# 加载配置
CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    return {}

def query_knowledge(question: str, top_k: int = 5, doc_filter: str = None,
                   verbose: bool = False) -> dict:
    """
    查询知识库
    
    Args:
        question: 问题
        top_k: 返回结果数
        doc_filter: 可选，按文档名过滤
        verbose: 是否输出详细信息
        
    Returns:
        查询结果
    """
    # 加载配置
    config = load_config()
    top_k = config.get("rag", {}).get("top_k", top_k)
    
    if verbose:
        print(f"🔍 查询: {question}")
    
    # 1. 检查嵌入服务
    if verbose:
        print("   [1/3] 加载嵌入模型...")
    embedder = Embedder()
    
    if not embedder.is_available():
        return {
            "success": False,
            "error": "Ollama 服务未运行，请先运行 ollama serve"
        }
    
    # 2. 向量化问题
    if verbose:
        print("   [2/3] 语义搜索...")
    query_embedding = embedder.embed_text(question)
    
    # 3. 搜索向量库
    if verbose:
        print("   [3/3] 检索知识...")
    store = VectorStore()
    results = store.search(query_embedding, top_k, doc_filter)
    
    if verbose:
        print(f"   找到 {len(results)} 个相关结果")
    
    return {
        "success": True,
        "question": question,
        "total_results": len(results),
        "results": results
    }


def format_results(results: dict) -> str:
    """格式化输出结果"""
    if not results.get("success"):
        return f"❌ 查询失败: {results.get('error', '未知错误')}"
    
    if results["total_results"] == 0:
        return "❓ 知识库为空，请先学习一些文档"
    
    output = []
    output.append(f"📚 关于「{results['question']}」的回答：\n")
    
    for i, r in enumerate(results["results"], 1):
        score = r.get("score", 0)
        content = r.get("content", "")
        metadata = r.get("metadata", {})
        doc_name = metadata.get("doc_name", "未知")
        
        output.append(f"--- 参考 {i} (相关性: {score:.2%}) ---")
        output.append(f"📖 来源: {doc_name}")
        output.append(f"📝 内容: {content[:500]}")
        if len(content) > 500:
            output.append("   ...")
        output.append("")
    
    return "\n".join(output)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python query.py <问题> [--top-k N] [--json]")
        print("示例: python query.py \"什么是机器学习\"")
        print("      python query.py \"问题\" --json")
        sys.exit(1)
    
    question = sys.argv[1]
    
    # 解析参数
    top_k = 5
    json_output = False
    
    for arg in sys.argv[2:]:
        if arg.startswith("--top-k="):
            top_k = int(arg.split("=")[1])
        elif arg == "--json":
            json_output = True
    
    try:
        result = query_knowledge(question, top_k=top_k)
        
        if json_output:
            import json
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_results(result))
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
