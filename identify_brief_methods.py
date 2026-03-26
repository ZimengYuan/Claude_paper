import os
import re

def is_brief(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        content = "".join(lines)
    
    # Check line count
    if len(lines) < 50:
        return True, "Line count < 50"
    
    # Check for mandatory sections (keywords in Chinese)
    keywords = [
        ["问题形式化", "Problem Formalization"],
        ["核心技术方案", "技术方法", "Technical Method"],
        ["实现细节", "Implementation Details"],
        ["实验设置", "Experimental Settings"],
        ["优缺点", "优势", "劣势", "Pros and Cons", "Technical Advantages", "Technical Weaknesses"]
    ]
    
    missing = []
    for group in keywords:
        found = False
        for kw in group:
            if kw.lower() in content.lower():
                found = True
                break
        if not found:
            missing.append(group[0])
            
    if len(missing) > 2: # If more than 2 main sections are missing
        return True, f"Missing sections: {', '.join(missing)}"
    
    return False, ""

if __name__ == "__main__":
    from glob import glob
    files = glob('data/papers/*/method.md')
    brief_files = []
    for f in files:
        brief, reason = is_brief(f)
        if brief:
            brief_files.append((f, reason))
            
    with open('brief_methods.txt', 'w', encoding='utf-8') as f:
        for path, reason in brief_files:
            f.write(f"{path} | {reason}\n")
    
    print(f"Identified {len(brief_files)} brief files.")
