---
name: batch-generate
description: 使用 Codex MCP 批量生成论文学习材料 (summary.md, method.md)
tools:
  - type: bash
    description: 运行批量生成脚本
  - type: bash
    description: 检查生成进度
---

# Batch Generate Learning Materials

使用 Codex MCP 批量生成论文的 learning materials。

## 配置

当前配置 (`config.local.yaml`):

```yaml
llm:
  backend: codex-mcp
  model: gpt-5.3-codex
  concurrency: 32
```

**注意**: `codex-mcp` backend 不需要 API key，通过 `claude --print` 子进程调用 `mcp__codex-cli__codex` 工具。

## 生成的文件

- `summary.md` - 论文详细总结
- `method.md` - 方法论详解

## 关键文件

- `scripts/batch_generate.py` - 批量生成脚本
- `scholaraio/metrics.py` - `_call_codex_mcp()` 函数实现 MCP 调用
- `scholaraio/generate.py` - `generate_summary()`, `generate_method()` 函数
- `data/batch_generate.log` - 运行日志

## 运行命令

```bash
# 启动批量生成（--force 覆盖已有文件）
nohup python3 scripts/batch_generate.py --force > data/batch_generate.log 2>&1 &

# 监控进度
tail -f data/batch_generate.log

# 检查当前状态
python3 -c "
from pathlib import Path
from scholaraio.papers import iter_paper_dirs, summary_path, method_path
papers = list(iter_paper_dirs(Path('data/papers')))
print(f'Total: {len(papers)}')
print(f'Summary: {sum(1 for p in papers if summary_path(p).exists())} / {len(papers)}')
print(f'Method: {sum(1 for p in papers if method_path(p).exists())} / {len(papers)}')
"
```

## 已知问题

1. **MCP 调用慢**: 每次调用需要 3-6 秒
2. **偶尔超时**: 120 秒超时限制有时会触发，脚本会自动重试
3. **生成速度**: 预计需要数小时完成全部生成

## 技术细节

`_call_codex_mcp()` 函数实现:

```python
def _call_codex_mcp(prompt, llm_cfg, *, system, json_mode, max_tokens):
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    cmd = [
        "claude", "--print", "-p", full_prompt,
        "--allowed-tools", "mcp__codex-cli__codex",
        "--dangerously-skip-permissions",
        "--model", llm_cfg.model  # e.g., gpt-5.3-codex
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout.strip(), ...
```

## 替代方案

如果 MCP 太慢，可以切换到原生 API:

```yaml
llm:
  backend: anthropic
  model: MiniMax-M2.5
  base_url: https://api.minimaxi.com/anthropic
  api_key: "your-key"
```
