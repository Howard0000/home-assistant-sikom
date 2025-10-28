# Sikom for Home Assistant

**Norsk** · [English](README.en.md)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

En moderne, robust og brukervennlig integrasjon for å koble Sikom-enheter (termostater, releer og AMS-målere) til Home Assistant.

Denne integrasjonen er en "custom component" som bruker Sikoms offisielle Connome-API. Den erstatter behovet for manuell konfigurasjon med `rest_sensor`, `rest_command` og andre YAML-baserte løsninger. Alt håndteres nå via et enkelt brukergrensesnitt.

![Eksempel på Sikom-enheter i Home Assistant](images/screenshot.png)
![Eksempel på Sikom-enheter i Home Assistant](images/screenshot1.png)

## Funksjoner

- **Automatisk Enhetsdeteksjon:** Finner automatisk alle termostater, releer og AMS-målere på din Sikom-konto.  

- **Klimakontroll:** Oppretter native `climate`-entiteter for termostatene dine.  
  - Viser nåværende temperatur.  
  - Lar deg enkelt bytte mellom "Komfort" og "Sparing"-modus (presets).  
  - Lar deg justere måltemperaturen for både komfort- og sparingsmodus direkte fra Home Assistant.  
  - **Målt temperatur:** For enheter som rapporterer faktisk temperatur (f.eks. *SI-4*, *Eco Glamox Receiver* og *Eco Controller 3*) opprettes det automatisk en ekstra sensor:  
    - `sensor.[navn]_malt_temperatur`  
    - Denne sensoren blir lagt i samme **Enhet** som termostaten i Home Assistant.  
    - Eksempel: *Stue* → inneholder både `climate.stue` og `sensor.stue_malt_temperatur`.  
  - For *Eco Controller 3* med kablede temperaturfølere opprettes én temperatursensor per relé (f.eks. `Temperatur Relé 1` og `Temperatur Relé 2`).  

- **Automatisk oppdatering:**  
  Integrasjonen sender et *AppView*-kall til Sikom API omtrent hvert **5.–6. minutt**, slik at verdier for temperatur, effekt og status holdes oppdatert uten at Sikom-appen må åpnes.
 

- **Brytere:** Oppretter `switch`-entiteter for enheter som varmtvannsberedere og releer.  

- **Energimåling:** Oppretter `sensor`-entiteter for AMS-målere med sanntids strømforbruk (W) og total energi (kWh), fullt kompatibelt med Home Assistants Energi-dashboard.  

- **Enkel Konfigurasjon:** Ingen YAML-redigering nødvendig. Hele oppsettet skjer i Home Assistants brukergrensesnitt.  


### 🧩 Støttede og testede enheter

Denne integrasjonen er testet og bekreftet å fungere med følgende enheter og sentraler.  
Andre modeller kan også fungere dersom de bruker de samme datafeltene i Sikom-API-et.

| Enhetstype / kategori | Modell / Type i API | Støtte og funksjonalitet |
|------------------------|--------------------|---------------------------|
| **Trådløs termostat** | `WirelessThermostat / SI-3` | ✅ Full støtte – climate + sensor for målt temperatur |
| **Trådløs termostat** | `WirelessThermostat / SI-4` | ✅ Full støtte – climate + sensor for målt temperatur |
| **Eco Glamox Receiver** | `ECOGlamoxPlug (Wireless Thermostat Glamox)` | ✅ Full støtte – climate + sensor for målt temperatur |
| **Varmtvannsbereder / Bryter** | `ECONode / Tech-Rel` | ✅ Full støtte – switch |
| **Billader** | `EaseeHome` | ✅ Full støtte – switch og sensor |
| **AMS-måler** | `ECOEnergyController / ECO-AMS` | ✅ Full støtte – sensorer for strøm, spenning og energi |
| **Internrelé i Eco Controller 3 (LTE-M)** | `GSMECOController3_Relay / GEC-III` | ✅ Full støtte – switch + temperatursensor(er) for relé 1 og 2 (hvis prober er tilkoblet) |
| **Sentralenhet (Gateway)** | `GSMECOController3_Relay / GEC-III (LTE-M)` | ⚙️ Delvis støtte – viser tilkoblingsstatus (`binary_sensor`) og *AppView Heartbeat* (oppdateres ca. hvert 5. minutt) |
| **Sentralenhet (Gateway)** | `ECOComfort2 4G` | ⚙️ Delvis støtte – viser tilkoblingsstatus (`binary_sensor`) og *AppView Heartbeat* (oppdateres ca. hvert 5. minutt) |

