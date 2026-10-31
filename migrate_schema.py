from app.core.database import engine, text

with engine.connect() as conn:
    print("Adding columns to dc_drivers...")
    conn.execute(text("ALTER TABLE dc_drivers ADD COLUMN IF NOT EXISTS driving_licence_expiry DATE;"))
    conn.execute(text("ALTER TABLE dc_drivers ADD COLUMN IF NOT EXISTS passport_expiry DATE;"))
    conn.execute(text("ALTER TABLE dc_drivers ADD COLUMN IF NOT EXISTS driver_id_badge_expiry DATE;"))
    conn.commit()
    print("Columns added successfully.")

    # Remove council and custom doc types from dc_document_types
    print("Cleaning dc_document_types...")
    conn.execute(text("DELETE FROM dc_document_types WHERE code IN ('scc_badge', 'dcc_clearance_letter', 'clearance_letter') OR is_custom = TRUE;"))
    
    # Ensure standard document types exist with correct requires_expiry flags
    standard_types = [
        ("driving_licence", "Driving Licence", "Full UK driving licence (front and back)", True, False, True),
        ("passport", "Passport", "Valid passport biometric page", True, False, True),
        ("driver_id_badge", "Driver ID Badge", "Official driver identification badge", True, False, True),
        ("dbs_update_service_proof", "DBS Update Service Proof", "Proof of active registration with DBS Update Service", True, False, True),
        ("safeguarding_certificate", "Safeguarding Certificate", "Child and adult safeguarding training certification", True, True, True),
        ("first_aid_certificate", "First Aid Certificate", "Emergency First Aid at Work certificate", True, True, True),
        ("autism_awareness_certificate", "Autism Awareness Certificate", "Autism and neurodiversity awareness certificate", False, False, False),
        ("dbs_certificate", "DBS Certificate", "Enhanced DBS Certificate (multi-page support)", False, True, True),
        ("proof_of_address", "Proof of Address", "Recent utility bill or bank statement (within 3 months)", False, True, True),
        ("proof_of_national_insurance", "Proof of National Insurance Number", "Official NI number document or card", False, False, True),
        ("passport_size_photograph", "Passport-size Photograph", "Recent passport-style photograph", False, False, True),
    ]

    for code, name, desc, req_exp, req_iss, is_mand in standard_types:
        row = conn.execute(text("SELECT id FROM dc_document_types WHERE code = :code"), {"code": code}).first()
        if row:
            conn.execute(text("""
                UPDATE dc_document_types 
                SET name = :name, description = :desc, requires_expiry = :req_exp, 
                    requires_issue_date = :req_iss, is_mandatory = :is_mand, is_custom = FALSE, council_tag = 'NONE'
                WHERE code = :code
            """), {"name": name, "desc": desc, "req_exp": req_exp, "req_iss": req_iss, "is_mand": is_mand, "code": code})
        else:
            conn.execute(text("""
                INSERT INTO dc_document_types (code, name, description, requires_expiry, requires_issue_date, is_mandatory, is_custom, council_tag)
                VALUES (:code, :name, :desc, :req_exp, :req_iss, :is_mand, FALSE, 'NONE')
            """), {"code": code, "name": name, "desc": desc, "req_exp": req_exp, "req_iss": req_iss, "is_mand": is_mand})

    conn.commit()
    print("Document types aligned successfully.")

    res = conn.execute(text("SELECT code, name, requires_expiry, is_mandatory FROM dc_document_types ORDER BY id;"))
    for r in res.fetchall():
        print(f"  {r[0]:<30} | {r[1]:<35} | Expiry: {r[2]} | Mandatory: {r[3]}")
