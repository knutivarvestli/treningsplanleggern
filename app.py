"""Treningsplanleggern – Flask-app for planlegging av treningsøkter.

Kjør:
    pip install -r requirements.txt
    python app.py
Åpne http://127.0.0.1:5000  (logg inn som admin / admin første gang).
"""
from __future__ import annotations

import calendar as cal
import os
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Database: bruker DATABASE_URL fra miljøet i produksjon (Render/Supabase/Neon),
# faller tilbake til SQLite for lokal utvikling.
db_url = os.environ.get("DATABASE_URL", "sqlite:///treningsplanlegger.db")
# SQLAlchemy 1.4+ aksepterer ikke postgres:// — Heroku/eldre tjenester bruker det
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bytt-meg-i-produksjon")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# ---------------------------------------------------------------------------
# Modeller
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="bruker")  # bruker | admin

    sessions = db.relationship("Session", backref="user", cascade="all, delete-orphan")
    templates = db.relationship("Template", backref="user", cascade="all, delete-orphan")

    @property
    def display_name(self) -> str:
        return self.name or self.username

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class LookupValue(db.Model):
    """Verdier i en utvidbar verdiliste (Aktivitet, Økttype, Teknikk)."""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(32), nullable=False)  # aktivitet | okttype | teknikk
    value = db.Column(db.String(64), nullable=False)
    sort_order = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint("category", "value"),)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    dato = db.Column(db.Date, nullable=False, default=date.today)
    aktivitet = db.Column(db.String(64), nullable=False)
    okttype = db.Column(db.String(64), nullable=False)
    teknikk = db.Column(db.String(64))
    varighet = db.Column(db.String(64))           # fri tekst (1:15, 10 km, 6 x 5 min)
    distanse_km = db.Column(db.Float)             # anbefalt utvidelse
    rpe = db.Column(db.Integer)                   # opplevd belastning 1–10
    kommentar = db.Column(db.Text)


class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    navn = db.Column(db.String(80), nullable=False)
    aktivitet = db.Column(db.String(64), nullable=False)
    okttype = db.Column(db.String(64), nullable=False)
    teknikk = db.Column(db.String(64))
    varighet = db.Column(db.String(64))
    kommentar = db.Column(db.Text)


# ---------------------------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def lookup(category: str) -> list[str]:
    rows = (LookupValue.query
            .filter_by(category=category)
            .order_by(LookupValue.sort_order, LookupValue.value)
            .all())
    return [r.value for r in rows]


@app.context_processor
def inject_lookups():
    return {
        "aktiviteter": lookup("aktivitet"),
        "okttyper": lookup("okttype"),
        "teknikker": lookup("teknikk"),
    }


