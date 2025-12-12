#!/usr/bin/env python3
"""
Debug script to check token generation
"""

from dreamberd_lexer import DreamBerdLexer

def debug_tokens(code: str):
    """Debug what tokens are generated for code."""
    print(f"Code: {repr(code)}")
    print("Tokens:")
    lexer = DreamBerdLexer(code)
    tokens = lexer.tokenize()
    for i, token in enumerate(tokens):
        print(f"  {i}: {token.type} = {repr(token.value)} at {token.line}:{token.column}")
    print()

# Test cases
debug_tokens("const const const x = 42")
debug_tokens("var x = 5")  
debug_tokens("++x")
debug_tokens("--y")