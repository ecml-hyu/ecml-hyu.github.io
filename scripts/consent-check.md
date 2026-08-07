# 동의 확인 필요 목록

갱신: 2026-08-07

**현재 확인이 필요한 항목은 없습니다.**

## 확인 완료

| 이름 | 그룹 | 확인일 |
|---|---|---|
| 조규상 (Gyu Sang Cho) | alumni | 2026-08-07 |
| 손수지 (Suji Son) | alumni | 2026-08-07 |

동의 확인 결과는 `scripts/parse_members.py` 의 `CONSENT_GRANTED` 에도 적어 두었다.
파서를 `--force` 로 다시 돌려도 `needs_consent` 가 다시 붙지 않는다.

## 새로 졸업생이 추가되면

파서가 자동으로 `needs_consent: true` 를 붙인다. 템플릿이 그 항목을 건너뛰므로
동의를 받기 전까지는 사이트에 노출되지 않는다.
동의를 받으면 `CONSENT_GRANTED` 에 이름을 추가하고 YAML 의 해당 줄을 지운다.