# ---------------------------------------------------------------------------
# Innlogging
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(url_for("calendar_month"))
        flash("Feil brukernavn eller passord", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/passord", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        ny = request.form.get("new_password", "")
        bekreft = request.form.get("confirm_password", "")
        if not current_user.check_password(current):
            flash("Feil nåværende passord", "error")
        elif len(ny) < 4:
            flash("Nytt passord må ha minst 4 tegn", "error")
        elif ny != bekreft:
            flash("Bekreftelsen matcher ikke det nye passordet", "error")
        else:
            current_user.set_password(ny)
            db.session.commit()
            flash("Passord oppdatert", "ok")
            return redirect(url_for("calendar_month"))
    return render_template("change_password.html")


# ---------------------------------------------------------------------------
# Kalender
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def index():
    return redirect(url_for("calendar_month"))


@app.route("/kalender/maned")
@login_required
def calendar_month():
    today = date.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    first_day = date(year, month, 1)
    _, days_in_month = cal.monthrange(year, month)
    last_day = date(year, month, days_in_month)

    sessions = (Session.query
                .filter(Session.user_id == current_user.id,
                        Session.dato >= first_day,
                        Session.dato <= last_day)
                .order_by(Session.dato)
                .all())
    by_date: dict[date, list[Session]] = {}
    for s in sessions:
        by_date.setdefault(s.dato, []).append(s)

    weeks = cal.Calendar(firstweekday=0).monthdatescalendar(year, month)
    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (last_day + timedelta(days=1))

    # Hvilken uke skal være synlig først i mobil-modus?
    default_week_index = 0
    if today.year == year and today.month == month:
        for i, w in enumerate(weeks):
            if today in w:
                default_week_index = i
                break
    else:
        for i, w in enumerate(weeks):
            if any(d.month == month for d in w):
                default_week_index = i
                break

    week_param = request.args.get("week")
    if week_param == "last":
        default_week_index = len(weeks) - 1
    elif week_param and week_param.isdigit():
        default_week_index = max(0, min(int(week_param), len(weeks) - 1))

    return render_template("calendar_month.html",
                           year=year, month=month, weeks=weeks,
                           by_date=by_date, today=today,
                           prev_month=prev_month, next_month=next_month,
                           month_name=cal.month_name[month],
                           default_week_index=default_week_index)


@app.route("/kalender/uke")
@login_required
def calendar_week():
    today = date.today()
    iso_year = int(request.args.get("year", today.isocalendar().year))
    iso_week = int(request.args.get("week", today.isocalendar().week))

    monday = date.fromisocalendar(iso_year, iso_week, 1)
    days = [monday + timedelta(days=i) for i in range(7)]

    sessions = (Session.query
                .filter(Session.user_id == current_user.id,
                        Session.dato >= days[0],
                        Session.dato <= days[-1])
                .order_by(Session.dato)
                .all())
    by_date: dict[date, list[Session]] = {d: [] for d in days}
    for s in sessions:
        by_date[s.dato].append(s)

    prev_monday = monday - timedelta(days=7)
    next_monday = monday + timedelta(days=7)
    return render_template("calendar_week.html",
                           days=days, by_date=by_date, today=today,
                           iso_year=iso_year, iso_week=iso_week,
                           prev=prev_monday.isocalendar(),
                           next=next_monday.isocalendar())


# ---------------------------------------------------------------------------
# Oppsummering
# ---------------------------------------------------------------------------
@app.route("/oppsummering")
@login_required
def summary():
    today = date.today()
    perioder = [
        ("Siste 7 dager", today - timedelta(days=6)),
        ("Siste 30 dager", today - timedelta(days=29)),
    ]

    summaries = []
    for label, start in perioder:
        sessions = (Session.query
                    .filter(Session.user_id == current_user.id,
                            Session.dato >= start,
                            Session.dato <= today)
                    .all())
        per_aktivitet: dict[str, dict] = {}
        for s in sessions:
            entry = per_aktivitet.setdefault(s.aktivitet, {
                "count": 0, "distanse": 0.0,
                "rpe_sum": 0, "rpe_count": 0,
                "okttyper": set(),
            })
            entry["count"] += 1
            if s.distanse_km:
                entry["distanse"] += s.distanse_km
            if s.rpe:
                entry["rpe_sum"] += s.rpe
                entry["rpe_count"] += 1
            entry["okttyper"].add(s.okttype)

        rader = []
        for aktivitet, e in sorted(per_aktivitet.items()):
            rader.append({
                "aktivitet": aktivitet,
                "count": e["count"],
                "distanse": round(e["distanse"], 1) if e["distanse"] else None,
                "snitt_rpe": round(e["rpe_sum"] / e["rpe_count"], 1) if e["rpe_count"] else None,
                "okttyper": sorted(e["okttyper"]),
            })

        summaries.append({
            "label": label,
            "start": start, "end": today,
            "total": len(sessions),
            "rader": rader,
        })

    return render_template("summary.html", summaries=summaries)


# ---------------------------------------------------------------------------
# Treningsøkter
# ---------------------------------------------------------------------------
def _populate_session(s: Session, form) -> None:
    s.dato = datetime.strptime(form["dato"], "%Y-%m-%d").date()
    s.aktivitet = form["aktivitet"].strip()
    s.okttype = form["okttype"].strip()
    s.teknikk = form.get("teknikk", "").strip() or None
    s.varighet = form.get("varighet", "").strip() or None
    s.distanse_km = float(form["distanse_km"]) if form.get("distanse_km") else None
    s.rpe = int(form["rpe"]) if form.get("rpe") else None
    s.kommentar = form.get("kommentar", "").strip() or None


@app.route("/okt/ny", methods=["GET", "POST"])
@login_required
def session_new():
    template_id = request.args.get("template_id", type=int)
    default_date = request.args.get("dato") or date.today().isoformat()

    if request.method == "POST":
        s = Session(user_id=current_user.id)
        _populate_session(s, request.form)
        db.session.add(s)
        if request.form.get("lagre_som_mal") and request.form.get("mal_navn"):
            t = Template(user_id=current_user.id,
                         navn=request.form["mal_navn"].strip(),
                         aktivitet=s.aktivitet, okttype=s.okttype,
                         teknikk=s.teknikk, varighet=s.varighet,
                         kommentar=s.kommentar)
            db.session.add(t)
        db.session.commit()
        flash("Økt registrert", "ok")
        return redirect(url_for("calendar_month",
                                year=s.dato.year, month=s.dato.month))

    prefill = None
    if template_id:
        prefill = db.session.get(Template, template_id)
        if prefill and prefill.user_id != current_user.id:
            prefill = None
    return render_template("session_form.html",
                           session=None, prefill=prefill,
                           default_date=default_date)


@app.route("/okt/<int:sid>/rediger", methods=["GET", "POST"])
@login_required
def session_edit(sid: int):
    s = db.session.get(Session, sid) or abort(404)
    if s.user_id != current_user.id:
        abort(403)
    if request.method == "POST":
        _populate_session(s, request.form)
        db.session.commit()
        flash("Økt oppdatert", "ok")
        return redirect(url_for("calendar_month",
                                year=s.dato.year, month=s.dato.month))
    return render_template("session_form.html",
                           session=s, prefill=None,
                           default_date=s.dato.isoformat())


@app.route("/okt/<int:sid>/json")
@login_required
def session_json(sid: int):
    s = db.session.get(Session, sid) or abort(404)
    if s.user_id != current_user.id:
        abort(403)
    return jsonify({
        "id": s.id,
        "dato": s.dato.isoformat(),
        "aktivitet": s.aktivitet,
        "okttype": s.okttype,
        "teknikk": s.teknikk,
        "varighet": s.varighet,
        "distanse_km": s.distanse_km,
        "rpe": s.rpe,
        "kommentar": s.kommentar,
        "edit_url": url_for("session_edit", sid=s.id),
        "delete_url": url_for("session_delete", sid=s.id),
    })


@app.route("/okt/<int:sid>/slett", methods=["POST"])
@login_required
def session_delete(sid: int):
    s = db.session.get(Session, sid) or abort(404)
    if s.user_id != current_user.id:
        abort(403)
    db.session.delete(s)
    db.session.commit()
    flash("Økt slettet", "ok")
    return redirect(request.referrer or url_for("calendar_month"))


# ---------------------------------------------------------------------------
# Maler
# ---------------------------------------------------------------------------
@app.route("/maler")
@login_required
def templates_list():
    items = (Template.query
             .filter_by(user_id=current_user.id)
             .order_by(Template.navn)
             .all())
    return render_template("templates_list.html", maler=items)


@app.route("/maler/<int:tid>/slett", methods=["POST"])
@login_required
def template_delete(tid: int):
    t = db.session.get(Template, tid) or abort(404)
    if t.user_id != current_user.id:
        abort(403)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for("templates_list"))


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
@app.route("/admin/brukere", methods=["GET", "POST"])
@admin_required
def admin_users():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        name = request.form.get("name", "").strip() or None
        email = request.form.get("email", "").strip() or None
        role = request.form.get("role", "bruker")
        if not username or not password:
            flash("Brukernavn og passord er påkrevd", "error")
        elif User.query.filter_by(username=username).first():
            flash(f"Brukernavn '{username}' finnes allerede", "error")
        elif len(password) < 4:
            flash("Passord må ha minst 4 tegn", "error")
        else:
            u = User(username=username, name=name, email=email, role=role)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash(f"Bruker '{username}' opprettet", "ok")
        return redirect(url_for("admin_users"))
    return render_template("admin_users.html",
                           users=User.query.order_by(User.username).all())


