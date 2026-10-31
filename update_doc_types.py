from app.core.database import SessionLocal, text
from app.services.cache import invalidate_doc_types_cache

db = SessionLocal()
try:
    db.execute(text("UPDATE dc_document_types SET requires_expiry = FALSE WHERE code IN ('passport', 'driving_licence', 'driver_id_badge');"))
    db.commit()
    invalidate_doc_types_cache()
    print("Updated dc_document_types requires_expiry = False for passport, driving_licence, driver_id_badge.")
    res = db.execute(text("SELECT code, name, requires_expiry FROM dc_document_types ORDER BY id;")).fetchall()
    for r in res:
        print(f"  {r[0]:<30} | {r[1]:<35} | Expiry: {r[2]}")
finally:
    db.close()
