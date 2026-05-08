TaskFlow - Team Task Manager
============================

A full-stack web app for managing team projects and tasks with role-based access control.
Built with Python Flask, PostgreSQL, and vanilla JavaScript. Deployed on Railway.

Roles:
  Admin  - Creates projects, adds members, creates/assigns/deletes tasks
  Member - Views assigned projects, updates status of own tasks

Main Features:
  - Signup and login with JWT authentication
  - Admin and Member role-based access
  - Project creation and team member management by email
  - Task creation, assignment, and status tracking (Todo / In Progress / Done)
  - Due dates with overdue detection
  - Dashboard showing project/task stats

Tech Stack:
  Backend    : Python 3.11, Flask 3.0, Gunicorn
  Database   : PostgreSQL (Railway), SQLite (local fallback)
  ORM        : Flask-SQLAlchemy / SQLAlchemy 2.0
  Auth       : Flask-JWT-Extended
  Frontend   : HTML5, CSS3, Vanilla JavaScript
  Deployment : Railway

How to Run Locally:
  1. python -m venv venv
  2. venv\Scripts\activate  (Windows) or source venv/bin/activate (Mac/Linux)
  3. pip install -r requirements.txt
  4. copy .env.example .env
  5. python app.py
  6. Open http://localhost:5000

Environment Variables (set in Railway → Service → Variables):
  DATABASE_URL    - Auto-provided by Railway PostgreSQL plugin
  SECRET_KEY      - Long random string (32+ chars)
  JWT_SECRET_KEY  - Long random string (32+ chars)
  FLASK_DEBUG     - false

Railway Deployment Steps:
  1. Push code to GitHub
  2. Railway → New Project → Deploy from GitHub
  3. Add PostgreSQL plugin (Railway sets DATABASE_URL automatically)
  4. Add SECRET_KEY and JWT_SECRET_KEY in Variables
  5. Railway auto-deploys on push
  6. Generate domain: Service → Settings → Networking → Generate Domain

API Routes:
  POST   /api/auth/signup
  POST   /api/auth/login
  POST   /api/auth/logout
  GET    /api/projects
  POST   /api/projects
  GET    /api/projects/<id>
  POST   /api/projects/<id>/members
  DELETE /api/projects/<id>/members/<user_id>
  GET    /api/projects/stats
  POST   /api/tasks
  GET    /api/tasks/<project_id>
  PUT    /api/tasks/<task_id>
  DELETE /api/tasks/<task_id>
  GET    /api/tasks/my
  GET    /api/health
