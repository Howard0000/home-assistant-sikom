# Changelog

All notable changes to this project will be documented here.

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


