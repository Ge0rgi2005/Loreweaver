# Loreweaver

## Run locally

From the project directory, create and activate a virtual environment, install
the requirements, apply migrations, and start Django's development server:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

`DEBUG` defaults to `True` for local development, and the development hostnames
`localhost`, `127.0.0.1`, and `[::1]` are allowed. The app's CSS is served from
the `static` directory in this mode.

## View the custom 404 page

Django only displays the project's custom 404 page when `DEBUG` is disabled.
In PowerShell, set `DEBUG` to `false` and run the development server with
`--insecure` so Django also serves static files while debug mode is off:

```powershell
$env:DEBUG = "false"
python manage.py runserver --insecure
```

Then visit a nonexistent URL, such as `http://127.0.0.1:8000/not-a-real-page/`.
Use `--insecure` only for local development, never in production.
