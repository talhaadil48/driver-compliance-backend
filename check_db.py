from app.core.database import engine, text

with engine.connect() as conn:
    res = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name LIKE '%dc_%';"))
    print("Tables found:", res.fetchall())
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'dc_drivers';"))
    print("Columns in dc_drivers:", [r[0] for r in res.fetchall()])
    res = conn.execute(text("SELECT code, name, requires_expiry, is_mandatory FROM driver_compliance.dc_document_types;"))
    print("Doc types:", res.fetchall())