@app.route("/admin/brukere/<int:uid>/passord", methods=["POST"])
@admin_required
def admin_user_password(uid: int):
    u = db.session.get(User, uid) or abort(404)
    new_password = request.form.get("new_password", "")
    if len(new_password) < 4:
        flash("Passord må ha minst 4 tegn", "error")
    else:
        u.set_password(new_password)
        db.session.commit()
        flash(f"Nytt passord satt for {u.username}", "ok")
    return redirect(url_for("admin_users"))


@app.route("/admin/brukere/<int:uid>/slett", methods=["POST"])
@admin_required
def admin_user_delete(uid: int):
    u = db.session.get(User, uid) or abort(404)
    if u.id == current_user.id:
        flash("Du kan ikke slette deg selv", "error")
    else:
        db.session.delete(u)
        db.session.commit()
        flash("Bruker slettet", "ok")
    return redirect(url_for("admin_users"))


@app.route("/admin/verdilister", methods=["GET", "POST"])
@admin_required
def admin_lookups():
    if request.method == "POST":
        category = request.form["category"]
        value = request.form["value"].strip()
        if category in {"aktivitet", "okttype", "teknikk"} and value:
            exists = LookupValue.query.filter_by(category=category, value=value).first()
            if not exists:
                db.session.add(LookupValue(category=category, value=value))
                db.session.commit()
        return redirect(url_for("admin_lookups"))
    return render_template("admin_lookups.html",
                           aktiviteter=LookupValue.query.filter_by(category="aktivitet").all(),
                           okttyper=LookupValue.query.filter_by(category="okttype").all(),
                           teknikker=LookupValue.query.filter_by(category="teknikk").all())


