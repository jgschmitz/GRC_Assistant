# GRC Assistant

> An AI-native Governance, Risk & Compliance (GRC) knowledge platform built on MongoDB Atlas.

[![Status](https://img.shields.io/badge/status-work%20in%20progress-orange)](#status)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB-Atlas-13aa52)](https://www.mongodb.com/atlas)
[![Vector Search](https://img.shields.io/badge/Atlas-Vector%20Search-00684A)](https://www.mongodb.com/products/platform/atlas-vector-search)

GRC Assistant extracts and centralizes governance, risk, and compliance data from Archer (EGRC) and other sources (Excel, shared folders, Word docs) into a queryable, AI-ready knowledge base.

## Overview

This repository explores how to redesign a traditional PostgreSQL-based GRC application into a flexible MongoDB document model optimized for:

- AI / agentic applications
- Atlas Vector Search
- Retrieval-Augmented Generation (RAG)
- Governance policy mapping
- Risk management
- Version-aware policy retrieval
- Agent feedback loops
- Operational and vector workloads in a single database

## Objectives

- Replace highly normalized relational tables with business-oriented aggregates.
- Support evolving policy schemas without migrations.
- Store structured and unstructured data together.
- Enable semantic search across governance content.
- Serve operational workloads and AI retrieval from the same platform.

## The Existing Relational Model

The current PostgreSQL design contains entities such as Policies, Security Standards, Control Standards, Risk Records, Vulnerability Types, Firewall Types, Risk Analysis, Risk Recommendations, Risk Groupings, Audit Logs, Policy Mapping Jobs, and Approved Control Mappings.

While relationally sound, the model becomes increasingly complex for AI retrieval, document ingestion, versioned content, attachments, vector search, and agent memory.

## Proposed MongoDB Architecture

The design organizes data into six logical groups of collections.

### 1. Governance Collections

Authoritative reference data.

| Collection | Purpose |
| --- | --- |
| `policies` | Policy definitions |
| `security_standards` | Security standards |
| `control_standards` | Control standards |
| `controls` | Individual controls |

Each document carries `version`, effective date, retired date, metadata, ownership, and governance information.

### 2. Vector Search Collections

One embedding per chunk, indexed by Atlas Vector Search.

| Collection | Source |
| --- | --- |
| `policy_chunks` | Policies |
| `standard_chunks` | Standards |
| `control_chunks` | Controls |
| `risk_record_chunks` | Risk records |

Each chunk contains the source text, metadata, source references, version, and an embedding vector.

### 3. Operational Collections

The primary aggregate is `risk_records`.

- **Embedded:** `typeDetails`, `classification`, `auditLog`
- **Referenced:** `policies`, `standards`, `controls`

### 4. Policy Mapping Workflow

Operational workflow collections: `mapping_jobs`, `mapping_job_rows`, and `approved_control_mappings`.

These capture AI recommendations, reviewer decisions, finalized mappings, mapping status, gaps, and lineage.

### 5. Agent Feedback Loop

The `agent_decisions` collection stores prompts, retrieved chunks, recommendations, human approvals, confidence scores, and feedback, enabling continuous improvement over time.

### 6. Metadata / Sources

The `sources` collection tracks ingestion status, source lineage, and synchronization history for inputs such as Archer, SharePoint, Excel, PDFs, and APIs.

## High-Level Architecture

```text
                    MongoDB Atlas

              Governance Content
        Policies · Standards · Controls
                        │
                        ▼
              Vector Search Layer
          Chunk Documents + Embeddings
                        │
                        ▼
                  Risk Records
        Exceptions · Reviews · Analysis
                   │         │
                   ▼         ▼
         Policy Mapping   Agent Feedback
              Jobs          Decisions
                   └────┬────┘
                        ▼
              Executive Reporting
```

## Modeling Principles

**Embed** data that is frequently read together: risk analysis, audit history, and type-specific details.

**Reference** shared governance content: policies, standards, and controls.

**Separate chunk collections** with one document per semantic chunk for better recall, easier re-embedding, metadata filtering, and simpler indexing.

## Atlas Features Used

- Atlas Vector Search
- Hybrid Search
- Compound metadata filtering
- Flexible document model and native JSON
- Horizontal scaling
- Atlas Search
- Version-aware filtering
- Change Streams (future)

## Why MongoDB?

Traditional SQL optimizes relationships; MongoDB optimizes business objects. Instead of dozens of joins, the application works directly with natural aggregates: Risk Record, Policy, Standard, Control, Mapping Job, and Agent Decision. Each is optimized for both operational workloads and AI retrieval.

## Roadmap

- [ ] Final MongoDB document model
- [ ] Collection design
- [ ] Sample JSON documents
- [ ] Index strategy
- [ ] Atlas Vector Search indexes
- [ ] Chunking strategy
- [ ] Embedding workflow
- [ ] Voyage AI integration
- [ ] Query examples
- [ ] Aggregation pipelines
- [ ] Architecture diagrams
- [ ] POC implementation

## Status

🚧 **Work in progress.** This repository documents the design and implementation of an AI-native GRC platform built on MongoDB Atlas, replacing a traditional relational model with a flexible document architecture optimized for semantic search, operational workloads, and agentic AI.
