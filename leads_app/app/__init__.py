"""Flask app factory for leads_app."""

from __future__ import annotations

from .config import Config


def create_app():
    from flask import Blueprint, Flask
    from .auth import login_manager
    from .routes import pages, api, auth as auth_routes

    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)
    app.config['APPLICATION_ROOT'] = Config.APPLICATION_ROOT

    login_manager.init_app(app)
    login_manager.login_view = 'leads.auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register blueprint with /leads prefix
    leads_bp = Blueprint('leads', __name__, url_prefix=Config.APPLICATION_ROOT)
    leads_bp.register_blueprint(pages.bp)
    leads_bp.register_blueprint(api.bp)
    leads_bp.register_blueprint(auth_routes.bp)

    @leads_bp.route('/health')
    def leads_health():
        return "OK"

    app.register_blueprint(leads_bp)

    @app.route('/health')
    def health():
        return "OK"

    return app
