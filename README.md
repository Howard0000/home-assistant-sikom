# Sikom for Home Assistant

En moderne, robust og brukervennlig integrasjon for å koble Sikom-enheter (termostater, releer og AMS-målere) til Home Assistant.

Denne integrasjonen er en "custom component" som bruker Sikoms offisielle Connome-API. Den erstatter behovet for manuell konfigurasjon med `rest_sensor`, `rest_command` og andre YAML-baserte løsninger. Alt håndteres nå via et enkelt brukergrensesnitt.

![Eksempel på termostat i Home Assistant](https://github.com/Howard0000/home-assistant-sikom/blob/main/images/Termostat%20Gang%20Komfort.png?raw=true)

## Funksjoner

-   **Automatisk Enhetsdeteksjon:** Finner automatisk alle termostater, releer og AMS-målere på din Sikom-konto.
-   **Klimakontroll:** Oppretter native `climate`-entiteter for termostatene dine.
    -   Viser nåværende temperatur.
    -   Lar deg enkelt bytte mellom "Komfort" og "Sparing"-modus (presets).
    -   Lar deg justere måltemperaturen for både komfort- og sparingsmodus direkte fra Home Assistant.
-   **Brytere:** Oppretter `switch`-entiteter for enheter som varmtvannsberedere og releer.
-   **Energimåling:** Oppretter `sensor`-entiteter for AMS-målere med sanntids strømforbruk (W) og total energi (kWh), fullt kompatibelt med Home Assistants Energi-dashboard.
-   **Enkel Konfigurasjon:** Ingen YAML-redigering nødvendig. Hele oppsettet skjer i Home Assistants brukergrensesnitt.

## Krav

-   Home Assistant 2024.x eller nyere.
-   En gyldig Sikom-konto med tilknyttede enheter.
-   [HACS (Home Assistant Community Store)](https://hacs.xyz/) installert.

## Installasjon

Den enkleste måten å installere er via HACS.

1.  Gå til **HACS > Integrations** i Home Assistant.
2.  Klikk på de tre prikkene øverst til høyre og velg **Custom repositories**.
3.  I feltet for "Repository", lim inn `https://github.com/Howard0000/home-assistant-sikom` og velg kategorien `Integration`. Klikk **Add**.
4.  Du skal nå finne "Sikom" i HACS. Klikk på den og velg **Install**.
5.  Start Home Assistant på nytt når HACS ber om det.

*(Når integrasjonen er offisielt lagt til i HACS, kan steg 2 og 3 hoppes over, og du kan søke den opp direkte).*

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