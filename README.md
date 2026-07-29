# Garage 차량관리 Home Assistant Integration (hass-garage)

[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-garage/tests.yml?branch=master&style=flat-square&label=tests)](https://github.com/eigger/hass-garage/actions/workflows/tests.yml)
[![GitHub Release](https://img.shields.io/github/v/release/eigger/hass-garage?style=flat-square)](https://github.com/eigger/hass-garage/releases)
[![License](https://img.shields.io/github/license/eigger/hass-garage?style=flat-square)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

셀프호스팅 차량관리 서버 [Garage](https://github.com/eigger/garage)와 Home Assistant를
**YAML 편집 없이** 양방향으로 연결하는 커스텀 통합구성요소입니다.

- **HA → Garage (자동 전송)**: 옵션 화면에서 위도/경도/속도/RPM/연료량/주행거리/탑승여부에
  해당하는 HA 엔티티를 고르면, 그 값이 바뀔 때마다 자동으로 Garage에 전송됩니다.
  `rest_command` YAML을 직접 쓰지 않아도 됩니다.
- **Garage → HA (자동 수신)**: Garage가 이미 계산해 둔 주행거리, 연료/배터리 잔량,
  마지막 위치, 기한 도래 리마인더를 HA 센서로 보여줍니다.

## 설치

1. 이 저장소를 HACS의 사용자 지정 저장소로 추가하거나, `custom_components/garage` 폴더를
   Home Assistant 설정 디렉터리의 `custom_components/` 아래에 복사합니다.
2. Home Assistant를 재시작합니다.
3. **설정 → 기기 및 서비스 → 통합구성요소 추가 → "Garage 차량관리"** 를 선택합니다.
4. Garage 서버 주소(예: `http://192.168.1.50` 또는 `https://garage.example.com`)와,
   Garage 웹 UI **차량 상세 → OBD & GPS** 탭에서 확인할 수 있는 해당 차량의
   **API 토큰**을 입력합니다.

차량 한 대당 통합구성요소 항목을 하나씩 추가합니다(여러 대를 등록하려면 통합구성요소를
여러 번 추가하세요).

## HA → Garage로 자동 전송하기

통합구성요소 카드의 **"구성"(옵션)**에서 전송할 엔티티를 고릅니다. 나중에 센서를
바꾸고 싶으면(고장, 교체, 새 센서 추가 등) 같은 화면을 다시 열어서 바꾸면 됩니다 —
저장하는 즉시 자동으로 재로드되어 새로 고른 센서로 바로 반영됩니다.

| Garage 필드 | 어떤 엔티티를 고르면 되나 |
| --- | --- |
| 위도 / 경도 | GPS 좌표를 갖는 `sensor` 또는 `device_tracker`(예: 휴대폰 위치, OwnTracks, Traccar) |
| 속도 | 속도(km/h) `sensor` |
| 엔진 회전수(RPM) | RPM `sensor`(ESPHome OBD 리더 등) |
| 연료/배터리 잔량 | 퍼센트(%) `sensor` |
| 주행거리 | km 단위 `sensor` |
| 차량 탑승 여부 | `binary_sensor`/`device_tracker`, 또는 엔진로드·RPM 같은 **숫자 `sensor`**(0보다 크면 탑승중으로 판단) |

전부 선택 사항입니다 — 갖고 있는 센서만 고르면 됩니다. 값이 바뀌면 곧바로 전송되고,
같은 순간에 여러 값이 연달아 바뀌면 10초 안에 묶어서 한 번만 보냅니다.

**탑승 중일 때만 전송**: 옵션 화면의 토글을 켜면, 위 "차량 탑승 여부"가 참일 때만
전송하고 아닐 땐 건너뜁니다(꺼져 있으면 시동이 꺼진 상태에서도 `inVehicle: false`를
포함해 계속 전송합니다). "차량 탑승 여부"를 지정하지 않았다면 판단 근거가 없어 이
토글은 무시됩니다.

정상 동작 여부는 진단 센서 **"마지막 전송 시각"**, **"마지막 전송 상태"**,
**"탑승 중 아님으로 건너뜀"**으로 확인할 수 있습니다.

## Garage → HA로 자동 수신되는 센서

| 센서 | 내용 | 갱신 주기 |
| --- | --- | --- |
| 주행거리 | Garage에 저장된 현재 주행거리 | 5분 |
| 연료/배터리 잔량 | 가장 최근 텔레메트리의 연료량 | 5분 |
| 속도 | 가장 최근 텔레메트리의 속도 | 5분 |
| 위치(device_tracker) | 마지막으로 알려진 위·경도 — 지도에 표시됨 | 5분 |
| 기한 도래 리마인더 | `isDue`인 정비/행정 리마인더 개수 | 30분 |

## API 토큰 발급

Garage 웹 UI에 관리자로 로그인 → 해당 차량 상세 페이지 → **OBD & GPS** 탭에서 확인할 수
있습니다. 이 토큰은 로그인 없이 텔레메트리를 주고받는 용도로, 차량마다 하나씩 자동
발급되어 있습니다.

## 개발 / 테스트

`homeassistant` 패키지 설치 없이(`tests/conftest.py`가 필요한 모듈만 mock) 순수 로직을
단위 테스트합니다.

```bash
pip install ruff pytest
python -m ruff check custom_components/ tests/
python -m pytest tests/ -v
```

PR을 올리면 GitHub Actions가 Python 3.12/3.13/3.14에서 동일하게 검증합니다
(`.github/workflows/tests.yml`).

## 라이선스

MIT
