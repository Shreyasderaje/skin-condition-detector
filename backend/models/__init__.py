"""Import all models so db.create_all() sees every table."""
from models.audit_log import AuditLog  # noqa: F401
from models.consent import Consent  # noqa: F401
from models.consultation import Consultation  # noqa: F401
from models.patient import Patient  # noqa: F401
from models.phc_staff import PhcStaff  # noqa: F401
