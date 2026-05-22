# 🖥️ 리눅스 프로세스 및 시스템 리소스 트러블슈팅

## 1. 프로젝트 개요 (미션 목표)
운영 중인 서버 환경에서 발생할 수 있는 주요 시스템 장애인 **OOM(Out Of Memory) Crash, CPU Latency, Deadlock(교착상태)** 현상을 시스템 관제 데이터를 기반으로 분석하고, 환경변수 설정을 통해 임시 조치 및 예방책을 수립합니다. 본 프로젝트는 장애 원인을 단순 추정이 아닌 로그와 시스템 도구(`ps`, `top`, `monitor.sh` 등)의 객관적 증거를 기반으로 역추적하여 GitHub Issue 형식의 기술 리포트로 작성하고, 보너스 미션으로 스케줄링 알고리즘(Round-Robin)을 로그의 타임스탬프를 통해 논리적으로 역추론하는 역량을 기르는 것을 목표로 합니다.

---

## 2. 실행 환경
본 트러블슈팅 미션은 다음과 같은 로컬 개발 및 OS 환경에서 실행 및 분석되었습니다.
- **OS**: macOS Sequoia 15.x (Darwin 24.6.0, xnu-11417.140.69.708.3~1/RELEASE_X86_64 x86_64)
- **Shell**: `/bin/zsh`
- **Terminal**: zsh (macOS Terminal)
- **Git Version**: `git version 2.53.0`
- **대상 바이너리**: `agent-app-leak` (Python 기반 컴파일 바이너리)

### ⚙️ 어플리케이션 사전 준비 요구사항 (Agent Startup Prerequisites)
애플리케이션이 정상 부팅되기 위해 사전에 다음과 같은 환경 설정 및 디렉터리 구조를 수립했습니다.
- 일반 사용자 계정으로 실행
- 포트 `15034` 고정 사용 및 `0.0.0.0` 네트워크 바인딩
- 필수 환경변수 및 파일 생성:
  - `AGENT_HOME` 환경변수 지정
  - `AGENT_PORT=15034`
  - `$AGENT_HOME/upload_files` 디렉터리 생성 및 쓰기 권한 부여
  - `$AGENT_HOME/api_keys` 디렉터리 생성 및 `secret.key` 파일 배치 (내용: `agent_api_key_test`)
  - `$AGENT_HOME/logs` 디렉터리 생성 및 쓰기 권한 부여

---

## 3. 수행 항목 체크리스트
본 프로젝트에서 수행한 모든 태스크와 세부 요구사항을 아래와 같이 이행 완료하였습니다.

- [x] **사전 준비 및 환경 구축**: 필수 디렉터리 및 환경변수 설정, `secret.key` 생성 확인
- [x] **OOM Crash 분석 및 리포팅**:
  - [x] `monitor.sh` 및 프로세스 RSS 물리 메모리 사용량이 선형적으로 급상승(Memory Leak)하는 패턴 관측
  - [x] `MemoryGuard` 임계치 초과 자폭 로그 식별 및 종료 코드 `137`(SIGKILL) 확인
  - [x] `MEMORY_LIMIT` 변경 전후 비교(최소 2회 실행: 50MB vs 100MB) 및 생존 시간(5초 vs 11초) Before & After 입증
- [x] **CPU 과점유 분석 및 리포팅**:
  - [x] 특정 프로세스의 CPU 사용률이 급상승하는 패턴 관측
  - [x] `CpuWorker` 내부 감시 정책(Watchdog)에 의한 `CPU Threshold Violated` 및 자체 `SIGTERM`(종료 코드 `143`) 확인
  - [x] `CPU_MAX_OCCUPY` 변경 전후 비교(100% vs 10%)를 통해 쿨다운(Cooldown) 제어 메커니즘 동작 확인
- [x] **교착상태(Deadlock) 진단 및 리포팅**:
  - [x] 프로세스가 살아있으나(PID 존재) CPU/메모리 변화 및 로그 기록이 정체된 무응답 상태 식별
  - [x] `ps -L`을 통해 개별 워커 스레드의 CPU 사용률이 `0.0%`로 멈춘 증거 확보
  - [x] `Worker-Thread-1`과 `Worker-Thread-2`가 `Shared_Memory_A`와 `Socket_Pool_B` 자원을 두고 상호 배제 및 순환 대기하고 있는 순환 인과 관계 도식화
  - [x] `MULTI_THREAD_ENABLE` 변경 전후(true -> false) 재현/회피 대조 검증 수행
