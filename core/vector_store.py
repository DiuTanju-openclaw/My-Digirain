#!/usr/bin/env python3
"""
My-Digirain 向量存储模块
使用 ChromaDB 存储和检索向量
"""

import chromadb
from chromadb.config import Settings
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import hashlib

# 配置
CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"


class VectorStore:
    """基于 ChromaDB 的向量存储"""
    
    COLLECTION_NAME = "my_digirain_knowledge"
    
    def __init__(self, persist_path: Optional[str] = None):
        # 加载配置
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                config = yaml.safe_load(f)
                self.persist_path = persist_path or config.get("storage", {}).get(
                    "knowledge_base_path", 
                    "./knowledge_base/chroma_db"
                )
        else:
            self.persist_path = persist_path or "./knowledge_base/chroma_db"
        
        # 确保目录存在
        Path(self.persist_path).mkdir(parents=True, exist_ok=True)
        
        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "My-Digirain 知识库"}
        )
        
        # 加载文档索引
        self._load_index()
    
    def _load_index(self):
        """加载文档索引"""
        index_file = Path(self.persist_path) / "document_index.json"
        if index_file.exists():
            with open(index_file) as f:
                self.doc_index = json.load(f)
        else:
            self.doc_index = {}
    
    def _save_index(self):
        """保存文档索引"""
        index_file = Path(self.persist_path) / "document_index.json"
        with open(index_file, "w") as f:
            json.dump(self.doc_index, f, indent=2)
    
    def add_chunks(self, chunks: List[Any], embeddings: List[List[float]], 
                   doc_name: str) -> int:
        """
        添加文本块到向量库
        
        Args:
            chunks: 文本块列表
            embeddings: 对应的向量列表
            doc_name: 文档名称
            
        Returns:
            添加的块数量
        """
        if not chunks:
            return 0
        
        # 生成 IDs
        ids = [chunk.id if hasattr(chunk, 'id') else f"chunk_{i}" for i, chunk in enumerate(chunks)]
        
        # 提取内容
        contents = [chunk.content if hasattr(chunk, 'content') else str(chunk) for chunk in chunks]
        
        # 提取元数据
        metadatas = []
        for i, chunk in enumerate(chunks):
            meta = {}
            if hasattr(chunk, 'metadata'):
                meta = chunk.metadata
            meta["doc_name"] = doc_name
            meta["chunk_id"] = ids[i]
            metadatas.append(meta)
        
        # 添加到 ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )
        
        # 更新索引
        self.doc_index[doc_name] = {
            "chunk_count": len(chunks),
            "added": True
        }
        self._save_index()
        
        return len(chunks)
    
    def search(self, query_embedding: List[float], top_k: int = 5,
               doc_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索相似内容
        
        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            doc_filter: 可选，按文档名过滤
            
        Returns:
            搜索结果列表
        """
        # 搜索参数
        where = {"doc_name": doc_filter} if doc_filter else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # 格式化结果
        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i]
                # 距离值已经按相似度排序，距离越小越相似
                # 直接使用归一化的相似度 (1 / (1 + distance))
                score = 1 / (1 + distance)
                search_results.append({
                    "content": doc,
                    "score": score,
                    "distance": distance,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                })
        
        return search_results
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """获取所有已学习的文档"""
        docs = []
        for doc_name, info in self.doc_index.items():
            docs.append({
                "name": doc_name,
                "chunk_count": info.get("chunk_count", 0),
                "added": info.get("added", False)
            })
        return docs
    
    def delete_document(self, doc_name: str) -> bool:
        """删除指定文档"""
        # ChromaDB 不支持按元数据删除，需要重建集合
        # 这里简化处理：标记为已删除
        if doc_name in self.doc_index:
            self.doc_index[doc_name]["added"] = False
            self._save_index()
            return True
        return False
    
    def clear(self):
        """清空知识库"""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "My-Digirain 知识库"}
        )
        self.doc_index = {}
        self._save_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_chunks": self.collection.count(),
            "total_documents": len([d for d in self.doc_index.values() if d.get("added", False)]),
            "collection_name": self.COLLECTION_NAME,
            "persist_path": self.persist_path
        }


def main():
    """测试向量存储"""
    print("🧪 测试向量存储...")
    
    # 初始化（使用测试目录）
    store = VectorStore(persist_path="./test_knowledge_base")
    
    print("✅ 向量存储初始化成功")
    
    # 测试统计
    stats = store.get_stats()
    print(f"   文档数: {stats['total_documents']}")
    print(f"   知识块: {stats['total_chunks']}")
    
    # 清理测试目录
    import shutil
    shutil.rmtree("./test_knowledge_base", ignore_errors=True)


if __name__ == "__main__":
    main()
