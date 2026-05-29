import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import io
from backend.database import get_db
from backend.models import Lead, LeadImport

router = APIRouter()

VALID_STAGES = {"new", "contacted", "proposal", "won", "lost"}


def row_to_lead(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"] or "",
        "email": row["email"] or "",
        "phone": row["phone"] or "",
        "company": row["company"] or "",
        "role": row["role"] or "",
        "value": row["value"] or "",
        "source": row["source"] or "Manual",
        "stage": row["stage"] or "new",
        "notes": row["notes"] or "",
        "followUp": row["follow_up"] or "",
        "createdAt": row["created_at"] or "",
    }


# ── GET all leads ──────────────────────────────────────────────────────────────
@router.get("")
def list_leads(stage: Optional[str] = None, source: Optional[str] = None, q: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if stage and stage != "all":
        query += " AND stage = ?"
        params.append(stage)
    if source and source != "all":
        query += " AND source = ?"
        params.append(source)
    if q:
        query += " AND (name LIKE ? OR email LIKE ? OR company LIKE ? OR notes LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like, like])
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_lead(r) for r in rows]


# ── GET single lead ────────────────────────────────────────────────────────────
@router.get("/{lead_id}")
def get_lead(lead_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return row_to_lead(row)


# ── POST create lead ───────────────────────────────────────────────────────────
@router.post("", status_code=201)
def create_lead(lead: Lead):
    lead_id = lead.id or uuid.uuid4().hex[:12]
    stage = lead.stage if lead.stage in VALID_STAGES else "new"
    conn = get_db()
    conn.execute("""
        INSERT INTO leads (id, name, email, phone, company, role, value, source, stage, notes, follow_up)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead_id, lead.name, lead.email, lead.phone, lead.company,
        lead.role, lead.value, lead.source, stage, lead.notes, lead.followUp,
    ))
    conn.commit()
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    return row_to_lead(row)


# ── PUT update lead ────────────────────────────────────────────────────────────
@router.put("/{lead_id}")
def update_lead(lead_id: str, lead: Lead):
    stage = lead.stage if lead.stage in VALID_STAGES else "new"
    conn = get_db()
    result = conn.execute("""
        UPDATE leads SET
            name=?, email=?, phone=?, company=?, role=?,
            value=?, source=?, stage=?, notes=?, follow_up=?,
            updated_at=datetime('now')
        WHERE id=?
    """, (
        lead.name, lead.email, lead.phone, lead.company, lead.role,
        lead.value, lead.source, stage, lead.notes, lead.followUp, lead_id,
    ))
    conn.commit()
    if result.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found")
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    return row_to_lead(row)


# ── DELETE lead ────────────────────────────────────────────────────────────────
@router.delete("/{lead_id}")
def delete_lead(lead_id: str):
    conn = get_db()
    result = conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"ok": True}


# ── POST bulk import ───────────────────────────────────────────────────────────
@router.post("/import/bulk")
def import_leads(payload: LeadImport):
    conn = get_db()
    inserted = 0
    skipped = 0
    for lead in payload.leads:
        lead_id = lead.id or uuid.uuid4().hex[:12]
        stage = lead.stage if lead.stage in VALID_STAGES else "new"
        existing = conn.execute("SELECT id FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute("""
            INSERT INTO leads (id, name, email, phone, company, role, value, source, stage, notes, follow_up)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_id, lead.name, lead.email, lead.phone, lead.company,
            lead.role, lead.value, lead.source, stage, lead.notes, lead.followUp,
        ))
        inserted += 1
    conn.commit()
    conn.close()
    return {"inserted": inserted, "skipped": skipped}


# ── GET export JSON ────────────────────────────────────────────────────────────
@router.get("/export/json")
def export_json():
    conn = get_db()
    rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    conn.close()
    import json
    data = json.dumps([row_to_lead(r) for r in rows], indent=2)
    return StreamingResponse(
        io.BytesIO(data.encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=mintos-leads.json"},
    )


# ── GET export CSV ─────────────────────────────────────────────────────────────
@router.get("/export/csv")
def export_csv():
    conn = get_db()
    rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    conn.close()
    cols = ["id", "name", "email", "phone", "company", "role", "value", "source", "stage", "followUp", "notes", "createdAt"]
    lines = [",".join(cols)]
    for r in rows:
        lead = row_to_lead(r)
        lines.append(",".join(f'"{str(lead.get(c,"")).replace(chr(34), chr(39))}"' for c in cols))
    csv_data = "\n".join(lines)
    return StreamingResponse(
        io.BytesIO(csv_data.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mintos-leads.csv"},
    )
