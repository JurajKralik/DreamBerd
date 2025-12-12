"""
DreamBerd/Gulf of Mexico Interpreter
Main entry point for running DreamBerd programs.
"""

import sys
import argparse
from pathlib import Path
from dreamberd_interpreter import run_dreamberd, DreamBerdError


def main():
    parser = argparse.ArgumentParser(description='DreamBerd/Gulf of Mexico Interpreter')
    parser.add_argument('file', nargs='?', help='DreamBerd source file to run')
    parser.add_argument('-c', '--code', help='Execute DreamBerd code directly')
    parser.add_argument('-i', '--interactive', action='store_true', help='Start interactive mode')
    parser.add_argument('--version', action='version', version='DreamBerd Interpreter 1.0')
    
    args = parser.parse_args()
    
    if args.code:
        # Execute code directly
        try:
            output = run_dreamberd(args.code)
            for line in output:
                print(line)
        except DreamBerdError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.file:
        # Execute file
        try:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File '{args.file}' not found", file=sys.stderr)
                sys.exit(1)
            
            source = file_path.read_text(encoding='utf-8')
            output = run_dreamberd(source)
            for line in output:
                print(line)
        except DreamBerdError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.interactive:
        # Interactive mode
        interactive_mode()
    
    else:
        # No arguments - show help
        parser.print_help()


def interactive_mode():
    """Run DreamBerd in interactive mode."""
    print("DreamBerd/Gulf of Mexico Interactive Interpreter")
    print("Type 'exit' or 'quit' to exit, 'help' for help")
    print()
    
    while True:
        try:
            code = input(">>> ")
            
            if code.lower() in ('exit', 'quit'):
                print("Goodbye!")
                break
            
            if code.lower() == 'help':
                print_help()
                continue
            
            if not code.strip():
                continue
            
            # Add exclamation mark if missing (AEMI feature)
            if not code.strip().endswith(('!', '?')):
                code += '!'
            
            try:
                output = run_dreamberd(code)
                for line in output:
                    print(line)
            except DreamBerdError as e:
                print(f"Error: {e}")
        
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
        except EOFError:
            print("\nGoodbye!")
            break


def print_help():
    """Print help information."""
    print("""
DreamBerd/Gulf of Mexico Language Features:

Variables:
  const const name = "Luke"!     # Constant constant
  const var name = "Luke"!       # Constant variable (editable)
  var const name = "Luke"!       # Variable constant (reassignable)
  var var name = "Luke"!         # Variable variable

Arrays (start at -1):
  const const scores = [3, 2, 5]!
  print(scores[-1])!             # 3
  print(scores[0])!              # 2

Functions:
  function add(a, b) => a + b!
  func multiply(a, b) => a * b!
  fun subtract(a, b) => a - b!

Exclamation Marks:
  print("Hello")!                # Normal statement
  print("Hello")!!!             # Higher priority
  print("Hello")?               # Debug mode

Equality Levels:
  3 = 3.14!                     # Very loose (true)
  "3" == 3!                     # Loose (true) 
  "3" === 3!                    # Strict (false)
  3 ==== 3!                     # Super strict (true)

Special Values:
  true, false, maybe            # Booleans
  undefined, null               # Special values

Example Programs:
  const const name = "World"!
  print("Hello " + name)!
""")


if __name__ == '__main__':
    main()