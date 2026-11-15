# Web-Based Lost and Found System (Dev 1)

Django 5.2 · Python 3.10+ · MySQL on PythonAnywhere (SQLite on a laptop) · Bootstrap 5.3

Dev 1 covers: Student and Staff sign-up with email verification, log-in (refused until verified),
a separate Security desk log-in for the Admin, role checks on every page, reporting lost and found
items, recording found items with private details (Admin only), and searching found items.

## How the code is organised

| Folder | What it does |
|---|---|
| `accounts` | Sign up, email verification, log in, the Student / Staff / Admin accounts |
| `items` | Reporting lost and found items, the Admin recording found items with private details |
| `search` | Searching found items (public details only) |
| `core` | Home page, My page, Security desk, the shared form helper |
| `templates`, `static` | The shared page layout, CSS and JavaScript |
| `config` | Settings and the main list of web addresses |

Every page works the same way: `urls.py` (the address) -> `views.py` (the function that
answers) -> `forms.py` (checks what was typed) -> `templates` (the HTML page).

Every protected view starts the same way: `@login_required`, then a plain check of
`request.user.role`. A wrong role gets the "Access denied" page.

## Run it on your laptop

```bash
python -m venv venv
venv\Scripts\activate            # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # Windows   (Mac/Linux: cp .env.example .env)
python manage.py migrate
python manage.py createofficer --email achieng@campus.ac.ke --name "Grace Achieng" --officer-no SO-001
python manage.py runserver
```

Open http://127.0.0.1:8000. Verification emails are printed in the terminal on a laptop:
copy the link from there into the browser.

## Run the tests

```bash
python manage.py test
coverage run manage.py test && coverage report
```

## Put it live on PythonAnywhere

1. Upload the code (from GitHub: `git clone ...` in a PythonAnywhere Bash console).
2. `mkvirtualenv lostfound --python=python3.10` then `pip install -r requirements.txt mysqlclient`.
3. Databases tab: create a MySQL database called `lostfound`, set a password.
4. Create `.env` (copy `.env.example`) and fill in the "live" part.
5. `python manage.py migrate`, `python manage.py collectstatic`, `python manage.py createofficer ...`.
6. Web tab: add a new web app (Manual configuration, Python 3.10), set the virtualenv, and in the
   WSGI file point to this folder and `config.settings`.
7. Static files: URL `/static/` -> `.../lost_and_found/staticfiles`, URL `/media/` -> `.../lost_and_found/media`.
8. Turn on "Force HTTPS", press Reload.

The full steps, with explanations, are in the Dev 1 breakdown document.
