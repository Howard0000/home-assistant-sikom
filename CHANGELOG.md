# Changelog

All notable changes to this project will be documented here.

## [1.0.7] – 2025-12-30  
### 🔐 Fikset – Autentisering og stabilitet mot Sikom API  
Denne versjonen gjenoppretter stabil tilkobling mot **Sikom / Connome BPAPI** etter endringer på serversiden som kunne føre til `401/403 Authentication failed`.

**Endringer:**  
- Normaliserer passord-input (fjerner skjulte tegn ved copy/paste).  
- Automatisk håndtering av konti som krever `!!!`-suffix på passord.  
- Autentisering verifiseres eksplisitt via `VerifyCredentials`-endepunktet.  
- Forbedret HTTP-headere for å unngå feilaktige `403 Forbidden`-responser.  
- Mer robust feilhåndtering og logging ved innlogging.

**Anbefaling:**  
Alle brukere anbefales å oppdatere til **v1.0.7** dersom integrasjonen tidligere har sluttet å fungere uten lokale endringer.  
Ingen endringer i konfigurasjon eller entiteter er nødvendig.

---

### 🔐 Fixed – Authentication and API stability  
This release restores reliable connectivity to the **Sikom / Connome BPAPI** after server-side changes that could cause `401/403 Authentication failed` errors.

**Changes:**  
- Normalizes password input (removes hidden characters from copy/paste).  
- Automatically handles accounts requiring a `!!!` password suffix.  
- Explicit authentication verification via the `VerifyCredentials` endpoint.  
- Improved HTTP headers to avoid erroneous `403 Forbidden` responses.  
- More robust error handling and logging during login.

**Recommendation:**  
All users are recommended to update to **v1.0.7** if the integration stopped working without local changes.  
No configuration or entity changes are required.


---

## [1.0.6] – 2025-10-28  
### 🌡️ Ny funksjon – Temperaturprober og automatisk API-oppdatering  
Denne versjonen utvider støtten for **GSM Eco Controller 3 (4G)** med automatisk oppdagelse av kablede temperaturfølere tilknyttet relé 1 og 2.  
I tillegg oppdateres nå alle data automatisk hvert **5.–6. minutt** via *AppView*-endepunktet, slik at verdier i Home Assistant alltid holdes synkronisert uten behov for å åpne Sikom-appen.

**Endringer:**  
- Automatisk opprettelse av temperatursensorer for relé 1 og 2 på Eco Controller 3.  
- Full støtte for flere prober – én sensor per relé med gyldig temperatur.  
- Ny mekanisme som sender et *refresh-kall* til Sikom API hvert 5.–6. minutt (AppView v4.0).  
- Forbedret intern logging for feilsøking av API-oppdateringer.  
- Ingen andre endringer i funksjonalitet.

**Anbefaling:**  
Oppdater til **v1.0.6** dersom du bruker **Eco Controller 3 (4G)** eller ønsker kontinuerlig automatisk oppdatering av alle Sikom-enheter.  
Bakoverkompatibel for alle tidligere versjoner.

---

### 🌡️ Added – Temperature probes and automatic API refresh  
This version extends support for **GSM Eco Controller 3 (4G)** by automatically detecting wired temperature probes connected to relay 1 and 2.  
It also introduces a scheduled *AppView* refresh every **5–6 minutes**, ensuring that Home Assistant stays up to date without manually opening the Sikom app.

**Changes:**  
- Automatic creation of temperature sensors for relays 1 and 2 on Eco Controller 3.  
- Full support for multiple probes – one sensor per relay with valid temperature.  
- Introduced automatic *AppView* refresh every 5–6 minutes (AppView v4.0).  
- Improved internal logging for API refresh diagnostics.  
- No other functional changes.

**Recommendation:**  
Update to **v1.0.6** if you use **Eco Controller 3 (4G)** or want continuous automatic updates for all Sikom devices.  
Fully backward compatible.

---

