---
layout: doc
title: API Reference
permalink: /docs/api/
---

This Jekyll site uses a static API overview instead of the old MkDocs `mkdocstrings` renderer.

## Core Modules

| Module | Main responsibility | Typical entry points |
|--------|----------------------|----------------------|
| `scholaraio.cli` | CLI command routing | `scholaraio ...` |
| `scholaraio.mcp_server` | MCP tool surface | `scholaraio-mcp` |
| `scholaraio.config` | Config loading and path resolution | `load_config()` |
| `scholaraio.papers` | Canonical paper directory helpers | `iter_paper_dirs()`, `read_meta()` |
| `scholaraio.loader` | Layered loading and notes reuse | `load_l1()`–`load_l4()`, `append_notes()` |

## Search and Index

| Module | Main responsibility | Typical entry points |
|--------|----------------------|----------------------|
| `scholaraio.index` | FTS5 search, registry, citation edges | `build_index()`, `search()`, `unified_search()` |
| `scholaraio.vectors` | Semantic embeddings and vector retrieval | embedding/index update functions |
| `scholaraio.topics` | BERTopic clustering and topic artifacts | topic build / merge / visualize |
| `scholaraio.workspace` | Workspace subsets over the main library | `create()`, `add()`, `remove()` |

## Ingest Pipeline

| Module | Main responsibility |
|--------|----------------------|
| `scholaraio.ingest.pipeline` | End-to-end ingest orchestration |
| `scholaraio.ingest.mineru` | PDF to Markdown conversion |
| `scholaraio.ingest.extractor` | Metadata extraction pipeline |
| `scholaraio.ingest.metadata._api` | Crossref / Semantic Scholar / OpenAlex enrichment |
| `scholaraio.sources.zotero` | Zotero via zotero-cli / SQLite import |
| `scholaraio.sources.endnote` | Endnote XML / RIS import |

## Services for Web / Bridge

| Module | Main responsibility |
|--------|----------------------|
| `scholaraio.web_bridge` | Python action bridge for the Nuxt server |
| `scholaraio.services.library_service` | Library card payloads |
| `scholaraio.services.paper_service` | Single paper detail payloads |
| `scholaraio.services.graph_service` | Citation graph payloads |
| `scholaraio.services.explore_service` | Local-library trend analysis |

For a full repository-level map, see [Code Map]({{ '/docs/architecture/' | relative_url }}).
