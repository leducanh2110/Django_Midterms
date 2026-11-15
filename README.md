# Django Authentication Demo

A small, beginner-friendly Django application demonstrating registration,
login, logout, protected views, and database persistence. It uses Django's
built-in `User` model and authentication system, with a responsive HTML/CSS
interface. No frontend framework, JavaScript, or third-party authentication
package is required.

## Technologies

- Python 3.10 or later (tested with Python 3.12).
- Django 5.2 LTS (`requirements.txt` selects the latest available 5.2 patch).
- SQLite, Django ORM, and database-backed sessions.
- Django Templates, Django Forms, and plain CSS.

## Installation

Open a terminal in this directory, the one containing `manage.py`.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

These commands use the virtual environment directly, so activating it or
changing PowerShell's execution policy is unnecessary.

### macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open **http://127.0.0.1:8000/**. Stop the development server with `Ctrl+C`.

The `migrate` command creates `db.sqlite3` and Django's user, session, and
other built-in tables. There are no custom account tables or migrations;
the project uses Django's existing authentication migrations. Run `migrate`
when setting up a fresh checkout or after updating Django. Accounts persist
in `db.sqlite3` across server restarts; the file is excluded from version control.

## Try the complete flow

1. Open the application; you will be redirected to sign in.
2. Choose **Create account** and enter a username, a valid email, a password,
   and matching confirmation. Password rules appear underneath the field.
3. Submit. Django saves the account to SQLite and redirects you to sign in
   with a success message. Registration does not sign you in automatically.
4. Sign in with the registered **username** and password.
5. The dashboard displays your username, email, and account creation date.
6. Refresh the page: your session keeps you signed in.
7. Choose **Sign out** to end the session and return to sign in.
8. Visit `/dashboard/` again; you will be redirected to `/login/?next=/dashboard/`.

Usernames must be unique. Email is required and validated as an email address;
it is not a login identifier and is not required to be unique by the built-in
`User` model. This demo does not verify email ownership.

## Application routes

| Route | Methods | Behavior |
| --- | --- | --- |
| `/` | GET | Redirect to login, or dashboard when signed in. |
| `/register/` | GET, POST | Display and submit registration. |
| `/login/` | GET, POST | Display and submit login. |
| `/dashboard/` | GET | Show the current user's account; requires login. |
| `/logout/` | POST | Clear the session and redirect to login. |
| `/admin/` | Django admin | Optional built-in admin, unused by the demo flow. |

Signed-in users visiting login or registration are redirected to the dashboard.
Logout intentionally rejects GET requests. Use the dashboard's POST button.
The optional admin is available after running `python manage.py createsuperuser`
with the virtual environment's Python; a superuser is not needed for this demo.

## How it works

**Forms and validation.** `accounts/forms.py` extends `UserCreationForm` to
require email and style the fields. Django validates unique usernames,
email syntax, matching passwords, and the default password-strength rules.
`LoginForm` extends `AuthenticationForm`, which validates credentials using
Django's authentication backend. Field errors and general login errors are
rendered next to the relevant form. Server validation also works without JavaScript.

**Authentication.** Registration calls `form.save()` in `accounts/views.py`.
`LoginView` authenticates the username and password and signs the user in.
`LogoutView` signs the user out. These built-in views are wired in
`accounts/urls.py`. `LOGIN_REDIRECT_URL` and `LOGOUT_REDIRECT_URL` choose the
destinations. Login preserves a safe local `next` destination and Django
rejects external redirect URLs.

**Password hashing.** `UserCreationForm.save()` calls Django's password
handling code, which salts and hashes the password using the configured
default hasher (PBKDF2-SHA256). SQLite stores the encoded hash, never the
plaintext password. On login, Django checks the submitted password against
that stored hash. The application never logs passwords.

**Sessions.** `SessionMiddleware` and `AuthenticationMiddleware` restore the
signed-in user as `request.user`. After login, session data is persisted in
the `django_session` SQLite table. The browser gets an HTTP-only session ID
cookie, not the user's password. Logout clears the session. Authentication
survives page refreshes and server restarts while the session remains valid.

**Protected views and CSRF.** `@login_required` guards the dashboard and
redirects anonymous visitors to login with a `next` parameter. Dashboard
responses disable caching. Every POST form includes `{% csrf_token %}` and
`CsrfViewMiddleware` rejects missing or invalid tokens, including logout.
Templates automatically escape account data when displaying it.

**ORM and database.** The built-in `django.contrib.auth.models.User` model
maps accounts to SQLite's `auth_user` table. `form.save()` uses the ORM to
insert a user; authentication uses the ORM to retrieve the account. The
dashboard reads the authenticated model instance through `request.user`.
For example, `User.objects.get(username="alice")` retrieves an existing user
without writing SQL. There is no custom user model or raw SQL in the app.

## Project layout

```text
django-auth-demo/
├── manage.py
├── config/                 # Settings and project URL configuration
├── accounts/
│   ├── migrations/         # No custom models to migrate
│   ├── templates/accounts/ # Login, register, dashboard, shared fields
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
├── templates/              # Shared page and authentication layouts
├── static/                 # CSS and a small SVG favicon
├── requirements.txt
└── README.md
```

## Verification

Using your virtual environment's Python:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

On macOS/Linux, substitute `.venv/bin/python` for the executable above.
The tests use a separate temporary database and leave local accounts untouched.
They cover the complete registration/login/dashboard/logout flow, password
hashing, input validation, persisted sessions, protected routes, redirect
safety, POST-only logout, and CSRF enforcement (including successful requests
with real tokens).

## Scope

This is a local educational demo. The development secret key, `DEBUG=True`,
local hosts, and Django development server are deliberate conveniences,
not production deployment settings. There is no OAuth, REST API, password
reset, email delivery, or custom role management.

Reference: [Django's authentication documentation](https://docs.djangoproject.com/en/5.2/topics/auth/default/).
