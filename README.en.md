# Sikom for Home Assistant

[Norsk](README.md) · **English**

[![HACS](https://img.shields.io/badge/HACS-Default-green.svg)](https://hacs.xyz/) 

A modern, robust, and user-friendly integration for connecting Sikom devices  
(thermostats, relays, and AMS meters) to Home Assistant.

This integration is a *custom component* that uses Sikom’s official
Connome API. It replaces the need for manual configuration using
`rest_sensor`, `rest_command`, and other YAML-based solutions.  
Everything is handled through a simple and clean user interface.

![Example of Sikom devices in Home Assistant](images/screenshot.png)
![Example of Sikom devices in Home Assistant](images/screenshot1.png)

---

## Features

### Automatic device discovery
Automatically discovers all thermostats, relays, and AMS meters connected to your Sikom account.

### Climate control
Creates native `climate` entities for your thermostats.

- Displays current temperature  
- Easily switch between **Comfort** and **Eco** presets  
- Adjust target temperature for both modes directly from Home Assistant  

**Measured temperature**  
For devices that report actual temperature (e.g. *SI-4*, *Eco Glamox Receiver*, and *Eco Controller 3*), an additional sensor is created automatically:

- `sensor.[name]_measured_temperature`
- The sensor is added to the same **Device** as the thermostat in Home Assistant  
- Example: *Living Room* → `climate.living_room` + `sensor.living_room_measured_temperature`

For *Eco Controller 3* with wired temperature probes, one temperature sensor per relay is created
(e.g. *Temperature Relay 1* and *Temperature Relay 2*).

### Automatic updates
The integration performs an *AppView* request to the Sikom API approximately every **5–6 minutes**, keeping
temperature, power, and status values up to date without needing to open the Sikom mobile app.

### Switches
Creates `switch` entities for devices such as water heaters and relays.

### Energy monitoring
Creates `sensor` entities for AMS meters with:

- Real-time power usage (W)
- Total energy consumption (kWh)

Fully compatible with Home Assistant’s **Energy Dashboard**.

### Easy configuration
No YAML editing required. All setup is handled through the Home Assistant UI.

---

## 🧩 Supported and tested devices

This integration has been tested and confirmed to work with the following devices and controllers.
Other models may also work if they use the same data fields in the Sikom API.

| Device type / category | Model / API type | Support |
|-----------------------|------------------|---------|
| Wireless thermostat | WirelessThermostat / SI-3 | ✅ Full support |
| Wireless thermostat | WirelessThermostat / SI-4 | ✅ Full support |
| Eco Glamox Receiver | ECOGlamoxPlug | ✅ Full support |
| Water heater / Relay | ECONode / Tech-Rel | ✅ Full support |
| EV charger | EaseeHome | ✅ Full support |
| AMS meter | ECOEnergyController / ECO-AMS | ✅ Full support |
| Internal relay (Eco Controller 3) | GSMECOController3_Relay | ✅ Full support |
| Gateway (Controller) | GEC-III / ECOComfort2 | ⚙️ Partial support |

💡 **Tip:**  
If you don’t see the *AppView Heartbeat* sensor immediately, search for  
`sensor.appview_heartbeat` and add it manually to your dashboard.

---

## 📥 Import blueprint into Home Assistant

Blueprint for notifications from Sikom devices (thermostats, switches, and connectivity).

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](
https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Howard0000/home-assistant-sikom/main/blueprints/sikom_varslingssentral.yaml
)

---

## Requirements

- Home Assistant 2024.x or newer  
- A valid Sikom account  
- HACS installed

---

## Installation

1. Open **HACS → Integrations**
2. Search for **Sikom**
3. Click **Install**
4. Restart Home Assistant if prompted

---

## 🔄 Upgrading from older versions

When upgrading from older versions of the Sikom integration (such as `v1.0.x` or early `v1.1.x`),
you may notice inactive or legacy devices remaining in Home Assistant.

This is expected behavior and is caused by improvements in:
- stable `unique_id` usage
- internal device and entity structure
- more accurate mapping between Sikom devices and Home Assistant entities

Home Assistant does **not automatically remove old devices** when an integration changes its internal structure.

### Recommended one-time cleanup

For a fully clean and consistent setup, it is recommended to perform the following **once after upgrading**:

1. Go to **Settings → Devices & Services → Sikom**
2. Select **Delete integration**
3. Add the Sikom integration again

This will normally **not** affect:
- automations
- scripts
- dashboards

As long as the same devices are present, Home Assistant will automatically reconnect everything
using the integration’s stable `unique_id`s.

⚠️ **Note:**  
Entity history will be reset when the integration is removed and re-added.

---

## Configuration

1. **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Sikom**
4. Log in using your normal username and password
5. Select the devices you want to add
6. Finish setup

### Modify devices later
Go to **Settings → Devices & Services → Sikom → Configure**

---

## Sikom API information
The integration uses Sikom’s Connome REST API to communicate with your devices.

---

## Troubleshooting

- **Authentication failed:** Verify username and password
- **Entities unavailable:** Check the Home Assistant log for `custom_components.sikom`

---

## Acknowledgements
Developed and maintained by [@Howard0000](https://github.com/Howard0000).  
An AI assistant was used for troubleshooting and documentation support.

---

## License
MIT License

---

## Trademarks and naming
The name and logo are the property of **Sikom Connect AS** and are used for identification purposes only.

This is an unofficial community project and is not developed, supported, endorsed, or maintained by
Sikom Connect AS.

---

## ⚠️ Disclaimer
This integration is a third-party project and does not replace the Sikom mobile app.

Use at your own risk.  
For heating control — especially in cabins or remote properties — a separate **frost protection**
system is strongly recommended.

The integration is intended for monitoring and automation only and must not be used as a primary
control system for critical functions.
