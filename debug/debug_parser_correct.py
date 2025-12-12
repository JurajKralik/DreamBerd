#!/usr/bin/env python3
"""
Debug parser for correct DreamBerd syntax
"""

from dreamberd_parser import parse_dreamberd
from dreamberd_lexer import DreamBerdLexer

def debug_parse(code: str):
    """Debug parsing of code."""
    print(f"Code: {repr(code)}")
    try:
        ast = parse_dreamberd(code)
        print(f"AST: {ast}")
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        
        # Let's see the tokens
        lexer = DreamBerdLexer(code)
        tokens = lexer.tokenize()
        print("Tokens:")
        for i, token in enumerate(tokens):
            print(f"  {i}: {token.type} = {repr(token.value)} at {token.line}:{token.column}")
    print()

# Test cases with proper DreamBerd syntax
debug_parse("const const const x = 42!")
debug_parse("var x = 5!")  
debug_parse("++x!")
debug_parse("print(42)!")