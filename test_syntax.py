#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
구문 검사 스크립트
"""

import sys
import os

def check_syntax():
    try:
        with open('src/intelligent_content_analyzer.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, 'src/intelligent_content_analyzer.py', 'exec')
        print('✅ 파일 컴파일 성공!')
        return True
        
    except SyntaxError as e:
        print(f'❌ 구문 오류: {e}')
        print(f'📍 줄 번호: {e.lineno}')
        print(f'📍 위치: {e.offset}')
        return False
        
    except IndentationError as e:
        print(f'❌ 들여쓰기 오류: {e}')
        print(f'📍 줄 번호: {e.lineno}')
        return False

if __name__ == "__main__":
    check_syntax() 