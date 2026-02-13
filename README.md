# Sikom for Home Assistant

**Norsk** · [English](README.en.md)

[![HACS](https://img.shields.io/badge/HACS-Default-green.svg)](https://hacs.xyz/) 

En moderne, robust og brukervennlig integrasjon for å koble Sikom-enheter  
(termostater, releer og AMS-målere) til Home Assistant.

Denne integrasjonen er en *custom component* som bruker Sikoms offisielle
Connome-API. Den erstatter behovet for manuell konfigurasjon med `rest_sensor`,
`rest_command` og andre YAML-baserte løsninger.  
Alt håndteres nå via et enkelt brukergrensesnitt.

![Eksempel på Sikom-enheter i Home Assistant](images/screenshot.png)
![Eksempel på Sikom-enheter i Home Assistant](images/screenshot1.png)

---

## Funksjoner

### Automatisk enhetsdeteksjon
Finner automatisk alle termostater, releer og AMS-målere på din Sikom-konto.

### Klimakontroll
Oppretter native `climate`-entiteter for termostatene dine.

- Viser nåværende temperatur  
- Bytt enkelt mellom **Komfort** og **Sparing** (presets)  
- Juster måltemperatur for begge moduser direkte i Home Assistant  

**Målt temperatur**  
For enheter som rapporterer faktisk temperatur (f.eks. *SI-4*, *Eco Glamox Receiver* og *Eco Controller 3*) opprettes automatisk en ekstra sensor:

- `sensor.[navn]_malt_temperatur`
- Sensoren legges i samme **Enhet** som termostaten i Home Assistant  
- Eksempel: *Stue* → `climate.stue` + `sensor.stue_malt_temperatur`

For *Eco Controller 3* med kablede temperaturfølere opprettes én temperatursensor per relé
(f.eks. *Temperatur Relé 1* og *Temperatur Relé 2*).

### Automatisk oppdatering
Integrasjonen sender et *AppView*-kall til Sikom API omtrent hvert **5.–6. minutt**, slik at
temperatur, effekt og status holdes oppdatert uten at Sikom-appen må åpnes.

### Brytere
Oppretter `switch`-entiteter for enheter som varmtvannsberedere og releer.

### Energimåling
Oppretter `sensor`-entiteter for AMS-målere med:

- Sanntids strømforbruk (W)
- Total energi (kWh)

Fullt kompatibelt med Home Assistants **Energi-dashboard**.

### Enkel konfigurasjon
Ingen YAML-redigering nødvendig. Hele oppsettet skjer i Home Assistants UI.

---

## 🧩 Støttede og testede enheter

Denne integrasjonen er testet og bekreftet å fungere med følgende enheter og sentraler.
Andre modeller kan også fungere dersom de bruker de samme datafeltene i Sikom-API-et.

| Enhetstype / kategori | Modell / Type i API | Støtte |
|----------------------|--------------------|--------|
| Trådløs termostat | WirelessThermostat / SI-3 | ✅ Full støtte |
| Trådløs termostat | WirelessThermostat / SI-4 | ✅ Full støtte |
| Eco Glamox Receiver | ECOGlamoxPlug | ✅ Full støtte |
| Varmtvannsbereder / Bryter | ECONode / Tech-Rel | ✅ Full støtte |
| Billader | EaseeHome | ✅ Full støtte |
| AMS-måler | ECOEnergyController / ECO-AMS | ✅ Full støtte |
| Internrelé Eco Controller 3 | GSMECOController3_Relay | ✅ Full støtte |
| Sentral (Gateway) | GEC-III / ECOComfort2 | ⚙️ Delvis støtte |

💡 **Tips:**  
Hvis du ikke ser *AppView Heartbeat*-sensoren med en gang, søk etter  
`sensor.appview_heartbeat` og legg den manuelt til i dashbordet.

---

## 📥 Importer blueprint til Home Assistant

Blueprint for varsler fra Sikom-enheter (termostater, brytere og tilkobling).

[![Importer blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](
https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Howard0000/home-assistant-sikom/main/blueprints/sikom_varslingssentral.yaml
)

---

## Krav

- Home Assistant 2024.x eller nyere  
- Gyldig Sikom-konto  
- HACS installert

---

## Installasjon

1. Åpne **HACS → Integrations**
2. Søk etter **Sikom**
3. Klikk **Install**
4. Start Home Assistant på nytt om nødvendig

---

## 🔄 Oppgradering fra eldre versjoner

Ved oppgradering fra eldre versjoner av Sikom-integrasjonen (for eksempel `v1.0.x` eller tidlige `v1.1.x`)
kan det forekomme at **inaktive eller gamle enheter blir liggende igjen** i Home Assistant.

Dette er forventet oppførsel og skyldes forbedringer i:
- bruk av stabile `unique_id`
- intern struktur for enheter og entiteter
- mer korrekt kobling mellom Sikom-enheter og Home Assistant-entiteter

Home Assistant sletter **ikke** gamle enheter automatisk når en integrasjon endrer intern struktur.

### Anbefalt engangsopprydding

For et helt ryddig og konsistent oppsett anbefales følgende **én gang etter oppgradering**:

1. Gå til **Innstillinger → Enheter og tjenester → Sikom**
2. Velg **Slett integrasjon**
3. Legg til Sikom-integrasjonen på nytt

Dette vil normalt **ikke påvirke**:
- automasjoner
- scripts
- dashboards

Så lenge de samme enhetene finnes, vil Home Assistant automatisk koble alt tilbake
ved hjelp av integrasjonens stabile `unique_id`.

⚠️ **Merk:**  
Historikk for entiteter vil bli nullstilt når integrasjonen slettes og legges til på nytt.

---

## Konfigurasjon

1. **Innstillinger → Enheter og tjenester**
2. **Legg til integrasjon**
3. Søk etter **Sikom**
4. Logg inn med vanlig brukernavn og passord
5. Velg enhetene du vil legge til
6. Fullfør

### Endre enheter senere
Gå til **Innstillinger → Enheter og tjenester → Sikom → Konfigurer**

---

## Informasjon om Sikom API
Integrasjonen bruker Sikoms Connome REST API for kommunikasjon med enhetene.

---

## Feilsøking

- **Innlogging feiler:** Kontroller brukernavn og passord
- **Enheter utilgjengelige:** Sjekk Home Assistant-loggen for `custom_components.sikom`

---

## Anerkjennelser
Utviklet og vedlikeholdt av [@Howard0000](https://github.com/Howard0000).  
KI-assistent brukt til feilsøking og dokumentasjon.

---

## Lisens
MIT License

---

## Varemerker og navn
Logo og navn tilhører **Sikom Connect AS** og brukes kun for identifikasjon.

Dette er et uoffisielt community-prosjekt og er ikke utviklet, støttet eller godkjent av
Sikom Connect AS.

---

## ⚠️ Ansvarsfraskrivelse
Denne integrasjonen er et tredjepartsprosjekt og erstatter ikke Sikom-appen.

All bruk skjer på eget ansvar.  
For varme i fritidsboliger anbefales alltid et separat system for **frostsikring**.

Integrasjonen er ment for overvåking og automatisering – ikke som primær
styringsløsning for kritiske funksjoner.


