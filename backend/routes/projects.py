from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from backend.models import db, Project, User, Task, project_members
from datetime import datetime
from sqlalchemy import or_
import re
import logging

projects_bp = Blueprint("projects", __name__)
logger = logging.getLogger(__name__)


def current_user():
    return User.query.get(int(get_jwt_identity()))


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@projects_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    """Create a new project - ADMIN ONLY"""
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required to create projects"}), 403

    user = current_user()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()

    if not title:
        return jsonify({"error": "Project title is required"}), 400
    if len(title) < 3:
        return jsonify({"error": "Project title must be at least 3 characters"}), 400

    try:
        project = Project(
            title=title,
            description=description,
            created_by=user.id,
        )
        # Add creator as first member
        project.team_members.append(user)

        # Add additional members by email list
        member_emails = data.get("member_emails", [])
        for email in member_emails:
            email = email.strip().lower()
            if not validate_email(email):
                return jsonify({"error": f"Invalid email: {email}"}), 400
            
            member = User.query.filter_by(email=email).first()
            if not member:
                return jsonify({"error": f"User not found: {email}"}), 404
            if member.id != user.id and member not in project.team_members:
                project.team_members.append(member)

        db.session.add(project)
        db.session.commit()

        return jsonify({
            "message": "Project created successfully",
            "project": project.to_dict(include_members=True),
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create project: {str(e)}"}), 500


@projects_bp.route("", methods=["GET"])
@jwt_required()
def list_projects():
    """List projects - admin sees created, members see assigned"""
    user = current_user()
    claims = get_jwt()

    try:
        if claims.get("role") == "admin":
            # Admins see all projects they created
            projects = Project.query.filter_by(created_by=user.id).order_by(Project.created_at.desc()).all()
        else:
            # Members see projects they're assigned to
            projects = user.projects

        return jsonify({
            "projects": [p.to_dict() for p in projects],
            "count": len(projects),
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch projects: {str(e)}"}), 500


@projects_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    """Get project details with tasks"""
    user = current_user()

    try:
        project = Project.query.get_or_404(project_id)

        # Check if user has access (member or creator)
        if user.id not in [m.id for m in project.team_members] and project.created_by != user.id:
            return jsonify({"error": "Access denied"}), 403

        data = project.to_dict(include_members=True)
        data["tasks"] = [t.to_dict() for t in project.tasks]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch project: {str(e)}"}), 500


@projects_bp.route("/<int:project_id>/members", methods=["POST"])
@jwt_required()
def add_member(project_id):
    """Add member to project - ADMIN & PROJECT OWNER ONLY"""
    claims = get_jwt()
    user = current_user()

    try:
        project = Project.query.get_or_404(project_id)

        # Only project creator can add members
        if project.created_by != user.id:
            return jsonify({"error": "Only the project owner can add members"}), 403

        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()

        if not email:
            return jsonify({"error": "Email is required"}), 400
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        member = User.query.filter_by(email=email).first()
        if not member:
            return jsonify({"error": "User not found"}), 404
        if member.id == user.id:
            return jsonify({"error": "Cannot add yourself again"}), 400

        if member in project.team_members:
            return jsonify({"error": "User is already a member"}), 409

        project.team_members.append(member)
        db.session.commit()

        return jsonify({
            "message": "Member added successfully",
            "project": project.to_dict(include_members=True),
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add member: {str(e)}"}), 500


@projects_bp.route("/<int:project_id>/members/<int:member_id>", methods=["DELETE"])
@jwt_required()
def remove_member(project_id, member_id):
    """Remove member from project - PROJECT OWNER ONLY"""
    user = current_user()

    try:
        project = Project.query.get_or_404(project_id)

        if project.created_by != user.id:
            return jsonify({"error": "Only the project owner can remove members"}), 403

        member = User.query.get_or_404(member_id)

        if member not in project.team_members:
            return jsonify({"error": "User is not a member of this project"}), 404

        project.team_members.remove(member)
        db.session.commit()

        return jsonify({
            "message": "Member removed successfully",
            "project": project.to_dict(include_members=True),
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to remove member: {str(e)}"}), 500


@projects_bp.route("/stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    user = current_user()
    claims = get_jwt()
    today = datetime.utcnow().date()

    if claims.get("role") == "admin":
        projects = Project.query.filter_by(created_by=user.id).all()
        project_ids = [p.id for p in projects]
        tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    else:
        projects = user.projects
        tasks = Task.query.filter_by(assigned_to=user.id).all()

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "done")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    todo = sum(1 for t in tasks if t.status == "todo")
    overdue = sum(
        1 for t in tasks
        if t.is_overdue
    )

    return jsonify({
        "total_projects": len(projects),
        "total_tasks": total,
        "completed": completed,
        "in_progress": in_progress,
        "todo": todo,
        "overdue": overdue,
    }), 200
