#!/usr/bin/env python3
"""
My-Digirain 管理模块
知识库管理命令
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector_store import VectorStore
import json


def list_documents():
    """列出所有已学习的文档"""
    store = VectorStore()
    docs = store.get_documents()
    
    if not docs:
        print("📚 知识库为空，还没有学习任何文档")
        return
    
    print("📚 已学习的文档：\n")
    print(f"{'文档名':<30} {'知识块数':>10}")
    print("-" * 42)
    
    total_chunks = 0
    for doc in docs:
        name = doc.get("name", "未知")
        chunks = doc.get("chunk_count", 0)
        print(f"{name:<30} {chunks:>10}")
        total_chunks += chunks
    
    print("-" * 42)
    print(f"{'共 ' + str(len(docs)) + ' 个文档':<30} {total_chunks:>10}")
    
    # 显示统计
    stats = store.get_stats()
    print(f"\n📊 总知识块: {stats['total_chunks']}")


def delete_document(doc_name: str):
    """删除指定文档"""
    store = VectorStore()
    
    # 确认存在
    docs = store.get_documents()
    exists = any(d["name"] == doc_name for d in docs)
    
    if not exists:
        print(f"❌ 文档不存在: {doc_name}")
        return False
    
    # 删除
    store.delete_document(doc_name)
    print(f"✅ 已删除文档: {doc_name}")
    return True


def clear_knowledge_base():
    """清空知识库"""
    store = VectorStore()
    store.clear()
    print("✅ 已清空知识库")


def show_stats():
    """显示统计信息"""
    store = VectorStore()
    stats = store.get_stats()
    
    print("📊 知识库统计：\n")
    print(f"  文档数:   {stats['total_documents']}")
    print(f"  知识块:   {stats['total_chunks']}")
    print(f"  存储路径: {stats['persist_path']}")


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python manage.py list           # 列出文档")
        print("  python manage.py delete <名称>  # 删除文档")
        print("  python manage.py clear          # 清空知识库")
        print("  python manage.py stats          # 显示统计")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "list":
            list_documents()
        elif command == "delete":
            if len(sys.argv) < 3:
                print("用法: python manage.py delete <文档名>")
                sys.exit(1)
            doc_name = sys.argv[2]
            delete_document(doc_name)
        elif command == "clear":
            confirm = input("确定要清空知识库吗？(y/N): ")
            if confirm.lower() == "y":
                clear_knowledge_base()
            else:
                print("已取消")
        elif command == "stats":
            show_stats()
        else:
            print(f"未知命令: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
