# Changelog

All notable changes to this project will be documented here.

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