@app.route("/admin/verdilister/<int:lid>/slett", methods=["POST"])
@admin_required
def admin_lookup_delete(lid: int):
    v = db.session.get(LookupValue, lid) or abort(404)
    db.session.delete(v)
    db.session.commit()
    return redirect(url_for("admin_lookups"))


# ---------------------------------------------------------------------------
# Initialdata
# ---------------------------------------------------------------------------
def init_db() -> None:
    db.create_all()

    # Light migration: legg til nye kolonner på User-tabellen hvis de mangler
    # på en eldre database (PythonAnywhere SQLite eller Render Postgres som
    # ble opprettet før name/email ble lagt til).
    inspector = db.inspect(db.engine)
    if inspector.has_table("user"):
        existing = {c["name"] for c in inspector.get_columns("user")}
        with db.engine.begin() as conn:
            if "name" not in existing:
                conn.execute(db.text('ALTER TABLE "user" ADD COLUMN name VARCHAR(120)'))
            if "email" not in existing:
                conn.execute(db.text('ALTER TABLE "user" ADD COLUMN email VARCHAR(120)'))

    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password("admin")
        db.session.add(admin)

    defaults = {
        "aktivitet": ["Løp", "Rulleski", "Langrenn", "Sykkel", "Skyting", "Fotball", "Kombi"],
        "okttype":   ["Intervall", "Rolig", "Konkurranse", "Styrke"],
        "teknikk":   ["Klassisk", "Skøyting", "Motbakke"],
    }
    for category, values in defaults.items():
        for i, v in enumerate(values):
            if not LookupValue.query.filter_by(category=category, value=v).first():
                db.session.add(LookupValue(category=category, value=v, sort_order=i))
    db.session.commit()


# Kjør init_db() ved oppstart – også når gunicorn (Render) importerer appen,
# ikke bare når den startes direkte med `python app.py`. Operasjonen er
# idempotent (oppretter kun manglende tabeller / standardverdier).
with app.app_context():
    init_db()


if __name__ == "__main__":
    import socket
    port = 5000
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except OSError:
        local_ip = None
    print("=" * 60)
    print(f"  PC:     http://127.0.0.1:{port}")
    if local_ip:
        print(f"  Mobil:  http://{local_ip}:{port}   (samme wifi som PC-en)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=True)
