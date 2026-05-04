# Treningsplanleggern

## 🎯 Formål
Utvikle en enkel og fleksibel app for planlegging og oppfølging av treningsøkter for en ungdom som driver med skiskyting. Løsningen skal støtte strukturert treningsarbeid over tid og være intuitiv i bruk.

---

## 🧩 Funksjonelle krav

### 1. Registrering av treningsøkt
Brukeren skal kunne opprette treningsøkter med følgende felter:

#### Aktivitet
Hovedaktiviteten for økten.

**Verdiliste (utvidbar):**
- Løp  
- Rulleski  
- Langrenn  
- Sykkel  
- Skyting  
- Fotball  
- Kombi  
- Styrke

---

#### Økttype
Beskriver intensitet eller formål med treningsøkten.

**Verdiliste:**
- Intervall  
- Rolig  
- Konkurranse  
- Trening

---

#### Teknikk / Terreng
Spesifiserer hvordan økten gjennomføres.

**Verdiliste:**
- Klassisk  
- Skøyting  
- Motbakke  
- Annet

---

#### Varighet / Omfang
Fri tekst for å beskrive økten.

**Eksempler:**
- 1:15  
- 10 km  
- 6 x 5 min  

---

#### Dato
Dato for når økten skal gjennomføres.

---

### 2. Kalendervisning
- Alle treningsøkter skal presenteres i en kalender
- Støtte for:
  - Dagvisning  
  - Ukevisning  
  - (valgfritt) Måned  

---

### 3. Maler (gjenbruk av økter)
Brukeren skal kunne:
- Lagre treningsøkter som maler  
- Gjenbruke maler ved opprettelse av nye økter  

Dette forenkler registrering av standardøkter (f.eks. intervaller).

---

### 4. Brukerhåndtering
Systemet skal støtte:

#### Pålogging
- Brukernavn og passord  

#### Roller
- **Administrator**
  - Administrere brukere  
  - Vedlikeholde verdilister  
- **Bruker**
  - Registrere og følge opp egne treningsøkter  

---

## 🏷️ Begrepsbruk (standardisering)

| Begrep | Beskrivelse |
|--------|------------|
| Aktivitet | Hva slags aktivitet som gjennomføres |
| Økttype | Intensitet eller formål |
| Teknikk / Terreng | Hvordan økten gjennomføres |
| Varighet / Omfang | Lengde eller belastning |
| Verdiliste | Oppslagsdata som kan vedlikeholdes |

---

## 🧠 Anbefalte utvidelser (videreutvikling)

For bedre analyse og oppfølging:

- Skille mellom:
  - **Varighet (tid)**  
  - **Distanse (km)**  

- Legge til:
  - Kommentar / notat  
  - Opplevd belastning (RPE 1–10)  

- Mulighet for:
  - Analyse av treningsmengde per uke  
  - Visualisering av progresjon  

---

## 🚀 Oppsummering

En treningsøkt består av:

**Aktivitet + Økttype + Teknikk + Varighet + Dato**

Med støtte for:
- Gjenbruk via maler  
- Kalenderbasert visning  
- Fleksible og utvidbare verdilister  
