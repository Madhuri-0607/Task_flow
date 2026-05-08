# TaskFlow — Team Task Manager

A full-stack web application for managing team projects and tasks with role-based access control. Built with Python Flask, PostgreSQL, and vanilla JavaScript. Deployed on Railway.

---

## Live Demo
[web-production-a7572.up.railway.app](https://web-production-a7572.up.railway.app/)


how to test after deploying

the link is working in mobile but not in desktop,)**

**Demo credentials:**

| Role   | Email               | Password   |
|--------|---------------------|------------|
| Admin  | admin@123.com      | admin123   |
| Member | hani@123.com     | hani123  |

---

## Features

- **JWT Authentication** — Secure signup/login with token-based sessions
- **Role-Based Access Control** — Admin and Member roles with enforced permissions
- **Project Management** — Admins create projects and manage team membership by email
- **Task Management** — Create, assign, and track tasks with due dates
- **Task Status Tracking** — `Todo`, `In Progress`, `Done` with overdue detection
- **Dashboard** — Real-time stats: total projects, task counts by status, overdue alerts
- **REST API** — Clean JSON API with proper validation and error responses

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.11, Flask 3.0              |
| Database   | PostgreSQL (Railway), SQLite (local) |
| ORM        | Flask-SQLAlchemy / SQLAlchemy 2.0   |
| Auth       | Flask-JWT-Extended                  |
| Server     | Gunicorn                            |
| Frontend   | HTML5, CSS3, Vanilla JavaScript     |
| Deployment | Railway                             |

---

## Project Structure

```
team-task-manager/
├── app.py                    # Application factory & route registration
├── Procfile                  # Railway/Gunicorn process config
├── railway.json              # Railway deployment config
├── nixpacks.toml             # Build config (Python 3.11)
├── runtime.txt               # Python version pin
├── requirements.txt          # Python dependencies
├── init_db.py                # Database initializer (Railway release command)
├── .env.example              # Environment variable template
├── backend/
│   ├── config.py             # App configuration & DB URL handling
│   ├── models.py             # SQLAlchemy models: User, Project, Task
│   └── routes/
│       ├── auth.py           # POST /api/auth/signup, /api/auth/login
│       ├── projects.py       # CRUD + member management
│       └── tasks.py          # CRUD + status updates
└── frontend/
    ├── templates/
    │   ├── login.html
    │   ├── signup.html
    │   ├── dashboard.html
    │   └── project.html
    └── static/
        ├── css/
        │   ├── app.css
        │   └── auth.css
        └── js/
            └── app.js
```

---

## Role Permissions

| Action                       | Admin              | Member             |
|------------------------------|--------------------|--------------------|
| Create project               | ✅ Yes             | ❌ No              |
| View projects                | ✅ Own projects    | ✅ If added as member |
| Add/remove team members      | ✅ Own projects    | ❌ No              |
| Create/delete tasks          | ✅ Own projects    | ❌ No              |
| Assign tasks                 | ✅ To project members | ❌ No           |
| Update task status           | ✅ Yes             | ✅ Own tasks only  |
| View dashboard               | ✅ Full stats      | ✅ Own task stats  |

---

## API Reference

### Authentication

```
POST /api/auth/signup     { name, email, password }
POST /api/auth/login      { email, password }
POST /api/auth/logout
```

### Projects

```
GET    /api/projects                        List projects (role-filtered)
POST   /api/projects                        Create project [Admin]
GET    /api/projects/<id>                   Get project + tasks
POST   /api/projects/<id>/members           Add member by email [Admin]
DELETE /api/projects/<id>/members/<user_id> Remove member [Admin]
GET    /api/projects/stats                  Dashboard stats
```

### Tasks

```
POST   /api/tasks                   Create task [Admin]
GET    /api/tasks/<project_id>      List tasks in project
PUT    /api/tasks/<task_id>         Update task
DELETE /api/tasks/<task_id>         Delete task [Admin]
GET    /api/tasks/my                My assigned tasks
```

---

## Running Locally

```bash
# 1. Clone and enter the project
git clone https://github.com/your-username/team-task-manager.git
cd team-task-manager

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env — for local dev, you can leave DATABASE_URL blank to use SQLite

# 5. Run the app
python app.py
```

Visit: [http://localhost:5000](http://localhost:5000)

---

## Deploying to Railway

### Prerequisites
- A [Railway](https://railway.app) account
- The project pushed to a GitHub repository

### Steps

**1. Create Railway project**
- Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
- Select your repository

**2. Add PostgreSQL**
- In your Railway project → **+ New** → **Database** → **Add PostgreSQL**
- Railway will auto-set `DATABASE_URL` in your service environment

**3. Set environment variables**
In your **app service** → **Variables**, add:

```
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
FLASK_DEBUG=false
```

> `DATABASE_URL` is automatically injected by Railway's PostgreSQL plugin — do not set it manually.

**4. Deploy**
Railway will auto-deploy on every push to your main branch.

**5. Generate public domain**
Go to your service → **Settings** → **Networking** → **Generate Domain**

---

## Environment Variables

| Variable        | Required | Description                                      |
|-----------------|----------|--------------------------------------------------|
| `DATABASE_URL`  | Yes      | Auto-provided by Railway PostgreSQL plugin       |
| `SECRET_KEY`    | Yes      | Flask session secret — use a 32+ char random string |
| `JWT_SECRET_KEY`| Yes      | JWT signing secret — use a 32+ char random string |
| `FLASK_DEBUG`   | No       | Set to `false` in production                     |
| `PORT`          | No       | Auto-provided by Railway                         |

---

## Database Schema

```
users          id, name, email (unique), password (hashed), role, created_at
projects       id, title, description, created_by (FK→users), created_at
project_members  project_id (FK), user_id (FK)   [many-to-many]
tasks          id, title, description, project_id (FK), assigned_to (FK→users),
               status, due_date, created_at
```
