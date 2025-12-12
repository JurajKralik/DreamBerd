"""
DreamBerd/Gulf of Mexico AST Nodes
Abstract Syntax Tree node definitions for the DreamBerd language.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Union
from dataclasses import dataclass


class ASTNode(ABC):
    """Base class for all AST nodes."""
    pass


class Expression(ASTNode):
    """Base class for expressions."""
    pass


class Statement(ASTNode):
    """Base class for statements."""
    pass


# Literals
@dataclass
class NumberLiteral(Expression):
    value: Union[int, float, str]  # str for fractions like "1/2"


@dataclass
class StringLiteral(Expression):
    value: str


@dataclass
class BooleanLiteral(Expression):
    value: bool


@dataclass
class MaybeLiteral(Expression):
    pass


@dataclass
class UndefinedLiteral(Expression):
    pass


@dataclass
class NullLiteral(Expression):
    pass


# Identifiers
@dataclass
class Identifier(Expression):
    name: str


# Arrays
@dataclass
class ArrayLiteral(Expression):
    elements: List[Expression]


@dataclass
class ArrayAccess(Expression):
    array: Expression
    index: Expression


# Binary operations
@dataclass
class BinaryOperation(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass
class UnaryOperation(Expression):
    operator: str
    operand: Expression


# Assignment
@dataclass
class Assignment(Expression):
    target: Expression
    value: Expression


# Increment/Decrement
@dataclass
class IncrementExpression(Expression):
    target: Expression
    is_prefix: bool = True  # True for ++x, False for x++


@dataclass
class DecrementExpression(Expression):
    target: Expression
    is_prefix: bool = True  # True for --x, False for x--


# Function calls
@dataclass
class FunctionCall(Expression):
    function: Expression
    arguments: List[Expression]
    
    
# Member access
@dataclass
class MemberAccess(Expression):
    object: Expression
    property: str


# Method calls for string operations
@dataclass
class MethodCall(Expression):
    object: Expression
    method_name: str
    arguments: List[Expression]


# Variable declarations
@dataclass
class VariableDeclaration(Statement):
    const_count: int  # Number of 'const' keywords
    var_count: int    # Number of 'var' keywords
    name: str
    value: Optional[Expression]
    lifetime: Optional[str]  # For lifetimes like <2>, <20s>, <Infinity>
    priority: int = 0  # From exclamation marks
    type_annotation: Optional[str] = None


# Function declarations
@dataclass
class FunctionDeclaration(Statement):
    keyword: str  # 'function', 'func', 'fun', 'fn', 'functi', 'f', 'union'
    name: str
    parameters: List[str]
    body: Union[Expression, List[Statement]]  # Can be expression or block
    is_async: bool = False


# Class declarations
@dataclass
class ClassDeclaration(Statement):
    keyword: str  # 'class' or 'className'
    name: str
    body: List[Statement]


# Control flow
@dataclass
class IfStatement(Statement):
    condition: Expression
    then_body: List[Statement]
    else_body: Optional[List[Statement]] = None


@dataclass
class WhenStatement(Statement):
    condition: Expression  # Usually an assignment like (health = 0)
    body: List[Statement]


# Return statement
@dataclass
class ReturnStatement(Statement):
    value: Optional[Expression] = None


# Print statement
@dataclass
class PrintStatement(Statement):
    value: Expression
    is_debug: bool = False  # True if using ? instead of !


# Delete statement
@dataclass
class DeleteStatement(Statement):
    target: Expression


# Import/Export
@dataclass
class ImportStatement(Statement):
    name: str


@dataclass
class ExportStatement(Statement):
    name: str
    target_file: str


# Temporal operations
@dataclass
class PreviousExpression(Expression):
    target: Expression


@dataclass
class NextExpression(Expression):
    target: Expression


@dataclass
class CurrentExpression(Expression):
    target: Expression


# Reverse statement
@dataclass
class ReverseStatement(Statement):
    pass


# Signals
@dataclass
class UseExpression(Expression):
    initial_value: Expression


@dataclass
class SignalCall(Expression):
    signal: Expression
    arguments: List[Expression]


# New/instantiation
@dataclass
class NewExpression(Expression):
    class_name: str
    arguments: List[Expression]


# Await
@dataclass
class AwaitExpression(Expression):
    expression: Expression


# File structure
@dataclass
class FileBlock(Statement):
    name: Optional[str]
    body: List[Statement]


# Program (root)
@dataclass
class Program(ASTNode):
    body: List[Statement]


# Global immutable constant (const const const)
@dataclass
class GlobalConstantDeclaration(Statement):
    name: str
    value: Expression
    priority: int = 0


# String interpolation
@dataclass
class StringInterpolation(Expression):
    template: str
    expressions: List[Expression]
    currency_symbol: str  # '$', '£', '¥', '€'


# Noop statement
@dataclass
class NoopStatement(Statement):
    content: str  # The string content used as noop


# Expression statement (for expressions used as statements)
@dataclass
class ExpressionStatement(Statement):
    expression: Expression
    priority: int = 0  # From exclamation marks
    is_debug: bool = False  # True if using ? instead of !


# DBX (HTML-like) elements
@dataclass  
class DBXElement(Expression):
    tag: str
    attributes: dict
    children: List[Union[Expression, str]]


# Rich text elements
@dataclass
class RichTextElement(Expression):
    tag: str  # 'b', 'i', 'a', etc.
    content: str
    attributes: dict = None