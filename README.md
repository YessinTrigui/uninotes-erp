# UniNotes ERP

A university web application built with Django 6 that manages student enrollment, academic grading, and role-based dashboards for students, tutors, and administrators.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 6.0.6 |
| Language | Python 3.13 |
| Database | SQLite (development) |
| Frontend | Bootstrap 5.3, Font Awesome 6.4 |
| Charts | Chart.js 4.4 |
| Authentication | Django built-in (session-based) |

---

## Architecture — Three-App Structure

```
uninotes_erp/          ← Project configuration (settings, root URLs)
├── accounts/          ← WHO: Custom User model with role system
├── catalog/           ← WHAT: Academic catalog (Specialization, Semester, Subject)
└── enrollment/        ← ACTION: Cart, Enrollment engine, Grading, Dashboards
```

Each app owns its domain completely. Cross-app communication happens through ForeignKeys and Python imports — never by sharing files.

---

## Database Schema

```
accounts_user
    ├── role              → student | tutor | admin
    ├── student_id        → unique per student
    └── current_semester  → FK → catalog_semester

catalog_specialization
    └── catalog_semester
            └── catalog_subject
                    ├── responsible_tutor → FK → accounts_user (tutors only)
                    ├── credits
                    └── coefficient

enrollment_enrollment
    ├── student   → FK → accounts_user
    ├── subject   → FK → catalog_subject
    └── status    → pending | confirmed | dropped

enrollment_grade          (OneToOne → enrollment)
    ├── continuous_assessment  (DS — 40%)
    ├── final_exam             (Exam — 60%)
    └── calculated_grade       (auto-computed)

enrollment_cartitem
    ├── student → FK → accounts_user
    └── subject → FK → catalog_subject
```

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/YessinTrigui/uninotes-erp.git
cd uninotes-erp

# 2. Install Django (if not already installed)
pip install django

# 3. Apply migrations
py manage.py migrate

# 4. Create a superuser (admin)
py manage.py createsuperuser

# 5. Run the development server
py manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

---

## User Roles & Workflows

### Admin (via `/admin/`)
1. Create a **Specialization** (e.g., "Computer Science Licence 3")
2. Create a **Semester** under it (e.g., S1 / 2025-2026 / 30 credit limit)
3. Create **Subjects** with credits, coefficient, and assign a tutor
4. Create **Tutor** accounts and assign subjects to them
5. Create **Student** accounts and set their `current_semester`

### Student (via `/enrollment/`)
1. Register at `/accounts/register/`
2. Browse the subject catalog at `/enrollment/catalog/`
3. Add subjects to cart — system shows "Recommended for You" (mandatory first)
4. Review cart at `/enrollment/cart/` — live credit counter vs semester limit
5. Confirm enrollment — 60-credit gate validates before creating records
6. View grades and weighted average at `/enrollment/dashboard/student/`

### Tutor (via `/enrollment/`)
1. Log in — redirected to tutor dashboard
2. See all their subjects with class statistics (avg grade, pass rate)
3. Click "Manage Grades" → see all enrolled students
4. Enter DS (40%) and Exam (60%) grades per student
5. System computes `final = DS×0.4 + Exam×0.6` and saves automatically

---

## URL Map

| URL | View | Who |
|---|---|---|
| `/` | login_view | Public |
| `/accounts/login/` | login_view | Public |
| `/accounts/register/` | register_view | Public |
| `/accounts/logout/` | logout_view | Authenticated |
| `/dashboard/` | dashboard_redirect_view | Authenticated (routes by role) |
| `/enrollment/catalog/` | subject_catalog_view | Students only |
| `/enrollment/cart/` | cart_view | Students only |
| `/enrollment/cart/add/<id>/` | add_to_cart_view | Students only — POST |
| `/enrollment/cart/remove/<id>/` | remove_from_cart_view | Students only — POST |
| `/enrollment/cart/confirm/` | confirm_enrollment_view | Students only — POST |
| `/enrollment/dashboard/student/` | student_dashboard_view | Students only |
| `/enrollment/dashboard/tutor/` | tutor_dashboard_view | Tutors only |
| `/enrollment/grades/<id>/` | subject_grades_view | Tutors only (own subjects) |
| `/enrollment/grades/enter/<id>/` | enter_grade_view | Tutors only (own subjects) |
| `/admin/` | Django Admin | Staff/Admin only |

