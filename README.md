<!-- hass-standards:header:start -->
# Garage Home Assistant Integration (hass-garage)

A Home Assistant custom integration for bidirectional vehicle telemetry and maintenance reminders with a self-hosted Garage vehicle management server.

**English** | [한국어](README.ko.md)

<!-- hass-standards:badges:start -->
[![Release](https://img.shields.io/github/v/release/eigger/hass-garage?style=flat)](https://github.com/eigger/hass-garage/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat)](#installation)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.3.0-41BDF5?style=flat)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-garage/tests.yml?branch=master&style=flat&label=Tests)](https://github.com/eigger/hass-garage/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-garage/validate.yml?branch=master&style=flat&label=Validate)](https://github.com/eigger/hass-garage/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-garage?style=flat)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/eigger/hass-garage/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/eigger/hass-garage/releases)
<!-- hass-standards:badges:end -->
<!-- hass-standards:header:end -->

A custom Home Assistant integration that connects a self-hosted [Garage](https://github.com/eigger/garage) vehicle management server with Home Assistant in **both directions without YAML configuration**.


## Features

- **HA → Garage (telemetry push)**: Pick optional HA entities for location (`device_tracker`), RPM, speed, fuel/battery level, and odometer. Whenever a non-location value changes, the integration pushes those values together with the latest location to `POST /api/ingest/telemetry`.
- **Garage → HA (status & reminders pull)**: Exposes the vehicle's last known GPS location (`device_tracker`, every 5 minutes) and due/upcoming maintenance reminders (`sensor`, every 30 minutes).
- **Diagnostics & manual actions**: Includes a `Last push time` diagnostic timestamp sensor (`success` and `forwarded_entities` attributes) plus `Push now` and `Refresh now` buttons.

## Requirements

Home Assistant **2025.3.0 or newer**, a reachable self-hosted [Garage](https://github.com/eigger/garage) server, and a per-vehicle API token (`Vehicle detail → OBD & GPS`). Uses local HTTP/HTTPS; no Bluetooth proxy is needed.

## Installation

<!-- hass-standards:installation:start -->
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eigger&repository=hass-garage&category=integration)
<!-- hass-standards:installation:end -->

1. Add `eigger/hass-garage` as a custom **Integration** repository in HACS.
2. Install the integration and restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → Garage 차량관리**.
4. Enter the Garage server URL and the vehicle API token, then optionally choose HA entities to forward as telemetry.

Add one integration entry per vehicle. [Token lookup, entity mapping, and manual installation](docs/user-guide.md#installation)

## Usage

```yaml
action: button.press
target:
  entity_id: button.my_car_push_now
```

Use the actual `push_now` or `refresh_now` button entity ID created by your installation.

Only non-location changes (RPM, speed, fuel/battery level, odometer) trigger automatic pushes, coalesced within the configured debounce interval (default 10s, 1–300s) and serialized in order. State recovery from `unknown`/`unavailable` right after a Home Assistant restart is ignored. [Forwarding details and troubleshooting](docs/user-guide.md#forwarding-telemetry-ha--garage)

## Documentation

| Guide | Contents |
|---|---|
| [User guide](docs/user-guide.md) | Setup and API token, entity mapping, debounce and ordering, pull sensors, troubleshooting, Usage badge meaning |
| [Development and tests](docs/development.md) | Actual HA tests, minimum/current environments, dependencies, and commands |
| [Adopted standards](STANDARDS.md) · [Checklist](ADOPTION_CHECKLIST.md) | Common rules and verification records |

<!-- hass-standards:support:start -->
## Support

- [Issues](https://github.com/eigger/hass-garage/issues): Report bugs or request features.
- [Discussions](https://github.com/eigger/hass-garage/discussions): Ask questions and share your experience.
<!-- hass-standards:support:end -->

<!-- hass-standards:related-projects:start -->
<!-- hass-standards:related-projects:end -->

<!-- hass-standards:license:start -->
## License

Released under the [MIT License](LICENSE).
<!-- hass-standards:license:end -->
