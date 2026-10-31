import os
import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path and load .env
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))
load_dotenv(backend_dir / ".env")

from app.core.database import SessionLocal, engine, text
from app.models.driver import Driver

def migrate_and_insert():
    with engine.connect() as conn:
        # 1. Add type column if it doesn't exist
        conn.execute(text("ALTER TABLE dc_drivers ADD COLUMN IF NOT EXISTS type VARCHAR(50) DEFAULT 'Driver';"))
        conn.commit()
        print("Column 'type' verified in dc_drivers.")

        # 2. Ensure all existing drivers have type='Driver'
        conn.execute(text("UPDATE dc_drivers SET type = 'Driver' WHERE type IS NULL;"))
        conn.commit()
        print("Existing drivers set to type='Driver'.")

    db = SessionLocal()
    try:
        new_people = [
            {
                "full_name": "Nadia Azam",
                "type": "Passenger",
                "callsign": "P1",
                "safeguarding_expiry": datetime.date(2029, 7, 22),
                "dbs_update_service_expiry": datetime.date(2027, 9, 8),
                "dbs_certificate_number": "18465545274",
                "notes": "Card Type: Passenger"
            },
            {
                "full_name": "Suddaf Begum",
                "type": "Passenger",
                "callsign": "P2",
                "safeguarding_expiry": datetime.date(2027, 8, 2),
                "dbs_update_service_expiry": datetime.date(2027, 4, 30),
                "dbs_certificate_number": "17336573614",
                "notes": "Card Type: Passenger"
            },
            {
                "full_name": "Georgi Chernev",
                "type": "Driver",
                "callsign": "241",
                "safeguarding_expiry": datetime.date(2028, 4, 10),
                "dbs_update_service_expiry": datetime.date(2027, 7, 11),
                "dbs_certificate_number": "18864964923",
                "notes": "Card Type: Driver"
            },
            {
                "full_name": "Angela Topliss",
                "type": "Passenger",
                "callsign": "P3",
                "safeguarding_expiry": datetime.date(2027, 8, 16),
                "dbs_update_service_expiry": datetime.date(2027, 8, 7),
                "dbs_certificate_number": "18901632932",
                "notes": "Card Type: Passenger"
            },
            {
                "full_name": "Loraine Farley",
                "type": "Passenger",
                "callsign": "P4",
                "safeguarding_expiry": datetime.date(2027, 8, 15),
                "dbs_update_service_expiry": datetime.date(2027, 10, 10),
                "dbs_certificate_number": "16760977001",
                "notes": "Card Type: Passenger"
            }
        ]

        for p in new_people:
            # Check if person already exists by name
            existing = db.query(Driver).filter(Driver.full_name == p["full_name"]).first()
            if existing:
                print(f"Updating existing record: {p['full_name']}")
                existing.type = p["type"]
                existing.callsign = p["callsign"]
                existing.safeguarding_expiry = p["safeguarding_expiry"]
                existing.dbs_update_service_expiry = p["dbs_update_service_expiry"]
                existing.dbs_certificate_number = p["dbs_certificate_number"]
                existing.notes = p["notes"]
            else:
                print(f"Adding new record: {p['full_name']} ({p['type']} #{p['callsign']})")
                driver = Driver(
                    full_name=p["full_name"],
                    type=p["type"],
                    callsign=p["callsign"],
                    safeguarding_expiry=p["safeguarding_expiry"],
                    dbs_update_service_expiry=p["dbs_update_service_expiry"],
                    dbs_certificate_number=p["dbs_certificate_number"],
                    notes=p["notes"],
                    is_active=True
                )
                db.add(driver)

        db.commit()
        print("\nAll 5 records successfully inserted/updated!")

        total = db.query(Driver).count()
        drivers_count = db.query(Driver).filter(Driver.type == "Driver").count()
        passengers_count = db.query(Driver).filter(Driver.type == "Passenger").count()
        print(f"Total fleet roster: {total} (Drivers: {drivers_count}, Passengers: {passengers_count})")

    except Exception as e:
        db.rollback()
        print("Error:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_and_insert()
