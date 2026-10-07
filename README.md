# Densial Nexus — Home Assistant Integration

Home Assistant integration for the Densial Nexus Device Hub.

## Installation with HACS

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository:
   https://github.com/DensialTech/densial-nexus-home-assistant
3. Select **Integration**.
4. Install **Densial Nexus**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration**.
7. Search for **Densial Nexus**.
8. Enter the Nexus URL and the bridge token generated in Densial Nexus → Devices.

## Architecture

Home Assistant polls the Densial Nexus Device Bridge. The Nexus cloud does not require inbound access to the local Home Assistant network.

The integration discovers Home Assistant climate entities, registers them in Nexus, executes queued commands, and reports state back to Nexus.
