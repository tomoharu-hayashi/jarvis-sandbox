"""
JARVIS E2E テスト用のダミーアプリケーション
"""

def hello(name: str) -> str:
    """挨拶を返す"""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """2つの数値を足す"""
    return a + b

if __name__ == "__main__":
    print(hello("JARVIS"))
