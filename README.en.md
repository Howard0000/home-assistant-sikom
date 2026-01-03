
---

# Sikom for Home Assistant

[Norsk](README.md) · **English**

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

A modern, robust, and user-friendly integration to connect Sikom devices (thermostats, relays, and AMS meters) to Home Assistant.

This integration is a custom component that uses Sikom's official Connome API. It replaces the need for manual configuration with `rest_sensor`, `rest_command`, and other YAML-based solutions. Everything is now handled through a simple user interface.

![Example of Sikom devices in Home Assistant](images/screenshot.png)
![Example of Sikom devices in Home Assistant](images/screenshot1.png)

## Features (English)

- **Automatic Device Detection:** Automatically discovers all thermostats, relays, and AMS meters on your Sikom account.  

- **Climate Control:** Creates native `climate` entities for your thermostats.  
  - Displays the current temperature.  
  - Allows you to easily switch between "Comfort" and "Eco" presets.  
  - Lets you adjust the target temperature for both comfort and eco modes directly from Home Assistant.  
  - **Measured Temperature:** For devices that report actual temperature (e.g. *SI-4*, *Eco Glamox Receiver*, and *Eco Controller 3*), an additional sensor is automatically created:  
    - `sensor.[name]_measured_temperature`  
    - This sensor appears in the same **Device** as the thermostat in Home Assistant.  
    - Example: *Living Room* → contains both `climate.living_room` and `sensor.living_room_measured_temperature`.  
  - For **Eco Controller 3 (4G)** with connected wired temperature probes, one temperature sensor per relay (e.g., `Temperature Relay 1` and `Temperature Relay 2`) is automatically added.

- **Automatic API Refresh:**  
  The integration now triggers a background *AppView* refresh every **5–6 minutes**, ensuring temperatures and device statuses stay updated without needing to open the Sikom mobile app.
  
- **Switches:** Creates `switch` entities for devices like water heaters and relays.  

- **Energy Monitoring:** Creates `sensor` entities for AMS meters with real-time power usage (W) and total energy (kWh), fully compatible with Home Assistant’s Energy dashboard.  

- **Easy Configuration:** No YAML editing required. Setup is handled entirely through the Home Assistant UI.  


### 🧩 Supported and Tested Devices

This integration has been tested and confirmed to work with the following devices and controllers.  
Other models may also function partially or fully if they use the same data fields in the Sikom API.

| Device type / category | Model / Type in API | Support and functionality |
|-------------------------|--------------------|---------------------------|
| **Wireless Thermostat** | `WirelessThermostat / SI-3` | ✅ Fully supported – climate + sensor for measured temperature |
| **Wireless Thermostat** | `WirelessThermostat / SI-4` | ✅ Fully supported – climate + sensor for measured temperature |
| **Eco Glamox Receiver** | `ECOGlamoxPlug (Wireless Thermostat Glamox)` | ✅ Fully supported – climate + measured temperature sensor |
| **Water Heater / Relay** | `ECONode / Tech-Rel` | ✅ Fully supported – switch |
| **EV Charger** | `EaseeHome` | ✅ Fully supported – switch and sensor |
| **AMS Power Meter** | `ECOEnergyController / ECO-AMS` | ✅ Fully supported – sensors for power, voltage and energy |
| **Internal Relay in Eco Controller 3 (LTE-M)** | `GSMECOController3_Relay / GEC-III` | ✅ Fully supported – switch + temperature sensors for relay 1 and 2 (if probes connected) |
| **Main Controller (Gateway)** | `GSMECOController3_Relay / GEC-III (LTE-M)` | ⚙️ Partial support – connection status (`binary_sensor`) and *AppView Heartbeat* (updates approx. every 5 minutes) |
| **Main Controller (Gateway)** | `ECOComfort2 4G` | ⚙️ Partial support – connection status (`binary_sensor`) and *AppView Heartbeat* (updates approx. every 5 minutes) |

💡 **Tip:**  
If you don’t see the *AppView Heartbeat* sensor immediately, search for it in Home Assistant (`sensor.appview_heartbeat`) and add it manually to your dashboard.  
This sensor confirms that the integration is communicating with the Sikom cloud and updates automatically every 5–6 minutes.



## 📥 Import blueprint directly into Home Assistant

This blueprint makes it easy to receive notifications from your **Sikom devices** in Home Assistant.  
It supports thermostats, water heater switches, and connectivity sensors (for power outages).  
For switches, built-in logic ensures that the state change is **stable** before a notification is sent, avoiding false alarms from rapid on/off flickering.

[![Importer blueprint til Home Assistant](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Howard0000/home-assistant-sikom/main/blueprints/sikom_varslingssentral.yaml)

## Requirements

-   Home Assistant 2024.x or newer.
-   A valid Sikom account with connected devices.
-   [HACS (Home Assistant Community Store)](https://hacs.xyz/) installed.

## Installation

The easiest way to install is via HACS.

1.  Open HACS → Integrations in Home Assistant.
2.  Search for “Sikom”.
3.  Select the integration and click Install.
4.  Restart Home Assistant if prompted.

## Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **Add Integration** in the bottom right corner.
3.  Search for **"Sikom"** and select it.
4.  Enter the username (email) and password for your Sikom account.
5.  You will be presented with a list of all discovered devices. Check the boxes for the ones you want to add to Home Assistant.
6.  Click "Submit", and your devices will be added!

### Modifying devices later
To add or remove devices, go to **Settings > Devices & Services**, find the Sikom integration, and click **"Configure"**.

## Tips & Tricks

### Temperature display on the thermostat card
Home Assistant's built-in thermostat card may sometimes hide the measured room temperature on the dashboard when the thermostat is idle. This is normal. You can **always see the exact temperature** by **clicking the card** to open the details view.

For full control over the appearance, you can use alternative cards from HACS, like the [Simple Thermostat Card](https://github.com/nervetattoo/simple-thermostat).

## Contributions
This integration has been tested with the devices available to the author. Because it's built to be flexible, it may work fully or partially with other Sikom devices as well.

If you have a Sikom device that is not fully supported, please open an 'issue' on GitHub and feel free to share API data (without personal information), so we can look into adding better support.

## Disclaimer
This is an unofficial, community-driven project and is not affiliated with or supported by Sikom AS. Use at your own risk. The integration depends on Sikom's current Connome API. Future changes by Sikom may affect functionality.
The logo and name are the property of Sikom Connect AS and are used for identification purposes only.

## Acknowledgements
This project is written and maintained by [@Howard0000](https://github.com/Howard0000). An AI assistant provided help with troubleshooting, code improvements, and documentation.

## License
This project is licensed under the [MIT License](LICENSE).

---

### ⚠️ Disclaimer

This integration is an independent community project using the official Sikom public API for data access and control.  
It does **not** replace the Sikom mobile app and has no deeper control capabilities beyond what the API provides.

Use at your own risk.  
For heating control — especially in cabins or remote properties — a separate and independent **frost protection** system is strongly recommended.  
Neither the developer of this integration nor Sikom Connect AS can be held responsible for damage, malfunction, or financial loss resulting from misconfiguration, network issues, or API changes.

The integration is intended as a monitoring and automation tool within Home Assistant, not as a primary safety or control system.