## [1.0.5] – 2025-10-25  
### 🔧 Hotfix – Tilbakestilling til v1.0.3  
Denne versjonen gjenoppretter stabil kode etter feil introdusert i v1.0.4.  
Ingen nye funksjoner eller endringer i funksjonalitet.

**Endringer:**  
- Rullet hele kodebasen tilbake til v1.0.3 (stabil versjon).  
- Fjernet regresjoner og API-feil fra v1.0.4.  
- Beholder full funksjonalitet fra tidligere stabil versjon.

**Anbefaling:**  
Alle brukere bør oppdatere til **v1.0.5** for stabil drift.

---

### 🔧 Hotfix – Rollback to v1.0.3  
This release restores the stable codebase after issues introduced in v1.0.4.  
No new features or changes in functionality.

**Changes:**  
- Reverted the entire codebase to v1.0.3 (stable release).  
- Removed regressions and API issues from v1.0.4.  
- Retains all features from the previous stable version.

**Recommendation:**  
All users should update to **v1.0.5** for stable operation.

---

## [1.0.4] – 2025-10-24  
### 🔥 Ny funksjon – Grunnleggende temperatursensor  
Denne versjonen introduserte første versjon av temperatursensor for **Eco Controller 3 (GEC-III)**.  
Sensoren ble opprettet automatisk når API-et rapporterte en numerisk temperaturverdi. Tekstverdier som *«Less than 55°C»* ble ignorert.  

**Forbedret:**  
- Automatisk *refresh* mot `AppView/v4.0` hvert 5. minutt.  
- Robust håndtering av temperaturdata og tekstverdier.  
- Forberedt kode for fremtidig støtte for flere sensortyper og kontrollerverdier.

---

### 🔥 Added – Basic temperature sensor  
Introduced the first version of the temperature sensor for **Eco Controller 3 (GEC-III)**.  
The sensor was automatically created when the API reported a numeric temperature value. Text values like *“Less than 55°C”* were ignored.  

**Improved:**  
- Added periodic *AppView/v4.0* refresh every 5 minutes.  
- Improved parsing of temperature values.  
- Prepared for additional sensors and control values in future versions.

---

## [1.0.3] – 2025-09-23  
### 🧩 Rettet  
- Fjernet duplikate “tomskall”-enheter for termostater.  
- Termostat-enhet (`climate`) og tilhørende `*_målt_temperatur`-sensor grupperes nå under samme enhet i Home Assistant.

---

### 🧩 Fixed  
- Removed duplicate “empty shell” devices for thermostats.  
- Thermostat (`climate`) and related `*_measured_temperature` sensors are now grouped under the same device in Home Assistant.

---

## [1.0.2] – 2025-09-22  
### ➕ Nytt  
- Ny `*_målt_temperatur`-sensor for enheter som rapporterer faktisk temperatur i API-et (f.eks. SI-4, Eco Glamox Receiver).  
- Støtte for **Eco Glamox Receiver** (`ECOGlamoxPlug`).  

**Forbedret:**  
- Sensorer arver nå “vennlige navn” fra tilhørende enhet (f.eks. *Stue Målt temperatur*) for enklere identifisering.

---

### ➕ Added  
- New `*_measured_temperature` sensor for devices exposing actual temperature in the API (e.g. SI-4, Eco Glamox Receiver).  
- Support for **Eco Glamox Receiver** (`ECOGlamoxPlug`).  

**Improved:**  
- Sensors now inherit “friendly names” from their parent device (e.g. *Living Room Measured Temperature*).

---

## [1.0.1] – 2025-09-20  
### ✏️ Endret  
- Oppdatert `README.md` med engelsk installasjonsguide.  
- Forbedret HACS-installasjonsbeskrivelse (søk etter **Sikom → Install**).

---

### ✏️ Changed  
- Updated `README.md` with English installation guide.  
- Improved HACS installation instructions (search for **Sikom → Install**).

---

## [1.0.0] – 2025-09-15  
### 🚀 Første offisielle utgivelse  
- Første HACS-release.  
- Oppdatert `manifest.json`.

---

### 🚀 Initial Release  
- First official HACS release.  
- Updated `manifest.json`.
