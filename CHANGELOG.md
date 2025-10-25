# Changelog

All notable changes to this project will be documented here.

## [v1.0.4] – 2025-10-24
### Added
- **Temperatursensor for Eco Controller 3 (GEC-III)**  
  Viser nå en egen sensor med navnet `Temperatur` under samme enhet som kontrolleren.  
  Sensoren opprettes automatisk dersom API-et rapporterer en numerisk verdi.  
  Tekstverdier som *«Less than 55°C»* ignoreres.

### Improved
- Integrasjonen sender nå et *refresh-kall* (`AppView/v4.0`) til Sikom-API ca. hvert **5. minutt**,  
  slik at temperaturer og status oppdateres automatisk uten at Sikom-appen må åpnes.  
- Robust parsing av temperaturdata (tekstverdier håndteres uten feil).
- Koden forberedt for fremtidig støtte av flere sensortyper og kontrollerverdier.


## [v1.0.3] – 2025-09-23
### Fixed
- Removed duplicate "empty shell" devices for thermostats.  
- Thermostat (`climate`) and related `*_malt_temperatur` sensor are now grouped under the same device in Home Assistant.  

---

## [v1.0.2] – 2025-09-22
### Added
- New `*_malt_temperatur` sensor for devices exposing measured temperature in the API (e.g. SI-4, Eco Glamox Receiver).
- Support for Eco Glamox Receiver (`ECOGlamoxPlug`).

### Improved
- Sensors now inherit "friendly names" from their parent devices (e.g. *Stue Målt temperatur*) for easier identification in Home Assistant.

---

## [v1.0.1] – 2025-09-20
### Changed
- Updated `README.md` with English installation guide.
- Improved installation instructions for HACS (search for **Sikom → Install**).

---

## [v1.0.0] – 2025-09-15
### Initial Release
- First HACS release.
- Updated `manifest.json`.


