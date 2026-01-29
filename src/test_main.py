"""テスト"""
from main import hello, add

def test_hello():
    assert hello("World") == "Hello, World!"

def test_add():
    assert add(1, 2) == 3
