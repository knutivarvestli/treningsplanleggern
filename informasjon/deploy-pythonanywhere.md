# Deploy på PythonAnywhere (gratis-tier)

Denne fila beskriver hvordan du deployer Treningsplanleggern til
[PythonAnywhere](https://www.pythonanywhere.com) sin gratis «Beginner»-konto.

PythonAnywhere passer godt for denne appen fordi:

- Persistent disk → SQLite kan brukes direkte, du slipper ekstern database.
- Appen sovner ikke som på Render Free — alltid umiddelbar respons.
- Alt (kode + database + Python-miljø) ligger på én konto.

## Når bør du velge PythonAnywhere fremfor Render?

| Behov | Velg |
|---|---|
| Familie-app, liten trafikk, sjelden brukt | **PythonAnywhere** (slipper cold start) |
| Auto-deploy ved `git push main` | **Render** (PythonAnywhere må oppdateres manuelt) |
| Egen domene-binding | Begge støtter det på betalt tier |

---

## 1. Opprett konto

1. Gå til https://www.pythonanywhere.com og registrer en **Beginner**-konto (gratis).
2. Velg et brukernavn — det blir også URL-en din: `<brukernavn>.pythonanywhere.com`.

---

## 2. Klon repoet via Bash-konsoll

1. På dashbordet: **Consoles → Bash → New console**.
2. Klon repoet og opprett virtuelt miljø:

   ```bash
   git clone https://github.com/knutivarvestli/treningsplanleggern.git treningsplanlegger
   cd treningsplanlegger
   python3.11 -m venv .venv
   .venv/bin/pip install --upgrade pip
   .venv/bin/pip install -r requirements.txt
   ```

   `psycopg2-binary` og `gunicorn` blir installert men ikke brukt på
   PythonAnywhere — de gjør ingen skade.

---

## 3. Sett opp web-app

1. **Web → Add a new web app**.
2. På gratis-tier får du domenet `<brukernavn>.pythonanywhere.com` automatisk — klikk **Next**.
3. Velg **Manual configuration** (ikke «Flask»-malen — vi har egen `app.py`).
4. Velg **Python 3.11**.
5. Bekreft.

På Web-fanen som åpnes, fyll inn:

| Felt | Verdi |
|---|---|
| **Source code** | `/home/<brukernavn>/treningsplanlegger` |
| **Working directory** | `/home/<brukernavn>/treningsplanlegger` |
| **Virtualenv** | `/home/<brukernavn>/treningsplanlegger/.venv` |

---

## 4. Rediger WSGI-fila

PythonAnywhere lager en WSGI-fil for deg, typisk
`/var/www/<brukernavn>_pythonanywhere_com_wsgi.py`. Klikk lenken på
Web-fanen for å åpne den i editor.

Erstatt hele innholdet med:

```python
import sys

path = "/home/<brukernavn>/treningsplanlegger"
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application  # noqa: E402
```

Bytt `<brukernavn>` med ditt faktiske PythonAnywhere-brukernavn. Lagre.

---

## 5. Sett miljøvariabler

På Web-fanen, finn seksjonen **Environment variables** og legg til:

| Navn | Verdi |
|---|---|
| `SECRET_KEY` | lang tilfeldig streng (f.eks. fra https://1password.com/password-generator) |

`DATABASE_URL` settes **ikke** — da faller appen tilbake til SQLite, som
ligger som `treningsplanlegger.db` i prosjektmappa.

---

## 6. Reload og test

1. Klikk den grønne **Reload**-knappen øverst på Web-fanen.
2. Åpne `https://<brukernavn>.pythonanywhere.com`.
3. Logg inn som `admin` / `admin` og bytt passordet umiddelbart via
   «Brukere»-siden.

---

## 7. Begrensninger og tips for Beginner-tier

- **512 MB disk** totalt — masse for en SQLite-database med treningsøkter.
- **Én web-app** per gratis-konto.
- **Utgående internett er begrenset** til en whitelist av domener — ikke
  et problem for denne appen siden den ikke kaller eksterne API-er.
- **Kontoen utløper etter 3 måneders inaktivitet** — du logger inn og
  klikker en knapp for å fornye. Eposterminnelse sendes på forhånd.
- **Bytt admin-passordet** umiddelbart etter første innlogging.
- **Backup av SQLite-fila:** last ned `treningsplanlegger.db` fra Files-fanen
  med jevne mellomrom hvis dataene er viktige.

---

## 8. Oppdatere appen senere

PythonAnywhere har **ikke** auto-deploy fra Git. Når du har pushet
endringer til GitHub, må du oppdatere manuelt:

1. Åpne en Bash-konsoll (eller bruk en eksisterende).
2. Kjør:

   ```bash
   cd ~/treningsplanlegger
   git pull
   .venv/bin/pip install -r requirements.txt   # bare hvis requirements.txt er endret
   ```
3. Gå til Web-fanen og klikk **Reload**.

Tips: Lag en kort `update.sh` i hjemmemappa hvis du gjør dette ofte:

```bash
#!/bin/bash
cd ~/treningsplanlegger && git pull
```

---

## 9. Feilsøking

| Symptom | Sannsynlig årsak |
|---|---|
| «Something went wrong :-(» | Sjekk **Web → Error log** for stack trace. |
| `ModuleNotFoundError: No module named 'flask'` | Virtualenv-stien er feil eller `pip install` feilet. Sjekk Web-fanen. |
| Endringer vises ikke etter `git pull` | Glemt å klikke **Reload** på Web-fanen. |
| `sqlite3.OperationalError: unable to open database file` | Working directory peker feil sted. Sjekk Web-fanen. |
| Login fungerer ikke / sesjoner mistes | `SECRET_KEY` ikke satt — sett den under Environment variables og reload. |

---

## 10. Hvordan miljøvariablene brukes i koden

Se `app.py`:

```python
db_url = os.environ.get("DATABASE_URL", "sqlite:///treningsplanlegger.db")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bytt-meg-i-produksjon")
```

- Uten `DATABASE_URL` (PythonAnywhere-oppsett) → SQLite på lokal disk.
- `init_db()` kjøres ved oppstart og er idempotent — oppretter kun
  manglende tabeller og standard verdilister.
