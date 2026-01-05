# Changelog

---

All notable changes to this project will be documented here.

## [1.1.1] – 2026-01-05  
### 🛠️ Fikset – Migrering for eksisterende installasjoner

Denne versjonen retter et migreringsproblem som kunne oppstå ved oppgradering fra eldre versjoner til **v1.1.0**, hvor Home Assistant kunne vise *Migration Error* og midlertidig fjerne alle entiteter.

### Endringer

- **Automatisk migrering av eksisterende config entries**
  - `async_migrate_entry` er nå implementert.
  - Rydder opp i utgåtte konfigurasjonsfelt (bl.a. `ADRESSE`).
  - Oppdaterer intern config-versjon på en trygg måte.

- **Oppdatert config entry-versjon**
  - Sikrer at Home Assistant korrekt trigget migrering ved oppgradering.

### Viktig
- **Ingen reinstallering er nødvendig** fra og med denne versjonen.
- Brukere som allerede har slettet og lagt inn integrasjonen på nytt påvirkes ikke negativt.

### Anbefaling
Alle brukere på **v1.1.0** anbefales å oppgradere til **v1.1.1** for å sikre korrekt migrering og stabil oppstart.

---

### 🛠️ Fixed – Migration for existing installations

This release fixes a migration issue that could occur when upgrading from older versions to **v1.1.0**, where Home Assistant could report a *Migration Error* and temporarily remove all entities.

### Changes

- **Automatic migration of existing config entries**
  - `async_migrate_entry` is now implemented.
  - Cleans up deprecated configuration fields (including `ADRESSE`).
  - Safely updates the internal config entry version.

- **Updated config entry version**
  - Ensures Home Assistant correctly triggers migration during upgrades.

### Important
- **No reinstallation is required** starting from this version.
- Users who have already removed and re-added the integration are not negatively affected.

### Recommendation
All users on **v1.1.0** are recommended to upgrade to **v1.1.1** to ensure proper migration and stable startup.

---

## [1.1.0] – 2026-01-04  
### 🧠 Forbedret oppsett, stabilitet og datagrunnlag (AppView)

Denne versjonen markerer en større intern forbedring av integrasjonen, med fokus på stabilitet, ryddigere oppstart og mer presis håndtering av data fra Sikom sitt *AppView*-endepunkt.

Endringene er bakoverkompatible for de fleste brukere, men konfigurasjonsflyten og intern datamodell er forbedret sammenlignet med **1.0.x**.

### Viktige forbedringer

- **Ny og mer robust config flow:**
  - Gateway (sentralenhet) identifiseres eksplisitt.
  - Brukeren velger hvilke enheter som skal inkluderes.

- **Forbedret håndtering av AppView v4.0:**
  - Kun tilgjengelige og gyldige måleverdier opprettes som sensorer.
  - Fjerner støy fra sensorer som tidligere ble stående som *utilgjengelig*.

- **Mer presis filtrering av temperaturverdier:**
  - Temperatursensorer opprettes kun når gyldig temperatur faktisk rapporteres.

- **Ny AppView Heartbeat (diagnostisk sensor):**
  - Bekrefter at integrasjonen mottar oppdateringer fra Sikom-skyen.
  - Oppdateres automatisk ca. hvert **5.–6. minutt**.

- Forbedret intern struktur og koordinering av API-data.

### Merk
Denne versjonen bygger videre på dagens offentlige **Connome / AppView API**.  
Integrasjonen er gjort mer robust mot endringer i tilgjengelige felter, men fremtidige endringer i Sikom sin backend kan fortsatt påvirke funksjonalitet.

### Anbefaling
Alle brukere anbefales å oppgradere til **v1.1.0** for best stabilitet og ryddigere entitetsoppsett.

---

### 🧠 Improved setup, stability, and AppView handling

This release introduces significant internal improvements focused on stability, clean startup behavior, and more accurate handling of data from Sikom’s *AppView* endpoint.

While largely backward compatible, configuration flow and internal data handling have been improved compared to the **1.0.x** series.

### Key improvements

- **New and more robust configuration flow:**
  - Explicit gateway (controller) identification.
  - User-controlled device selection.

- **Improved handling of AppView v4.0:**
  - Sensors are only created for values that are actually available.
  - Eliminates noisy *unavailable* entities.

- **More accurate temperature handling:**
  - Temperature sensors are created only when valid values are reported.

- **New AppView Heartbeat diagnostic sensor:**
  - Confirms ongoing communication with the Sikom cloud.
  - Updates automatically every **~5–6 minutes**.

- Improved internal structure and API coordination.

### Note
This version continues to rely on the current public **Connome / AppView API**.  
While more resilient to API changes, future backend updates by Sikom may still affect functionality.

### Recommendation
All users are recommended to upgrade to **v1.1.0** for improved stability and cleaner entity management.

---

## [1.0.8] – 2025-12-31  
### 🔐 Hotfix – Sikom API klientvalidering  

Denne versjonen retter en feil i **v1.0.7** der enkelte API-kall kunne feile med  
`403 Forbidden` etter nye klientkrav hos **Sikom / Connome BPAPI**.

**Endringer:**  
- API-kall etterligner nå en standard nettleser (User-Agent og HTTP-headere).  
- Løser `403 Forbidden` på:
  - `VerifyCredentials`
  - `AddProperty`
  - `TurnOn` / `TurnOff`
- Forbedret stabilitet ved styring og statusoppdateringer.  
- Ingen endringer i konfigurasjon, entiteter eller brukerinndata.

