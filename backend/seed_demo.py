"""Seed a demo PHC staff account and sample consultations (idempotent).

Run from backend/:  python seed_demo.py
Login afterwards:   demo@phc.in / Demo@12345  (Mulki PHC)
"""
import os

from app import create_app
from extensions import db
from ml import inference as ml_inference
from models.consent import Consent
from models.consultation import Consultation
from models.patient import Patient
from models.phc_staff import PhcStaff
from PIL import Image
from utils.image_handler import save_image

SAMPLES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "sample_images")
)


def main():
    app = create_app()
    with app.app_context():
        staff = db.session.query(PhcStaff).filter_by(email="demo@phc.in").first()
        if staff is None:
            staff = PhcStaff(
                phc_name="Mulki PHC",
                staff_name="Demo Nurse",
                email="demo@phc.in",
                phone="+919000000001",
            )
            staff.staff_id = "STF-DEMO01"
            staff.set_password("Demo@12345")
            db.session.add(staff)
            db.session.commit()
            print("Created demo staff: demo@phc.in / Demo@12345 (Mulki PHC)")
        else:
            print("Demo staff already exists: demo@phc.in / Demo@12345")

        if not os.path.isdir(SAMPLES_DIR):
            print("No sample_images directory found; skipping sample consultations")
            return

        for index, filename in enumerate(sorted(os.listdir(SAMPLES_DIR)), start=1):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            contact = f"+91900000001{index:02d}"
            if db.session.query(Patient).filter_by(contact_number=contact).first():
                continue  # already seeded

            patient = Patient(
                phc_id=staff.id,
                age=30 + index * 7,
                gender="Female" if index % 2 else "Male",
                location="Mulki",
                contact_number=contact,
            )
            db.session.add(patient)
            db.session.flush()
            db.session.add(
                Consent(
                    patient_id=patient.id,
                    phc_id=staff.id,
                    consent_to_screening=True,
                    consent_to_data_storage=True,
                )
            )

            img = Image.open(os.path.join(SAMPLES_DIR, filename)).convert("RGB")
            result = ml_inference.predict(img)
            consultation = Consultation(
                patient_id=patient.id,
                phc_id=staff.id,
                image_path=save_image(img, app.config["UPLOAD_FOLDER"]),
                model_mode=result["mode"],
                risk_level=result["risk_level"],
                confidence_scores=result["confidence"],
                condition_type=result["condition_type"],
                staff_notes=f"Seeded sample ({filename})",
            )
            db.session.add(consultation)
            db.session.commit()
            print(
                f"Seeded patient #{patient.id} -> consultation #{consultation.id} "
                f"({consultation.risk_level}, mode={consultation.model_mode})"
            )

        db.session.commit()


if __name__ == "__main__":
    main()
