# Treningsplanleggern

Web-app for planlegging og oppfølging av treningsøkter — opprinnelig laget
for en ungdom som driver med skiskyting, men generell nok for andre
utholdenhetsidretter.

Bygget med **Flask + SQLAlchemy + SQLite** (lokalt) eller **Postgres**
(produksjon på Render). Server-rendret HTML med litt vanilla JS for
mobil-modus og detaljkort.

---

## ✨ Implementerte funksjoner

### Treningsøkter
- Registrering med felter: aktivitet, økttype, teknikk/terreng,
  varighet/omfang, dato, distanse (km), opplevd belastning (RPE 1–10)
  og kommentar.
- Detaljkort med alle data (modal som glir opp fra bunnen) når du
  trykker på en økt — fargekodet etter økttype.
- Rediger/slett via redigeringsskjemaet.

### Kalender
- **Månedsvisning** som tradisjonelt grid på desktop.
- **Ukesvisning** med detaljerte øktkort per dag.
- Klikk på dagnummer eller `＋`-knapp for å opprette ny økt med datoen
  ferdig utfylt — du slipper å gå via «Ny økt» i menyen.

### Mobil-modus
- `📱`-knapp i toppen veksler til en **iPhone-ramme** (390 × 844 med
  Dynamic Island og home-indikator) for å forhåndsvise mobil-layout fra
  PC-en.
- Auto-mobil aktiveres på smale skjermer (< 720 px).
- I mobil vises månedskalenderen som **én uke om gangen**, med sticky
  uke-navigering: `[← Forrige]  4.–10. mai  [Neste →]`.
- Cross-month-navigering: `Forrige` på første uke hopper til siste uke
  i forrige måned, og motsatt for `Neste`.
- Fulle ukedagnavn (Mandag, Tirsdag …) i mobil-listen.
- Topbar er sticky inni iPhone-rammen så menyen alltid er tilgjengelig.

### Maler
- Lagre treningsøkter som maler (kryss av når du lagrer en økt).
- Gjenbruk maler ved opprettelse av ny økt — dropdown øverst i skjemaet.

### Brukerhåndtering
- Innlogging med brukernavn/passord (hashet via Werkzeug).
- To roller:
  - **Administrator** — administrerer brukere og verdilister.
  - **Bruker** — registrerer og følger opp egne økter.

### Admin
- CRUD for brukere.
- Vedlikehold av verdilister (Aktivitet, Økttype, Teknikk).

---

## 🚀 Komme i gang lokalt

### Enkleste vei (Windows)

Dobbeltklikk `start.bat`. Den oppretter virtuelt miljø, installerer
avhengigheter, starter serveren og åpner nettleseren.

```
============================================================
  PC:     http://127.0.0.1:5000
  Mobil:  http://192.168.x.x:5000   (samme wifi som PC-en)
============================================================
```

### Manuelt

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Logg inn med **`admin` / `admin`** første gang og bytt passordet med en
gang via «Brukere»-siden.

---

## 📁 Mappestruktur

```
treningsplanlegger/
├── app.py                  Flask-app (modeller, ruter, init)
├── requirements.txt        Flask, SQLAlchemy, Login, psycopg2, gunicorn
├── start.bat               Windows-launcher
├── Procfile                Produksjonsstart for Render (gunicorn)
├── static/style.css        All styling (desktop, mobil, iPhone-ramme, modal)
├── templates/              Jinja2-templates
│   ├── base.html           topp-meny + modal-kort + JS for mobil-toggle
│   ├── login.html
│   ├── calendar_month.html
│   ├── calendar_week.html
│   ├── session_form.html   ny/rediger økt + lagre-som-mal
│   ├── templates_list.html
│   ├── admin_users.html
│   └── admin_lookups.html
└── informasjon/
    └── deploy-render.md    deploy-veiledning for Render + Supabase
```

---

## 🛠 Teknologi

| Lag | Verktøy |
|---|---|
| Backend | Flask 3, Flask-SQLAlchemy, Flask-Login |
| Database | SQLite (lokalt), Postgres (produksjon) via `DATABASE_URL` |
| Frontend | Server-rendret Jinja2 + vanilla JS, ingen byggesteg |
| Produksjonsserver | Gunicorn |
| Hosting | Render Free Web Service |

Alt UI er server-rendret — ingen npm, ingen byggesteg, ingen frontend-rammeverk.

---

## ☁️ Deploy

To gratis-alternativer er dokumentert:

- **[informasjon/deploy-pythonanywhere.md](informasjon/deploy-pythonanywhere.md)** —
  PythonAnywhere Beginner med SQLite på persistent disk. Appen sovner
  ikke, men oppdateringer må trekkes manuelt med `git pull` + reload.
- **[informasjon/deploy-render.md](informasjon/deploy-render.md)** —
  Render Free + Supabase Postgres. Auto-deploy ved push til `main`,
  men appen sovner etter 15 min uten trafikk (30–60 sek cold start).

Kortversjon: appen leser `DATABASE_URL` og `SECRET_KEY` fra
miljøvariabler. Settes ingen `DATABASE_URL`, brukes lokal SQLite.

---

## 🧩 Funksjonelle krav (opprinnelig spec)

### Registrering av treningsøkt
Felter: **Aktivitet · Økttype · Teknikk/Terreng · Varighet/Omfang · Dato**

Standard verdilister (kan utvides via admin):

- **Aktivitet:** Løp, Rulleski, Langrenn, Sykkel, Skyting, Fotball,
  Kombi, Styrke
- **Økttype:** Intervall, Rolig, Konkurranse, Trening
- **Teknikk/Terreng:** Klassisk, Skøyting, Motbakke, Annet

### Begrepsbruk

| Begrep | Beskrivelse |
|---|---|
| Aktivitet | Hva slags aktivitet som gjennomføres |
| Økttype | Intensitet eller formål |
| Teknikk / Terreng | Hvordan økten gjennomføres |
| Varighet / Omfang | Lengde eller belastning |
| Verdiliste | Oppslagsdata som kan vedlikeholdes |

---

## 🧠 Mulige videreutvikling

- **Analyse:** treningsmengde per uke, fordeling økttyper, RPE-trend.
- **Visualisering:** progresjonsgrafer (distanse/varighet over tid).
- **Eksport:** CSV-eksport av økter for ekstern analyse.
- **Skiskyting-spesifikt:** treffstatistikk per skytestilling.
- **Push-varsler / iCal-eksport** for planlagte økter.
