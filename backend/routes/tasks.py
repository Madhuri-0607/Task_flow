from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from backend.models import db, Task, Project, User
from datetime import datetime
import logging

tasks_bp = Blueprint("tasks", __name__)
logger = logging.getLogger(__name__)

VALID_STATUSES = ("todo", "in_progress", "done")


def current_user():
    return User.query.get(int(get_jwt_identity()))


def parse_assignee(value, project):
    """Parse and validate assignee ID"""
    if value in (None, ""):
        return None, None

    try:
        assignee_id = int(value)
    except (TypeError, ValueError):
        return None, ("assigned_to must be a valid user ID", 400)

    assignee = User.query.get(assignee_id)
    if not assignee:
        return None, ("Assigned user not found", 404)

    member_ids = {member.id for member in project.team_members}
    if assignee_id not in member_ids:
        return None, ("Assigned user must be a member of the project", 400)

    return assignee_id, None


@tasks_bp.route("/my", methods=["GET"])
@jwt_required()
def my_tasks():
    """Get current user's assigned tasks"""
    user = current_user()

    try:
        tasks = Task.query.filter_by(assigned_to=user.id).order_by(Task.due_date.asc()).all()

        # Group by status
        todo_tasks = [t for t in tasks if t.status == "todo"]
        in_progress = [t for t in tasks if t.status == "in_progress"]
        done_tasks = [t for t in tasks if t.status == "done"]

        # Count overdue
        overdue_count = sum(1 for t in tasks if t.is_overdue)

        return jsonify({
            "tasks": [t.to_dict() for t in tasks],
            "by_status": {
                "todo": len(todo_tasks),
                "in_progress": len(in_progress),
                "done": len(done_tasks),
            },
            "overdue_count": overdue_count,
            "count": len(tasks),
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500


@tasks_bp.route("", methods=["POST"])
@jwt_required()
def create_task():
    """Create task - ADMIN & PROJECT OWNER ONLY"""
    claims = get_jwt()
    user = current_user()

    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    project_id = data.get("project_id")

    if not title:
        return jsonify({"error": "Task title is required"}), 400
    if len(title) < 3:
        return jsonify({"error": "Task title must be at least 3 characters"}), 400
    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        if project.created_by != user.id:
            return jsonify({"error": "Only the project owner can create tasks"}), 403

        # Validate assignee
        assigned_to, assignee_error = parse_assignee(data.get("assigned_to"), project)
        if assignee_error:
            message, status_code = assignee_error
            return jsonify({"error": message}), status_code

        # Parse and validate due_date
        due_date = None
        if data.get("due_date"):
            try:
                due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
                if due_date < datetime.now().date():
                    return jsonify({"error": "Due date cannot be in the past"}), 400
            except ValueError:
                return jsonify({"error": "Due date format must be YYYY-MM-DD"}), 400

        status = (data.get("status") or "todo").lower()
        if status not in VALID_STATUSES:
            return jsonify({"error": f"Status must be one of {VALID_STATUSES}"}), 400

        task = Task(
            title=title,
            description=data.get("description", "").strip(),
            project_id=project_id,
            assigned_to=assigned_to,
            status=status,
            due_date=due_date,
        )
        db.session.add(task)
        db.session.commit()

        return jsonify({
            "message": "Task created successfully",
            "task": task.to_dict(),
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create task: {str(e)}"}), 500


@tasks_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required()
def list_tasks(project_id):
    """List all tasks in a project"""
    user = current_user()

    try:
        project = Project.query.get_or_404(project_id)

        # Check access
        user_ids = [m.id for m in project.team_members]
        if user.id not in user_ids and project.created_by != user.id:
            return jsonify({"error": "Access denied"}), 403

        tasks = Task.query.filter_by(project_id=project_id).order_by(Task.created_at.desc()).all()
        return jsonify({
            "tasks": [t.to_dict() for t in tasks],
            "count": len(tasks),
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    """Update task - Admin can update all, members can update status of own tasks"""
    user = current_user()
    claims = get_jwt()

    try:
        task = Task.query.get_or_404(task_id)
        project = Project.query.get(task.project_id)

        # Check access
        if claims.get("role") == "admin":
            if project.created_by != user.id:
                return jsonify({"error": "Only the project owner can update tasks"}), 403
        else:
            # Members can only update status of their own tasks
            if task.assigned_to != user.id:
                return jsonify({"error": "You can only update your own tasks"}), 403

        data = request.get_json(silent=True) or {}

        # Anyone can update their own task status
        if "status" in data:
            status = (data["status"] or "").lower()
            if status not in VALID_STATUSES:
                return jsonify({"error": f"Status must be one of {VALID_STATUSES}"}), 400
            task.status = status

        # Only admins can update other fields
        if claims.get("role") == "admin":
            if "title" in data:
                title = (data["title"] or "").strip()
                if not title:
                    return jsonify({"error": "Task title cannot be empty"}), 400
                task.title = title

            if "description" in data:
                task.description = (data["description"] or "").strip()

            if "assigned_to" in data:
                assigned_to, assignee_error = parse_assignee(data["assigned_to"], project)
                if assignee_error:
                    message, status_code = assignee_error
                    return jsonify({"error": message}), status_code
                task.assigned_to = assigned_to

            if "due_date" in data:
                if data["due_date"]:
                    try:
                        due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
                        if due_date < datetime.now().date():
                            return jsonify({"error": "Due date cannot be in the past"}), 400
                        task.due_date = due_date
                    except ValueError:
                        return jsonify({"error": "Due date format must be YYYY-MM-DD"}), 400
                else:
                    task.due_date = None

        db.session.commit()
        return jsonify({
            "message": "Task updated successfully",
            "task": task.to_dict(),
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update task: {str(e)}"}), 500


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    """Delete task - ADMIN & PROJECT OWNER ONLY"""
    claims = get_jwt()
    user = current_user()

    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    try:
        task = Task.query.get_or_404(task_id)
        project = Project.query.get(task.project_id)

        if project.created_by != user.id:
            return jsonify({"error": "Only the project owner can delete tasks"}), 403

        db.session.delete(task)
        db.session.commit()

        return jsonify({"message": "Task deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete task: {str(e)}"}), 500



