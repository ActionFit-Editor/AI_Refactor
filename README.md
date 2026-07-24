# AI Refactor (com.actionfit.ai-refactor)

AI Code Convention을 기준으로 Unity 프로젝트 아키텍처를 읽기 전용으로 조사하고, 증거에 근거한 단계별 리팩터링 제안을 만드는 패키지입니다. 명시적으로 선언된 패키지 소유 제품 composition root, 남아 있는 프로젝트 shell, 현재 소유권 graph, 트리 지향 목표 DAG, 응집력 있는 패키지 후보와 이를 연결하는 좁은 port 및 프로젝트 adapter를 설명할 수 있게 합니다. 제안 전에 AI Jira의 프로젝트 전체 `todo`, `progress`, `done` 작업을 완전 조회해 기존 리팩터링 작업과의 중복도 검사합니다.

이 패키지는 **Public** 저장소에서 배포되며 Runtime 어셈블리, 게임플레이 프레임워크, 자동 리팩터링 엔진, 에셋 마이그레이션 또는 publish workflow를 포함하지 않습니다. 제안을 자동 적용하지도 않습니다. Public 공개 범위는 소스를 읽을 수 있게 할 뿐, 자격 증명을 포함하거나 저장소의 명시적 라이선스 범위를 넘는 권리를 부여하지 않습니다.

## 설치

```json
{
  "dependencies": {
    "com.actionfit.custompackagemanager": "https://github.com/ActionFit-Editor/Custom_Package_Manager.git#1.1.106",
    "com.actionfit.referencebinding": "https://github.com/ActionFit-Editor/ReferenceBinding.git#0.2.2",
    "com.actionfit.ai-codeconvention": "https://github.com/ActionFit-Editor/AI_Code_Convention.git#0.5.2",
    "com.actionfit.ai-jira": "https://github.com/ActionFit-Editor/AI_Jira.git#1.0.28",
    "com.actionfit.ai-refactor": "https://github.com/ActionFit-Editor/AI_Refactor.git#0.2.6"
  }
}
```

Custom Package Manager는 선언된 AI Code Convention, AI Jira와 package manager 의존성을 카탈로그에서 해석합니다. Unity는 semantic-version 패키지 의존성에서 전이 Git URL을 해석하지 않으므로 Git UPM을 직접 사용하는 경우에는 위 다섯 개의 root 항목을 모두 유지해야 합니다.

## Agent Skill 안내

- `$refactor-help`: 패키지 출력, 의존성, 메뉴, 관련 skill과 읽기 전용 경계를 설명합니다.
- `$refactor-plan`: 선택한 Unity 저장소를 조사하고 유효한 AI Code Convention 및 설치된 API owner guide와 결과를 대조해, 증거 기반의 단계별 제안을 반환합니다.

`$refactor-plan`은 먼저 `Skills~/Shared/scripts/ai_refactor_jira_cli.py`를 통해 AI Jira의 읽기 전용 overlap 조회를 실행합니다. 설정된 프로젝트의 모든 담당자를 대상으로 정확히 `todo`, `progress`, `done` 상태를 끝 페이지까지 조회하고 각 이슈 상세를 확인합니다. Jira 도구·설정·인증·권한·상태 매핑·pagination 완료 증거·상세 중 하나라도 없으면 전체 분석을 중단합니다. `Exact overlap` 또는 범위가 중요한 `Partial overlap`은 완료 이슈를 포함해 목표 DAG나 단계 제안 전에 중단하고 기존 이슈 재사용, 중복 범위 제외, 검증된 잔여 범위만 계획 중 하나를 사용자에게 결정하도록 요청합니다. `Related`는 경계를 기록하고 계속할 수 있으며 모든 이슈를 확인한 뒤에만 `No overlap`을 사용할 수 있습니다.

중복이 없으면 번들된 `Skills~/Shared/scripts/refactor_inventory.py` 읽기 전용 inventory를 실행합니다. Schema v2는 후보 신호, 설치된 embedded 및 소스가 확인된 PackageCache 어셈블리/패키지 edge와 cycle을 보고합니다. 외부 local-package root는 인식하지만 내부를 순회하지 않고, BOM 유무와 관계없이 UTF-8 JSON을 허용하며, 고아·오래된·모호한 cache copy와 Markdown fenced/indented code 또는 HTML comment 안의 marker 예제를 무시합니다. 명시적 제품 composition 선언은 `absent`, `valid`, `invalid`로 보고합니다. 조사하지 않은 외부 local package에 다른 선언이 있을 수 있으므로 해당 항목은 `unscanned-local-package` 누락 증거가 되어 유효한 root 선택을 막습니다. 잘못되거나 순환하는 `file:` 참조는 inventory를 중단하지 않고 제한된 진단으로 남습니다. 유효한 선언은 정확한 AI Code Convention marker 계약을 사용해야 하며 profile 선택, 마이그레이션 완료 또는 편집 권한을 뜻하지 않습니다. Convention 위반을 분류하기 전에는 소스를 직접 확인해야 합니다.

출력에는 제품 composition과 project shell, 현재 조사 결과, 목표 소유권 tree/DAG, 패키지 후보, port/adapter, 순서가 있는 단계, 마이그레이션 및 호환 위험, 검증, 신뢰도와 누락된 증거가 포함됩니다. 증거가 있을 때만 제품 node를 `Composition`, `Product`, `Reusable`, `Project Shell`, `Exception`으로 분류할 수 있습니다.

이 workflow는 소스, 에셋, Scene, Prefab, ScriptableObject, 설정, manifest, Jira, Git ref, 패키지 또는 설치된 skill을 수정하지 않습니다. Jira 사용은 프로젝트 범위 overlap 및 이슈 상세 읽기로 제한됩니다. 쓰기 가능한 Unity 명령, publish, 저장소 생성도 실행하지 않으며 후보 신호를 자동으로 결함이라고 판단하지 않습니다.

## Unity 메뉴

- README: `Tools > Package > AI Refactor > README`
- 설정 에셋이나 실행 가능한 Unity 분석 메뉴는 없습니다.

## AI 가이드

- 사용하는 프로젝트에서 이 패키지를 변경하거나 진단하기 전에 `AI_GUIDE.md`를 읽습니다.
- 안정적인 `AFCC-*` 의미는 AI Code Convention `0.5.2`가 소유합니다. AI Jira `1.0.28`은 Jira REST/JQL, 완전 pagination과 이슈 상세 읽기를 소유합니다. AI Refactor는 해당 증거의 의미 기반 overlap 분류, inventory 및 제안 orchestration만 소유합니다.

## 어셈블리

- **Editor** (`com.actionfit.ai-refactor.Editor`): Editor 전용 패키지 어셈블리입니다.