💡 **Tips:**  
Hvis du ikke ser sensoren *AppView Heartbeat* umiddelbart, kan du søke den opp i Home Assistant (`sensor.appview_heartbeat`) og legge den manuelt til i dashbordet.  
Denne sensoren viser at integrasjonen kommuniserer med Sikom-skyen og oppdateres automatisk hvert 5.–6. minutt.



## 📥 Importer blueprint direkte til Home Assistant

Dette blueprintet gjør det enkelt å motta varsler fra dine **Sikom-enheter** i Home Assistant.  
Det støtter både termostater, varmtvannsbereder/brytere og tilkoblingssensorer (for strømbrudd).  
For brytere er det bygget inn logikk som sikrer at endringen er **stabil** før varselet sendes, slik at du slipper falske alarmer ved raske av/på-flimringer.

[![Importer blueprint til Home Assistant](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Howard0000/home-assistant-sikom/main/blueprints/sikom_varslingssentral.yaml)

## Krav

-   Home Assistant 2024.x eller nyere.
-   En gyldig Sikom-konto med tilknyttede enheter.
-   [HACS (Home Assistant Community Store)](https://hacs.xyz/) installert.

## Installasjon

Den enkleste måten å installere er via HACS.

1.  Åpne HACS → Integrations i Home Assistant.
2.  Søk etter Sikom.
3.  Velg integrasjonen og klikk Install.
4.  Start Home Assistant på nytt hvis du blir bedt om det.

## Konfigurasjon

Når integrasjonen er installert, konfigurerer du den i Home Assistant:

1.  Gå til **Innstillinger > Enheter og tjenester**.
2.  Klikk på **Legg til integrasjon** nede til høyre.
3.  Søk etter **"Sikom"** og velg den.
4.  Skriv inn brukernavn (e-post) og passord for din Sikom-konto.
5.  Du vil få presentert en liste over alle enheter som ble funnet. Kryss av for de du ønsker å legge til i Home Assistant.
6.  Klikk "Fullfør", og enhetene dine vil bli lagt til!

### Endre enheter senere

Hvis du legger til eller fjerner enheter i Sikom-systemet ditt, kan du enkelt oppdatere Home Assistant:
1.  Gå til **Innstillinger > Enheter og tjenester** og finn Sikom-integrasjonen.
2.  Klikk på **«Konfigurer»** (tannhjul-ikonet).
3.  Du vil nå se den oppdaterte listen over enheter og kan endre hvilke som skal være inkludert.

## Informasjon om Sikom API

Integrasjonen bruker Sikoms Connome REST API.

#### Autentisering
APIet krever at passordet ditt etterfølges av `!!!`. Denne integrasjonen legger til dette automatisk for deg, så du skal kun skrive inn ditt vanlige passord i konfigurasjonen.

## Feilsøking

-   **"Authentication failed" / "Innlogging feilet" under konfigurasjon:** Dobbeltsjekk at brukernavn og passord er korrekt.
-   **Enheter viser "utilgjengelig":** Sjekk Home Assistant-loggen for feilmeldinger fra `custom_components.sikom`. Det kan skyldes midlertidige problemer med Sikom-APIet eller din internett-tilkobling.

## Anerkjennelser

Prosjektet er skrevet og vedlikeholdt av [@Howard0000](https://github.com/Howard0000). En KI-assistent har hjulpet til med feilsøking, kodeforbedringer og dokumentasjon. All konfigurasjon og testing er gjort av meg.

## Lisens

Dette prosjektet er lisensiert under [MIT License](LICENSE).

## Merknad


Dette er et uoffisielt community-prosjekt og er ikke utviklet, støttet eller vedlikeholdt av Sikom AS. All bruk skjer på eget ansvar.



























