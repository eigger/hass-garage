# Garage 차량관리 Home Assistant Integration (hass-garage)

[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-garage/tests.yml?branch=master&style=flat-square&label=tests)](https://github.com/eigger/hass-garage/actions/workflows/tests.yml)
[![GitHub Release](https://img.shields.io/github/v/release/eigger/hass-garage?style=flat-square)](https://github.com/eigger/hass-garage/releases)
[![License](https://img.shields.io/github/license/eigger/hass-garage?style=flat-square)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

셀프호스팅 차량관리 서버 [Garage](https://github.com/eigger/garage)와 Home Assistant를
**YAML 편집 없이** 양방향으로 연결하는 커스텀 통합구성요소입니다.

- **HA → Garage (자동 전송)**: 설치 시 또는 옵션 화면에서 위치(device_tracker)/RPM/
  속도/연료·배터리 잔량/주행거리에 해당하는 HA 엔티티를 고르면, 위치를 제외한 값이
  바뀔 때마다 그 시점의 최신 위치와 함께 자동으로 Garage에 전송됩니다. `rest_command`
  YAML을 직접 쓰지 않아도 됩니다.
- **Garage → HA (자동 수신)**: Garage가 이미 계산해 둔 마지막 위치, 지난·임박
  리마인더를 HA 센서로 보여줍니다. 주행거리/연료/속도는 애초에 HA 엔티티가 보내는
  원본 값이라 Garage 쪽 계산 결과를 HA에 다시 표시하는 중복 센서는 두지 않습니다.

## 설치

1. 이 저장소를 HACS의 사용자 지정 저장소로 추가하거나, `custom_components/garage` 폴더를
   Home Assistant 설정 디렉터리의 `custom_components/` 아래에 복사합니다.
2. Home Assistant를 재시작합니다.
3. **설정 → 기기 및 서비스 → 통합구성요소 추가 → "Garage 차량관리"** 를 선택합니다.
4. Garage 서버 주소(예: `http://192.168.1.50` 또는 `https://garage.example.com`)와,
   Garage 웹 UI **차량 상세 → OBD & GPS** 탭에서 확인할 수 있는 해당 차량의
   **API 토큰**을 입력합니다.
5. 이어서 전송할 센서(위치/RPM/속도/연료/주행거리)를 고르는 화면이 뜹니다 — 지금 안
   고르고 비워둬도 되고, 나중에 옵션에서 언제든 설정할 수 있습니다.

차량 한 대당 통합구성요소 항목을 하나씩 추가합니다(여러 대를 등록하려면 통합구성요소를
여러 번 추가하세요).

## HA → Garage로 자동 전송하기

통합구성요소 카드의 **"구성"(옵션)**에서 전송할 엔티티를 고릅니다. 나중에 센서를
바꾸고 싶으면(고장, 교체, 새 센서 추가 등) 같은 화면을 다시 열어서 바꾸면 됩니다 —
저장하는 즉시 자동으로 재로드되어 새로 고른 센서로 바로 반영됩니다.

| Garage 필드 | 어떤 엔티티를 고르면 되나 |
| --- | --- |
| 위치(위도+경도) | 위도/경도 속성을 함께 갖는 `device_tracker` 엔티티 하나(예: 휴대폰 위치, OwnTracks, Traccar) |
| 엔진 회전수(RPM) | RPM `sensor`(ESPHome OBD 리더 등) |
| 속도 | 속도(km/h) `sensor` |
| 연료/배터리 잔량 | 퍼센트(%) `sensor` |
| 주행거리 | km 단위 `sensor` |

전부 선택 사항입니다 — 갖고 있는 센서만 고르면 됩니다.

전송 트리거는 **위치를 제외한 나머지 값(RPM/속도/연료/주행거리)이 바뀔 때만**
걸립니다 — 위치는 주행 중 계속 바뀌므로 트리거에 넣지 않고, 트리거가 걸린 시점의
최신 위치를 함께 실어 보냅니다. 같은 순간에 여러 번 바뀌면 **최소 전송 간격**(기본
10초, 옵션에서 1~300초로 조절 가능) 안에 묶어서 한 번만 보내고, 실제 전송은
직렬화되어 있어 여러 전송이 겹쳐도 발생한 순서 그대로 서버에 도착합니다. RPM처럼
1초 단위로 계속 바뀌는 센서를 쓴다면 이 간격을 늘려서 요청 빈도를 줄일 수 있습니다.

HA를 재시작하면 트리거 엔티티가 잠깐 "알 수 없음"이었다가 원본 통합구성요소가
다시 붙으면서 마지막 값으로 돌아오는데, 이건 실제 값 변화가 아니므로 전송을
트리거하지 않습니다.

정상 동작 여부는 진단 센서 **"마지막 전송 시각"**(timestamp 타입)으로 확인할 수
있습니다 — 성공 여부(`success`)와 실제로 전송한 엔티티 목록(`forwarded_entities`)은
이 센서의 속성으로 함께 들어 있습니다.

트리거를 기다리지 않고 바로 확인하고 싶을 때를 위해 버튼 두 개도 제공합니다:
**"지금 전송"**은 디바운스 대기 없이 텔레메트리를 즉시 한 번 보내고, **"지금
새로고침"**은 상태(5분)·리마인더(30분) 폴링 주기를 기다리지 않고 즉시 다시
조회합니다.

## Garage → HA로 자동 수신되는 센서

| 센서 | 내용 | 갱신 주기 |
| --- | --- | --- |
| 위치(device_tracker) | 마지막으로 알려진 위·경도 — 지도에 표시됨 | 5분 |
| 지난·임박 리마인더 | `isDue` 또는 `isUpcoming`인 정비/행정 리마인더 개수(Garage 대시보드의 "지난/임박" 배지와 동일 기준) | 30분 |

주행거리·연료/배터리 잔량·속도는 애초에 HA 쪽 엔티티가 Garage로 보내는 원본 값이라,
Garage가 그걸 다시 계산해서 HA에 표시하는 중복 센서는 두지 않았습니다.

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

## Garage란?

[Garage](https://github.com/eigger/garage)는 가족·홈랩용 셀프호스팅 차량 관리 앱입니다 —
정비 스케줄, 주유/충전 기록, 리마인더, OBD/GPS 주행 리포트를 제공합니다. 이 통합구성요소는
그 Garage 서버와 Home Assistant를 연결하는 역할만 하며, 실제 기록 관리·리포트·알림은
Garage 웹 UI에서 이루어집니다.

## 라이선스

MIT
