# User guide and troubleshooting

[English](user-guide.md) | [한국어](ko/user-guide.md) | [README](../README.md)

## Requirements

- Home Assistant **2025.3.0 or newer**, a reachable self-hosted [Garage](https://github.com/eigger/garage) server, and a per-vehicle API token.
- Local HTTP/HTTPS communication (`POST /api/ingest/telemetry`, `GET /api/ingest/status`, `GET /api/ingest/reminders`); no Bluetooth adapter or proxy is used by this integration.

## Installation

1. Add `eigger/hass-garage` as a custom **Integration** repository in HACS, or copy the `custom_components/garage` folder into `custom_components/` under your Home Assistant configuration directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → "Garage 차량관리"**.
4. Enter your Garage server address (for example `http://192.168.1.50` or `https://garage.example.com`) and the vehicle's **API token** shown under **Vehicle detail → OBD & GPS** in the Garage web UI.
5. In the next step, choose which HA entities (location, RPM, speed, fuel/battery, odometer) to forward to Garage. All fields are optional — you can leave them blank now and configure or change them anytime from the integration's options.

Add one integration entry per vehicle (add the integration multiple times if you manage multiple vehicles). To remove, delete the integration entry in Home Assistant, uninstall through HACS or remove `custom_components/garage`, and restart.

## Issuing a vehicle API token

Log in to the Garage web UI as an administrator → open the vehicle's detail page → go to the **OBD & GPS** tab. Each vehicle automatically has its own token dedicated to unauthenticated telemetry ingestion and status polling. If a token is rotated or rejected (`401`), Home Assistant starts a reauthentication flow where you can enter the new token.

## Forwarding telemetry (HA → Garage)

Open **"Configure" (Options)** on the integration card to select the HA entities to forward. Whenever you replace a sensor or add a new one, update the selection in the same options dialog — saving reloads the entry immediately so the new entity mapping takes effect right away.

| Garage field | Entity to select |
| --- | --- |
| Location (latitude + longitude) | One `device_tracker` entity that carries both `latitude` and `longitude` attributes (e.g. companion app phone tracker, OwnTracks, Traccar) |
| Engine RPM | RPM `sensor` (e.g. ESPHome OBD reader) |
| Speed | Speed (`km/h`) `sensor` |
| Fuel / battery level | Percentage (`%`) `sensor` |
| Odometer | Distance (`km`) `sensor` |

All fields are optional — only select the sensors you have.

- **Trigger exclusion for location**: Telemetry pushes are triggered **only when a non-location value (RPM, speed, fuel/battery level, or odometer) changes**. Because GPS coordinates change continuously while driving, location updates alone do not trigger a push; instead, the latest location from the configured `device_tracker` is attached whenever another mapped sensor triggers a push.
- **Minimum push interval (debounce) and FIFO ordering**: Rapid updates within the **minimum push interval** (default `10` seconds, configurable from `1` to `300` seconds in options) are coalesced into a single push carrying the latest values. Actual HTTP `POST` calls are serialized with an async lock so concurrent triggers always arrive at the Garage server in order without reversing trip paths. If you use a fast-changing sensor such as 1-second RPM updates, increase the interval to reduce request frequency.
- **Restart recovery filtering**: Right after Home Assistant restarts, trigger entities briefly transition from `unknown` or `unavailable` back to their restored values as their source integrations load. Because this is state restoration rather than a real vehicle state change (and transitions into `unknown`/`unavailable` carry no valid value), these transitions do not trigger a push.
- **Diagnostic sensor (`Last push time`)**: Verify forwarding health via the diagnostic timestamp sensor **Last push time** (`last_push_at`). Its state attributes include `success` (`true`/`false`/`null`) and `forwarded_entities` (the list of configured entity IDs), and its icon switches to `mdi:alert-circle` when the last push failed. When no forwarded entities are configured, `Last push time` and `Push now` are marked unavailable.
- **Manual trigger buttons**:
  - **Push now** (`push_now`): Sends telemetry immediately without waiting for the debounce window (cancelling any pending delayed push). Useful right after a Home Assistant restart when values have not changed yet.
  - **Refresh now** (`refresh_now`): Immediately refreshes both the status (5-minute) and reminders (30-minute) coordinators without waiting for the next poll.

## Sensors pulled from Garage (Garage → HA)

| Entity | Description | Poll interval |
| --- | --- | --- |
| Location (`device_tracker`) | Last known latitude and longitude from Garage (`location_updated_at` attribute) — shown on the map | 5 minutes |
| Due & upcoming reminders (`sensor`) | Count of maintenance/administrative reminders where `isDue` or `isUpcoming` is true (matching the "Due / Upcoming" badge in the Garage dashboard), with `due_count`, `upcoming_count`, `due_types`, and `upcoming_types` attributes | 30 minutes |

Odometer, fuel/battery level, and speed originate from your Home Assistant entities in the first place, so the integration intentionally does not create duplicate pull sensors for those values from Garage.

## Usage example

```yaml
action: button.press
target:
  entity_id: button.my_car_push_now
```

```yaml
action: button.press
target:
  entity_id: button.my_car_refresh_now
```

Replace `button.my_car_push_now` and `button.my_car_refresh_now` with the actual entity IDs created for your vehicle.

## What is Garage?

[Garage](https://github.com/eigger/garage) is a self-hosted vehicle management web app for families and homelabs — providing maintenance schedules, fuel/charging logs, administrative reminders, and OBD/GPS trip reports. This integration bridges Home Assistant and your Garage server; record management, reporting, and notifications are handled in the Garage web UI.

## Troubleshooting and issue reporting

- Check that the Garage server URL is reachable from Home Assistant over HTTP or HTTPS and that the vehicle API token matches **Vehicle detail → OBD & GPS**.
- If `Last push time` (`last_push_at`) or `Push now` (`push_now`) is `unavailable`, open **Configure** on the integration entry and select at least one entity to forward. If only `entity_location` is selected, automatic state-change pushes will not fire because location is excluded from triggers — either add a trigger sensor (RPM, speed, fuel, odometer) or press **Push now** via an automation.
- Remove API tokens, private server URLs, license plates, VINs, and exact GPS coordinates before sharing logs or opening a GitHub Issue. Automated tests run against real Home Assistant fixtures with mocked HTTP responses and do not replace verification against your live Garage server.

## Usage badge

The Usage badge reports installations participating in Home Assistant Analytics, rather than all installations. It stays linked to live analytics data even when this integration has no published count yet; an unavailable value does not mean zero installations.
