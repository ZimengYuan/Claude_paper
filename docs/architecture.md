---
layout: doc
title: Code Map
permalink: /docs/architecture/
---

This page summarizes the repository as a system map instead of a file dump.

## Runtime Graph

```text
User
 ├─ CLI (`scholaraio`)
 ├─ MCP (`scholaraio-mcp`)
 └─ Local Web UI (`scholaraio/web`)
          │
          └─ Nuxt server API
               └─ `scholaraio.web_bridge`
                    └─ `scholaraio.services.*`
                         └─ data/, workspace/, index.db
```

## Main Data Flow

```text
PDF / Markdown / Zotero / Endnote
        │
        └─ `scholaraio.ingest.pipeline`
             ├─ `mineru.py`
             ├─ `extractor.py`
             ├─ `ingest.metadata._api`
             └─ write to `data/papers/<Author-Year-Title>/`
                        │
                        ├─ `meta.json`
                        ├─ `paper.md`
                        ├─ `notes.md`
                        └─ `images/`
                               │
                               ├─ `index.py`   -> FTS5 + `papers_registry`
                               ├─ `vectors.py` -> semantic vectors
                               ├─ `topics.py`  -> BERTopic artifacts
                               └─ `workspace.py` -> project subsets
```

## Source Map

| Area | Files | Responsibility |
|------|-------|----------------|
| Config and logging | `config.py`, `log.py`, `metrics.py` | configuration resolution, logging, runtime metrics |
| Canonical paper layer | `papers.py`, `loader.py` | file paths, metadata IO, layered reading, notes reuse |
| Ingest | `ingest/`, `sources/` | conversion, metadata extraction, import from external tools |
| Retrieval | `index.py`, `vectors.py`, `topics.py` | keyword search, semantic search, topic modeling |
| Writing / generation | `generate.py`, `generation_worker.py` | generated study materials and task queue |
| App interfaces | `cli.py`, `mcp_server.py`, `web_bridge.py` | command line, MCP, local web integration |
| Web-facing services | `services/` | payload shaping for library, paper, graph, explore, knowledge |

## Directory Map

| Path | Role |
|------|------|
| `data/inbox/` | standard papers waiting for ingest |
| `data/inbox-thesis/` | thesis ingest entry |
| `data/inbox-doc/` | general document ingest entry |
| `data/papers/` | canonical library storage |
| `data/pending/` | unresolved or duplicate items |
| `workspace/` | user project subsets and writing outputs |
| `scholaraio/web/` | local Nuxt UI for browsing the library |
| `.claude/skills/` | reusable agent skills |

## Recommended Reading Order

1. `scholaraio/config.py`
2. `scholaraio/papers.py`
3. `scholaraio/loader.py`
4. `scholaraio/ingest/pipeline.py`
5. `scholaraio/index.py`
6. `scholaraio/services/library_service.py`
7. `scholaraio/cli.py`

That path gives the fastest mental model for how the project hangs together.
