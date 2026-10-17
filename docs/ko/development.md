# 개발과 테스트

[English](../development.md) | [한국어](development.md) | [README](../../README.ko.md)

최신 테스트 환경은 HA 2026.10.2·플러그인 0.13.373·Python 3.14.2 이상입니다. 지원 최소 버전은 HA 2025.3.0으로 유지하며, 별도 Python 3.13 환경에서 그 버전에 호환되는 플러그인 0.13.221로 검증합니다.

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements_test.txt -r requirements_lint.txt
.venv/bin/python -m pip check
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest tests/components/garage/ -v
```

최소 HA 검증은 별도 Python 3.13 가상환경에서 `requirements_test_min.txt`를 설치해 같은 pytest 명령을 실행합니다. 테스트는 현재·최소 환경별 정확한 HA/플러그인 설치값을 확인하고 최소 환경이 `hacs.json`의 지원 하한과 일치하는지 검사합니다. 최신 테스트 환경을 갱신하는 것만으로 컴포넌트 지원 하한을 올리지 않습니다. 테스트 의존성은 런타임 manifest(`requirements: []`)와 분리하며 호환 HA·플러그인 버전을 함께 검토합니다. 자세한 환경·검증 범위는 [적용 기준](../../STANDARDS.md)과 [체크리스트](../../ADOPTION_CHECKLIST.md)를 참고하세요.
