"""
DreamBerd/Gulf of Mexico Interpreter
Evaluates DreamBerd AST nodes and executes the program.
"""

import math
import time
import re
from typing import Any, Dict, List, Optional, Union, Callable
from dreamberd_ast import *
from dreamberd_parser import parse_dreamberd


class DreamBerdValue:
    """Wrapper for DreamBerd values with metadata."""
    def __init__(self, value: Any, deleted: bool = False, lifetime: Optional[float] = None):
        self.value = value
        self.deleted = deleted
        self.lifetime = lifetime  # Expiry time
        self.history: List[Any] = [value]  # For previous/next/current
        
    def is_expired(self) -> bool:
        return self.lifetime is not None and time.time() > self.lifetime
    
    def set_value(self, new_value: Any):
        self.history.append(new_value)
        self.value = new_value
    
    def get_previous(self) -> Any:
        if len(self.history) >= 2:
            return self.history[-2]
        return self.value
    
    def get_current(self) -> Any:
        return self.value


class Maybe:
    """Represents the 'maybe' boolean value."""
    def __str__(self):
        return "maybe"
    
    def __bool__(self):
        import random
        return random.choice([True, False])


class DreamBerdError(Exception):
    pass


class DreamBerdInterpreter:
    def __init__(self):
        self.global_scope: Dict[str, DreamBerdValue] = {}
        self.scope_stack: List[Dict[str, DreamBerdValue]] = [self.global_scope]
        self.functions: Dict[str, FunctionDeclaration] = {}
        self.classes: Dict[str, ClassDeclaration] = {}
        self.class_instances: Dict[str, Any] = {}  # Track single instances per class
        self.deleted_values: set = set()
        self.reversed = False
        self.output: List[str] = []
        self.immutable_globals: set = set()  # Track globally immutable variables
        
        # Initialize built-in functions
        self._init_builtins()
    
    def _init_builtins(self):
        """Initialize built-in functions and values."""
        # Built-in print function
        def builtin_print(*args):
            output = ' '.join(str(arg) for arg in args)
            self.output.append(output)
            print(output)
        
        self.global_scope['print'] = DreamBerdValue(builtin_print)
        
        # Date object with now() method
        class DateObject:
            @staticmethod
            def now():
                return time.time() * 1000  # JavaScript-style timestamp
        
        self.global_scope['Date'] = DreamBerdValue(DateObject())
        
        # Number names
        number_names = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'eleven': 11, 'twelve': 12
        }
        
        for name, value in number_names.items():
            self.global_scope[name] = DreamBerdValue(value)
    
    def current_scope(self) -> Dict[str, DreamBerdValue]:
        """Get the current scope."""
        return self.scope_stack[-1]
    
    def push_scope(self, scope: Optional[Dict[str, DreamBerdValue]] = None):
        """Push a new scope onto the scope stack."""
        if scope is None:
            scope = {}
        self.scope_stack.append(scope)
    
    def pop_scope(self):
        """Pop the current scope from the scope stack."""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
    
    def get_variable(self, name: str) -> DreamBerdValue:
        """Get a variable from the scope chain."""
        # Check for expired variables
        for scope in reversed(self.scope_stack):
            if name in scope:
                var = scope[name]
                if var.is_expired():
                    del scope[name]
                    continue
                if var.deleted:
                    raise DreamBerdError(f"Variable '{name}' has been deleted")
                return var
        
        raise DreamBerdError(f"Undefined variable: {name}")
    
    def set_variable(self, name: str, value: DreamBerdValue, create_new: bool = False):
        """Set a variable in the appropriate scope."""
        # For new variables or global assignment
        if create_new:
            self.current_scope()[name] = value
            return
        
        # Update existing variable
        for scope in reversed(self.scope_stack):
            if name in scope:
                scope[name].set_value(value.value)
                return
        
        # If not found, create in current scope
        self.current_scope()[name] = value
    
    def parse_lifetime(self, lifetime_str: str) -> Optional[float]:
        """Parse lifetime string and return expiry timestamp."""
        if not lifetime_str:
            return None
        
        if lifetime_str.lower() == 'infinity':
            return None  # Never expires
        
        # Parse negative lifetimes (variable hoisting)
        if lifetime_str.startswith('-'):
            # For negative lifetimes, the variable should disappear after creation
            # This is a special case we'll handle differently
            return time.time() + abs(int(lifetime_str))
        
        # Parse time-based lifetimes
        if lifetime_str.endswith('s'):
            seconds = float(lifetime_str[:-1])
            return time.time() + seconds
        elif lifetime_str.endswith('m'):
            minutes = float(lifetime_str[:-1])
            return time.time() + (minutes * 60)
        elif lifetime_str.endswith('h'):
            hours = float(lifetime_str[:-1])
            return time.time() + (hours * 3600)
        else:
            # Assume it's a number of lines (simplified: 1 second per line)
            try:
                lines = int(lifetime_str)
                return time.time() + lines
            except ValueError:
                return None
    
    def evaluate_arithmetic(self, left: Any, operator: str, right: Any) -> Any:
        """Evaluate arithmetic operations with DreamBerd semantics."""
        # Handle deleted values
        if left in self.deleted_values or right in self.deleted_values:
            raise DreamBerdError("Cannot perform arithmetic on deleted values")
        
        # Handle fractions
        if isinstance(left, str) and '/' in left:
            parts = left.split('/')
            left = float(parts[0]) / float(parts[1])
        
        if isinstance(right, str) and '/' in right:
            parts = right.split('/')
            right = float(parts[0]) / float(parts[1])
        
        # Division by zero returns undefined
        if operator == '/' and right == 0:
            return "undefined"
        
        # Arithmetic operations
        if operator == '+':
            return left + right
        elif operator == '-':
            return left - right
        elif operator == '*':
            return left * right
        elif operator == '/':
            return left / right
        elif operator == '^':
            return left ** right
        elif operator == '%':
            return left % right
        
        return None
    
    def evaluate_comparison(self, left: Any, operator: str, right: Any) -> bool:
        """Evaluate comparison operations with DreamBerd equality levels."""
        if operator == '=':  # Very loose equality
            return abs(left - right) < 0.5  # Close enough
        elif operator == '==':  # Loose equality
            return str(left) == str(right)
        elif operator == '===':  # Strict equality
            return left == right and type(left) == type(right)
        elif operator == '====':  # Super strict equality (reference equality)
            return left is right
        elif operator == '!=':
            return left != right
        elif operator == '<':
            return left < right
        elif operator == '>':
            return left > right
        elif operator == '<=':
            return left <= right
        elif operator == '>=':
            return left >= right
        
        return False
    
    def interpret(self, source: str):
        """Interpret DreamBerd source code."""
        try:
            ast = parse_dreamberd(source)
            return self.visit(ast)
        except Exception as e:
            raise DreamBerdError(f"Interpretation error: {e}")
    
    def visit(self, node: ASTNode) -> Any:
        """Visit an AST node and evaluate it."""
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node: ASTNode) -> Any:
        """Default visitor for unknown nodes."""
        raise DreamBerdError(f"No visitor for {type(node).__name__}")
    
    def visit_Program(self, node: Program) -> Any:
        """Visit program node."""
        result = None
        statements = node.body
        
        # Handle reverse execution
        if self.reversed:
            statements = reversed(statements)
        
        for stmt in statements:
            result = self.visit(stmt)
        
        return result
    
    def visit_NumberLiteral(self, node: NumberLiteral) -> Any:
        """Visit number literal."""
        if isinstance(node.value, str) and '/' in node.value:
            # Handle fractions
            parts = node.value.split('/')
            return float(parts[0]) / float(parts[1])
        
        return node.value
    
    def visit_StringLiteral(self, node: StringLiteral) -> str:
        """Visit string literal."""
        return node.value
    
    def visit_BooleanLiteral(self, node: BooleanLiteral) -> bool:
        """Visit boolean literal."""
        return node.value
    
    def visit_MaybeLiteral(self, node: MaybeLiteral) -> Maybe:
        """Visit maybe literal."""
        return Maybe()
    
    def visit_UndefinedLiteral(self, node: UndefinedLiteral) -> str:
        """Visit undefined literal."""
        return "undefined"
    
    def visit_NullLiteral(self, node: NullLiteral) -> None:
        """Visit null literal."""
        return None
    
    def visit_Identifier(self, node: Identifier) -> Any:
        """Visit identifier."""
        var = self.get_variable(node.name)
        return var.value
    
    def visit_ArrayLiteral(self, node: ArrayLiteral) -> List[Any]:
        """Visit array literal."""
        return [self.visit(element) for element in node.elements]
    
    def visit_ArrayAccess(self, node: ArrayAccess) -> Any:
        """Visit array access with DreamBerd indexing (starts at -1)."""
        array = self.visit(node.array)
        index = self.visit(node.index)
        
        if not isinstance(array, list):
            raise DreamBerdError("Can only index arrays")
        
        # DreamBerd arrays start at -1
        if isinstance(index, int):
            dreamberd_index = index + 1
            if 0 <= dreamberd_index < len(array):
                return array[dreamberd_index]
        elif isinstance(index, float):
            # Float indexing - insert between elements
            base_index = int(index) + 1
            if 0 <= base_index < len(array):
                return array[base_index]
        
        raise DreamBerdError("Array index out of bounds")
    
    def visit_BinaryOperation(self, node: BinaryOperation) -> Any:
        """Visit binary operation."""
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        # Logical operations
        if node.operator == '&&':
            return left and right
        elif node.operator == '||':
            return left or right
        
        # Comparison operations
        if node.operator in ('=', '==', '===', '====', '!=', '<', '>', '<=', '>='):
            return self.evaluate_comparison(left, node.operator, right)
        
        # Arithmetic operations
        return self.evaluate_arithmetic(left, node.operator, right)
    
    def visit_UnaryOperation(self, node: UnaryOperation) -> Any:
        """Visit unary operation."""
        operand = self.visit(node.operand)
        
        if node.operator == ';':  # NOT operator in DreamBerd
            return not operand
        elif node.operator == '-':
            return -operand
        elif node.operator == '+':
            return +operand
        
        return operand
    
    def visit_Assignment(self, node: Assignment) -> Any:
        """Visit assignment."""
        value = self.visit(node.value)
        
        if isinstance(node.target, Identifier):
            var = DreamBerdValue(value)
            self.set_variable(node.target.name, var)
            return value
        elif isinstance(node.target, ArrayAccess):
            # Array element assignment with float indexing
            array = self.visit(node.target.array)
            index = self.visit(node.target.index)
            
            if isinstance(index, float):
                # Insert at float position
                insert_pos = int(index) + 1  # Convert from DreamBerd indexing
                if 0 <= insert_pos <= len(array):
                    array.insert(insert_pos, value)
            else:
                # Regular assignment
                dreamberd_index = index + 1
                if 0 <= dreamberd_index < len(array):
                    array[dreamberd_index] = value
            
            return value
        
        raise DreamBerdError("Invalid assignment target")
    
    def visit_FunctionCall(self, node: FunctionCall) -> Any:
        """Visit function call."""
        if isinstance(node.function, Identifier):
            func_name = node.function.name
            
            # Get function
            try:
                func_var = self.get_variable(func_name)
                func = func_var.value
            except DreamBerdError:
                raise DreamBerdError(f"Undefined function: {func_name}")
            
            # Evaluate arguments
            args = [self.visit(arg) for arg in node.arguments]
            
            # Call built-in function
            if callable(func):
                return func(*args)
            
            # Call user-defined function
            if isinstance(func, FunctionDeclaration):
                return self.call_function(func, args)
        
        raise DreamBerdError("Invalid function call")
    
    def call_function(self, func_decl: FunctionDeclaration, args: List[Any]) -> Any:
        """Call a user-defined function."""
        # Create new scope for function
        func_scope = {}
        
        # Bind parameters
        for i, param in enumerate(func_decl.parameters):
            if i < len(args):
                func_scope[param] = DreamBerdValue(args[i])
        
        self.push_scope(func_scope)
        
        try:
            if isinstance(func_decl.body, list):
                # Block body
                result = None
                for stmt in func_decl.body:
                    result = self.visit(stmt)
                    if isinstance(stmt, ReturnStatement):
                        break
                return result
            else:
                # Expression body
                return self.visit(func_decl.body)
        finally:
            self.pop_scope()
    
    def visit_MemberAccess(self, node: MemberAccess) -> Any:
        """Visit member access."""
        obj = self.visit(node.object)
        
        if hasattr(obj, node.property):
            attr = getattr(obj, node.property)
            if callable(attr):
                return attr()
            return attr
        
        raise DreamBerdError(f"Property '{node.property}' not found")
    
    def visit_VariableDeclaration(self, node: VariableDeclaration) -> None:
        """Visit variable declaration."""
        # Handle overloading - higher priority wins
        existing_var = None
        try:
            existing_var = self.get_variable(node.name)
        except DreamBerdError:
            pass
        
        # Check if this declaration has higher priority
        if existing_var and hasattr(existing_var, 'priority'):
            if node.priority <= existing_var.priority:
                return  # Don't overwrite higher priority variable
        
        # Evaluate initial value
        value = None
        if node.value:
            value = self.visit(node.value)
        
        # Parse lifetime
        lifetime = self.parse_lifetime(node.lifetime) if node.lifetime else None
        
        # Create DreamBerd value
        dreamberd_value = DreamBerdValue(value, lifetime=lifetime)
        dreamberd_value.priority = node.priority
        
        # Store variable
        self.set_variable(node.name, dreamberd_value, create_new=True)
    
    def visit_FunctionDeclaration(self, node: FunctionDeclaration) -> None:
        """Visit function declaration."""
        # Store function in global scope
        func_var = DreamBerdValue(node)
        self.set_variable(node.name, func_var, create_new=True)
        self.functions[node.name] = node
    
    def visit_ClassDeclaration(self, node: ClassDeclaration) -> None:
        """Visit class declaration."""
        self.classes[node.name] = node
    
    def visit_PrintStatement(self, node: PrintStatement) -> None:
        """Visit print statement."""
        value = self.visit(node.value)
        
        if node.is_debug:
            # Debug print with line info
            debug_info = f"DEBUG: {value} (type: {type(value).__name__})"
            self.output.append(debug_info)
            print(debug_info)
        else:
            output = str(value)
            self.output.append(output)
            print(output)
    
    def visit_ExpressionStatement(self, node: ExpressionStatement) -> Any:
        """Visit expression statement."""
        result = self.visit(node.expression)
        
        if node.is_debug:
            # Print debug info
            debug_info = f"DEBUG: {result} (type: {type(result).__name__})"
            self.output.append(debug_info)
            print(debug_info)
        
        return result
    
    def visit_ReturnStatement(self, node: ReturnStatement) -> Any:
        """Visit return statement."""
        if node.value:
            return self.visit(node.value)
        return None
    
    def visit_DeleteStatement(self, node: DeleteStatement) -> None:
        """Visit delete statement."""
        if isinstance(node.target, Identifier):
            # Delete variable
            var_name = node.target.name
            try:
                var = self.get_variable(var_name)
                var.deleted = True
            except DreamBerdError:
                pass
        elif isinstance(node.target, NumberLiteral):
            # Delete number
            value = self.visit(node.target)
            self.deleted_values.add(value)
    
    def visit_ReverseStatement(self, node: ReverseStatement) -> None:
        """Visit reverse statement."""
        self.reversed = not self.reversed
    
    def visit_PreviousExpression(self, node: PreviousExpression) -> Any:
        """Visit previous expression."""
        if isinstance(node.target, Identifier):
            var = self.get_variable(node.target.name)
            return var.get_previous()
        
        raise DreamBerdError("Previous can only be used with variables")
    
    def visit_CurrentExpression(self, node: CurrentExpression) -> Any:
        """Visit current expression."""
        return self.visit(node.target)
    
    def visit_UseExpression(self, node: UseExpression) -> Any:
        """Visit use expression (signals)."""
        initial_value = self.visit(node.initial_value)
        
        # Create a signal function
        def signal(*args):
            if args:
                # Setter
                signal.value = args[0]
                return args[0]
            else:
                # Getter
                return getattr(signal, 'value', initial_value)
        
        signal.value = initial_value
        return signal
    
    def visit_NewExpression(self, node: NewExpression) -> Any:
        """Visit new expression."""
        class_name = node.class_name
        
        # Check if class exists
        if class_name not in self.classes:
            raise DreamBerdError(f"Undefined class: {class_name}")
        
        # Check single instance restriction
        if class_name in self.class_instances:
            raise DreamBerdError(f"Can't have more than one '{class_name}' instance!")
        
        # Create instance
        class_decl = self.classes[class_name]
        instance = {}
        
        # Execute class body in instance context
        instance_scope = {}
        self.push_scope(instance_scope)
        
        try:
            for stmt in class_decl.body:
                self.visit(stmt)
            
            # Copy instance variables
            for name, var in instance_scope.items():
                instance[name] = var.value
        finally:
            self.pop_scope()
        
        # Register instance
        self.class_instances[class_name] = instance
        
        return instance
    
    def visit_FileBlock(self, node: FileBlock) -> Any:
        """Visit file block."""
        # Create new scope for file
        file_scope = {}
        self.push_scope(file_scope)
        
        try:
            result = None
            for stmt in node.body:
                result = self.visit(stmt)
            return result
        finally:
            self.pop_scope()
    
    def visit_NoopStatement(self, node: NoopStatement) -> None:
        """Visit noop statement (does nothing)."""
        pass
    
    def visit_GlobalConstantDeclaration(self, node) -> None:
        """Handle const const const global immutable declarations."""
        value = self.visit(node.value)
        # Global constants are truly immutable and accessible from anywhere
        wrapped_value = DreamBerdValue(value)
        self.global_scope[f"__global_const_{node.name}"] = wrapped_value
        # Also make accessible normally but mark as immutable
        self.global_scope[node.name] = wrapped_value
        self.immutable_globals.add(node.name)
    
    def visit_IncrementExpression(self, node) -> Any:
        """Handle increment expressions (++x or x++)."""
        if not isinstance(node.target, Identifier):
            raise DreamBerdError("Can only increment variables")
        
        var_name = node.target.name
        var_wrapper = self.get_variable(var_name)
        current_value = var_wrapper.value
        
        if not isinstance(current_value, (int, float)):
            raise DreamBerdError(f"Cannot increment non-numeric value: {type(current_value)}")
        
        if node.is_prefix:
            # ++x: increment first, return new value
            new_value = current_value + 1
            var_wrapper.set_value(new_value)
            return new_value
        else:
            # x++: return current value, then increment
            var_wrapper.set_value(current_value + 1)
            return current_value
    
    def visit_DecrementExpression(self, node) -> Any:
        """Handle decrement expressions (--x or x--)."""
        if not isinstance(node.target, Identifier):
            raise DreamBerdError("Can only decrement variables")
        
        var_name = node.target.name
        var_wrapper = self.get_variable(var_name)
        current_value = var_wrapper.value
        
        if not isinstance(current_value, (int, float)):
            raise DreamBerdError(f"Cannot decrement non-numeric value: {type(current_value)}")
        
        if node.is_prefix:
            # --x: decrement first, return new value
            new_value = current_value - 1
            var_wrapper.set_value(new_value)
            return new_value
        else:
            # x--: return current value, then decrement
            var_wrapper.set_value(current_value - 1)
            return current_value


def run_dreamberd(source: str) -> List[str]:
    """Run DreamBerd source code and return output."""
    interpreter = DreamBerdInterpreter()
    interpreter.interpret(source)
    return interpreter.output