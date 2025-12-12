"""
DreamBerd/Gulf of Mexico Parser
Parses DreamBerd tokens into an Abstract Syntax Tree.
"""

from typing import List, Optional, Union, Any
from dreamberd_lexer import Token, TokenType, DreamBerdLexer
from dreamberd_ast import *


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"Parse error at line {token.line}, column {token.column}: {message}")


class DreamBerdParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None
    
    def advance(self):
        """Move to the next token."""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = self.tokens[-1]  # EOF token
    
    def peek(self, offset: int = 1) -> Optional[Token]:
        """Look ahead at the next token without consuming it."""
        pos = self.pos + offset
        if 0 <= pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current_token and self.current_token.type in token_types
    
    def consume(self, token_type: TokenType, message: str = "") -> Token:
        """Consume a token of the expected type or raise an error."""
        if not self.current_token or self.current_token.type != token_type:
            error_msg = message or f"Expected {token_type}, got {self.current_token.type if self.current_token else 'EOF'}"
            raise ParseError(error_msg, self.current_token or Token(TokenType.EOF, "", 0, 0))
        
        token = self.current_token
        self.advance()
        return token
    
    def skip_newlines(self):
        """Skip newline tokens."""
        while self.match(TokenType.NEWLINE):
            self.advance()
    
    def parse(self) -> Program:
        """Parse the tokens into a Program AST node."""
        statements = []
        
        while not self.match(TokenType.EOF):
            self.skip_newlines()
            
            if self.match(TokenType.EOF):
                break
                
            # Check for file separator
            if self.match(TokenType.FILE_SEPARATOR):
                self.advance()
                # Look for optional file name
                file_name = None
                if self.match(TokenType.IDENTIFIER):
                    file_name = self.current_token.value
                    self.advance()
                
                # Parse file body until next separator or EOF
                file_body = []
                while not self.match(TokenType.FILE_SEPARATOR, TokenType.EOF):
                    self.skip_newlines()
                    if not self.match(TokenType.FILE_SEPARATOR, TokenType.EOF):
                        stmt = self.parse_statement()
                        if stmt:
                            file_body.append(stmt)
                
                statements.append(FileBlock(file_name, file_body))
            else:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
        
        return Program(statements)
    
    def parse_statement(self) -> Optional[Statement]:
        """Parse a statement."""
        self.skip_newlines()
        
        if self.match(TokenType.EOF):
            return None
        
        # Variable declarations (const/var combinations and const const const)
        if self.match(TokenType.CONST, TokenType.VAR, TokenType.CONST_CONST_CONST):
            return self.parse_variable_declaration()
        
        # Function declarations
        if self.match(TokenType.FUNCTION, TokenType.FUNC, TokenType.FUN, 
                     TokenType.FN, TokenType.FUNCTI, TokenType.F, TokenType.UNION):
            return self.parse_function_declaration()
        
        # Async function declarations
        if self.match(TokenType.ASYNC):
            self.advance()
            if self.match(TokenType.FUNCTION, TokenType.FUNC, TokenType.FUN, 
                         TokenType.FN, TokenType.FUNCTI, TokenType.F, TokenType.UNION):
                func_decl = self.parse_function_declaration()
                func_decl.is_async = True
                return func_decl
        
        # Class declarations
        if self.match(TokenType.CLASS, TokenType.CLASSNAME):
            return self.parse_class_declaration()
        
        # Control flow
        if self.match(TokenType.IF):
            return self.parse_if_statement()
        
        if self.match(TokenType.WHEN):
            return self.parse_when_statement()
        
        if self.match(TokenType.RETURN):
            return self.parse_return_statement()
        
        # Special statements
        if self.match(TokenType.DELETE):
            return self.parse_delete_statement()
        
        if self.match(TokenType.IMPORT):
            return self.parse_import_statement()
        
        if self.match(TokenType.EXPORT):
            return self.parse_export_statement()
        
        if self.match(TokenType.REVERSE):
            self.advance()
            self.consume_statement_terminator()
            return ReverseStatement()
        
        # Noop statement (any string used as a statement)
        if self.match(TokenType.STRING):
            content = self.current_token.value
            self.advance()
            self.consume_statement_terminator()
            return NoopStatement(content)
        
        # Expression statement
        expr = self.parse_expression()
        priority, is_debug = self.consume_statement_terminator()
        return ExpressionStatement(expr, priority, is_debug)
    
    def consume_statement_terminator(self) -> tuple[int, bool]:
        """Consume statement terminator (! or ?) and return priority and debug flag."""
        priority = 0
        is_debug = False
        
        if self.match(TokenType.EXCLAMATION):
            priority = self.current_token.priority
            self.advance()
        elif self.match(TokenType.INVERTED_EXCLAMATION):
            priority = self.current_token.priority
            self.advance()
        elif self.match(TokenType.QUESTION):
            is_debug = True
            self.advance()
            # Handle multiple question marks
            while self.match(TokenType.QUESTION):
                self.advance()
        
        return priority, is_debug
    
    def parse_variable_declaration(self) -> Union[VariableDeclaration, GlobalConstantDeclaration]:
        """Parse variable declaration with const/var combinations."""
        # Special case: const const const (global immutable)
        if self.match(TokenType.CONST_CONST_CONST):
            self.advance()
            name_token = self.consume(TokenType.IDENTIFIER, "Expected variable name")
            name = name_token.value
            
            self.consume(TokenType.ASSIGN, "Expected '=' in const const const declaration")
            value = self.parse_expression()
            
            priority, _ = self.consume_statement_terminator()
            return GlobalConstantDeclaration(name, value, priority)
        
        const_count = 0
        var_count = 0
        
        # Count const and var keywords
        while self.match(TokenType.CONST, TokenType.VAR):
            if self.match(TokenType.CONST):
                const_count += 1
            else:
                var_count += 1
            self.advance()
        
        # Variable name
        name_token = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        name = name_token.value
        
        # Optional lifetime annotation
        lifetime = None
        if self.match(TokenType.LESS_THAN):
            self.advance()
            lifetime_token = self.consume(TokenType.IDENTIFIER, "Expected lifetime")
            lifetime = lifetime_token.value
            self.consume(TokenType.GREATER_THAN, "Expected '>' after lifetime")
        
        # Optional type annotation
        type_annotation = None
        if self.match(TokenType.COLON):
            self.advance()
            type_token = self.consume(TokenType.IDENTIFIER, "Expected type name")
            type_annotation = type_token.value
        
        # Assignment
        value = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            value = self.parse_expression()
        
        priority, _ = self.consume_statement_terminator()
        
        return VariableDeclaration(const_count, var_count, name, value, lifetime, priority, type_annotation)
    
    def parse_function_declaration(self) -> FunctionDeclaration:
        """Parse function declaration."""
        keyword = self.current_token.value
        self.advance()
        
        # Function name
        name_token = self.consume(TokenType.IDENTIFIER, "Expected function name")
        name = name_token.value
        
        # Parameters
        parameters = []
        if self.match(TokenType.LPAREN):
            self.advance()
            
            while not self.match(TokenType.RPAREN):
                if parameters:  # Not first parameter
                    self.consume(TokenType.COMMA, "Expected ',' between parameters")
                
                param_token = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
                parameters.append(param_token.value)
            
            self.consume(TokenType.RPAREN, "Expected ')' after parameters")
        
        # Arrow for function body
        self.consume(TokenType.ARROW, "Expected '=>' after function signature")
        
        # Function body - can be expression or block
        if self.match(TokenType.LBRACE):
            # Block body
            self.advance()
            body = []
            
            while not self.match(TokenType.RBRACE):
                self.skip_newlines()
                if self.match(TokenType.RBRACE):
                    break
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
            
            self.consume(TokenType.RBRACE, "Expected '}' after function body")
        else:
            # Expression body
            body = self.parse_expression()
        
        self.consume_statement_terminator()
        
        return FunctionDeclaration(keyword, name, parameters, body)
    
    def parse_class_declaration(self) -> ClassDeclaration:
        """Parse class declaration."""
        keyword = self.current_token.value
        self.advance()
        
        # Class name
        name_token = self.consume(TokenType.IDENTIFIER, "Expected class name")
        name = name_token.value
        
        # Class body
        self.consume(TokenType.LBRACE, "Expected '{' after class name")
        
        body = []
        while not self.match(TokenType.RBRACE):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.consume(TokenType.RBRACE, "Expected '}' after class body")
        
        return ClassDeclaration(keyword, name, body)
    
    def parse_if_statement(self) -> IfStatement:
        """Parse if statement."""
        self.advance()  # consume 'if'
        
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after if condition")
        
        self.consume(TokenType.LBRACE, "Expected '{' after if condition")
        
        then_body = []
        while not self.match(TokenType.RBRACE):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            stmt = self.parse_statement()
            if stmt:
                then_body.append(stmt)
        
        self.consume(TokenType.RBRACE, "Expected '}' after if body")
        
        # Optional else clause
        else_body = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.consume(TokenType.LBRACE, "Expected '{' after 'else'")
            
            else_body = []
            while not self.match(TokenType.RBRACE):
                self.skip_newlines()
                if self.match(TokenType.RBRACE):
                    break
                stmt = self.parse_statement()
                if stmt:
                    else_body.append(stmt)
            
            self.consume(TokenType.RBRACE, "Expected '}' after else body")
        
        return IfStatement(condition, then_body, else_body)
    
    def parse_when_statement(self) -> WhenStatement:
        """Parse when statement."""
        self.advance()  # consume 'when'
        
        self.consume(TokenType.LPAREN, "Expected '(' after 'when'")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after when condition")
        
        self.consume(TokenType.LBRACE, "Expected '{' after when condition")
        
        body = []
        while not self.match(TokenType.RBRACE):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.consume(TokenType.RBRACE, "Expected '}' after when body")
        
        return WhenStatement(condition, body)
    
    def parse_return_statement(self) -> ReturnStatement:
        """Parse return statement."""
        self.advance()  # consume 'return'
        
        value = None
        if not self.match(TokenType.EXCLAMATION, TokenType.QUESTION, TokenType.NEWLINE, TokenType.EOF):
            value = self.parse_expression()
        
        self.consume_statement_terminator()
        return ReturnStatement(value)
    
    def parse_delete_statement(self) -> DeleteStatement:
        """Parse delete statement."""
        self.advance()  # consume 'delete'
        
        target = self.parse_expression()
        self.consume_statement_terminator()
        
        return DeleteStatement(target)
    
    def parse_import_statement(self) -> ImportStatement:
        """Parse import statement."""
        self.advance()  # consume 'import'
        
        name_token = self.consume(TokenType.IDENTIFIER, "Expected import name")
        name = name_token.value
        
        self.consume_statement_terminator()
        return ImportStatement(name)
    
    def parse_export_statement(self) -> ExportStatement:
        """Parse export statement."""
        self.advance()  # consume 'export'
        
        name_token = self.consume(TokenType.IDENTIFIER, "Expected export name")
        name = name_token.value
        
        self.consume(TokenType.TO, "Expected 'to' after export name")
        
        target_token = self.consume(TokenType.STRING, "Expected target file name")
        target_file = target_token.value
        
        self.consume_statement_terminator()
        return ExportStatement(name, target_file)
    
    def parse_expression(self) -> Expression:
        """Parse expression with operator precedence."""
        return self.parse_assignment()
    
    def parse_assignment(self) -> Expression:
        """Parse assignment expressions."""
        expr = self.parse_or()
        
        # Only treat single = as assignment in specific contexts (variable declarations, etc.)
        # In expressions, single = is very loose equality
        return expr
    
    def parse_or(self) -> Expression:
        """Parse logical OR expressions."""
        expr = self.parse_and()
        
        while self.match(TokenType.OR):
            operator = self.current_token.value
            self.advance()
            right = self.parse_and()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def parse_and(self) -> Expression:
        """Parse logical AND expressions."""
        expr = self.parse_equality()
        
        while self.match(TokenType.AND):
            operator = self.current_token.value
            self.advance()
            right = self.parse_equality()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def parse_equality(self) -> Expression:
        """Parse equality expressions."""
        expr = self.parse_comparison()
        
        while self.match(TokenType.ASSIGN, TokenType.LOOSE_EQUAL, TokenType.STRICT_EQUAL, 
                        TokenType.SUPER_STRICT_EQUAL, TokenType.VERY_LOOSE_EQUAL,
                        TokenType.NOT_EQUAL):
            operator = self.current_token.value
            self.advance()
            right = self.parse_comparison()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def parse_comparison(self) -> Expression:
        """Parse comparison expressions."""
        expr = self.parse_addition()
        
        while self.match(TokenType.LESS_THAN, TokenType.GREATER_THAN,
                        TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            operator = self.current_token.value
            self.advance()
            right = self.parse_addition()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def parse_addition(self) -> Expression:
        """Parse addition and subtraction with spacing precedence."""
        expr = self.parse_multiplication()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.current_token.value
            self.advance()
            right = self.parse_multiplication()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def parse_multiplication(self) -> Expression:
        """Parse multiplication, division, and modulo."""
        expr = self.parse_power()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            operator = self.current_token.value
            self.advance()
            right = self.parse_power()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def parse_power(self) -> Expression:
        """Parse power expressions."""
        expr = self.parse_unary()
        
        while self.match(TokenType.POWER):
            operator = self.current_token.value
            self.advance()
            right = self.parse_unary()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def parse_unary(self) -> Expression:
        """Parse unary expressions."""
        if self.match(TokenType.NOT, TokenType.MINUS, TokenType.PLUS):
            operator = self.current_token.value
            self.advance()
            operand = self.parse_unary()
            return UnaryOperation(operator, operand)
        
        # Temporal operators
        if self.match(TokenType.PREVIOUS):
            self.advance()
            target = self.parse_unary()
            return PreviousExpression(target)
        
        if self.match(TokenType.NEXT):
            self.advance()
            target = self.parse_unary()
            return NextExpression(target)
        
        if self.match(TokenType.CURRENT):
            self.advance()
            target = self.parse_unary()
            return CurrentExpression(target)
        
        if self.match(TokenType.AWAIT):
            self.advance()
            expr = self.parse_unary()
            return AwaitExpression(expr)
        
        return self.parse_postfix()
    
    def parse_postfix(self) -> Expression:
        """Parse postfix expressions (member access, array access, function calls)."""
        expr = self.parse_primary()
        
        while True:
            if self.match(TokenType.DOT):
                self.advance()
                prop_token = self.consume(TokenType.IDENTIFIER, "Expected property name after '.'")
                expr = MemberAccess(expr, prop_token.value)
            
            elif self.match(TokenType.LBRACKET):
                self.advance()
                index = self.parse_expression()
                self.consume(TokenType.RBRACKET, "Expected ']' after array index")
                expr = ArrayAccess(expr, index)
            
            elif self.match(TokenType.LPAREN):
                # Function call
                self.advance()
                
                arguments = []
                while not self.match(TokenType.RPAREN):
                    if arguments:  # Not first argument
                        self.consume(TokenType.COMMA, "Expected ',' between arguments")
                    
                    arguments.append(self.parse_expression())
                
                self.consume(TokenType.RPAREN, "Expected ')' after function arguments")
                expr = FunctionCall(expr, arguments)
            
            else:
                break
        
        return expr
    
    def parse_primary(self) -> Expression:
        """Parse primary expressions."""
        # Numbers
        if self.match(TokenType.NUMBER):
            value = self.current_token.value
            self.advance()
            
            # Handle fractions
            if '/' in value:
                return NumberLiteral(value)  # Keep as string for evaluation
            
            # Try to convert to int or float
            try:
                if '.' in value:
                    return NumberLiteral(float(value))
                else:
                    return NumberLiteral(int(value))
            except ValueError:
                return NumberLiteral(value)  # Keep as string if conversion fails
        
        # Strings
        if self.match(TokenType.STRING):
            value = self.current_token.value
            self.advance()
            return StringLiteral(value)
        
        # Booleans
        if self.match(TokenType.BOOLEAN):
            value = self.current_token.value.lower() in ('true', 'True')
            self.advance()
            return BooleanLiteral(value)
        
        # Maybe
        if self.match(TokenType.MAYBE):
            self.advance()
            return MaybeLiteral()
        
        # Identifiers
        if self.match(TokenType.IDENTIFIER):
            name = self.current_token.value
            self.advance()
            
            # Special literals
            if name == 'undefined':
                return UndefinedLiteral()
            elif name == 'null':
                return NullLiteral()
            
            return Identifier(name)
        
        # Arrays
        if self.match(TokenType.LBRACKET):
            self.advance()
            
            elements = []
            while not self.match(TokenType.RBRACKET):
                if elements:  # Not first element
                    self.consume(TokenType.COMMA, "Expected ',' between array elements")
                
                elements.append(self.parse_expression())
            
            self.consume(TokenType.RBRACKET, "Expected ']' after array elements")
            return ArrayLiteral(elements)
        
        # Parentheses (remember: they do nothing in DreamBerd!)
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        
        # Use expression (signals)
        if self.match(TokenType.USE):
            self.advance()
            self.consume(TokenType.LPAREN, "Expected '(' after 'use'")
            initial_value = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after use argument")
            return UseExpression(initial_value)
        
        # New expression
        if self.match(TokenType.NEW):
            self.advance()
            class_name_token = self.consume(TokenType.IDENTIFIER, "Expected class name after 'new'")
            
            self.consume(TokenType.LPAREN, "Expected '(' after class name")
            
            arguments = []
            while not self.match(TokenType.RPAREN):
                if arguments:
                    self.consume(TokenType.COMMA, "Expected ',' between arguments")
                arguments.append(self.parse_expression())
            
            self.consume(TokenType.RPAREN, "Expected ')' after new arguments")
            
            return NewExpression(class_name_token.value, arguments)
        
        # Print is handled as a regular identifier/function
        if self.match(TokenType.PRINT):
            self.advance()
            return Identifier('print')
        
        # Prefix increment
        if self.match(TokenType.INCREMENT):
            self.advance()
            target = self.parse_primary()
            return IncrementExpression(target, is_prefix=True)
        
        # Prefix decrement
        if self.match(TokenType.DECREMENT):
            self.advance()
            target = self.parse_primary()
            return DecrementExpression(target, is_prefix=True)
        
        raise ParseError(f"Unexpected token {self.current_token.type}", self.current_token)


def parse_dreamberd(source: str) -> Program:
    """Parse DreamBerd source code into an AST."""
    lexer = DreamBerdLexer(source)
    tokens = lexer.tokenize()
    
    parser = DreamBerdParser(tokens)
    return parser.parse()