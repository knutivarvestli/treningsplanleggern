# Oppdatere appen på PythonAnywhere

Kort referanse for å rulle ut nye endringer fra GitHub til
PythonAnywhere. For førstegangsoppsett, se
[deploy-pythonanywhere.md](deploy-pythonanywhere.md).

---

## Standard oppdateringsrutine

### 1. Push endringer fra PC-en til GitHub

```powershell
git add <filer-du-har-endret>
git commit -m "Beskrivelse av endring"
git push
```

(Eller la Claude Code gjøre det — be om «commit og push».)

### 2. Trekk ned endringer på PythonAnywhere

Logg inn på https://www.pythonanywhere.com → **Consoles** → åpne en
eksisterende Bash-konsoll, eller start en ny.

```bash
cd ~/treningsplanleggern
git pull
```

### 3. Reload web-appen

Gå til **Web**-fanen og klikk den grønne **Reload**-knappen øverst.

Vent ~10 sekunder, last inn nettsiden og bekreft at endringene er der.

---

## Når du har endret `requirements.txt`

Hvis du har lagt til eller fjernet pakker, kjør i Bash etter `git pull`:

```bash
cd ~/treningsplanleggern
.venv/bin/pip install -r requirements.txt
```

Deretter Reload på Web-fanen.

---

## Når du har endret database-modellen

Appen bruker en innebygget «light migration» i `init_db()` som kjører
`ALTER TABLE ADD COLUMN` for nye kolonner ved oppstart. For typiske
endringer (legge til en kolonne) trenger du **ikke** gjøre noe manuelt
— bare reload, så er det i orden.

For større endringer (slette/endre kolonner, ny tabell-struktur) må du
enten utvide migrations-koden eller resette databasen manuelt:

```bash
cd ~/treningsplanleggern
mv treningsplanlegger.db treningsplanlegger.db.backup
```

Reload appen, så lager `init_db()` en fersk database. **OBS:** dette
sletter all eksisterende data — bruk kun hvis du er sikker.

---

## Sjekkliste når noe går galt

1. **Endringer vises ikke i nettleseren**
   - Glemt å klikke **Reload**? Web-fanen → grønn knapp.
   - Hard refresh i nettleseren: `Ctrl+F5` (Windows) eller `Cmd+Shift+R` (Mac).

2. **«Something went wrong» / Unhandled Exception**
   - Web-fanen → **Log files** → `<brukernavn>.pythonanywhere.com.error.log`.
   - Se på de nederste 30 linjene — feilen er der.

3. **`git pull` sier «Your local changes would be overwritten»**
   - Du har endret filer direkte på PythonAnywhere. Enten:
     - Forkast endringene: `git checkout -- <fil>`
     - Eller commit dem først: `git stash` før `git pull`, så `git stash pop`.

4. **Får ikke `git pull` til å logge inn**
   - Hvis repoet ble klonet med Personal Access Token i URL-en, og tokenet
     er utløpt, oppdater remote:
     ```bash
     git remote set-url origin https://<NYTT-TOKEN>@github.com/knutivarvestli/treningsplanleggern.git
     ```
   - For offentlig repo trengs ingen autentisering.

---

## Tips: én-linjes update

Når alt sitter, kan du gjøre dette i én kommando i Bash:

```bash
cd ~/treningsplanleggern && git pull && echo "OK – husk å klikke Reload"
```
