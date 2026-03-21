#!/usr/bin/env python3
"""
My-Digirain 环境检测和安装引导脚本

用于检测用户环境是否满足 My-Digirain 的运行条件，
并提供详细的安装引导。
"""

import sys
import os
import subprocess
import yaml
from pathlib import Path

# 项目根目录
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.yaml"


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_status(ok: bool, message: str):
    """打印状态"""
    symbol = f"{Colors.GREEN}✓{Colors.END}" if ok else f"{Colors.RED}✗{Colors.END}"
    print(f"  {symbol} {message}")
    return ok


def check_python_version():
    """检查 Python 版本"""
    print(f"\n{Colors.BOLD}[1/5] 检查 Python 版本...{Colors.END}")
    version = sys.version_info
    ok = version.major >= 3 and (version.minor >= 8)
    print_status(ok, f"Python {version.major}.{version.minor}.{version.micro}")
    if not ok:
        print(f"  {Colors.RED}需要 Python 3.8 或更高版本{Colors.END}")
    return ok


def check_ollama():
    """检查 Ollama 是否安装"""
    print(f"\n{Colors.BOLD}[2/5] 检查 Ollama...{Colors.END}")
    
    # 检查 ollama 命令是否可用
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print_status(True, f"Ollama 已安装: {result.stdout.strip()}")
        
        # 检查 ollama 是否在运行
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # 检查 bge-m3 是否已安装
            if "bge-m3" in result.stdout:
                print_status(True, "BGE-M3 模型已安装")
                return True
            else:
                print_status(False, "BGE-M3 模型未安装")
                print(f"\n  {Colors.YELLOW}请运行以下命令安装模型：{Colors.END}")
                print(f"  {Colors.BLUE}ollama pull bge-m3{Colors.END}")
                return False
        except subprocess.TimeoutExpired:
            print_status(False, "Ollama 服务未运行")
            print(f"\n  {Colors.YELLOW}请运行以下命令启动：{Colors.END}")
            print(f"  {Colors.BLUE}ollama serve{Colors.END}")
            return False
            
    except FileNotFoundError:
        print_status(False, "Ollama 未安装")
        print(f"\n  {Colors.YELLOW}安装方法：{Colors.END}")
        print(f"  {Colors.BLUE}macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh{Colors.END}")
        print(f"  {Colors.BLUE}Windows: 下载 https://ollama.com/download/windows{Colors.END}")
        return False


def check_chromadb():
    """检查 ChromaDB 是否安装"""
    print(f"\n{Colors.BOLD}[3/5] 检查 ChromaDB...{Colors.END}")
    
    try:
        import chromadb
        version = chromadb.__version__
        print_status(True, f"ChromaDB {version} 已安装")
        return True
    except ImportError:
        print_status(False, "ChromaDB 未安装")
        print(f"\n  {Colors.YELLOW}请运行以下命令安装：{Colors.END}")
        print(f"  {Colors.BLUE}pip install chromadb{Colors.END}")
        return False


def check_dependencies():
    """检查其他依赖"""
    print(f"\n{Colors.BOLD}[4/5] 检查其他依赖...{Colors.END}")
    
    deps = {
        "pypdf": "pypdf",
        "yaml": "pyyaml", 
        "requests": "requests",
    }
    
    all_ok = True
    for name, import_name in deps.items():
        try:
            __import__(import_name)
            print_status(True, f"{name} 已安装")
        except ImportError:
            print_status(False, f"{name} 未安装")
            all_ok = False
    
    return all_ok


def check_knowledge_base():
    """检查知识库目录"""
    print(f"\n{Colors.BOLD}[5/5] 检查知识库目录...{Colors.END}")
    
    kb_path = SCRIPT_DIR / "knowledge_base"
    chroma_path = kb_path / "chroma_db"
    
    # 创建目录（如果不存在）
    chroma_path.mkdir(parents=True, exist_ok=True)
    print_status(True, f"知识库目录: {chroma_path}")
    
    return True


def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{'='*50}")
    print("🔍 My-Digirain 环境检测")
    print(f"{'='*50}{Colors.END}")
    
    results = {
        "Python": check_python_version(),
        "Ollama": check_ollama(),
        "ChromaDB": check_chromadb(),
        "依赖": check_dependencies(),
        "知识库": check_knowledge_base(),
    }
    
    print(f"\n{Colors.BOLD}{'='*50}")
    print("📊 检测结果")
    print(f"{'='*50}{Colors.END}")
    
    all_ok = all(results.values())
    
    if all_ok:
        print(f"\n{Colors.GREEN}✅ 所有检查通过！My-Digirain 已准备就绪。{Colors.END}")
        print(f"\n{Colors.BOLD}开始使用：{Colors.END}")
        print(f"  1. 打开 OpenClaw")
        print(f"  2. 上传一个文档文件")
        print(f"  3. 对我说：'学习这个文档'")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  环境检测未通过，请按照上述提示安装缺失的组件。{Colors.END}")
        print(f"\n{Colors.YELLOW}安装所有依赖的命令：{Colors.END}")
        print(f"  {Colors.BLUE}pip install -r requirements.txt{Colors.END}")
        print(f"\n{Colors.YELLOW}安装 Ollama 和模型：{Colors.END}")
        print(f"  {Colors.BLUE}curl -fsSL https://ollama.com/install.sh | sh{Colors.END}")
        print(f"  {Colors.BLUE}ollama pull bge-m3{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
