import os
import re

def fix_math_and_formatting(content):
    # 1. Replace s' and a' with s^\prime and a^\prime
    # Use word boundary or non-letter prefix/suffix to avoid matching inside words
    content = re.sub(r"(\$[^$]*?)s'([^$]*?\$)", r"\1s^\\prime\2", content)
    content = re.sub(r"(\$[^$]*?)a'([^$]*?\$)", r"\1a^\\prime\2", content)
    # Also for $$ blocks
    content = re.sub(r"(\$\$[\s\S]*?)s'([\s\S]*?\$\$)", r"\1s^\\prime\2", content)
    content = re.sub(r"(\$\$[\s\S]*?)a'([\s\S]*?\$\$)", r"\1a^\\prime\2", content)
    
    # 2. Check and complete backslashes for \min, \max, \tanh, \log, \exp
    # Match these only within math blocks
    def math_func_fix(match):
        math_content = match.group(0)
        for func in ['min', 'max', 'tanh', 'log', 'exp']:
            # Replace func if it doesn't have a backslash and is preceded by something that isn't a backslash or a letter
            # More simply, replace "([^\])func" with "\1\func" or start of math content "func" with "\func"
            math_content = re.sub(r'(?<!\\)\b' + func + r'\b', r'\\' + func, math_content)
        return math_content

    content = re.sub(r'\$[^$]+\$', math_func_fix, content)
    content = re.sub(r'\$\$[\s\S]+?\$\$', math_func_fix, content)

    # 3. Inline formulas with multiple underscores
    # e.g., $P_{best_so_far}$ -> $P_{\text{best\_so\_far}}$
    def fix_underscores(match):
        math_content = match.group(0)
        # Check if it's inline and has multiple underscores
        if math_content.startswith('$') and not math_content.startswith('$$'):
            underscores = math_content.count('_')
            if underscores > 1:
                # If it contains underscores that are not escaped or already in \text
                # A simple fix is to put the whole subscript part in \text and escape underscores
                # But a more general way is requested.
                # Example: $P_{best_so_far}$
                # Let's try to find _{...} and if the inside has underscores, fix it.
                new_math = re.sub(r'_\{([^}]+)\}', lambda m: '_{\\text{' + m.group(1).replace('_', '\\_') + '}}', math_content)
                if new_math != math_content:
                    return new_math
                # Or just $P_best_so_far$ (no braces)
                new_math = re.sub(r'_([a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)+)', lambda m: '_{\\text{' + m.group(1).replace('_', '\\_') + '}}', math_content)
                return new_math
        return math_content

    content = re.sub(r'\$[^$]+\$', fix_underscores, content)

    # 4. Ensure $$ formulas have empty lines before and after
    # Fix: \n\n$$\n...\n$$\n\n
    # First, handle the case where there's text immediately before or after
    content = re.sub(r'([^\n])\s*\n*\$\$', r'\1\n\n$$', content)
    content = re.sub(r'\$\$\s*\n*([^\n])', r'$$\n\n\1', content)
    
    # Clean up triple or more newlines to double newlines around $$
    content = re.sub(r'\n{3,}\$\$', r'\n\n$$', content)
    content = re.sub(r'\$\$\n{3,}', r'$$\n\n', content)

    return content

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = fix_math_and_formatting(content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

if __name__ == "__main__":
    import sys
    from glob import glob
    
    files = glob('data/papers/*/method.md')
    modified_count = 0
    for f in files:
        if process_file(f):
            modified_count += 1
            print(f"Fixed: {f}")
    
    print(f"Total modified: {modified_count}")
