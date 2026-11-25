# Zigbee2MQTT for ZimaOS

ZimaOS App Store packaging for the upstream Zigbee2MQTT container. This repo contributes the app definition; it does not fork or rebuild Zigbee2MQTT.

## Requirements

- A running MQTT broker reachable from the container (for example, Mosquitto).
- A supported Zigbee coordinator connected to the ZimaOS host for actual Zigbee operation.

## First-run setup

1. Install/prepare an MQTT broker and note its address and credentials.
2. Connect the coordinator. On the host, identify its persistent path under `/dev/serial/by-id/` (do not rely on changing `/dev/ttyUSB0` numbering).
3. Edit `configuration.yaml` in the app data directory mounted at `/app/data` (host path `/DATA/AppData/$AppID/data`) to configure MQTT and the coordinator. Example (replace the MQTT address and adapter value with your setup):

   ```yaml
   mqtt:
     server: mqtt://192.168.1.10:1883
   serial:
     port: /dev/ttyACM0
     adapter: ember
   ```

   Use the adapter value documented for your coordinator; common choices include `ember` and `zstack`. Add MQTT credentials if your broker requires them.
4. Add the host device mapping to the Compose service using the stable path found above. Map it to `/dev/ttyACM0` and set `serial.port: /dev/ttyACM0`; adjust the container path if needed for the adapter.
5. Deploy and open the web UI on port 8080. Configure Zigbee2MQTT authentication (`frontend.auth_token`) before exposing the UI beyond a trusted LAN.

The app definition intentionally does not guess a USB device path: that path differs by adapter and host. Add the host-to-container `devices` mapping in the Compose service before deployment; set `serial.port` to the mapped container path. Validate actual passthrough on ZimaOS with supported hardware before claiming end-to-end readiness.

## Development status

Initial packaging draft, tracking upstream release 2.14.3 (checked 2026-11-25). Compose follows the current ZimaOS v2 app source convention (`Apps/<App>/docker-compose.yml` with `x-casaos` metadata) and uses the standard `/DATA/AppData/$AppID` persistent-data location. The official v2 builder successfully processed this app in isolation (1 app, 0 warnings/errors); `docker compose config -q` also passes with ZimaOS app variables supplied. The pinned upstream image publishes both `amd64` and `arm64` manifests. Full catalog CI, actual container runtime, official catalog acceptance, and ZimaOS USB passthrough remain unverified.
