"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

app = typer.Typer(add_completion=False)


# --- Synthetic legacy rows (what a SELECT * would return per table) ----------

LEGACY: dict[str, list[dict[str, Any]]] = {
    "policies": [
        {
            "policy_id": "POL-111",
            "title": "Data Encryption at Rest",
            "version": 4,
            "status": "active",
            "effective_date": "2026-01-01",
            "retired_date": None,
            "body": "All production data stores must encrypt data at rest using AES-256.",
            "owner_team": "Security Engineering",
            "owner_contact": "ciso@example.com",
        }
    ],
    "documents": [
        {
            "document_id": "DOC-9001",
            "policy_id": "POL-111",
            "filename": "encryption-policy-v4.pdf",
            "mime_type": "application/pdf",
            "version": 4,
            "blob_ref": "s3://grc-docs/POL-111/v4.pdf",
        }
    ],
    "risk_records": [
        {
            "risk_record_id": "RISK-7781",
            "title": "Unencrypted backup bucket",
            "severity": "high",
            "likelihood": "medium",
            "business_unit": "Platform",
            "risk_owner": "j.schmitz",
        }
    ],
    "vulnerability_type": [
        {
            "risk_record_id": "RISK-7781",
            "term_source": "scanner",
            "device_scope": "external",
            "is_application": False,
            "ip_simple_id": "10.0.4.12",
            "justification": "Public bucket with no SSE.",
        }
    ],
    "firewall_type": [],  # not applicable to this risk record
    "risk_grouping": [
        {
            "item_set_id": "GRP-1",
            "risk_record_id": "RISK-7781",
            "flow_1": "data",
            "flow_2": "backup",
            "flow_3": "s3",
        }
    ],
    "change_log": [
        {
            "change_record_id": "CHG-1",
            "policy_id": "POL-111",
            "risk_record_id": "RISK-7781",
            "change_description": "Reviewed by risk owner",
            "change_type": "review",
            "created_at": "2026-06-21T09:12:00Z",
            "actor": "j.schmitz",
        }
    ],
    "risk_rules_log": [
        {
            "record_id": "LOG-1",
            "risk_record_id": "RISK-7781",
            "event_class": "created",
            "field_changed": "*",
            "changed_at": "2026-06-20T14:00:00Z",
            "actor": "scanner",
        }
    ],
    "control_refs": {"RISK-7781": ["111.1.01"]},
    "jobs": [
        {
            "job_id": "JOB-501",
            "status": "complete",
            "progress": 100,
            "control_filename": "controls_q2.csv",
            "standards_filename": "standards_q2.csv",
        }
    ],
    "job_rows": [
        {
            "job_id": "JOB-501",
            "row_id": 1,
            "raw_input": "Encrypt backups",
            "recommended_standards": ["111.1.1"],
            "finalized_standard_pair": "111.1.01",
            "row_status": "approved",
            "identifier_gaps": None,
        }
    ],
}


def convert_policies(rows, documents) -> list[dict]:
    docs_by_policy: dict[str, list[dict]] = {}
    for d in documents:
        docs_by_policy.setdefault(d["policy_id"], []).append(
            {
                "documentId": d["document_id"],
                "filename": d["filename"],
                "mimeType": d["mime_type"],
                "version": d["version"],
                "blobRef": d["blob_ref"],
            }
        )
    out = []
    for p in rows:
        out.append(
            {
                "_id": p["policy_id"],
                "title": p["title"],
                "version": p["version"],
                "status": p["status"],
                "effectiveDate": p["effective_date"],
                "retiredDate": p["retired_date"],
                "owner": {"team": p["owner_team"], "contact": p["owner_contact"]},
                "body": p["body"],
                "attachments": docs_by_policy.get(p["policy_id"], []),
            }
        )
    return out


