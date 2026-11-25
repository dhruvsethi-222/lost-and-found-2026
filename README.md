# Web-Based Lost and Found System

Django 5.2 · Python 3.10 to 3.14 · SQLite on a laptop (MySQL ready for the live site) · Bootstrap 5.3

**Dev 1 (Sprints 1 and 2):** Student and Staff sign-up with email verification, log-in (refused until
verified), a separate Security desk log-in for the Admin, role checks on every page, reporting lost and
found items, recording found items with private details (Admin only), and searching found items.

**Dev 2 (Sprints 3 and 4):** the matching algorithm (category, place, date and keywords, scored out of 100
and ranked), email match alerts, the hand-in confirmation for Staff, claims with their status on My page,
and the Admin's verification: the claim beside the private details, then approve, reject or ask for
more details, with a reason. Every decision is emailed and can never be changed.

**Dev 3 (Sprints 5 and 6):** the hand-over (the collector's ID must match the claimant, the item becomes
Returned, the owner gets a receipt), disposal of items past the 90-day retention period (their private
details are deleted), Manage accounts (switch an account off or on, verify by hand), the Admin's reports
with an audit log of every decision, hand-over and disposal, and posts and replies for Students and Staff.

**Update (25 November 2026), with Jerry's changes:**
- Sign-up for Students and Staff needs an email ending exactly in `@strathmore.edu`. The demo accounts
  use that ending too. An existing database moves the five demo accounts in place when `migrate` runs.
- Every text box people type into takes at most 500 characters: descriptions, posts and replies, the
  first claim answer and each follow-up, decision and disposal reasons, search, and the private
  serial number, marks and contents. The whole claim conversation is kept, so it can be longer.
- A report can have one optional photo (JPEG, PNG or WebP, up to 5 MB). It is kept in the private
  `report_photos` folder and only the reporter and the security desk can open it.
- Choosing **Other** as the place shows a "Specify the location" box (up to 500 characters). The typed
  place is saved on its own, shown wherever the place is shown, found by search, and used by matching:
  two "Other" places score the same-place points only when the typed places are the same.

## Documents

| Development | Document | What it is |
|---|---|---|
| Dev 1 | [Dev1_Breakdown.docx](docs/Dev1_Breakdown.docx) | How Dev 1 was built and how every part of the code works |
| Dev 1 | [Dev1_Requirements_Check.docx](docs/Dev1_Requirements_Check.docx) | Dev 1 checked against the functional requirements, non-functional requirements and objectives |
| Dev 2 | [Dev2_Breakdown.docx](docs/Dev2_Breakdown.docx) | How Dev 2 (matching, alerts, claims, verification) was built |
| Dev 2 | [Dev2_Requirements_Check.docx](docs/Dev2_Requirements_Check.docx) | Dev 2 checked against the requirements and objectives |
| Dev 3 | [Dev3_Breakdown.docx](docs/Dev3_Breakdown.docx) | How Dev 3 (hand-over, disposal, accounts, reports, posts) was built |
| All | [Final_Requirements_Check.docx](docs/Final_Requirements_Check.docx) | The whole system checked against all 77 functional requirements, the non-functional requirements and the objectives |

## How the code is organised

| Folder | What it does |
|---|---|
| `accounts` | Sign up, email verification, log in, the Student / Staff / Admin accounts |
| `items` | Reporting lost and found items, the Admin recording found items with private details |
| `search` | Searching found items (public details only), with a Claim button on each result |
| `matching` | The back-end matching of lost reports and found items, and the match alert email. No pages of its own |
| `claims` | Claiming an item, and the Admin's verification decision |
| `handover` | Handing an item back to its owner |
| `posts` | Posts and replies for Students and Staff (the user tweet and response module) |
| `core` | Home page, My page, Security desk, the Admin's reports, the shared form helper |
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
python manage.py createofficer --email achieng@strathmore.edu --name "Grace Achieng" --officer-no SO-001
python manage.py runserver
```

After getting a newer copy of the code, always run `python manage.py migrate` again before `runserver`.
If `runserver` shows a warning about `STUDENT_EMAIL_DOMAINS` or `STAFF_EMAIL_DOMAINS`, open `.env` and
set both lines to `strathmore.edu`.

Open http://127.0.0.1:8000. Without Brevo set up, verification emails are printed in the terminal:
copy the link from there into the browser.

## Use MySQL on your laptop

1. Install MySQL Server and MySQL Workbench from https://dev.mysql.com/downloads/
2. In Workbench, open and run `docs/mysql_setup.sql` (makes the `lostandfound` database and its account).
3. `pip install mysqlclient`
4. In `.env`, remove the `#` from the six "MySQL on your laptop" lines.
5. `python manage.py migrate` makes all the tables in MySQL. Then `python manage.py runserver`.

## Emails (verification link and notifications)

Without any email settings, every email is printed in the window running the site. Copy the
verification link from there into the browser.

To send real emails, the system uses the free **Brevo** email API through the `django-anymail` library:

1. In Brevo, add a sender (Senders, Domains & Dedicated IPs, then Senders) and confirm it with the code
   Brevo emails you. Then create an API key (SMTP & API, then API keys).
2. Run `pip install -r requirements.txt`, then open `.env` and add (the key stays in `.env`, never on GitHub):

   ```
   EMAIL_BACKEND=anymail.backends.brevo.EmailBackend
   BREVO_API_KEY=xkeysib-your-key-here
   DEFAULT_FROM_EMAIL=Lost and Found <the-sender-you-confirmed@gmail.com>
   ```
3. Test it: `python manage.py sendtestemail your.name@strathmore.edu`, then restart the site.

If an email cannot be sent (no internet, a wrong key), the action is still saved, the page says the
email was not sent, and the reason is printed in the window running the site.

## Run the tests

```bash
python manage.py test
coverage run manage.py test && coverage report
```

## Put it live on PythonAnywhere

1. Upload the code (from GitHub: `git clone ...` in a PythonAnywhere Bash console).
2. `mkvirtualenv lostfound --python=python3.13` then `pip install -r requirements.txt` (add `mysqlclient` on a paid account).
3. Paid accounts only: on the Databases tab create a MySQL database called `lostfound`. Free accounts keep SQLite.
4. Create `.env` (copy `.env.example`) and fill in the "live" part.
5. `python manage.py migrate`, `python manage.py collectstatic`, `python manage.py createofficer ...`.
6. Web tab: add a new web app (Manual configuration, Python 3.13), set the virtualenv, and in the
   WSGI file point to this folder and `config.settings`.
7. Static files: URL `/static/` -> `.../lost_and_found/staticfiles`, URL `/media/` -> `.../lost_and_found/media`.
8. Turn on "Force HTTPS", press Reload.

The full steps, with explanations, are in the breakdown documents.

## Back up and restore the database (NFR-07)

Back up (run it regularly; on PythonAnywhere add it as a daily Scheduled task):

```
python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission --exclude sessions --output backup.json
```

Restore, into an empty database after `python manage.py migrate`:

```
python manage.py loaddata backup.json
```

Keep `backup.json`, the `media` folder (found-item photos) and the `report_photos` folder (report photos) somewhere safe. They contain personal data, so never put them on GitHub.
