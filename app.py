import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from flask_cors import CORS

from backend.config import Config
from backend.models import db, User, Project, Task
from backend.routes.auth import auth_bp
from backend.routes.projects import projects_bp
from backend.routes.tasks import tasks_bp

# ─── Configure Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )
    app.config.from_object(Config)

    # Redundant safety: fix DATABASE_URL at runtime too (handles env var set after import)
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://", 1)

    # ─── Extensions ──────────────────────────────────────────────────────────
    db.init_app(app)
    jwt = JWTManager(app)
    
    # CORS Configuration - restrict in production
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    if cors_origins != "*":
        cors_origins = [origin.strip() for origin in cors_origins.split(",")]
    
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # ─── JWT Error Handlers ────────────────────────────────────────────────────
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning("Token expired for user: %s", jwt_payload.get("sub"))
        return jsonify({"error": "Token has expired. Please login again."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.warning("Invalid token attempt: %s", str(error))
        return jsonify({"error": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authorization token required"}), 401

    # ─── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")

    # ─── Frontend Page Routes ───────────────────────────────────────────────────
    @app.route("/")
    @app.route("/login")
    def login_page():
        return send_from_directory(app.template_folder, "login.html")

    @app.route("/signup")
    def signup_page():
        return send_from_directory(app.template_folder, "signup.html")

    @app.route("/dashboard")
    @app.route("/admin/dashboard")
    @app.route("/member/dashboard")
    def dashboard_page():
        return send_from_directory(app.template_folder, "dashboard.html")

    @app.route("/project")
    def project_page():
        return send_from_directory(app.template_folder, "project.html")

    # ─── Dashboard API ──────────────────────────────────────────────────────────
    @app.route("/api/dashboard/admin", methods=["GET"])
    @jwt_required()
    def admin_dashboard_data():
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        try:
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            projects = Project.query.filter_by(created_by=user.id).all()
            all_users = User.query.count()
            all_tasks = (
                db.session.query(Task)
                .join(Project)
                .filter(Project.created_by == user.id)
                .all()
            )
            overdue_tasks = [t for t in all_tasks if t.is_overdue]
            return jsonify({
                "total_projects": len(projects),
                "total_users": all_users,
                "total_tasks": len(all_tasks),
                "overdue_tasks": len(overdue_tasks),
                "recent_projects": [p.to_dict() for p in projects[-5:]],
            }), 200
        except Exception as e:
            logger.error(f"Admin dashboard error: {str(e)}")
            return jsonify({"error": f"Failed to fetch dashboard data: {str(e)}"}), 500

    @app.route("/api/dashboard/member", methods=["GET"])
    @jwt_required()
    def member_dashboard_data():
        user_id = int(get_jwt_identity())
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            assigned_tasks = Task.query.filter_by(assigned_to=user_id).all()
            return jsonify({
                "assigned_tasks": len(assigned_tasks),
                "todo": sum(1 for t in assigned_tasks if t.status == "todo"),
                "in_progress": sum(1 for t in assigned_tasks if t.status == "in_progress"),
                "done": sum(1 for t in assigned_tasks if t.status == "done"),
                "overdue": sum(1 for t in assigned_tasks if t.is_overdue),
                "tasks": [t.to_dict() for t in assigned_tasks[:10]],
            }), 200
        except Exception as e:
            logger.error(f"Member dashboard error: {str(e)}")
            return jsonify({"error": f"Failed to fetch dashboard data: {str(e)}"}), 500

    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        return jsonify({"message": "Logged out successfully"}), 200

    # ─── Health Check ───────────────────────────────────────────────────────────
    @app.route("/api/health")
    def health():
        try:
            # Simple database health check
            db.session.execute("SELECT 1")
            return jsonify({
                "status": "healthy",
                "message": "Team Task Manager API is running",
                "version": "1.0.0"
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                "status": "unhealthy",
                "message": "Database connection failed"
            }), 503

    # ─── Global Error Handlers ──────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden - insufficient permissions"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    # ─── DB Initialization ──────────────────────────────────────────────────────
    # Database tables are created by init_db.py during Railway release phase
    # This is just a safety check to ensure tables exist
    with app.app_context():
        try:
            db.create_all()
            logger.info("✓ Database tables verified/created")
        except Exception as e:
            logger.warning(f"Database tables may already exist: {str(e)}")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
    )
