// ============================================================================
// Target MongoDB schema (the "after").
// The collection-validator equivalent of sql/legacy_schema.sql. Run with:
//   mongosh "<MONGODB_URI>" mongo/target_schema.js - demo grade 
//
// Each createCollection uses a $jsonSchema validator so the document model is
// explicit and enforced, the MongoDB analogue of CREATE TABLE column types.
// Dozens of normalized tables collapse into 6 business-oriented collections:
//   policies · control_standards · risk_records · mapping_jobs
//   *_chunks (vector) · agent_decisions
// ============================================================================

const db = db.getSiblingDB("grc_assistant");

// ---- Governance reference data (referenced by _id elsewhere) ---------------

db.createCollection("policies", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "title", "version", "status"],
      properties: {
        _id: { bsonType: "string", description: "policy id, version at end of name e.g. POL-111" },
        title: { bsonType: "string" },
        version: { bsonType: "int" },
        status: { enum: ["draft", "active", "retired"] },
        effectiveDate: { bsonType: ["string", "date", "null"] },
        retiredDate: { bsonType: ["string", "date", "null"] },
        body: { bsonType: "string" },
        owner: {
          bsonType: "object",
          properties: { team: { bsonType: "string" }, contact: { bsonType: "string" } }
        },
        tags: { bsonType: "array", items: { bsonType: "string" } },
        // legacy `documents` rows fold in here as an embedded array
        attachments: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["documentId", "filename"],
            properties: {
              documentId: { bsonType: "string" },
              filename: { bsonType: "string" },
              mimeType: { bsonType: "string" },
              version: { bsonType: "int" },
              blobRef: { bsonType: "string" }
            }
          }
        }
      }
    }
  }
});

db.createCollection("control_standards", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "controlName", "status"],
      properties: {
        _id: { bsonType: "string", description: "e.g. 111.1.01" },
        securityStandardId: { bsonType: "string", description: "e.g. 111.1.1" },
        controlName: { bsonType: "string" },
        statement: { bsonType: "string" },
        status: { enum: ["draft", "active", "retired"] },
        version: { bsonType: "int" },
        effectiveDate: { bsonType: ["string", "date", "null"] },
        retiredDate: { bsonType: ["string", "date", "null"] }
      }
    }
  }
});

// ---- Operational risk aggregate --------------------------------------------
// Collapses risk_records + vulnerability_type + firewall_type + risk_grouping
// + change_log + risk_rules_log into ONE document.

db.createCollection("risk_records", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "title", "classification"],
      properties: {
        _id: { bsonType: "string" },
        title: { bsonType: "string" },
        classification: {
          bsonType: "object",
          required: ["severity"],
          properties: {
            severity: { enum: ["low", "medium", "high", "critical"] },
            likelihood: { enum: ["low", "medium", "high"] },
            grouping: {
              bsonType: "object",
              description: "from legacy risk_grouping flow_1/2/3",
              properties: {
                flow_1: { bsonType: "string" },
                flow_2: { bsonType: "string" },
                flow_3: { bsonType: "string" }
              }
            }
          }
        },
        // 1:1 type tables collapse into a single polymorphic sub-document
        typeDetails: {
          bsonType: ["object", "null"],
          properties: {
            type: { enum: ["vulnerability", "firewall"] },
            termSource: { bsonType: "string" },
            deviceScope: { enum: ["internal", "external"] },
            isApplication: { bsonType: "bool" },
            asset: { bsonType: "string" },
            protocolsUsed: { bsonType: "string" },
            connectionScope: { enum: ["internal", "external"] }
          }
        },
        policyRefs: { bsonType: "array", items: { bsonType: "string" } },
        controlRefs: { bsonType: "array", items: { bsonType: "string" } },
        businessUnit: { bsonType: "string" },
        riskOwner: { bsonType: "string" },
        // change_log + risk_rules_log merge into one chronological array
        auditLog: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["ts", "action"],
            properties: {
              ts: { bsonType: ["string", "date"] },
              actor: { bsonType: "string" },
              action: { bsonType: "string" },
              source: { enum: ["change_log", "risk_rules_log"] }
            }
          }
        }
      }
    }
  }
});

// ---- Policy mapping workflow -----------------------------------------------
// jobs + job_rows become one aggregate with an embedded rows array.

db.createCollection("mapping_jobs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "status"],
      properties: {
        _id: { bsonType: "string" },
        status: { enum: ["pending", "running", "complete", "failed"] },
        progress: { bsonType: "int", minimum: 0, maximum: 100 },
        controlFilename: { bsonType: "string" },
        standardsFilename: { bsonType: "string" },
        rows: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["rowId", "rowStatus"],
            properties: {
              rowId: { bsonType: "int" },
              rawInput: { bsonType: "string" },
              recommendedStandards: { bsonType: "array", items: { bsonType: "string" } },
              finalizedStandardPair: { bsonType: ["string", "null"] },
              rowStatus: { enum: ["pending", "recommended", "approved", "rejected"] },
              identifierGaps: { bsonType: ["string", "null"] }
            }
          }
        }
      }
    }
  }
});

db.createCollection("approved_control_mappings", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "controlId"],
      properties: {
        _id: { bsonType: "string" },
        controlId: { bsonType: "string" },
        sourceJobId: { bsonType: "string" },
        createdAt: { bsonType: ["string", "date"] }
      }
    }
  }
});

// ---- Vector Search collections (one embedding per chunk) -------------------
// Generic validator reused for policy_chunks / standard_chunks /
// control_chunks / risk_record_chunks. embedding is validated by the Atlas
// Vector Search index (numDimensions/similarity), see examples/vector_index.json.

const chunkValidator = {
  $jsonSchema: {
    bsonType: "object",
    required: ["_id", "text", "embedding"],
    properties: {
      _id: { bsonType: "string" },
      policyId: { bsonType: "string" },
      version: { bsonType: "int" },
      text: { bsonType: "string" },
      metadata: { bsonType: "object" },
      embedding: { bsonType: "array", items: { bsonType: "double" } }
    }
  }
};

["policy_chunks", "standard_chunks", "control_chunks", "risk_record_chunks"].forEach(function (name) {
  db.createCollection(name, { validator: chunkValidator });
});

// ---- Agent feedback loop ---------------------------------------------------
// Replaces the derived risk_analysis table; stores prompts, retrieved chunks,
// recommendations, and human approvals for continuous improvement.

db.createCollection("agent_decisions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "prompt", "recommendation"],
      properties: {
        _id: { bsonType: "string" },
        riskRecordId: { bsonType: "string" },
        prompt: { bsonType: "string" },
        retrievedChunks: { bsonType: "array", items: { bsonType: "string" } },
        recommendation: { bsonType: "string" },
        confidence: { bsonType: "double", minimum: 0, maximum: 1 },
        humanApproved: { bsonType: "bool" }
      }
    }
  }
});

print("Created GRC Assistant target collections with $jsonSchema validators.");
