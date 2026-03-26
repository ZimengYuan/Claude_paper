#!/usr/bin/env python
"""检查 Zotero 与 ScholarAIO 知识库的一致性，不一致则自动导入"""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

# Zotero 数据库路径
ZOTERO_SQLITE = "/home/nie/Zotero/zotero.sqlite"

# 当前项目目录
PROJECT_DIR = Path("/home/nie/Claude/papers/scholaraio")
INBOX_DIR = PROJECT_DIR / "data" / "inbox"


def get_zotero_pdfs():
    """获取 Zotero 中所有 PDF 附件"""
    zotero_db = sqlite3.connect(ZOTERO_SQLITE)
    cursor = zotero_db.cursor()

    cursor.execute('''
        SELECT path FROM itemAttachments
        WHERE contentType = 'application/pdf'
    ''')
    attachments = cursor.fetchall()

    pdfs = set()
    for (path,) in attachments:
        if path.startswith('storage:'):
            pdf_name = path.replace('storage:', '').replace('.pdf', '')
            pdfs.add(pdf_name)

    return pdfs


def get_inbox_pdfs():
    """获取 inbox 中的 PDF"""
    if not INBOX_DIR.exists():
        return set()

    pdfs = set()
    for f in os.listdir(INBOX_DIR):
        if f.endswith('.pdf'):
            pdfs.add(f.replace('.pdf', ''))

    return pdfs


def check_and_import():
    """检查一致性并导入"""
    print(f"检查 Zotero 与知识库一致性...")

    zotero_pdfs = get_zotero_pdfs()
    inbox_pdfs = get_inbox_pdfs()

    print(f"Zotero PDF 数量: {len(zotero_pdfs)}")
    print(f"Inbox PDF 数量: {len(inbox_pdfs)}")

    # 找出需要导入的（Zotero 有但 inbox 没有的）
    to_import = zotero_pdfs - inbox_pdfs

    if to_import:
        print(f"\n发现 {len(to_import)} 篇需要导入的论文:")
        for pdf in list(to_import)[:10]:
            print(f"  - {pdf[:60]}...")
        if len(to_import) > 10:
            print(f"  ... 还有 {len(to_import) - 10} 篇")

        # 复制缺失的 PDF 到 inbox
        print("\n正在复制 PDF 到 inbox...")
        zotero_storage = Path("/home/nie/Zotero/storage")

        for pdf_name in to_import:
            src = zotero_storage / f"{pdf_name}.pdf"
            dst = INBOX_DIR / f"{pdf_name}.pdf"
            if src.exists() and not dst.exists():
                import shutil
                shutil.copy2(src, dst)

        print("PDF 复制完成，现在运行导入...")
        # 运行导入
        os.chdir(PROJECT_DIR)
        result = subprocess.run(
            ["scholaraio", "import-zotero", "--local", ZOTERO_SQLITE],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        return True
    else:
        print("\n知识库已是最新状态，无需导入")
        return False


if __name__ == "__main__":
    check_and_import()
