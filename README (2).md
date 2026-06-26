# GRC Schema Design

> Designing an AI-native Governance, Risk & Compliance (GRC) knowledge
> platform on MongoDB Atlas.

------------------------------------------------------------------------

## Overview

This repository explores how to redesign a traditional PostgreSQL-based
GRC application into a flexible MongoDB document model optimized for:

-   AI / Agentic applications
-   Atlas Vector Search
-   RAG (Retrieval-Augmented Generation)
-   Governance policy mapping
-   Risk management
-   Version-aware policy retrieval
-   Agent feedback loops
-   Operational + Vector workloads in a single database

------------------------------------------------------------------------

# Objectives

-   Replace highly normalized relational tables with business-oriented
    aggregates.
-   Support evolving policy schemas without migrations.
-   Store structured and unstructured data together.
-   Enable semantic search across governance content.
-   Support operational workloads and AI retrieval from the same
    platform.

------------------------------------------------------------------------

# Existing Relational Model

The current PostgreSQL design contains entities such as:

-   Policies
-   Security Standards
-   Control Standards
-   Risk Records
-   Vulnerability Types
-   Firewall Types
-   Risk Analysis
-   Risk Recommendations
-   Risk Groupings
-   Audit Logs
-   Policy Mapping Jobs
-   Approved Control Mappings

While relationally sound, the model becomes increasingly complex for:

-   AI retrieval
-   Document ingestion
-   Versioned content
-   Attachments
-   Vector search
-   Agent memory

------------------------------------------------------------------------

# Proposed MongoDB Architecture

## 1. Governance Collections

Authoritative reference data.

``` text
policies
security_standards
control_standards
controls
```

Each document contains:

-   version
-   effective date
-   retired date
-   metadata
-   ownership
-   governance information

------------------------------------------------------------------------

## 2. Vector Search Collections

One embedding per chunk.

``` text
policy_chunks
standard_chunks
control_chunks
risk_record_chunks
```

Each chunk contains:

-   text
-   metadata
-   source references
-   version
-   embedding

Atlas Vector Search indexes these collections.

------------------------------------------------------------------------

## 3. Operational Collections

Primary aggregate:

``` text
risk_records
```

Embedded documents:

-   typeDetails
-   classification
-   auditLog

Referenced documents:

-   policies
-   standards
-   controls

------------------------------------------------------------------------

## 4. Policy Mapping Workflow

Operational workflow collections.

``` text
mapping_jobs
mapping_job_rows
approved_control_mappings
```

These collections capture:

-   AI recommendations
-   reviewer decisions
-   finalized mappings
-   mapping status
-   gaps
-   lineage

------------------------------------------------------------------------

## 5. Agent Feedback Loop

``` text
agent_decisions
```

Stores:

-   prompts
-   retrieved chunks
-   recommendations
-   human approvals
-   confidence
-   feedback

This enables continuous improvement over time.

------------------------------------------------------------------------

## 6. Metadata / Sources

``` text
sources
```

Examples:

-   Archer
-   SharePoint
-   Excel
-   PDFs
-   APIs

Tracks:

-   ingestion status
-   source lineage
-   synchronization history

------------------------------------------------------------------------

# High-Level Architecture

``` text
                 MongoDB Atlas

     Governance Content
 Policies • Standards • Controls
              │
              ▼
      Vector Search Layer
 Chunk Documents + Embeddings
              │
              ▼
         Risk Records
 Exceptions • Reviews • Analysis
         │              │
         ▼              ▼
 Policy Mapping     Agent Feedback
 Jobs               Decisions
         └──────────────┘
                │
                ▼
        Executive Reporting
```

------------------------------------------------------------------------

# Modeling Principles

## Embed

-   Risk analysis
-   Audit history
-   Type-specific details
-   Frequently read together

## Reference

-   Policies
-   Standards
-   Controls
-   Shared governance content

## Separate Chunk Collections

One document per semantic chunk.

Advantages:

-   Better recall
-   Easier re-embedding
-   Metadata filtering
-   Simpler indexing

------------------------------------------------------------------------

# Atlas Features

-   Atlas Vector Search
-   Hybrid Search
-   Compound Metadata Filtering
-   Flexible Document Model
-   Native JSON
-   Horizontal Scaling
-   Change Streams (future)
-   Atlas Search
-   Version-aware filtering

------------------------------------------------------------------------

# Why MongoDB?

Traditional SQL optimizes relationships.

MongoDB optimizes business objects.

Instead of dozens of joins, the application works with:

-   Risk Record
-   Policy
-   Standard
-   Control
-   Mapping Job
-   Agent Decision

Each becomes a natural aggregate optimized for both operational
workloads and AI retrieval.

------------------------------------------------------------------------

# Repository Roadmap

-   [ ] Final MongoDB document model
-   [ ] Collection design
-   [ ] Sample JSON documents
-   [ ] Index strategy
-   [ ] Atlas Vector Search indexes
-   [ ] Chunking strategy
-   [ ] Embedding workflow
-   [ ] Voyage AI integration
-   [ ] Query examples
-   [ ] Aggregation pipelines
-   [ ] Architecture diagrams
-   [ ] POC implementation

------------------------------------------------------------------------

## Status

🚧 Work in Progress

This repository documents the design and implementation of an AI-native
GRC platform built on MongoDB Atlas, replacing a traditional relational
model with a flexible document architecture optimized for semantic
search, operational workloads, and agentic AI.
