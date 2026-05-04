# Deploy på Render med Supabase Postgres

Denne fila beskriver hvordan du deployer Treningsplanleggern til Render
sin gratis-tier med Supabase som ekstern Postgres-database.

## Hvorfor ikke SQLite på Render?

Render Free har **ingen persistent disk** — `treningsplanlegger.db` blir
slettet ved hver redeploy og potensielt ved restart etter dvale. Derfor
bruker vi en ekstern Postgres-database. Supabase har 500 MB gratis tier
som varer (Render sin egen gratis Postgres slettes etter 90 dager).

---

## 1. Opprett gratis Postgres (Supabase)

1. Gå til https://supabase.com → **New project**
2. Velg gratis-tier, region «North EU (Stockholm)» eller «West EU (Ireland)»
3. Sett et passord og noter det
4. Etter ~1 min: **Project Settings → Database → Connection string → URI**
5. Kopiér strengen — den ser ut som:

   ```
   postgresql://postgres.PROSJEKTID:PASSORD@aws-0-eu-north-1.pooler.supabase.com:6543/postgres
   ```

   Bruk `:6543` («Transaction pooler») — den passer for serverless-style
   apps som Render Free.

---

## 2. Deploy på Render

1. Gå til https://dashboard.render.com → **New → Web Service**
2. **Connect repository** → velg `knutivarvestli/treningsplanleggern`
3. Fyll inn:
   - **Name:** `treningsplanleggern` (eller noe annet)
   - **Region:** Frankfurt
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** la stå tomt — Render plukker opp `Procfile` automatisk
   - **Plan:** Free
4. Under **Environment variables** legger du til:
   - `DATABASE_URL` = URI-en fra Supabase (steg 1)
   - `SECRET_KEY` = lang tilfeldig streng (f.eks. fra
     https://1password.com/password-generator)
5. Klikk **Create Web Service**.

Render bygger og starter. Når det er grønt: åpne URL-en, logg inn som
`admin` / `admin` og bytt passordet med en gang via «Brukere»-siden.

---

## 3. Begrensninger og tips for Free-tier

- **Free-instansen sover etter 15 min uten trafikk.** Første kall etter
  dvale tar 30–60 sek (cold start). For en familie-app er det greit.
- **750 timer instans-tid per måned** deles mellom alle dine free-services.
  En enkelt alltid-på-app bruker ~720 timer alene.
- **512 MB RAM** og delt CPU per tjeneste.
- **Bytt admin-passordet** umiddelbart etter første innlogging.
- **Lokalt utviklingsmiljø påvirkes ikke** — `python app.py` (eller
  `start.bat`) bruker fortsatt SQLite og defaulten.

---

## 4. Hvordan miljøvariablene brukes i koden

Se `app.py`:

```python
db_url = os.environ.get("DATABASE_URL", "sqlite:///treningsplanlegger.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bytt-meg-i-produksjon")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
```

- Når `DATABASE_URL` ikke er satt (lokalt), brukes SQLite.
- Når den er satt (Render), brukes Postgres.
- `init_db()` kjøres ved oppstart og er idempotent — oppretter kun
  manglende tabeller og standard verdilister.

---

## 5. Feilsøking

| Symptom | Sannsynlig årsak |
|---|---|
| `sqlalchemy.exc.OperationalError: could not translate host name` | Feil eller tom `DATABASE_URL`. Sjekk Supabase-strengen. |
| `psycopg2.OperationalError: SSL connection ...` | Bruk pooler-URL-en (port 6543), ikke direkte connection (5432). |
| Får 500-feil etter første deploy | Sjekk Render → Logs. Ofte at `DATABASE_URL` mangler eller har feil format. |
| Cold start hver gang | Free-tier-oppførsel. Pro tier holder appen vekket, eller bruk en cron-pinger som [cron-job.org](https://cron-job.org) hvert 10. min. |
| `gunicorn: command not found` | `requirements.txt` ble ikke installert. Sjekk Build-loggen. |

---

## 6. Oppdatere appen senere

Bare push til `main`:

```powershell
git add .
git commit -m "Beskrivelse av endring"
git push
```

Render bygger og redeployer automatisk. Eksisterende data i Postgres
bevares (det er kun koden som oppdateres).
