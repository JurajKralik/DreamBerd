# DreamBerd Language Support for VS Code

Syntax highlighting and language support for the DreamBerd programming language (also known as "Gulf of Mexico").

## Features

- **Syntax Highlighting**: Complete syntax highlighting for DreamBerd code
- **Code Snippets**: Pre-built code snippets for common DreamBerd constructs
- **Language Configuration**: Bracket matching, auto-closing pairs, and comment toggling
- **IntelliSense**: Hover information and auto-completion for DreamBerd keywords
- **File Extensions**: Supports `.db`, `.gom`, and `.dreamberd` file extensions

## Supported DreamBerd Features

### Variables
- `const` - Variables that can be changed
- `const const` - Constant variables that cannot be changed  
- `const const const` - Global immutable constants
- `var` - Regular variables

### Functions
- `function`, `func`, `fun`, `fn`, `functi`, `f` - All valid function declarations

### Control Flow
- `if`, `else` - Conditional statements
- `when` - Executes when condition is met
- `return` - Return values from functions

### Operators
- `===` - Loose equality
- `====` - Strict equality  
- `++`, `--` - Increment/decrement operators
- Exclamation marks (`!`) for statement priority
- Question marks (`?`) for uncertain statements

### Data Types
- `true`, `false`, `maybe` - Boolean values
- Numbers (integers, floats, fractions, word numbers)
- Strings with interpolation support
- Arrays (remember: they start at -1!)

### Special Features
- String interpolation with `${}`, `£{}`, `¥{}`, `€{}`
- Cape Verdean interpolation with `{...€}`
- Unquoted strings
- Previous/next/current variable values
- File separators with 5+ equals signs
- DBX (DreamBerd XML) support
- Time manipulation
- Memory management with `delete`
- Operation reversal with `reverse`
- No-operation with `noop`

### Built-in Functions
- `print()` - Output values
- `Date.now()` - Current date/time

## Installation

1. Copy the `vscode-dreamberd` folder to your VS Code extensions directory:
   - **Windows**: `%USERPROFILE%\.vscode\extensions`
   - **macOS**: `~/.vscode/extensions`
   - **Linux**: `~/.vscode/extensions`

2. Reload VS Code

3. Open any `.db`, `.gom`, or `.dreamberd` file to activate the extension

## Development

To build and develop this extension:

```bash
npm install
npm run compile
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! This extension aims to support all DreamBerd language features as they are implemented.

---

*"Perfect is the enemy of good, but not in DreamBerd."*