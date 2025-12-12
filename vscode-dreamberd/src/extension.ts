import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('DreamBerd language extension is now active!');

    // Register hover provider for DreamBerd language features
    const hoverProvider = vscode.languages.registerHoverProvider('dreamberd', {
        provideHover(document, position) {
            const range = document.getWordRangeAtPosition(position);
            const word = document.getText(range);

            // Provide helpful information about DreamBerd features
            const dreamBerdInfo: { [key: string]: string } = {
                'const': 'DreamBerd const variables can be changed.',
                'var': 'Variables that can change.',
                'const const': 'Constant variables that cannot be changed.',
                'const const const': 'Global immutable constant that affects all files.',
                'maybe': 'A boolean that might be true, might be false, might be maybe.',
                'true!': 'Definitely true (exclamation mark indicates priority level).',
                'false?': 'Possibly false (question mark indicates uncertainty).',
                'print': 'Built-in function to output values.',
                'when': 'Conditional statement that executes when condition is met.',
                'reverse': 'Reverses the last operation or statement.',
                'previous': 'Accesses the previous value of a variable.',
                'next': 'Accesses the next value of a variable.',
                'current': 'Accesses the current value of a variable.',
                'Date.now': 'Gets the current date and time.',
                'function': 'Declares a function in DreamBerd.',
                'func': 'Short form of function declaration.',
                'fun': 'Fun way to declare a function.',
                'fn': 'Shortest function declaration.',
                'functi': 'Incomplete function declaration (valid in DreamBerd).',
                'f': 'Single letter function declaration.',
                'delete': 'Removes a variable from memory.',
                'noop': 'No operation - does nothing.',
                '===': 'Loose equality operator.',
                '====': 'Strict equality operator.',
                '=====': 'File separator (5 or more equals signs).'
            };

            if (dreamBerdInfo[word]) {
                return new vscode.Hover(new vscode.MarkdownString(`**${word}**\n\n${dreamBerdInfo[word]}`));
            }

            return undefined;
        }
    });

    // Register completion provider for DreamBerd keywords
    const completionProvider = vscode.languages.registerCompletionItemProvider('dreamberd', {
        provideCompletionItems(document, position) {
            const completions: vscode.CompletionItem[] = [
                new vscode.CompletionItem('const const const', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('const const', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('const', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('var', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('function', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('func', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('fun', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('fn', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('functi', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('f', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('when', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('if', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('else', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('return', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('print', vscode.CompletionItemKind.Function),
                new vscode.CompletionItem('delete', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('reverse', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('noop', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('true', vscode.CompletionItemKind.Value),
                new vscode.CompletionItem('false', vscode.CompletionItemKind.Value),
                new vscode.CompletionItem('maybe', vscode.CompletionItemKind.Value),
                new vscode.CompletionItem('previous', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('next', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('current', vscode.CompletionItemKind.Keyword),
                new vscode.CompletionItem('Date.now', vscode.CompletionItemKind.Function)
            ];

            return completions;
        }
    });

    context.subscriptions.push(hoverProvider, completionProvider);
}

export function deactivate() {
    // Clean up resources when extension is deactivated
}