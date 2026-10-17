# 적용한 공통 규칙

- 표준: https://github.com/eigger/hass-repo-standards/tree/8bf07f496b4688f64d71980e2c36696751be91fb
- 참조 커밋 SHA: `8bf07f496b4688f64d71980e2c36696751be91fb` (착수 시 실제 원격 main 확인)
- 채택 작업일: 2026-10-18
- profile: integration / ha (실제 HA fixture·통합 로딩 필수)
- 실제 기본 브랜치: `master`; domain: `garage`
- 적용 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황표: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 조율 / 구현 / 독립 리뷰·검증 담당: 조율 `root` · 구현 `garage_implementation` · 독립 리뷰 `garage_review`
- 중앙 현황 갱신일: 2026-10-18 (시작 등록 [`e30cd06`](https://github.com/eigger/hass-repo-standards/commit/e30cd06))
- 시작 대상 커밋: `f7f88a1ca828b94b0cb2b54c223f550cb88db3f1`
- 테스트 경로: `tests/components/garage/`
- 변경 전 지원 최소 HA / 선언 근거: `2025.3.0` (`hacs.json` 선언; `manifest.json` 및 기존 `README.md`에 별도 상충 선언 없음)
- 적용 후 지원 최소 HA: `2025.3.0` 보존 (통합 버전 `1.3.0` 보존)
- current HA 테스트 환경: Python 3.14.5 (원격 3.14) / HA `2026.10.2` / `pytest-homeassistant-custom-component==0.13.373` (`requirements_test.txt`)
- 최소 HA 검증 환경: Python 3.13.14 (원격 3.13) / HA `2025.3.0` / `pytest-homeassistant-custom-component==0.13.221` (`requirements_test_min.txt`)
- 최소 package 검증: 해당 없음 (`manifest.requirements=[]`)

## 검증 환경과 경계

실제 HA loader·config entry manager·플랫폼(`button`, `device_tracker`, `sensor`)·flow·options·service·registry를 실행합니다. 외부 HTTP 응답만 플러그인의 `aioclient_mock` 및 단위 테스트용 세션 경계로 대체하며, 기존 47개 단위/회귀 테스트를 보존하고 실제 HA 통합 테스트를 더해 총 79개 테스트(`0 skipped, 0 warnings`)를 구성했습니다. `sys.modules` 가짜 HA 모듈과 `FakeHass` 기반 통합 대체는 제거했습니다.

domain(`garage`), entry schema(`VERSION = 1`), unique ID(`{entry_id}_due_reminders`, `{entry_id}_last_push_at`, `{entry_id}_location`, `{entry_id}_push_now`, `{entry_id}_refresh_now`), 상태/속성 계약, 통합 버전(`1.3.0`)은 변경하지 않습니다.

보완 사항:
- `api.py`: `ClientTimeout(total=15)` 명시 적용 및 네트워크 예외(`ClientError`, `ValueError`, `TimeoutError`) 발생 시 URL·인증 토큰·응답 원문이 로그나 예외 문자열에 노출되지 않도록 예외 타입만 남기도록 비식별화(`HA-06`, `HA-12`).
- `__init__.py`: `GarageTelemetryForwarder.async_stop()`에서 상태 변화 리스너와 대기 중인 디바운스 타이머(`_unsub_call_later`)를 함께 해제하고, `async_setup_entry`에서 플랫폼 포워딩이 완료된 뒤 `forwarder.async_start()`를 등록해 부분 setup 실패 시 리스너가 남지 않도록 보장(`HA-05`). 연속 전송 실패 시 첫 회만 `WARNING`, 이후 연속 실패는 `DEBUG`, 복구 시 `INFO`로 기록해 중복 경고를 억제(`HA-12`).
- `config_flow.py`: 옵션/센서 선택 스키마에서 선택하지 않은 `EntitySelector` 필드에 빈 문자열 기본값(`default=""`)을 넣지 않고 기존 설정값이 있을 때만 `suggested_value`를 제공하도록 수정해 실제 HA selector 검증을 통과(`HA-04`).

`test_supported_environment.py`는 최소 테스트 HA가 `hacs.json`의 지원 하한(`2025.3.0`)과 정확히 일치하고 현재 테스트 HA(`2026.10.2`)가 그 하한 이상인지, 그리고 실제 설치된 HA와 플러그인이 각 환경의 정확한 requirements와 일치하는지 검증합니다. 최소 환경은 HA 2025.3.0이 고정한 `aiohttp==3.11.13`과 [당시 공식 Bluetooth manifest](https://github.com/home-assistant/core/blob/2025.3.0/homeassistant/components/bluetooth/manifest.json)의 6개 helper 버전을 `constraints/homeassistant-min.txt`에 고정합니다. Dependabot의 `exclude-paths`로 역사적 최소 requirements와 constraints를 자동 갱신에서 제외합니다.

## 예외

현재 기록된 적용 예외는 없습니다.

- `master` branch protection 조회는 `404 (Branch not protected)`, rulesets는 빈 배열(`[]`)이므로 기존 required checks를 대기 상태로 만드는 설정 변경은 없습니다.
- 로컬 브랜드 아이콘(`custom_components/garage/brand/icon.png` 256×256, `icon@2x.png` 512×512)은 기존 리포 자산을 그대로 유지합니다. 로컬 brand의 HA UI 표시는 HA 2026.3부터 지원되므로 지원 최소 HA 2025.3.0에서의 UI 표시나 실제 HA frontend 렌더링 검증을 주장하지 않습니다.
- 운영 Garage 서버·실물 차량 OBD/GPS 환경과의 실물 검증은 이번 작업에서 수행하지 않았습니다. 채택 작업만으로 태그나 GitHub Release를 새로 생성하지 않습니다.
