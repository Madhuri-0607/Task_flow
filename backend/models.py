from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Many-to-many association table for Project <-> User (team members)
project_members = db.Table(
    "project_members",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")  # admin / member
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    created_projects = db.relationship("Project", back_populates="creator", foreign_keys="Project.created_by")
    assigned_tasks = db.relationship("Task", back_populates="assignee", foreign_keys="Task.assigned_to")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship("User", back_populates="created_projects", foreign_keys=[created_by])
    team_members = db.relationship("User", secondary=project_members, backref="projects")
    tasks = db.relationship("Task", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self, include_members=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_by": self.created_by,
            "creator_name": self.creator.name if self.creator else None,
            "created_at": self.created_at.isoformat(),
            "task_count": len(self.tasks),
        }
        if include_members:
            data["team_members"] = [m.to_dict() for m in self.team_members]
        return data


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="todo")  # todo / in_progress / done
    due_date = db.Column(db.Date, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    project = db.relationship("Project", back_populates="tasks")
    assignee = db.relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_to])

    @property
    def is_overdue(self):
        """Check if task is overdue (due_date has passed and status is not done)"""
        if not self.due_date:
            return False
        return self.due_date < date.today() and self.status != "done"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "assigned_to": self.assigned_to,
            "assignee_name": self.assignee.name if self.assignee else None,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "is_overdue": self.is_overdue,
        }
