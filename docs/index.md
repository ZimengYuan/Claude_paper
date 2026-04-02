---
layout: doc
title: 文档首页
permalink: /docs/
---

**Scholar All-In-One** — a local academic literature explorer powered by AI.

ScholarAIO is a research terminal built around Claude Code. You interact with your literature knowledge base through natural language — searching, reading, analyzing, and writing — all from the command line.

## Features

- **PDF Ingestion**: Convert PDFs to structured Markdown via MinerU (cloud or local)
- **Hybrid Search**: FTS5 keyword search + FAISS semantic search + RRF fusion
- **Topic Modeling**: BERTopic clustering with interactive HTML visualizations
- **Citation Graph**: View references, citing papers, and shared references
- **BibTeX Export**: Filtered export with standard citation formats
- **Literature Exploration**: Multi-dimensional OpenAlex queries with isolated data
- **Workspace Management**: Organize papers into subsets for focused work
- **22 Agent Skills**: Literature review, paper writing, gap analysis, and more
- **MCP Server**: 31 tools for integration with Claude Desktop, Cursor, etc.

## Quick Start

```bash
pip install -e ".[full]"
scholaraio setup
```

See [Installation]({{ '/docs/getting-started/installation/' | relative_url }}) for detailed instructions.

## Documentation Map

- [Installation]({{ '/docs/getting-started/installation/' | relative_url }})
- [Configuration]({{ '/docs/getting-started/configuration/' | relative_url }})
- [Search & Browse]({{ '/docs/guide/search/' | relative_url }})
- [Paper Ingestion]({{ '/docs/guide/ingestion/' | relative_url }})
- [Academic Writing]({{ '/docs/guide/writing/' | relative_url }})
- [API Reference]({{ '/docs/api/' | relative_url }})
- [Code Map]({{ '/docs/architecture/' | relative_url }})
- [Project Analysis: Explore Enhancement]({{ '/docs/project-analysis/01-explore-enhancement/' | relative_url }})
- [Project Analysis: Long PDF Splitting]({{ '/docs/project-analysis/02-long-pdf-splitting/' | relative_url }})
- [Project Analysis: General Document Ingestion]({{ '/docs/project-analysis/03-general-document-ingestion/' | relative_url }})

## Three Usage Modes

| Mode | Interface | Best for |
|------|-----------|----------|
| **Agent** | Claude Code CLI | Full research workflow via natural language |
| **MCP** | Claude Desktop / Cursor | IDE-integrated literature access |
| **CLI** | Terminal | Scripting and automation |