---

## Security Layer

### Authentication & Authorization
- All protected views perform a two-step check:
  1. `if not request.user.is_authenticated` → redirect to login
  2. `if not request.user.is_<role>()` → redirect to their own dashboard
- No cross-role access is possible at any URL

### Object-Level Authorization
- Tutors can only grade subjects where `responsible_tutor == request.user`
- Students can only remove their own cart items (`student == request.user`)
- Both enforced via `get_object_or_404` lookup conditions — a wrong ID returns 404, not data

### CSRF Protection
- Every HTML form includes `{% csrf_token %}`
- Django's `CsrfViewMiddleware` validates the token on every POST request

### HTTP Method Enforcement
- All state-changing action views (add, remove, confirm, enter grade) reject GET requests and redirect to the appropriate page

### Security Headers (settings.py)
| Header | Value | Purpose |
|---|---|---|
| `X_FRAME_OPTIONS` | `DENY` | Prevents clickjacking via iframes |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` | Prevents MIME-type sniffing |
| `SESSION_COOKIE_HTTPONLY` | `True` | JavaScript cannot read the session cookie |
| `CSRF_COOKIE_HTTPONLY` | `True` | JavaScript cannot read the CSRF token cookie |

### Production Checklist (before deploying)
- Change `SECRET_KEY` to a long random value
- Set `DEBUG = False`
- Set `ALLOWED_HOSTS` to your domain
- Set `SESSION_COOKIE_SECURE = True`
- Set `CSRF_COOKIE_SECURE = True`
- Set `SECURE_SSL_REDIRECT = True`
- Switch database to PostgreSQL

---

## Key ORM Patterns Used

### aggregate() — class statistics in one query
```python
Grade.objects.filter(enrollment__subject=subject).aggregate(
    avg_grade=Avg('calculated_grade'),
    pass_count=Count('id', filter=Q(calculated_grade__gte=10)),
    fail_count=Count('id', filter=Q(calculated_grade__lt=10)),
)
```

### annotate() — add computed columns to every subject row
```python
Subject.objects.filter(responsible_tutor=request.user).annotate(
    confirmed_count=Count('enrollments', filter=Q(enrollments__status='confirmed')),
    avg_grade=Avg('enrollments__grade__calculated_grade'),
    pass_count=Count('enrollments__grade', filter=Q(enrollments__grade__calculated_grade__gte=10)),
)
```

### F() + ExpressionWrapper — weighted average computed in SQL
```python
enrollments.annotate(
    weighted_score=ExpressionWrapper(
        F('grade__calculated_grade') * F('subject__coefficient'),
        output_field=FloatField()
    )
).aggregate(
    total_weighted=Sum('weighted_score'),
    total_coefficient=Sum('subject__coefficient'),
)
```

### values_list(flat=True) — efficient flat ID lists
```python
Enrollment.objects.filter(student=request.user, status='confirmed').values_list('subject_id', flat=True)
```

---

## Chart.js Integration

Charts receive data from Django views as JSON strings injected into templates:

```python
# In the view
context['chart_labels'] = json.dumps(['ALGO-301', 'WEB-201', ...])
context['chart_values'] = json.dumps([13.5, 8.0, ...])
```

```javascript
// In the template (|safe prevents HTML-escaping of JSON quotes)
const labels = {{ chart_labels|safe }};
const values = {{ chart_values|safe }};
```

### Student Dashboard
Bar chart showing each subject's final grade. Green bars = passing, red bars = failing. A dashed red line marks the 10/20 passing threshold.

### Reconstitution Curve (Tutor — Subject Grades Page)
Histogram dividing grades into 2-point buckets (0-2, 2-4, ..., 18-20). Red buckets = failing range, yellow = borderline (8-10), green = passing range. Used by professors to analyse grade distribution of their class.

---

## Project built with Django 6 — ESPRIT University, 2026
