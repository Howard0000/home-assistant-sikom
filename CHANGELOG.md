# Changelog

Alle vesentlige endringer i dette prosjektet dokumenteres her.

## [v1.0.3] – 2025-09-23
### Fixed
- Fjernet dupliserte "tomt skall"-enheter for termostater.  
- Nå kombineres `climate` og tilhørende `målt temperatur`-sensor under samme enhet i Home Assistant.  

---

## [v1.0.2] – 2025-09-22
### Added
- Ny `*_malt_temperatur` sensor for enheter som eksponerer målt temperatur i API-et (f.eks. SI-4, Eco Glamox Receiver).
- Støtte for Eco Glamox Receiver (`ECOGlamoxPlug`).

### Improved
- Sensorer arver nå "friendly name" fra sine parent-enheter (f.eks. *Stue Målt temperatur*) for enklere identifisering i Home Assistant.

---

## [v1.0.1] – 2025-09-20
### Changed
- Oppdatert `README.md` med engelsk installasjonsveiledning.
- Forbedret installasjonsbeskrivelse for HACS (søk etter **Sikom → Install**).

---

## [v1.0.0] – 2025-09-15
### Initial Release
- Første HACS-release.
- Oppdatert `manifest.json`.

