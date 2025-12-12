"""
DreamBerd/Gulf of Mexico Lexer
Tokenizes DreamBerd source code into tokens for parsing.
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Iterator


class TokenType(Enum):
    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    MAYBE = "MAYBE"
    
    # Identifiers and names
    IDENTIFIER = "IDENTIFIER"
    
    # Keywords
    CONST = "CONST"
    CONST_CONST_CONST = "CONST_CONST_CONST"  # const const const for global immutable data
    VAR = "VAR"
    FUNCTION = "FUNCTION"
    FUNC = "FUNC"
    FUN = "FUN"
    FN = "FN"
    FUNCTI = "FUNCTI"
    F = "F"
    UNION = "UNION"  # Also a valid function declaration
    CLASS = "CLASS"
    CLASSNAME = "CLASSNAME"
    IF = "IF"
    ELSE = "ELSE"
    WHEN = "WHEN"
    RETURN = "RETURN"
    PRINT = "PRINT"
    DELETE = "DELETE"
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    TO = "TO"
    REVERSE = "REVERSE"
    PREVIOUS = "PREVIOUS"
    NEXT = "NEXT"
    CURRENT = "CURRENT"
    ASYNC = "ASYNC"
    NOOP = "NOOP"
    USE = "USE"
    NEW = "NEW"
    AWAIT = "AWAIT"
    
    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    POWER = "POWER"
    MODULO = "MODULO"
    INCREMENT = "INCREMENT"  # ++
    DECREMENT = "DECREMENT"  # --
    
    # Comparison operators
    ASSIGN = "ASSIGN"           # =
    LOOSE_EQUAL = "LOOSE_EQUAL" # ==
    STRICT_EQUAL = "STRICT_EQUAL" # ===
    SUPER_STRICT_EQUAL = "SUPER_STRICT_EQUAL" # ====
    VERY_LOOSE_EQUAL = "VERY_LOOSE_EQUAL" # =
    NOT_EQUAL = "NOT_EQUAL"     # !=
    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_EQUAL = "GREATER_EQUAL"
    
    # Logical operators  
    AND = "AND"
    OR = "OR"
    NOT = "NOT"  # semicolon in DreamBerd
    
    # Punctuation
    SEMICOLON = "SEMICOLON"
    COMMA = "COMMA"
    DOT = "DOT"
    COLON = "COLON"
    ARROW = "ARROW"  # =>
    
    # Brackets
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    ANGLE_LEFT = "ANGLE_LEFT"
    ANGLE_RIGHT = "ANGLE_RIGHT"
    
    # Exclamation marks and priority
    EXCLAMATION = "EXCLAMATION"
    INVERTED_EXCLAMATION = "INVERTED_EXCLAMATION"  # ¡
    QUESTION = "QUESTION"
    
    # Special
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    EOF = "EOF"
    
    # String interpolation
    DOLLAR = "DOLLAR"
    POUND = "POUND"
    YEN = "YEN"
    EURO = "EURO"
    
    # File structure
    FILE_SEPARATOR = "FILE_SEPARATOR"  # ======


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    priority: int = 0  # For exclamation mark priority


class DreamBerdLexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        
        # Keywords mapping
        self.keywords = {
            'const': TokenType.CONST,
            'var': TokenType.VAR,
            'function': TokenType.FUNCTION,
            'func': TokenType.FUNC,
            'fun': TokenType.FUN,
            'fn': TokenType.FN,
            'functi': TokenType.FUNCTI,
            'f': TokenType.F,
            'union': TokenType.UNION,
            'class': TokenType.CLASS,
            'className': TokenType.CLASSNAME,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'when': TokenType.WHEN,
            'return': TokenType.RETURN,
            'print': TokenType.PRINT,
            'delete': TokenType.DELETE,
            'import': TokenType.IMPORT,
            'export': TokenType.EXPORT,
            'to': TokenType.TO,
            'reverse': TokenType.REVERSE,
            'previous': TokenType.PREVIOUS,
            'next': TokenType.NEXT,
            'current': TokenType.CURRENT,
            'async': TokenType.ASYNC,
            'noop': TokenType.NOOP,
            'use': TokenType.USE,
            'new': TokenType.NEW,
            'await': TokenType.AWAIT,
            'true': TokenType.BOOLEAN,
            'false': TokenType.BOOLEAN,
            'maybe': TokenType.MAYBE,
            'True': TokenType.BOOLEAN,
            'False': TokenType.BOOLEAN,
            'undefined': TokenType.IDENTIFIER,  # Special value
            'null': TokenType.IDENTIFIER,      # Special value
        }
        
    def current_char(self) -> Optional[str]:
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self):
        if self.pos < len(self.source) and self.source[self.pos] == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1
    
    def skip_whitespace(self):
        while self.current_char() and self.current_char() in ' \t':
            self.advance()
    
    def read_number(self) -> Token:
        start_line, start_column = self.line, self.column
        value = ""
        
        # Handle number names like "one", "two", etc.
        number_names = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12'
        }
        
        # Check if this might be a word number
        word = ""
        temp_pos = self.pos
        while temp_pos < len(self.source) and self.source[temp_pos].isalpha():
            word += self.source[temp_pos]
            temp_pos += 1
        
        if word.lower() in number_names:
            value = number_names[word.lower()]
            while self.current_char() and self.current_char().isalpha():
                self.advance()
            return Token(TokenType.NUMBER, value, start_line, start_column)
        
        # Regular number parsing
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            value += self.current_char()
            self.advance()
        
        # Handle fractions
        if self.current_char() == '/' and self.peek_char() and self.peek_char().isdigit():
            value += self.current_char()
            self.advance()
            while self.current_char() and self.current_char().isdigit():
                value += self.current_char()
                self.advance()
        
        return Token(TokenType.NUMBER, value, start_line, start_column)
    
    def read_string(self, quote_char: str) -> Token:
        start_line, start_column = self.line, self.column
        value = ""
        quote_count = 1
        
        # Count consecutive quotes
        self.advance()  # Skip first quote
        while self.current_char() == quote_char:
            quote_count += 1
            self.advance()
        
        # Handle bare strings (no quotes - this is actually for identifiers)
        if quote_count == 1:
            # This is just a single quote, continue with regular string parsing
            pass
        
        # Regular string with quotes
        while self.current_char():
            if self.current_char() == quote_char:
                # Check if we have enough closing quotes
                closing_quotes = 0
                temp_pos = self.pos
                while (temp_pos < len(self.source) and 
                       self.source[temp_pos] == quote_char):
                    closing_quotes += 1
                    temp_pos += 1
                
                if closing_quotes >= quote_count:
                    # Skip the closing quotes
                    for _ in range(quote_count):
                        self.advance()
                    break
                else:
                    value += self.current_char()
                    self.advance()
            else:
                value += self.current_char()
                self.advance()
        
        return Token(TokenType.STRING, value, start_line, start_column)
    
    def read_identifier(self) -> Token:
        start_line, start_column = self.line, self.column
        value = ""
        
        # DreamBerd allows any Unicode character as identifier
        while (self.current_char() and 
               (self.current_char().isalnum() or 
                self.current_char() in '_$👍🎯1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣0️⃣')):
            value += self.current_char()
            self.advance()
        
        # Special handling for "const const const"
        if value.lower() == 'const':
            # Check if followed by another "const"
            saved_pos = self.pos
            saved_line = self.line
            saved_column = self.column
            
            # Skip whitespace
            while self.current_char() and self.current_char() in ' \t':
                self.advance()
            
            # Check for second "const"
            if self.current_char() and self.current_char().isalpha():
                next_word = ""
                temp_pos = self.pos
                while (temp_pos < len(self.source) and 
                       self.source[temp_pos].isalpha()):
                    next_word += self.source[temp_pos]
                    temp_pos += 1
                
                if next_word.lower() == 'const':
                    # Consume second "const"
                    for _ in range(len(next_word)):
                        self.advance()
                    
                    # Skip whitespace again
                    while self.current_char() and self.current_char() in ' \t':
                        self.advance()
                    
                    # Check for third "const"
                    if self.current_char() and self.current_char().isalpha():
                        third_word = ""
                        temp_pos = self.pos
                        while (temp_pos < len(self.source) and 
                               self.source[temp_pos].isalpha()):
                            third_word += self.source[temp_pos]
                            temp_pos += 1
                        
                        if third_word.lower() == 'const':
                            # Consume third "const"
                            for _ in range(len(third_word)):
                                self.advance()
                            return Token(TokenType.CONST_CONST_CONST, 'const const const', start_line, start_column)
            
            # Restore position if not const const const
            self.pos = saved_pos
            self.line = saved_line
            self.column = saved_column
        
        # Check if it's a keyword
        token_type = self.keywords.get(value.lower(), TokenType.IDENTIFIER)
        return Token(token_type, value, start_line, start_column)
    
    def read_exclamation_marks(self) -> Token:
        start_line, start_column = self.line, self.column
        count = 0
        
        while self.current_char() == '!':
            count += 1
            self.advance()
        
        return Token(TokenType.EXCLAMATION, '!' * count, start_line, start_column, priority=count)
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if not self.current_char():
                break
            
            char = self.current_char()
            start_line, start_column = self.line, self.column
            
            # Newlines
            if char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, char, start_line, start_column))
                self.advance()
            
            # Comments (// style)
            elif char == '/' and self.peek_char() == '/':
                while self.current_char() and self.current_char() != '\n':
                    self.advance()
            
            # Numbers
            elif char.isdigit():
                self.tokens.append(self.read_number())
            
            # Strings
            elif char in '"\'':
                self.tokens.append(self.read_string(char))
            
            # Identifiers and number names
            elif char.isalpha():
                self.tokens.append(self.read_identifier())
            
            # Arrow => (check before equals)
            elif char == '=' and self.peek_char() == '>':
                self.advance()  # =
                self.advance()  # >
                self.tokens.append(Token(TokenType.ARROW, '=>', start_line, start_column))
            
            # File separator (5+ equals)
            elif char == '=':
                equals_count = 0
                temp_pos = self.pos
                while temp_pos < len(self.source) and self.source[temp_pos] == '=':
                    equals_count += 1
                    temp_pos += 1
                
                if equals_count >= 5:
                    # This is a file separator
                    value = '=' * equals_count
                    for _ in range(equals_count):
                        self.advance()
                    self.tokens.append(Token(TokenType.FILE_SEPARATOR, value, start_line, start_column))
                elif equals_count == 4:
                    # ====
                    for _ in range(4):
                        self.advance()
                    self.tokens.append(Token(TokenType.SUPER_STRICT_EQUAL, '====', start_line, start_column))
                elif equals_count == 3:
                    # ===
                    for _ in range(3):
                        self.advance()
                    self.tokens.append(Token(TokenType.STRICT_EQUAL, '===', start_line, start_column))
                elif equals_count == 2:
                    # ==
                    for _ in range(2):
                        self.advance()
                    self.tokens.append(Token(TokenType.LOOSE_EQUAL, '==', start_line, start_column))
                else:
                    # Single =
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '=', start_line, start_column))
            
            # Exclamation marks
            elif char == '!':
                self.tokens.append(self.read_exclamation_marks())
            
            # Inverted exclamation
            elif char == '¡':
                self.tokens.append(Token(TokenType.INVERTED_EXCLAMATION, char, start_line, start_column, priority=-1))
                self.advance()
            
            # Question mark
            elif char == '?':
                self.tokens.append(Token(TokenType.QUESTION, char, start_line, start_column))
                self.advance()
            
            # Semicolon (NOT operator in DreamBerd)
            elif char == ';':
                self.tokens.append(Token(TokenType.NOT, char, start_line, start_column))
                self.advance()
            
            # Single character tokens
            elif char == '+':
                if self.peek_char() == '+':
                    self.advance()  # first +
                    self.advance()  # second +
                    self.tokens.append(Token(TokenType.INCREMENT, '++', start_line, start_column))
                else:
                    self.tokens.append(Token(TokenType.PLUS, char, start_line, start_column))
                    self.advance()
            elif char == '-':
                if self.peek_char() == '-':
                    self.advance()  # first -
                    self.advance()  # second -
                    self.tokens.append(Token(TokenType.DECREMENT, '--', start_line, start_column))
                else:
                    self.tokens.append(Token(TokenType.MINUS, char, start_line, start_column))
                    self.advance()
            elif char == '*':
                self.tokens.append(Token(TokenType.MULTIPLY, char, start_line, start_column))
                self.advance()
            elif char == '/':
                self.tokens.append(Token(TokenType.DIVIDE, char, start_line, start_column))
                self.advance()
            elif char == '^':
                self.tokens.append(Token(TokenType.POWER, char, start_line, start_column))
                self.advance()
            elif char == '%':
                self.tokens.append(Token(TokenType.MODULO, char, start_line, start_column))
                self.advance()
            elif char == '<':
                if self.peek_char() == '=':
                    self.advance()
                    self.advance()
                    self.tokens.append(Token(TokenType.LESS_EQUAL, '<=', start_line, start_column))
                else:
                    self.tokens.append(Token(TokenType.LESS_THAN, char, start_line, start_column))
                    self.advance()
            elif char == '>':
                if self.peek_char() == '=':
                    self.advance()
                    self.advance()
                    self.tokens.append(Token(TokenType.GREATER_EQUAL, '>=', start_line, start_column))
                else:
                    self.tokens.append(Token(TokenType.GREATER_THAN, char, start_line, start_column))
                    self.advance()
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, char, start_line, start_column))
                self.advance()
            elif char == '.':
                self.tokens.append(Token(TokenType.DOT, char, start_line, start_column))
                self.advance()
            elif char == ':':
                self.tokens.append(Token(TokenType.COLON, char, start_line, start_column))
                self.advance()
            elif char == '(':
                self.tokens.append(Token(TokenType.LPAREN, char, start_line, start_column))
                self.advance()
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, char, start_line, start_column))
                self.advance()
            elif char == '{':
                self.tokens.append(Token(TokenType.LBRACE, char, start_line, start_column))
                self.advance()
            elif char == '}':
                self.tokens.append(Token(TokenType.RBRACE, char, start_line, start_column))
                self.advance()
            elif char == '[':
                self.tokens.append(Token(TokenType.LBRACKET, char, start_line, start_column))
                self.advance()
            elif char == ']':
                self.tokens.append(Token(TokenType.RBRACKET, char, start_line, start_column))
                self.advance()
            
            # String interpolation currency symbols
            elif char == '$':
                self.tokens.append(Token(TokenType.DOLLAR, char, start_line, start_column))
                self.advance()
            elif char == '£':
                self.tokens.append(Token(TokenType.POUND, char, start_line, start_column))
                self.advance()
            elif char == '¥':
                self.tokens.append(Token(TokenType.YEN, char, start_line, start_column))
                self.advance()
            elif char == '€':
                self.tokens.append(Token(TokenType.EURO, char, start_line, start_column))
                self.advance()
            
            else:
                # Unknown character, skip it
                self.advance()
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens