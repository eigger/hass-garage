# 적용한 공통 규칙

- 표준: https://github.com/eigger/hass-repo-standards/tree/v1.1.4
- 참조 커밋 SHA: a90531d05613597632a4c10c11ce1dbc45e0bab6
- Standards release: v1.1.4
- Resolved standards SHA: a90531d05613597632a4c10c11ce1dbc45e0bab6
- 채택 작업일: 2026-10-18; 구현 `master` 반영·정확한 SHA 원격 검증·중앙 구현/검증 종료 보고 완료
- profile: integration / ha (실제 HA fixture·통합 로딩 필수)
- 실제 기본 브랜치: `master`; domain: `garage`
- 적용 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황표: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 조율 / 구현 / 독립 리뷰·검증 담당: 조율 `root` · 구현 `garage_implementation` · 독립 리뷰 `garage_review`
- 중앙 현황 갱신: 시작 등록 [`e30cd06`](https://github.com/eigger/hass-repo-standards/commit/e30cd06a3465a7b9f0b0977a47b4a269cf775274) 및 구현·검증 종료 보고 [`d665b57`](https://github.com/eigger/hass-repo-standards/commit/d665b57f7ff28bf81752500abb5d8ed52f99a3a3) 완료
- 시작 대상 커밋: `f7f88a1ca828b94b0cb2b54c223f550cb88db3f1`
- 구현 대상 커밋: [`f0e67cde683812d3fff062a9532ff33874a5a967`](https://github.com/eigger/hass-garage/commit/f0e67cde683812d3fff062a9532ff33874a5a967)
- 테스트 경로: `tests/components/garage/`
- 변경 전 지원 최소 HA / 선언 근거: `2025.3.0` (`hacs.json` 선언; `manifest.json` 및 기존 `README.md`에 별도 상충 선언 없음)
- 적용 후 지원 최소 HA: `2025.3.0` 보존 (통합 버전 `1.3.0` 보존)
- current HA 테스트 환경: 로컬 Python `3.14.5` · 원격 Python `3.14.8` / HA `2026.10.2` / `pytest-homeassistant-custom-component==0.13.373` (`requirements_test.txt`)
- 최소 HA 검증 환경: 로컬 Python `3.13.14` · 원격 Python `3.13.16` / HA `2025.3.0` / `pytest-homeassistant-custom-component==0.13.221` (`requirements_test_min.txt`)
- 최소 package 검증: 해당 없음 (`manifest.requirements=[]`)

## 검증 환경과 경계

실제 HA loader·config entry manager·플랫폼(`button`, `device_tracker`, `sensor`)·flow·options·service·registry를 실행합니다. 외부 HTTP 응답만 플러그인의 `aioclient_mock` 및 단위 테스트용 세션 경계로 대체하며, 기존 47개 단위/회귀 테스트를 보존하고 실제 HA 통합 테스트를 더해 총 79개 테스트(`0 skipped, 0 warnings`)를 구성했습니다. `sys.modules` 가짜 HA 모듈과 `FakeHass` 기반 통합 대체는 제거했습니다.

domain(`garage`), entry schema(`VERSION = 1`), unique ID(`{entry_id}_due_reminders`, `{entry_id}_last_push_at`, `{entry_id}_location`, `{entry_id}_push_now`, `{entry_id}_refresh_now`), 상태/속성 계약, 통합 버전(`1.3.0`)은 변경하지 않습니다.

보완 사항:
- `api.py`: `ClientTimeout(total=15)` 명시 적용 및 네트워크 예외(`ClientError`, `ValueError`, `TimeoutError`) 발생 시 URL·인증 토큰·응답 원문이 로그나 예외 문자열에 노출되지 않도록 예외 타입만 남기도록 비식별화(`HA-06`, `HA-12`).
- `__init__.py`: `GarageTelemetryForwarder.async_stop()`에서 상태 변화 리스너와 대기 중인 디바운스 타이머(`_unsub_call_later`)를 함께 해제하고, `async_setup_entry`에서 플랫폼 포워딩이 완료된 뒤 `forwarder.async_start()`를 등록해 부분 setup 실패 시 리스너가 남지 않도록 보장(`HA-05`). 연속 전송 실패 시 첫 회만 `WARNING`, 이후 연속 실패는 `DEBUG`, 복구 시 `INFO`로 기록해 중복 경고를 억제(`HA-12`).
- `config_flow.py`: 옵션/센서 선택 스키마에서 선택하지 않은 `EntitySelector` 필드에 빈 문자열 기본값(`default=""`)을 넣지 않고 기존 설정값이 있을 때만 `suggested_value`를 제공하도록 수정해 실제 HA selector 검증을 통과(`HA-04`).

`test_supported_environment.py`는 최소 테스트 HA가 `hacs.json`의 지원 하한(`2025.3.0`)과 정확히 일치하고 현재 테스트 HA(`2026.10.2`)가 그 하한 이상인지, 그리고 실제 설치된 HA와 플러그인이 각 환경의 정확한 requirements와 일치하는지 검증합니다. 최소 환경은 HA 2025.3.0이 고정한 `aiohttp==3.11.13`과 [당시 공식 Bluetooth manifest](https://github.com/home-assistant/core/blob/2025.3.0/homeassistant/components/bluetooth/manifest.json)의 6개 helper 버전을 `constraints/homeassistant-min.txt`에 고정합니다. Dependabot의 `exclude-paths`로 역사적 최소 requirements와 constraints를 자동 갱신에서 제외합니다.

## 게시와 원격 검증

- 구현 `master` 커밋: [`f0e67cde683812d3fff062a9532ff33874a5a967`](https://github.com/eigger/hass-garage/commit/f0e67cde683812d3fff062a9532ff33874a5a967)
- [Tests `39046204956`](https://github.com/eigger/hass-garage/actions/runs/39046204956): `current` (`Python 3.14.8 / HA 2026.10.2 / plugin 0.13.373 / aiohttp 3.14.5`) 79 passed in 2.19s, `minimum-ha` (`Python 3.13.16 / HA 2025.3.0 / plugin 0.13.221 / aiohttp 3.11.13`) 79 passed in 2.94s (양쪽 `0 skipped, 0 warnings`, `pip check` 및 lint 2개 job 모두 PASS)
- [Validate `39046204905`](https://github.com/eigger/hass-garage/actions/runs/39046204905): HACS 9/9 checks (brands 포함, ignore 없음) 및 Hassfest 모두 PASS
- 중앙 구현·검증 종료 보고: [`d665b57f7ff28bf81752500abb5d8ed52f99a3a3`](https://github.com/eigger/hass-repo-standards/commit/d665b57f7ff28bf81752500abb5d8ed52f99a3a3)

위 CI는 구현 커밋 `f0e67cde683812d3fff062a9532ff33874a5a967`의 실제 검증 결과입니다. 이 2문서 마감 커밋은 게시 후 독립 검증 담당이 자동 CI를 확인하고 중앙 최신 현황표에 최종 문서 커밋·CI와 완료 상태를 반영합니다.

## 예외

현재 기록된 적용 예외는 없습니다.

- `master` branch protection 조회는 `404 (Branch not protected)`, rulesets는 빈 배열(`[]`)이므로 기존 required checks를 대기 상태로 만드는 설정 변경은 없습니다.
- 로컬 브랜드 아이콘(`custom_components/garage/brand/icon.png` 256×256, `icon@2x.png` 512×512)은 기존 리포 자산을 그대로 유지합니다. 로컬 brand의 HA UI 표시는 HA 2026.3부터 지원되므로 지원 최소 HA 2025.3.0에서의 UI 표시나 실제 HA frontend 렌더링 검증을 주장하지 않습니다.
- 운영 Garage 서버·실물 차량 OBD/GPS 환경과의 실물 검증은 이번 작업에서 수행하지 않았습니다. 채택 작업만으로 태그나 GitHub Release를 새로 생성하지 않습니다.
## 2026-10-23 ZIP release and Downloads update

Base commit: `ebca866e31219836fb6c976594d18c3d4bf1fbea`. HACS remains Custom. `hacs.json` now selects `garage.zip`; publishing the next release builds and attaches that integration ZIP through the pinned central action. Analytics Usage is replaced by Downloads. The archive contains tracked integration files at its root. No existing release/tag/assets are modified.

Implementation and review: root; generated release caller reuses the independently reviewed central ZIP contract. Support minimum, manifest, code, dependencies, README body and prior adoption exceptions are preserved. Verification evidence is recorded in ADOPTION_CHECKLIST.md; this scoped update does not establish full standards compliance.

## 2026-10-25 중앙 검사기 갱신

- 검토한 중앙 main: `1863343638014adb8a4001afc8fddc1a27dc500f` (git ls-remote 확인). 이전 기본 기준 `8bf07f496b4688f64d71980e2c36696751be91fb`의 채택 이력은 위 기록을 보존합니다.
- 모든 중앙 workflow/action pin과 reusable workflow의 standards-ref를 같은 검토 SHA로 맞춥니다. HACS-04는 actions/*의 full SHA 고정을 유지하면서 SHA 값 차이를 허용합니다.
- Validate에 중앙 템플릿의 무조건 실행 standards job을 추가합니다. 기존 HACS/Hassfest와 HA test job 이름·입력은 보존하며, 기본 브랜치를 사용하는 중앙 실행 조건을 적용합니다.
- 통합 코드·런타임 의존성·지원 최소·배포 버전은 이번 변경 대상이 아닙니다. 기존 채택 범위를 전체 완료로 바꾸지 않으며 실제 검증 결과와 남은 항목은 ADOPTION_CHECKLIST.md의 같은 날짜 기록을 참조합니다.


### 2026-10-25 Standards 파일·표시 이름 분리

- 기존 Validate의 중앙 검사 job을 `standards.yml`로 옮기고 workflow/job 표시 이름을 `Standards`로 줄였습니다. Validate의 HACS/Hassfest, 검사 항목·통과 기준·실행 단계·조건·권한은 유지합니다.
- 위치 인식과 중앙 명명 안내를 맞춘 검토 소스: `ca740d88b32fa5dcbc94c41fce2908450c76ed50` ([중앙 PR #24](https://github.com/eigger/hass-repo-standards/pull/24), 현재 이 PR의 의존 변경). 이전 기준 `1863343638014adb8a4001afc8fddc1a27dc500f`의 검증 이력은 앞 기록으로 보존합니다. 모든 중앙 pin·standards-ref는 같은 새 검토 소스로 맞춥니다.
### 2026-10-25 immutable central release reference migration

- User-requested partial migration: current central caller references use immutable `v1.0.0` resolved to `44349ee5621eea5d80e5c427f7a2435d2c2491bb`. Prior scoped ZIP SHA evidence is retained here: `ca740d88b32fa5dcbc94c41fce2908450c76ed50`. Runtime code, dependencies, support minimum, manifest and integration version are unchanged.