**Anbefaling:**  
Alle brukere anbefales å oppdatere til **v1.0.8** dersom de opplever  
`Authentication failed (403)` eller ustabil styring.

---

### 🔐 Hotfix – Sikom API client validation  

This release fixes an issue in **v1.0.7** where certain API calls could fail with  
`403 Forbidden` due to new client validation requirements in the  
**Sikom / Connome BPAPI**.

**Changes:**  
- API requests now mimic a standard browser client (User-Agent and headers).  
- Fixes `403 Forbidden` errors on:
  - `VerifyCredentials`
  - `AddProperty`
  - `TurnOn` / `TurnOff`
- Improved stability for control actions and status updates.  
- No changes to configuration, entities, or user input.

**Recommendation:**  
All users are recommended to update to **v1.0.8** if they experience  
`Authentication failed (403)` or unreliable control.

---

## [1.0.7] – 2025-12-30  
### 🔐 Fikset – Autentisering og stabilitet mot Sikom API  

Denne versjonen gjenoppretter stabil tilkobling mot **Sikom / Connome BPAPI** etter endringer på serversiden som kunne føre til `401/403 Authentication failed`.

**Endringer:**  
- Normaliserer passord-input (fjerner skjulte tegn ved copy/paste).  
- Automatisk håndtering av konti som krever `!!!`-suffix på passord.  
- Autentisering verifiseres eksplisitt via `VerifyCredentials`.  
- Forbedret feilhåndtering og logging ved innlogging.

**Anbefaling:**  
Oppdater til **v1.0.7** dersom integrasjonen sluttet å fungere uten lokale endringer.  
Ingen endringer i konfigurasjon eller entiteter er nødvendig.

---

### 🔐 Fixed – Authentication and API stability  

This release restores reliable connectivity to the **Sikom / Connome BPAPI** after server-side changes that caused `401/403 Authentication failed` errors.

**Changes:**  
- Normalizes password input (removes hidden copy/paste characters).  
- Automatically handles accounts requiring a `!!!` password suffix.  
- Explicit authentication verification via `VerifyCredentials`.  
- Improved error handling and login logging.

**Recommendation:**  
Update to **v1.0.7** if the integration stopped working without local changes.  
No configuration or entity changes are required.

---

## [1.0.6] – 2025-10-28  
### 🌡️ Ny funksjon – Temperaturprober og automatisk API-oppdatering  

Denne versjonen utvider støtten for **GSM Eco Controller 3 (4G)** med automatisk oppdagelse av kablede temperaturfølere tilknyttet relé 1 og 2.  
I tillegg oppdateres nå alle data automatisk hvert **5.–6. minutt** via *AppView*-endepunktet.

**Endringer:**  
- Automatisk opprettelse av temperatursensorer for relé 1 og 2.  
- Støtte for flere prober – én sensor per relé med gyldig temperatur.  
- Automatisk *AppView v4.0*-refresh hvert 5.–6. minutt.  
- Forbedret intern logging.

**Anbefaling:**  
Oppdater til **v1.0.6** dersom du bruker **Eco Controller 3 (4G)**.

---

### 🌡️ Added – Temperature probes and automatic API refresh  

Extends support for **GSM Eco Controller 3 (4G)** by automatically detecting wired temperature probes on relay 1 and 2.  
Introduces a scheduled *AppView* refresh every **5–6 minutes**.

**Changes:**  
- Automatic creation of temperature sensors for relays 1 and 2.  
- One sensor per relay with valid temperature.  
- Automatic *AppView v4.0* refresh every 5–6 minutes.  
- Improved internal logging.

---

## [1.0.5] – 2025-10-25  
### 🔧 Hotfix – Tilbakestilling til v1.0.3  

Denne versjonen ruller hele kodebasen tilbake til siste stabile versjon.

**Endringer:**  
- Tilbakestilt til v1.0.3.  
- Fjernet regresjoner introdusert i v1.0.4.

---

### 🔧 Hotfix – Rollback to v1.0.3  

This release restores the last stable codebase.

**Changes:**  
- Full rollback to v1.0.3.  
- Removed regressions from v1.0.4.

---

## [1.0.4] – 2025-10-24  
### 🔥 Ny funksjon – Grunnleggende temperatursensor  

Første versjon av temperatursensor for **Eco Controller 3 (GEC-III)**.

---

### 🔥 Added – Basic temperature sensor  

Initial temperature sensor support for **Eco Controller 3 (GEC-III)**.

---

## [1.0.3] – 2025-09-23  
### 🧩 Rettet  
- Fjernet duplikate “tomskall”-enheter.  
- Termostat og temperatursensor grupperes nå korrekt.

---

### 🧩 Fixed  
- Removed duplicate “empty shell” devices.  
- Thermostat and temperature sensor are now grouped correctly.

---

## [1.0.2] – 2025-09-22  
### ➕ Nytt  
- Ny `*_målt_temperatur`-sensor.  
- Støtte for **Eco Glamox Receiver**.

---

### ➕ Added  
- New `*_measured_temperature` sensor.  
- Support for **Eco Glamox Receiver**.

---

## [1.0.1] – 2025-09-20  
### ✏️ Endret  
- Oppdatert README med engelsk installasjonsguide.

---

### ✏️ Changed  
- Updated README with English installation guide.

---

## [1.0.0] – 2025-09-15  
### 🚀 Første offisielle utgivelse  

---

### 🚀 Initial release  
