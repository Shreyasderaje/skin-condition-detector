"""Registers all API blueprints under the /api prefix."""


def register_routes(app):
    from routes.analytics import analytics_bp
    from routes.auth import auth_bp
    from routes.compliance import compliance_bp
    from routes.consultations import consultations_bp
    from routes.patients import patients_bp

    for bp in (auth_bp, patients_bp, consultations_bp, analytics_bp, compliance_bp):
        app.register_blueprint(bp, url_prefix="/api")