def convert_risk_records(legacy) -> list[dict]:
    by_id_vuln = {r["risk_record_id"]: r for r in legacy["vulnerability_type"]}
    by_id_fw = {r["risk_record_id"]: r for r in legacy["firewall_type"]}
    grouping = {r["risk_record_id"]: r for r in legacy["risk_grouping"]}

    # Merge both log tables into one chronological auditLog per risk record.
    audit: dict[str, list[dict]] = {}
    for r in legacy["risk_rules_log"]:
        audit.setdefault(r["risk_record_id"], []).append(
            {"ts": r["changed_at"], "actor": r["actor"], "action": r["event_class"], "source": "risk_rules_log"}
        )
    for c in legacy["change_log"]:
        if c.get("risk_record_id"):
            audit.setdefault(c["risk_record_id"], []).append(
                {"ts": c["created_at"], "actor": c["actor"], "action": c["change_type"], "source": "change_log"}
            )
    for entries in audit.values():
        entries.sort(key=lambda e: e["ts"])

    out = []
    for r in legacy["risk_records"]:
        rid = r["risk_record_id"]
        type_details = None
        if rid in by_id_vuln:
            v = by_id_vuln[rid]
            type_details = {
                "type": "vulnerability",
                "termSource": v["term_source"],
                "deviceScope": v["device_scope"],
                "isApplication": v["is_application"],
                "asset": v.get("ip_simple_id"),
            }
        elif rid in by_id_fw:
            f = by_id_fw[rid]
            type_details = {
                "type": "firewall",
                "protocolsUsed": f["protocols_used"],
                "connectionScope": f["connection_scope"],
            }
        g = grouping.get(rid, {})
        out.append(
            {
                "_id": rid,
                "title": r["title"],
                "classification": {
                    "severity": r["severity"],
                    "likelihood": r["likelihood"],
                    "grouping": {k: g[k] for k in ("flow_1", "flow_2", "flow_3") if k in g},
                },
                "typeDetails": type_details,
                "policyRefs": ["POL-111"],
                "controlRefs": legacy["control_refs"].get(rid, []),
                "businessUnit": r["business_unit"],
                "riskOwner": r["risk_owner"],
                "auditLog": audit.get(rid, []),
            }
        )
    return out


def convert_mapping_jobs(jobs, job_rows) -> list[dict]:
    rows_by_job: dict[str, list[dict]] = {}
    for r in job_rows:
        rows_by_job.setdefault(r["job_id"], []).append(
            {
                "rowId": r["row_id"],
                "rawInput": r["raw_input"],
                "recommendedStandards": r["recommended_standards"],
                "finalizedStandardPair": r["finalized_standard_pair"],
                "rowStatus": r["row_status"],
                "identifierGaps": r["identifier_gaps"],
            }
        )
    out = []
    for j in jobs:
        out.append(
            {
                "_id": j["job_id"],
                "status": j["status"],
                "progress": j["progress"],
                "controlFilename": j["control_filename"],
                "standardsFilename": j["standards_filename"],
                "rows": rows_by_job.get(j["job_id"], []),
            }
        )
    return out


def build_collections() -> dict[str, list[dict]]:
    return {
        "policies": convert_policies(LEGACY["policies"], LEGACY["documents"]),
        "risk_records": convert_risk_records(LEGACY),
        "mapping_jobs": convert_mapping_jobs(LEGACY["jobs"], LEGACY["job_rows"]),
    }


@app.command()
def main(
    write: bool = typer.Option(False, "--write", help="Upsert converted docs into MongoDB Atlas."),
):
    collections = build_collections()

    if not write:
        typer.echo(json.dumps(collections, indent=2))
        return

    try:
        from pymongo import MongoClient
    except ImportError:
        typer.echo("pymongo not installed. Run: pip install -r requirements.txt", err=True)
        raise typer.Exit(1)

    uri = os.getenv("MONGODB_URI")
    if not uri:
        typer.echo("MONGODB_URI not set. Copy .env.example to .env first.", err=True)
        raise typer.Exit(1)

    client = MongoClient(uri)
    db = client[os.getenv("DB_NAME", "grc_assistant")]
    for name, docs in collections.items():
        for doc in docs:
            db[name].replace_one({"_id": doc["_id"]}, doc, upsert=True)
        typer.echo(f"upserted {len(docs)} -> {name}")
    client.close()


if __name__ == "__main__":
    app()