- [x] **보너스 과제 (스케줄링 알고리즘 역추론)**:
  - [x] 무경쟁 상태 로그의 타임스탬프와 진행률(Progress) 변화를 분석하여 FCFS, Priority가 아닌 Round-Robin 방식임을 증명
  - [x] Round-Robin 방식의 장단점 및 웹 서버 아키텍처에 적합한 당위성 서술
- [x] **이슈 리포트 작성 및 기술 문서화**:
  - [x] 3대 장애 유형과 스케줄링 알고리즘에 대한 종합 기술 보고서 작성 (현상 -> 증거 -> 원인 -> 조치)

---

## 4. 검증 방법
프로젝트에 포함된 스크립트를 사용하여 각 장애 케이스를 아래와 같이 재현하고 검증을 수행했습니다.

### 🧪 시나리오별 실행 및 관제 자동화
- **실행 스크립트**: [run_agent_case.sh](file:///Users/f22losophysics1091/Desktop/check/scripts/run_agent_case.sh)
- **모니터링 스크립트**: [monitor.sh](file:///Users/f22losophysics1091/Desktop/check/scripts/monitor.sh)

각 검증 시나리오는 다음과 같은 환경변수 조합으로 백그라운드 프로세스를 가동하고 관제 로그(`.monitor.log`) 및 애플리케이션 실행 로그(`.app.log`)를 수집했습니다.

#### 1) OOM Crash 검증
```bash
# Before: 50MB 한계 설정 (자폭 재현)
./scripts/run_agent_case.sh oom-low 50 100 false 20

# After: 100MB 한계 설정 (수명 연장 확인)
./scripts/run_agent_case.sh oom-high 100 100 false 20
```

#### 2) CPU 과점유 검증
```bash
# Before: 제한 100% 설정 (폭주 모드 -> Watchdog 자폭 재현)
./scripts/run_agent_case.sh cpu-high 512 100 false 20

# After: 제한 10% 설정 (보안 모드 -> Cooldown 가동 및 자체 종료 무산)
./scripts/run_agent_case.sh cpu-low 512 10 false 20
```

#### 3) Deadlock 교착상태 검증
```bash
# Before: 멀티스레드 활성화 (교착상태 무응답 재현)
./scripts/run_agent_case.sh deadlock-on 512 10 true 25

# After: 싱글스레드(멀티스레드 비활성화) 설정 (스케줄러 순차 처리로 데드락 회피)
./scripts/run_agent_case.sh deadlock-off 512 10 false 20
```

---

## 5. 트러블슈팅
장애 상황별 주요 원인 분석과 조치 결과를 요약합니다. 세부 리포트는 링크된 각 문서를 참조하십시오.

### 🔴 OOM Crash ([상세 리포트](file:///Users/f22losophysics1091/Desktop/check/reports/oom-crash.md))
- **현상**: 실행 후 약 5초(50MB) 또는 11초(100MB)가 경과하면 `Memory limit exceeded`와 함께 강제 종료되는 현상.
- **증거**:
  - `monitor.log` 상 RSS 메모리가 `21MB` -> `47MB` -> `72MB` -> `98MB`로 급상승하는 힙 메모리 누수 패턴 확인.
  - 종료 직전 애플리케이션 `[MemoryGuard]` 로그 발생 및 리눅스 프로세스 종료 코드 `137`(SIGKILL 계열 강제 종료) 반환.
- **원인**: `MemoryWorker`가 사용을 마친 메모리 객체의 참조(Reference)를 끊지 않아 GC(Garbage Collector)가 쓰레기를 수집하지 못하고 메모리에 상주하여 지속해서 메모리가 증가함.
- **조치 및 검증**:
  - `MEMORY_LIMIT` 환경변수를 기존 50MB에서 100MB로 늘려 생존 시간이 5초에서 11초로 약 2배 연장됨을 실증.
  - **근본 대책**: 소스 코드 단에서 주기적으로 미사용 컬렉션이나 힙 영역 객체의 `del` 혹은 `pop` 처리를 유도하여 참조 누수를 제거해야 함.

### 🟡 CPU Latency ([상세 리포트](file:///Users/f22losophysics1091/Desktop/check/reports/cpu-latency.md))
- **현상**: 실행 후 내부 부하 수치(`Current Load`)가 서서히 올라가다 50%를 초과하는 순간 프로세스가 즉시 종료됨.
- **증거**:
  - 앱 로그에 `CPU Threshold Violated! (55.67%)` 임계치 위반 기록.
  - 종료 코드 `143`(128+15, 즉 SIGTERM 계열 정중한 자체 안전 종료) 반환 및 `monitor.log`에서 PID 소멸.
- **원인**: `CPU_MAX_OCCUPY=100`으로 폭주 허용 시 `CpuWorker` 내부 루프가 무리하게 계산량을 증가시킴. CPU 독점 현상은 전체 시스템의 run queue 적체와 타임아웃 지연을 발생시키기 때문에 Watchdog이 자체 안전장치로 작동함.
- **조치 및 검증**:
  - `CPU_MAX_OCCUPY=10`으로 안전 하향 조정 시, 부하가 10%에 달하면 `Peak reached. Starting cooldown...` 로그와 함께 스스로 연산을 비우며 안정성 확보(자체 강제 종료 미발생).
  - **근본 대책**: CPU 집약적 연산 주기에 Backoff, Sleep, 비동기 스레드 위임 및 성능 프로파일링 최적화 구현.

### 🔵 Deadlock (교착상태) ([상세 리포트](file:///Users/f22losophysics1091/Desktop/check/reports/deadlock.md))
- **현상**: 프로세스가 메모리나 CPU를 더 쓰지도 않고 로그도 전혀 올라오지 않으나 프로세스 PID는 계속 살아 있는 무응답 먹통 현상.
- **증거**:
  - `monitor.log` 관제 상 CPU 사용률이 `0.3%` 부근으로 수렴하며 RSS 메모리 크기가 전혀 변동되지 않음.
  - `ps -L` 스레드 레벨에서 각 Worker 스레드(`13122`, `13123`)의 CPU 점유율이 완전히 `0.0%`로 정지.
  - 마지막 로그: `Worker-Thread-1`이 `Shared_Memory_A`를 쥔 상태로 `Socket_Pool_B` 대기, `Worker-Thread-2`는 `Socket_Pool_B`를 쥔 채 `Shared_Memory_A` 대기 (상태: `BLOCKED`).
- **원인**: 상호 배제 성격의 락을 획득하는 순서가 스레드 간 교차하여 상호 의존하는 `순환 대기(Circular Wait)` 구조가 형성됨.
- **조치 및 검증**:
  - `MULTI_THREAD_ENABLE=false` 설정을 적용하여 단일 스레드로 실행하여 스케줄러가 순차 처리하도록 우회(데드락 회피).
  - **근본 대책**: 모든 스레드의 락 획득 순서를 일치시키거나, 락 타임아웃(`try_lock` 및 timeout)을 부여하여 정체 시 락을 해제하고 재시도하도록 코드 리팩토링.

### 🟢 보너스: 스케줄링 알고리즘 역추론 ([상세 리포트](file:///Users/f22losophysics1091/Desktop/check/reports/scheduling-analysis.md))
- **관측 로그 패턴**:
  - `Thread-A` 계산 20% -> 40% -> **`Preempted (Progress saved)`**
  - `Thread-B` 계산 20% -> 40% -> **`Preempted (Progress saved)`**
  - `Thread-C` 계산 20% -> 40% -> **`Preempted (Progress saved)`**
  - `Thread-A` 재개 **`Resumed 60%`**
- **추론 결과 및 논리**:
  - FCFS(선도착 순차처리)라면 A가 100% 다 끝나야 B가 실행되어야 하나, A가 중간에 쫓겨났으므로 FCFS 탈락.
  - Priority(우선순위)라면 편향된 우선도 스레드가 독점해야 하지만, A->B->C가 동일한 비율로 교차 수행되므로 Priority 탈락.
  - 따라서, 일정한 시간 간격 또는 작업량 단위(타임 퀀텀)로 작업을 강제 전환(`Preempted`)하고, 이전 상태를 복원(`Resumed`)하는 **라운드 로빈(Round-Robin)** 알고리즘이 적용되었음을 완벽하게 증명.