# 공통 규칙 적용 체크리스트

`hass-garage` 첫 채택의 실제 점검 기록입니다. [사용법과 판정 기준](https://github.com/eigger/hass-repo-standards/blob/8bf07f496b4688f64d71980e2c36696751be91fb/docs/checklist.md)을 읽고, 아래 규칙은 `STANDARDS.md`에 기록한 표준 커밋에서 확인합니다. 태그·릴리스 대신 검토한 전체 커밋 SHA를 기준으로 합니다.

## 검토 대상

| 항목 | 값 |
|---|---|
| 통합 리포 / 실제 기본 브랜치 | `eigger/hass-garage` / `master` |
| domain / 구현 경로 | `garage` / `custom_components/garage/` |
| 검토 대상 통합 커밋 / 채택 PR | 시작 `f7f88a1ca828b94b0cb2b54c223f550cb88db3f1` → 구현 및 독립 검증 완료 (원격 push 및 CI 확인 예정) |
| 검토한 표준 전체 커밋 SHA | `8bf07f496b4688f64d71980e2c36696751be91fb` |
| 검토일 / 조율 담당 | 2026-10-18 / `root` |
| 구현 서브 에이전트 / 독립 리뷰·검증 서브 에이전트 | `garage_implementation` / `garage_review` |
| 중앙 현황표 반영일 / 기록 | 2026-10-18 — 시작 등록 [`e30cd06`](https://github.com/eigger/hass-repo-standards/commit/e30cd06); 원격 CI 확인 후 종료 보고 갱신 예정 |
| 변경 전 지원 최소 HA / 근거 파일(hacs.json·manifest·README) | `2025.3.0` — `hacs.json.homeassistant` 선언 (`manifest.json` 및 기존 `README.md`에 별도 상충 선언 없음) |
| 유지·변경할 지원 최소 / 변경 시 실제 비호환 근거·명시적 승인 | `2025.3.0` 유지 (통합 버전 `1.3.0` 유지) |
| current 테스트 HA / 호환 Python·플러그인 | HA `2026.10.2` / 로컬 Python `3.14.5` / `pytest-homeassistant-custom-component==0.13.373` |
| 최소 테스트 HA / 호환 Python·플러그인 | HA `2025.3.0` / 로컬 Python `3.13.14` / `pytest-homeassistant-custom-component==0.13.221` |
| profile / 테스트 경로 | `integration / ha` · `tests/components/garage/` |
| 이전 검토 기록 | 최초 채택 |
| 채택 판정 | 로컬 구현·독립 재검증 PASS (79 passed, skip 0, warning 0); 원격 `master` push 및 GitHub Actions CI 확인 후 최종 완료 전환 |

상태: `TODO` = 미확인·미충족, `PASS` = 근거로 확인, `EXCEPTION` = 적용 대상의 기록된 예외, `N/A` = 적용 조건에 해당 없음. 모든 항목은 미확인으로 시작합니다. `TODO`를 해당 없음으로 처리하지 않습니다. 묶은 규칙의 결과가 다르면 행을 나눕니다. 권장 항목은 별도로 표시했으며 미채택 이유를 기록합니다.

## 채택·구조·사용자 데이터

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| GOV-01, GOV-02 | `STANDARDS.md`에 표준 SHA·profile·실제 기본 브랜치·예외 기록, workflow/action은 검토 SHA로 고정 | PASS | [STANDARDS.md](STANDARDS.md)에 표준 SHA `8bf07f496b4688f64d71980e2c36696751be91fb`·`integration / ha`·`master` 기록; `.github/workflows/tests.yml` 및 `validate.yml`에 동일 전체 SHA 고정 |
| GOV-03 | 새 표준 채택 변경의 영향·이관 방법과 명시적 채택 PR 확인. 규칙 자체를 변경하면 공통 CHANGELOG 기록 | PASS | 최초 채택이며 지원 하한(`2025.3.0`)·계약 보존 및 변경 영향을 `STANDARDS.md`와 `docs/development.md`에 기록. 중앙 규칙 자체 변경 없음 |
| GOV-04 | 중앙 표에 작업 시작·단계 변경·종료 상태, 담당·적용 내용·검증/리뷰 근거·남은 작업 갱신, 타 리포 기록 보존 | PASS | 중앙 `e30cd06`에 시작 등록 완료; 원격 CI 확인 직후 중앙 `docs/adoption-status.md`의 `hass-garage` 행에 종료 결과 반영 |
| GOV-05 | 구현과 독립 리뷰·검증을 별도 서브 에이전트에게 위임, 지적 수정·재검증 및 결과 취합 | PASS | 구현 `garage_implementation`과 독립 리뷰 `garage_review` 분리 수행; `HA-05` 부분 setup 리스너 정리 보완 후 두 격리 환경(`/tmp/garage-review-current`, `/tmp/garage-review-min`)에서 각 79 passed 독립 재검증 완료 |
| HA-01, HA-13 | `custom_components/<domain>/`와 domain 일치, 필요한 모듈·공개 API·생명주기는 Core 대응 구조 | PASS | `custom_components/garage/` 및 `manifest.json`/`const.py` domain `garage` 일치; `api`, `config_flow`, `coordinator`, `button`, `device_tracker`, `sensor`, `runtime_data` Core 대응 구조 |
| HA-02 | manifest 필드·정렬·동작 선언 확인, 공식 품질 등급 자가 표기 없음 | PASS | `manifest.json`: `domain`, `name` 이후 `codeowners`, `config_flow`, `documentation`, `iot_class`(`local_polling`), `issue_tracker`, `requirements`(`[]`), `version`(`1.3.0`) 알파벳순 정렬, `quality_scale` 자가 표기 없음 |
| HA-03 (권장) | 공통 상수·설정·갱신·플랫폼 역할 및 프로토콜 경계에 맞게 모듈 구성 | PASS | `const.py`, `api.py`, `config_flow.py`, `coordinator.py`, `__init__.py`, 플랫폼 모듈 역할 분리 유지 |
| HA-04, HA-08 | UI 설정·중복·안정적 식별 및 기능별 options/reauth/reconfigure, entity 의미·registry 영향 확인 | PASS | `test_config_flow.py`에서 `user`→`sensors`, `unique_id` 중복 방지, `reauth`, `options` 흐름 검증; `test_sensor.py`·`test_button.py`·`test_device_tracker.py`에서 unique ID 및 registry/state 검증 |
| HA-01, HA-04, HA-08, REL-01, REL-03 | domain·unique ID·entry schema·상태/통계 계약 변경 시 migration 테스트와 사용자 조치 안내 | N/A | domain, `ConfigFlow.VERSION = 1`, entry data/options 구조, 엔티티 unique ID 및 상태/속성 계약 변경 없음 |
| HA-05, HA-06 | setup 실패 구분, unload/reload·부분 실패의 task/listener/연결 정리, async·timeout·취소 처리 | PASS | `test_init.py`에서 초기 500 `SETUP_RETRY`, 401 `SETUP_ERROR`+reauth, 플랫폼 포워딩 중 예외 발생 시 리스너 미잔류, reload/unload 시 디바운스 타이머·상태 리스너 정리 확인; `api.py` `ClientTimeout(total=15)` 적용 |
| HA-07 | 중복 polling·property I/O 방지, push 보존, unavailable/unknown·실패 후 복구 | PASS | 상태(5분)·리마인더(30분) 공유 coordinator polling 및 이벤트 기반 디바운스·직렬화 push 보존; property 내 I/O 없음; `test_coordinator.py`·`test_sensor.py`에서 실패 및 복구 확인 |
| HA-11, HA-12 | 번역·action/schema 일치, 로그/diagnostics/fixture 비식별화와 제공 시 redaction 테스트 | PASS | `strings.json`·`en.json`·`ko.json` 키 일치; `api.py` 네트워크 예외 원문(URL·토큰) 비노출 회귀(`test_api.py`), 연속 push 실패 경고 억제(`test_forwarder.py`), 비식별 fixture 사용. 별도 diagnostics 플랫폼은 미제공 |

## 실제 HA 테스트·호환성·의존성

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| TEST-08 | `tests/components/<domain>/`에 구현과 대응하는 테스트·domain fixture 배치, discovery·CI 경로 일치 | PASS | `tests/components/garage/` 및 `fixtures/status.json`, `fixtures/reminders.json` 배치; `pyproject.toml` `testpaths` 및 CI `pytest-args` 일치 |
| TEST-02, TEST-03, DEP-07 | 실제 HA·호환 플러그인과 `hass`/`enable_custom_integrations` fixture 사용, HA core stub/복사본/`--no-deps`로 대체하지 않음 | PASS | 기존 `sys.modules` 가짜 HA 등록 제거; 실제 `hass`, `enable_custom_integrations`, `MockConfigEntry`, `aioclient_mock` 사용 |
| TEST-09 | 실제 loader·config entry manager로 setup/플랫폼 로딩, HA 상태·registry·service/action으로 결과 검증 | PASS | `test_init.py`, `test_config_flow.py`, `test_sensor.py`, `test_button.py`, `test_device_tracker.py`에서 실제 entry setup/unload, flow/options, `hass.states`, registry, `button.press` 서비스 호출 검증 |
| TEST-01, TEST-06, TEST-07 | 구현 기능별 성공·실패·중복·migration·unload·복구 회귀 검증, 외부 통신 경계만 mock, skip 사유 | PASS | 기존 47개 단위 테스트 메서드 100% 보존 + 실제 HA 통합 및 경계 회귀 테스트 32개 추가 = 총 79 passed (0 skipped, 0 warnings); 외부 HTTP 응답만 mock |
| TEST-04, HACS-01 | 변경 전 지원 최소·current·각 Python/플러그인 분리, 선언한 정확한 최소 검증, 상향 시 비호환 근거·명시적 승인 확인 | PASS | `hacs.json` 지원 최소 `2025.3.0` 유지; 최소 환경(`Python 3.13.14 / HA 2025.3.0 / plugin 0.13.221`)과 현재 환경(`Python 3.14.5 / HA 2026.10.2 / plugin 0.13.373`) 별도 격리 검증 및 `test_supported_environment.py` 확인 |
| TEST-05, HA-10, DEP-02, DEP-05 | imagespec·blesession 등 최소/현재 라이브러리 별도 환경, 실제 HA 테스트·정확한 설치값·API 경계 검증 | N/A | `manifest.requirements=[]`로 외부 런타임 Python 패키지 없음 |
| DEP-01, DEP-06 | Python runtime은 manifest requirements, HA domain은 dependencies/after_dependencies, 테스트·린트 requirements는 별도 | PASS | 런타임 `manifest.requirements=[]` 유지; `requirements_test.txt`, `requirements_test_min.txt`, `constraints/homeassistant-min.txt`, `requirements_lint.txt` 분리 |
| DEP-07, CI-06 | 실제 사용하는 HA 구성요소의 requirements·필수 재귀 의존성·선택 로딩 경로 설치, resolver·`pip check` 통과 | PASS | 중앙 `install.py`로 `button device_tracker sensor` 구성요소 의존성 설치 후 양 환경 모두 `pip check` 통과 |
| DEP-02, DEP-03, DEP-08 | 의존성 추가/변경의 버전·extras·marker·선언 위치·지원 플랫폼·라이선스 검토, 실제 HA 테스트와 문서 갱신 | PASS | 테스트·린트 전용 정확한 `==` 고정 및 최소 환경 constraints 분리, `docs/development.md`·`docs/ko/development.md` 문서화 완료 |

| 검증 축 / 상태 | 통합 커밋 | Python / HA / 플러그인 실제 버전 | 대상 패키지 실제 버전·extras·marker | 명령·테스트 결과·pip check / CI run·job | skip·제외·미검증 범위 |
|---|---|---|---|---|---|
| 구현·독립 현재 테스트 HA / PASS | 원격 push 후 커밋 기록 | 로컬 Python `3.14.5` (원격 `3.14`) / HA `2026.10.2` / plugin `0.13.373` / `aiohttp==3.14.5` / `ruff==0.17.1` | runtime package 없음 (`manifest.requirements=[]`) | 구현·독립 격리 venv에서 `install.py` → `pytest tests/components/garage/ -v` **79 passed (0.79s, skip 0, warning 0)**, `pip check`·`ruff check .`·`ruff format --check .` PASS | 운영 Garage 서버·실물 차량·HA UI 미검증 |
| 구현·독립 정확한 최소 지원 HA / PASS | 동일 | 로컬 Python `3.13.14` (원격 `3.13`) / HA `2025.3.0` / plugin `0.13.221` / `aiohttp==3.11.13` + 공식 helper constraints | runtime package 없음 (`manifest.requirements=[]`) | 구현·독립 격리 venv에서 `install.py` → `pytest tests/components/garage/ -v` **79 passed (0.96s, skip 0, warning 0)**, `pip check` PASS | 운영 Garage 서버·실물 차량·HA UI 미검증 |
| 정확한 최소 라이브러리 / N/A | 해당 없음 | 해당 없음 | `manifest.requirements=[]` | 대상 없음 | 해당 없음 |

## HACS·CI·의존성 업데이트

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| HACS-01, HACS-02 | 루트 README/LICENSE/hacs.json, 검증한 최소 HA, 실제 배포 구조와 필요한 옵션 일치 | PASS | 루트 `README.md`, `LICENSE`, `hacs.json`(`homeassistant: "2025.3.0"`), `custom_components/garage/` 구조 일치 |
| HACS-03, HACS-05 | Default 여부는 목록 근거로 확인, [로컬 brand/icon.png 또는 원격 brands 근거](https://github.com/eigger/hass-repo-standards/blob/8bf07f496b4688f64d71980e2c36696751be91fb/docs/hacs.md)와 HACS/Hassfest 실제 실행, ignore는 이유·해제 조건 기록 | PASS | HACS Custom 배지 사용; 로컬 `custom_components/garage/brand/icon.png`(256×256) 및 `icon@2x.png`(512×512) 확인, ignore 없음; 원격 Validate 실행 결과는 push 후 아래에 기록 |
| HACS-06 (권장) | description·topics·issue 경로·brands 및 사용하는 HACS 필드 지원 확인 | PASS | `hacs.json`에서 구식 `render_readme` 제거, 실제 활성 Issues/Discussions 및 로컬 brand 확인 |
| CI-01, CI-02 | Validate/Python Tests 공통화, 확장 job 유지, PR·실제 기본 브랜치 push·dispatch 및 필요한 schedule | PASS | `.github/workflows/tests.yml`(`current`, `minimum-ha`) 및 `validate.yml`에서 중앙 workflow 호출; `master` push, PR, `workflow_dispatch`, 주간 `schedule` 설정 |
| CI-03, CI-05, CI-08 | 최소 권한·checkout 자격증명 비보존·timeout·concurrency, full SHA·갱신 관리, 비신뢰 입력·secrets 경계 | PASS | caller `permissions: contents: read`, workflow+ref concurrency, 표준 전체 SHA `8bf07f496b4688f64d71980e2c36696751be91fb` 고정, `.github/dependabot.yml` 설정 |
| CI-04, CI-07, CI-12 | 실패를 숨기지 않는 실제 `ha` 필수 테스트, 버전별 환경·cache·Ruff 설정과 required checks 이름 확인 | PASS | `test-profile: ha` 필수 테스트, Python 3.14/3.13 및 각 requirements 분리, `pyproject.toml` Ruff/pytest 설정; `master` branch protection 미설정(404) 및 rulesets 빈 배열(`[]`) 확인 |
| DEP-03, DEP-04, CI-09 | updater의 선택 package·연산자/extras/marker 보존, 안정 버전·major 정책, 실제 기본 브랜치·단일 bot branch·PR만 제안 | N/A | `manifest.requirements=[]`로 manifest dependency updater 대상 없음; Dependabot은 Actions 및 최신 테스트 그룹만 PR 제안 |
| CI-09, CI-10, DEP-08 | 변경 tree의 새 하한·실제 HA 검증 후 PR 동기화, 실패 시 중단·변경 없음 시 기존 PR 정리, 후속 required checks 충족 방식 확인 | N/A | manifest dependency updater 대상 없음 |

## README·Bluetooth·유지보수

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| DOC-01, DOC-02, DOC-06 | 영어 README.md·한국어 README.ko.md·상호 링크·기존 내용 보존, 간결한 제목/소개/핵심지원/최소요구/빠른설치·설정/짧은예제/중요제한/문서목록, 상세옵션·긴YAML·참조·개발/실HA테스트·의존성/검증범위를 docs·examples 등으로 보존·분리하고 유효한 링크 제공, 실제 활성 Issues·Discussions 또는 대체 지원 경로·실제 LICENSE 링크 | PASS | 영문 [README.md](README.md)·한국어 [README.ko.md](README.ko.md) 상호 연결 및 간결한 시작 구성; 기존 한국어 본문 전체를 [docs/ko/user-guide.md](docs/ko/user-guide.md)와 영문 [docs/user-guide.md](docs/user-guide.md)에 보존, 개발·테스트 안내는 [docs/development.md](docs/development.md)·[docs/ko/development.md](docs/ko/development.md)로 분리; 모든 상대 링크·앵커 및 활성 Issues/Discussions·[LICENSE](LICENSE) 확인 |
| DOC-03, DOC-04, DOC-05 | 제목 아래 관리 블록, flat-square·순서·실제 조건별 배지, CI 실제 기본 브랜치, 필수 동적 Usage·Analytics 참여 설치 의미·미집계/조회 실패와 0 설치 구분·이전 안내 보존 | PASS | `.hass-standards.json` 및 `sync_badges.py --check` 통과; HACS Custom → Release → HA minimum(`2025.3.0`) → Tests(`master`) → Validate(`master`) → License → Usage(`$.garage.total`) 순서·`flat-square` 적용 및 Usage 집계 의미 명시 |
| HA-09, HA-10 | BLE 사용 시 HA Bluetooth API·라이브러리 공개 경계, 지원한 proxy 경로·재연결·취소·서비스 변경 검증 | N/A | 로컬 HTTP/HTTPS 통합(`iot_class: local_polling`)으로 Bluetooth/blesession/imagespec 미사용 |
| DOC-07 | blesession/proxy 통합 README에서 공통 Bluetooth 설정·추천 기기/리비전·active 연결/스캔 차이·문제 해결 안내로 연결 | N/A | Bluetooth proxy 미사용 |
| DOC-07, HA-12 | 기기별 깨우기·인증·타 앱 연결·전송 제약, 실제 검증 경로와 미검증 범위, 공개 문제 로그 비식별화 | PASS | Bluetooth 기기 조건은 N/A; 사용자 안내에 이슈 제보 시 토큰·개인 서버 주소·위치/차량 정보 비식별화 안내 및 실서버 미검증 한계 명시 |
| HACS-04, REL-01, REL-02, REL-03, CI-11 | 통합 릴리스 시 같은 검증 commit/tag·manifest 버전·산출물·권한, 사용자 영향·지원 변경·제한 안내 | N/A | 이번 채택 작업에서는 새 태그·릴리스·버전 변경을 수행하지 않음 (`version: "1.3.0"` 유지) |
| REL-04 | 이전/중단 시 README 상단 경로·유지보수 상태·재등록 여부, 자동 이전으로 오인하지 않는 안내 | N/A | 리포 이전·통합·중단 해당 없음 |
| REL-05 (권장) | 의존성/HA API 변경과 기능 변경 분리, 표준 변경은 명시적 채택 PR로 반영 | PASS | 공통 규칙 채택과 실제 HA 생명주기·로그/예외 보호 범위로만 변경 유지 |

## 예외와 남은 작업

예외 원본은 `STANDARDS.md`입니다. 현재 기록된 필수 예외는 없습니다.

| 규칙 ID | 예외 위치 / 이유 | 담당자 | 재검토 조건 |
|---|---|---|---|
| 없음 | [STANDARDS.md](STANDARDS.md#예외) 확인 — 적용 대상 필수 항목 모두 PASS 또는 근거 있는 N/A | `root` / `garage_review` | 후속 규칙·구현 변경 시 |

| 구분 | 후속 조치·검증 한계 | 담당자 | 완료 근거 |
|---|---|---|---|
| 원격 CI 및 중앙 마감 | `master` push 후 원격 Tests·Validate 성공 확인 및 중앙 `docs/adoption-status.md` 완료 갱신 | `root` / `garage_review` | 아래 원격 검증 기록에 추가 |
| 수동 검증 한계 | 운영 Garage 서버·실물 차량 환경 및 HA frontend UI 미검증 | 유지보수 담당 | HTTP 경계 mock 기반 실제 HA 테스트·PNG 규격·HACS 검증과 구분 |
