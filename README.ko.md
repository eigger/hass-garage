<!-- hass-standards:header:start -->
# Garage Home Assistant Integration (hass-garage)

셀프호스팅 Garage 차량관리 서버와 차량 텔레메트리·정비 알림을 양방향으로 연결하는 Home Assistant HACS 커스텀 통합구성요소입니다.

[English](README.md) | **한국어**

<!-- hass-standards:badges:start -->
[![Release](https://img.shields.io/github/v/release/eigger/hass-garage?style=flat)](https://github.com/eigger/hass-garage/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat)](#설치)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.3.0-41BDF5?style=flat)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-garage/tests.yml?branch=master&style=flat&label=Tests)](https://github.com/eigger/hass-garage/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-garage/validate.yml?branch=master&style=flat&label=Validate)](https://github.com/eigger/hass-garage/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-garage?style=flat)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/eigger/hass-garage/latest/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/eigger/hass-garage/releases)
<!-- hass-standards:badges:end -->
<!-- hass-standards:header:end -->

셀프호스팅 차량관리 서버 [Garage](https://github.com/eigger/garage)와 Home Assistant를 **YAML 편집 없이** 양방향으로 연결하는 커스텀 통합구성요소입니다.


## 주요 기능

- **HA → Garage (자동 전송)**: 위치(`device_tracker`), 엔진 회전수(RPM), 속도, 연료·배터리 잔량, 주행거리에 해당하는 HA 엔티티를 고르면 위치를 제외한 값이 바뀔 때마다 그 시점의 최신 위치와 함께 Garage(`POST /api/ingest/telemetry`)로 자동 전송합니다.
- **Garage → HA (자동 수신)**: Garage가 계산해 둔 차량 마지막 위치(`device_tracker`, 5분 주기)와 지난·임박 정비/행정 리마인더 개수(`sensor`, 30분 주기)를 HA 센서로 보여줍니다.
- **진단 및 수동 실행**: 마지막 전송 시각 진단 센서(`success`, `forwarded_entities` 속성 포함)와 **지금 전송**·**지금 새로고침** 버튼을 제공합니다.

## 요구사항

Home Assistant **2025.3.0 이상**, 네트워크로 접근 가능한 셀프호스팅 [Garage](https://github.com/eigger/garage) 서버와 차량별 API 토큰(**차량 상세 → OBD & GPS**)이 필요합니다. 로컬 HTTP/HTTPS를 사용하며 Bluetooth 프록시는 필요하지 않습니다.

## 설치

<!-- hass-standards:installation:start -->
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eigger&repository=hass-garage&category=integration)
<!-- hass-standards:installation:end -->

1. HACS의 사용자 지정 저장소에 `eigger/hass-garage`를 **Integration**으로 추가합니다.
2. 통합구성요소를 설치하고 Home Assistant를 재시작합니다.
3. **설정 → 기기 및 서비스 → 통합구성요소 추가 → "Garage 차량관리"**를 선택합니다.
4. Garage 서버 주소와 해당 차량의 API 토큰을 입력한 뒤, 전송할 HA 센서(선택 사항)를 고릅니다.

차량 한 대당 통합구성요소 항목을 하나씩 추가합니다. [API 토큰 확인·센서 매핑·수동 설치 안내](docs/ko/user-guide.md#설치)

## 사용 예시

```yaml
action: button.press
target:
  entity_id: button.my_car_push_now
```

실제 설치에서 생성된 **지금 전송**(`push_now`) 또는 **지금 새로고침**(`refresh_now`) 버튼의 엔티티 ID를 사용하세요.

전송 트리거는 위치를 제외한 나머지 값(RPM/속도/연료/주행거리)이 바뀔 때만 걸리며, 최소 전송 간격(기본 10초, 1~300초) 안에 묶어서 발생 순서대로 직렬화해 전송합니다. HA 재시작 직후 `unknown`/`unavailable`에서 복구되는 이벤트는 전송을 트리거하지 않습니다. [상세 동작과 문제 해결](docs/ko/user-guide.md#ha--garage로-자동-전송하기)

## 문서

| 안내 | 내용 |
|---|---|
| [사용 안내](docs/ko/user-guide.md) | 설치·API 토큰, 센서 매핑, 디바운스·직렬화, 수신 센서, 문제 해결, Usage 배지 의미 |
| [개발과 테스트](docs/ko/development.md) | 실제 HA 테스트, 최소·최신 환경, 의존성과 실행 명령 |
| [적용 기준](STANDARDS.md) · [체크리스트](ADOPTION_CHECKLIST.md) | 공통 규칙과 검증 기록 |

<!-- hass-standards:support:start -->
## 지원

- [Issues](https://github.com/eigger/hass-garage/issues): 버그를 신고하거나 기능을 요청하세요.
- [Discussions](https://github.com/eigger/hass-garage/discussions): 질문하고 사용 경험을 공유하세요.
<!-- hass-standards:support:end -->

<!-- hass-standards:related-projects:start -->
<!-- hass-standards:related-projects:end -->

<!-- hass-standards:license:start -->
## 라이선스

[MIT License](LICENSE) 라이선스로 배포됩니다.
<!-- hass-standards:license:end -->
