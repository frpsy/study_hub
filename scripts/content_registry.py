"""Read and validate the canonical study data without changing editorial content.

One-sentence key takeaways live in data/mini_courses.json. Old manuscripts
(5-minute summaries, mini-course fields) are kept in docs/archive/manuscripts and are not read.
"""
import json
from pathlib import Path

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def catalog_leads(root: Path):
    """{lecture id: one-sentence takeaway}. data/mini_courses.json must cover exactly the lectures in lectures.json."""
    courses=load_json(root/"data/mini_courses.json")
    ids={r["id"] for r in load_json(root/"lectures.json")}
    if set(courses)!=ids:
        raise ValueError(f"Lead coverage mismatch; missing={sorted(ids-set(courses))}, extra={sorted(set(courses)-ids)}")
    return {k:v["lead"] for k,v in courses.items()}

def validate_catalog(root: Path):
    """Return actionable validation errors for the hand-edited source records."""
    errors=[]
    rows=load_json(root/"lectures.json")
    materials=load_json(root/"materials.json") if (root/"materials.json").exists() else []
    if not isinstance(rows,list) or not isinstance(materials,list):
        return ["Lectures and materials registries must be arrays"]
    ids=[]
    for record in rows+materials:
        if not isinstance(record,dict):
            errors.append("Registry entry must be an object")
            continue
        key=record.get("id")
        if not isinstance(key,str) or not key.strip():
            errors.append("Registry entry missing stable string id")
            continue
        ids.append(key)
        for field in (("title","creator","description") if record in rows else ("title","creator")):
            if not isinstance(record.get(field),str) or not record[field].strip():
                errors.append(f"{key}: missing {field}")
        if not isinstance(record.get("tags"),list) or not record["tags"] or any(not isinstance(tag,str) or not tag.strip() for tag in record["tags"]):
            errors.append(f"{key}: tags must be a nonempty string array")
    if len(ids)!=len(set(ids)):
        errors.append("Duplicate stable content ID in registry")
    return errors

if __name__ == "__main__":
    import sys
    root=Path(__file__).resolve().parents[1]
    errors=validate_catalog(root)
    try:
        catalog_leads(root)
    except (ValueError,KeyError,TypeError) as exc:
        errors.append(str(exc))
    print("\\n".join(errors) if errors else "PASS: catalog and canonical leads")
    sys.exit(bool(errors))
