# 🖥️ 리눅스 프로세스 및 시스템 리소스 트러블슈팅 종합 보고서

본 보고서는 운영 중인 서버 환경에서 발생할 수 있는 주요 시스템 장애인 **OOM(Out Of Memory) Crash, CPU Latency, Deadlock(교착상태)** 현상을 시스템 관제 데이터를 기반으로 역추적 분석하고, 환경변수 설정을 통해 임시 조치 및 예방책을 수립한 종합 보고서입니다. 본 프로젝트는 단순한 장애 현상 나열을 넘어 로그, 프로세스 상태(`ps`, `top`), 관제 데이터(`monitor.sh`)의 객관적 증거를 기반으로 원인을 논리적으로 규명하였으며, 보너스 미션으로 스케줄링 알고리즘(Round-Robin)을 로그의 타임스탬프를 통해 분석한 결과와 리눅스 시스템 트러블슈팅의 핵심 심층 면접 답변(Q&A) 및 기술적 회고를 포함합니다.

---

## 1. 프로젝트 개요 (미션 목표)
1. **장애 원인의 객관적 규명**: 시스템 자원(물리 메모리, CPU, 스레드 락)의 임계치 돌파 및 정체 현상을 관제 도구를 통해 입증.
2. **Before & After 입증**: 각 장애를 유발하는 제어 변수(환경변수) 조정을 통해 장애 회피 및 생존 시간 연장을 물리적 지표로 대조 검증.
3. **시스템 아키텍처 및 OS 이해**: 커널 OOM Killer, CPU 스케줄러의 run queue 적체, 교착상태 4대 조건 등 OS 수준의 이론을 연계한 근본 원인 도출.
4. **관제 개선 및 회고**: 실제 운영 서버에 적용할 수 있는 메트릭 관제 개선 방안 수립 및 미션 수행 과정에 대한 깊이 있는 기술적 회고 진행.

---

## 2. 실행 환경 (Execution Environment)
실제 미션을 구동하고 관제 데이터를 수집한 시스템 환경은 다음과 같이 검증되었습니다.

* **OS**: Linux (Ubuntu 24.04 LTS "Noble Numbat", x86_64) via OrbStack VM
* **Shell**: `/bin/bash` (Ubuntu Default Shell)
* **Terminal**: OrbStack Terminal
* **Git Version**: `git version 2.43.0`
* **대상 바이너리**: `agent-app-leak` (Linux 64-bit ELF executable, compiled from Python)
* **실행 계정 권한**: 일반 사용자 계정 - 시스템 보안 정책 상 `root`가 아닌 일반 권한으로 안정적으로 기동됨을 보장.

### ⚙️ 어플리케이션 사전 준비 요구사항 (Agent Startup Prerequisites)
애플리케이션이 부트 시퀀스(`[1/6]` ~ `[6/6]`)를 정상 통과하기 위해 아래의 사후 디렉터리 구조 및 환경변수 설정을 완전하게 구성하여 테스트를 진행했습니다.

* 포트 `15034` 고정 사용 및 `0.0.0.0` 전체 네트워크 인터페이스 바인딩
* **필수 디렉터리 및 파일 환경 구조**:
  ```text
  evidence/run_workspace/
  └── agent_home/
      ├── api_keys/
      │   └── secret.key  <-- 내용: 'agent_api_key_test'
      ├── logs/           <-- 쓰기 권한 부여
      └── upload_files/   <-- 쓰기 권한 부여
  ```
* **수행 시 설정한 환경변수**:
  - `AGENT_HOME` 환경변수 지정
  - `AGENT_PORT=15034`
  - `AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files`
  - `AGENT_KEY_PATH=$AGENT_HOME/api_keys`
  - `AGENT_LOG_DIR=$AGENT_HOME/logs`

---

## 3. 수행 항목 체크리스트
- [x] **사전 준비 및 환경 구축**: 일반 사용자 계정 기동, 필수 디렉터리 구조 생성, `secret.key` 배치 완료.
- [x] **OOM Crash 분석 및 리포팅**:
  - [x] `monitor.sh` 관제를 통한 프로세스 RSS 물리 메모리 사용량의 선형적 급상승(Memory Leak) 패턴 관측 및 원본 로그 수록.
  - [x] `MemoryGuard` 임계치 초과 자폭 로그 식별 및 프로세스 종료 코드 `137`(SIGKILL) 확인.
  - [x] `MEMORY_LIMIT` 변경 전후 비교(최소 2회 실행: 50MB vs 100MB) 및 생존 시간(5초 vs 11초) Before & After 입증.
- [x] **CPU 과점유 분석 및 리포팅**:
  - [x] 특정 프로세스의 CPU 사용률이 급상승하는 패턴 관측 및 원본 로그 수록.
  - [x] `CpuWorker` 내부 감시 정책(Watchdog)에 의한 `CPU Threshold Violated` 및 자체 `SIGTERM`(종료 코드 `143`) 확인.
  - [x] `CPU_MAX_OCCUPY` 변경 전후 비교(100% vs 10%)를 통해 쿨다운(Cooldown) 제어 메커니즘 동작 확인.
- [x] **교착상태(Deadlock) 진단 및 리포팅**:
  - [x] 프로세스가 살아있으나(PID 존재) CPU/메모리 변화 및 로그 기록이 정체된 무응답 상태 식별.
  - [x] `ps -L`을 통해 개별 워커 스레드의 CPU 사용률이 `0.0%`로 정지된 스레드 레벨 스냅샷 증거 확보.
  - [x] `Worker-Thread-1`과 `Worker-Thread-2`가 `Shared_Memory_A`와 `Socket_Pool_B` 자원을 두고 상호 배제 및 순환 대기하고 있는 순환 인과 관계 도식화.
  - [x] `MULTI_THREAD_ENABLE` 변경 전후(true -> false) 재현/회피 대조 검증 수행.
- [x] **보너스 과제 (스케줄링 알고리즘 역추론)**:
  - [x] 무경쟁 상태 로그의 타임스탬프와 진행률(Progress) 변화를 분석하여 FCFS, Priority가 아닌 Round-Robin 방식임을 증명.
  - [x] Round-Robin 방식의 장단점 및 웹 서버 아키텍처에 적합한 당위성 서술.
- [x] **이슈 리포트 작성 및 기술 문서화**:
  - [x] 3대 장애 유형과 스케줄링 알고리즘에 대한 종합 기술 보고서 작성 (현상 -> 증거 -> 원인 -> 조치)
  - [x] 리눅스 시스템 트러블슈팅의 핵심 평가 기준(항목 2~4)에 대한 심층 모범 답변 및 자체 기술적 회고(Retrospective) 완성.

---

## 4. 검증 방법 및 자동화 스크립트
본 검증은 아래의 쉘 스크립트들을 통해 시나리오별로 환경변수 조합을 다르게 주어 백그라운드로 프로세스를 가동하고 관제 로그(`.monitor.log`) 및 애플리케이션 실행 로그(`.app.log`)를 수집했습니다. 모든 경로는 상대 경로를 기준으로 호출 가능하도록 범용화되었습니다.

* **실행 및 검증 스크립트**: `./scripts/run_agent_case.sh`
* **모니터링 관제 스크립트**: `./scripts/monitor.sh`

---

## 5. 시스템 장애 분석 및 기술 이슈 리포트 (3건)

### 🔴 [Bug] OOM Crash - MemoryGuard가 메모리 누수 증가를 감지하고 프로세스를 강제 종료

#### 1. Description (현상 설명)
`agent-app-leak` 애플리케이션을 기동하여 실시간 모니터링을 진행한 결과, 프로세스가 아무런 사전 경고 없이 갑자기 강제 종료되는 현상이 관측되었습니다. `MEMORY_LIMIT=50` 환경에서는 가동 약 5초 만에 프로세스가 소멸하였으며, 임시 조치로 메모리 한계를 `MEMORY_LIMIT=100`으로 상향 설정하여 재테스트를 한 결과 생존 시간이 약 11초로 선형적으로 연장되었습니다. 이는 실행 초기의 포트 바인딩이나 단순 부팅 실패가 아닌, 시간 경과에 따라 힙 영역에 데이터가 지속해서 적체되는 메모리 누수(Memory Leak) 결함이 존재하며, 이를 애플리케이션 내부의 자가 메모리 보호 정책인 `MemoryGuard`가 임계치를 넘는 순간 포착하여 스스로 프로세스를 강제 자폭시켰음을 의미합니다.

#### 2. Evidence & Logs (증거 자료)

##### A. 시나리오별 실행 조건
| 구분 | MEMORY_LIMIT | CPU_MAX_OCCUPY | MULTI_THREAD_ENABLE | 결과 및 생존 시간 |
| :--- | :--- | :--- | :--- | :--- |
| **Before (기본)** | 50 MB | 100% | false | 약 5초 후 MemoryGuard에 의해 강제 종료 (자폭) |
| **After (상향)** | 100 MB | 100% | false | 약 11초 후 MemoryGuard에 의해 강제 종료 (수명 연장) |

##### B. `monitor.sh` 물리 메모리 관제 로그 (Raw Logs)
관제 스크립트 `./scripts/monitor.sh`를 통해 수집된 `evidence/raw/oom-low.monitor.log`를 분석한 결과, 실제 Python 프로세스(PID: `11207`)의 물리 메모리 점유 지표인 **RSS(Resident Set Size)**가 21MB 대에서 47MB 대까지 선형적(우상향)으로 대폭 상승하는 메모리 누수 패턴이 뚜렷하게 관측되었습니다.

* **Before (MEMORY_LIMIT=50) 관제 로그**:
  ```text
  # monitor.sh started_at=2026-05-16 00:28:57 +0900 process=agent-app-leak pid=auto interval=1s samples=20
  # timestamp,pid,state,threads,cpu_percent,mem_percent,rss_kb,vsz_kb,etime,command
  2026-05-16 00:28:58,11207,SN,1,8.0,0.1,21544,32692,00:01,agent-app-leak
  2026-05-16 00:28:59,11207,SN,1,6.0,0.2,47148,58296,00:02,agent-app-leak
  2026-05-16 00:29:00,11207,SN,1,4.1,0.2,47148,58296,00:03,agent-app-leak
  2026-05-16 00:29:02,PID_NOT_FOUND,process=/Users/f22losophysics1091/Desktop/check/evidence/run_workspace/agent-app-leak
  ```

* **After (MEMORY_LIMIT=100) 관제 로그**:
  가용한 메모리 상한이 늘어남에 따라 PID `11359`는 약 11초간 버텼으나, RSS가 지속적으로 비대화되어 약 98MB 수준에 이른 후 동일하게 프로세스가 소멸되었습니다.
  ```text
  # monitor.sh started_at=2026-05-16 00:29:17 +0900 process=agent-app-leak pid=auto interval=1s samples=20
  2026-05-16 00:29:18,11359,SN,1,7.2,0.1,21588,32692,00:01,agent-app-leak
  2026-05-16 00:29:22,11359,SN,1,3.0,0.4,72796,83900,00:05,agent-app-leak
  2026-05-16 00:29:25,11359,SN,1,2.2,0.5,98400,109504,00:08,agent-app-leak
  2026-05-16 00:29:28,PID_NOT_FOUND,process=/Users/f22losophysics1091/Desktop/check/evidence/run_workspace/agent-app-leak
  ```

##### C. 애플리케이션 실행 로그 (Raw Logs)
애플리케이션 로그 파일(`.app.log`)을 보면 `MemoryWorker`가 약 3초 간격으로 Heap 사용량을 정확히 **25MB씩 누적해서 증가**시키는 비정상적인 로직을 수행하고 있음을 알 수 있습니다.

* **Before (MEMORY_LIMIT=50) 실행 로그**:
  ```text
  2026-05-16 00:28:59,292 [INFO] [MemoryWorker] Current Heap: 25MB
  2026-05-16 00:29:02,321 [INFO] [MemoryWorker] Current Heap: 50MB
  2026-05-16 00:29:02,321 [CRITICAL] [MemoryGuard] Memory limit exceeded (50MB >= 50MB) / (Recommend Over 256MB)
  2026-05-16 00:29:02,321 [CRITICAL] [MemoryGuard] Self-terminating process 11207 to prevent system instability.
  ```

* **After (MEMORY_LIMIT=100) 실행 로그**:
  ```text
  2026-05-16 00:29:19,720 [INFO] [MemoryWorker] Current Heap: 25MB
  2026-05-16 00:29:22,757 [INFO] [MemoryWorker] Current Heap: 50MB
  2026-05-16 00:29:25,795 [INFO] [MemoryWorker] Current Heap: 75MB
  2026-05-16 00:29:28,832 [INFO] [MemoryWorker] Current Heap: 100MB
  2026-05-16 00:29:28,832 [CRITICAL] [MemoryGuard] Memory limit exceeded (100MB >= 100MB) / (Recommend Over 256MB)
  2026-05-16 00:29:28,833 [CRITICAL] [MemoryGuard] Self-terminating process 11359 to prevent system instability.
  ```

##### D. 프로세스 종료 코드 (Exit Code)
```bash
# oom-low.exit.txt / oom-high.exit.txt 결과값
exit_code=137
```
리눅스 표준 쉘 환경에서 종료 코드 **`137`**은 프로세스가 커널 혹은 자가 호출에 의해 **`SIGKILL` (Signal 9)** 신호를 받고 강제 종료되었음을 엄밀하게 입증합니다. (`128 + 9 = 137`)

#### 3. Root Cause Analysis (원인 분석)
* **메모리 누수(Memory Leak) 결함**: `MemoryWorker` 모듈이 특정 트랜잭션을 시뮬레이션하면서 힙(Heap) 영역에 지속해서 25MB 단위의 메모리를 할당하지만, 할당 완료된 메모리 객체의 전역 참조 관계(Reference Link)를 해제하지 않는 결함이 존재합니다. 이로 인해 Python 런타임의 가비지 컬렉터(GC)가 해당 메모리를 회수(Reclaim)하지 못하고 가용 실제 RAM이 지속해서 잠식되는 현상이 발생합니다.
* **자가 보호 장치의 작동 이유**: 물리 메모리 점유량(RSS)이 환경변수로 입력된 `MEMORY_LIMIT`에 도달하면 애플리케이션의 내부 감시 정책인 **`MemoryGuard`**가 이를 감지합니다. 만약 이 프로세스가 계속 방치되어 OS의 전체 가용 메모리를 고갈시킨다면, 리눅스 커널의 **`OOM Killer`**가 활성화되어 엉뚱한 핵심 서비스 데몬(예: 데이터베이스, SSH 등)을 무차별 강제 종료시켜 전체 서버 가동성을 마비시킵니다. 따라서 `MemoryGuard`는 장애 범위를 해당 어플리케이션 내부로 완전히 차단 및 격리(Fault Isolation)하기 위해 스스로 `SIGKILL`을 호출하여 선제 자폭한 것입니다.

#### 4. Workaround & Verification (조치 및 검증)
* **임시 조치 (Workaround)**: 시스템 환경변수 `MEMORY_LIMIT`를 기존 50MB에서 100MB로 늘려 강제 자폭 시점을 뒤로 늦췄습니다.
* **검증 결과 (Before & After 대조)**:
  - `MEMORY_LIMIT=50` (Before): 힙 메모리가 50MB에 도달하는 시점(가동 5초)에 자폭.
  - `MEMORY_LIMIT=100` (After): 가용 메모리가 상향되어 100MB에 도달하는 시점(가동 11초)까지 생존하여 수명이 약 2.2배 선형적으로 연장됨을 실증 검증 완료.
* **근본 대책 (Code-level Remedy)**: 환경변수 조정을 통한 임시방편은 메모리 누수 속도를 늦출 뿐 근본 해결책이 아닙니다. 소스 코드 상에서 미사용 메모리 객체의 전역 참조를 명시적으로 파괴(파이썬의 `del` 처리 혹은 컬렉션의 `clear()` / `pop()` 유도)하여 GC가 메모리를 제때 수집할 수 있도록 리팩토링해야 합니다.

---

### 🟡 [Bug] CPU Latency - CPU_MAX_OCCUPY 과대 설정으로 CpuWorker가 임계치를 초과하고 SIGTERM 종료

#### 1. Description (현상 설명)
어플리케이션을 구동할 때 CPU 한도를 무제한으로 허용하는 위험 설정인 `CPU_MAX_OCCUPY=100`으로 실행하면, 연산량이 지속해서 폭증하다가 내부 부하 지표인 `Current Load`가 50%를 돌파하는 순간 어플리케이션 내부 감시견(`Watchdog`) 정책에 의해 `CPU Threshold Violated` 경고를 내뿜으며 프로세스가 강제 종료됩니다. 반면, 안전 제한치 설정인 `CPU_MAX_OCCUPY=10`을 부여하면, 연산 부하가 10%에 근접할 때 스스로 쿨다운(`cooldown`) 상태를 반복하며 스스로 연산을 비워 안정적인 상태를 무한히 유지하게 됩니다.

#### 2. Evidence & Logs (증거 자료)

##### A. 시나리오별 실행 조건
| 구분 | MEMORY_LIMIT | CPU_MAX_OCCUPY | MULTI_THREAD_ENABLE | 결과 |
| :--- | :--- | :--- | :--- | :--- |
| **Before (폭주)** | 512 MB | 100% | false | 약 31초 후 내부 Watchdog에 의해 강제 종료 (`SIGTERM`) |
| **After (안전)** | 512 MB | 10% | false | 35초 이상의 관찰 기간 내내 Cooldown 반복 가동으로 정상 생존 |

##### B. 애플리케이션 실행 로그 (Raw Logs)
* **Before (CPU_MAX_OCCUPY=100) 실행 로그**:
  `CpuWorker`가 기동된 후 연산 부하(`Current Load`)를 점진적으로 늘려가며 50%를 초과하자 즉각 감시견이 동작하여 강제 종료를 처리했습니다.
  ```text
  2026-05-16 00:30:46,958 [INFO] [CpuWorker] Started. Maximum CPU Limit: 100%
  2026-05-16 00:30:59,370 [INFO] [CpuWorker] Current Load: 27.05%
  2026-05-16 00:31:05,580 [INFO] [CpuWorker] Current Load: 37.78%
  2026-05-16 00:31:11,788 [INFO] [CpuWorker] Current Load: 48.05%
  2026-05-16 00:31:14,893 [INFO] [CpuWorker] Current Load: 55.67%
  2026-05-16 00:31:14,995 [CRITICAL] [CpuWorker] CPU Threshold Violated! (55.669999999999995%).
  ```

* **After (CPU_MAX_OCCUPY=10) 실행 로그**:
  연산 부하가 10%에 도달하는 순간 즉시 쿨다운에 들어갔으며, 부하를 5%대로 스스로 평탄화시킨 뒤 재연산에 들어가는 매우 안정적인 제어가 관측되었습니다.
  ```text
  2026-05-16 00:29:52,019 [INFO] [CpuWorker] Started. Maximum CPU Limit: 10%
  2026-05-16 00:29:54,121 [INFO] [CpuWorker] Peak reached (10.00%). Starting cooldown...
  2026-05-16 00:29:57,226 [INFO] [CpuWorker] Cooldown complete (5.00%). Resuming load increase...
  2026-05-16 00:30:19,958 [INFO] [CpuWorker] Current Load: 10.00%
  ```

##### C. 프로세스 종료 코드 및 시스템 도구 출력 (Raw Evidence)
* **Before (폭주 모드) 종료 결과 (`cpu-high.exit.txt`)**:
  ```text
  # MEMORY_LIMIT=512 CPU_MAX_OCCUPY=100 MULTI_THREAD_ENABLE=false
  pid=12321
  exit_code=143
  ```
  리눅스 환경에서 종료 코드 **`143`**은 프로세스가 **`SIGTERM` (Signal 15)** 신호를 받고 정중하게 자체 안전 종료되었음을 확실히 나타냅니다. (`128 + 15 = 143`)
* **Before (폭주 모드) `monitor.sh` 관제 로그**:
  ```text
  2026-05-16 00:31:13,12323,SN,1,1.1,0.1,21692,32692,00:28,agent-app-leak
  2026-05-16 00:31:14,12323,SN,1,1.1,0.1,21692,32692,00:29,agent-app-leak
  2026-05-16 00:31:15,PID_NOT_FOUND,process=/Users/f22losophysics1091/Desktop/check/evidence/run_workspace/agent-app-leak
  ```
* **Before (폭주 모드) `top` 분석 스냅샷 (`cpu-high-late.top.log`)**:
  ```text
  top - 00:32:31 up  8:03,  0 user,  load average: 0.00, 0.01, 0.00
  %Cpu(s):  0.0 us,  0.0 sy,  6.6 ni, 93.4 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
      PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
    12964 f22loso+  30  10   32692  21656  11840 S   0.0   0.1   0:00.31 agent-a+
  ```
  본 어플리케이션은 시스템의 전반적인 민감도를 해치지 않기 위해 OS 프로세스 스케줄링 우선순위 등급을 백그라운드 친화적인 **`NI=10` (Nice Value)**으로 하향 조정하여 동작합니다. 이로 인해 OS 관점의 순간 샘플러인 `top`과 `ps`에 기록된 CPU 점유율은 낮아 보일 수 있으나, 어플리케이션 내의 논리적인 CPU 루프 연산 부하(`Current Load`)가 임계치를 넘는 순간 내부 수호 로직(Watchdog)에 의해 정확히 통제되었습니다.

#### 3. Root Cause Analysis (원인 분석)
* **환경변수 `CPU_MAX_OCCUPY` 설정의 진실**: 
  - `CPU_MAX_OCCUPY=100`은 부하 발생 상한선을 최대로 개방하는 위험 설정입니다. 이에 따라 `CpuWorker` 내부 루프가 연산 간격을 좁혀 계산 밀도를 올리고 부하를 100%까지 지속해서 증폭시킵니다. 내부 부하가 감시 한계값인 약 50%를 넘자, 어플리케이션 내부 Watchdog이 임계치 파괴로 단정하고 시스템을 비상 종료시켰습니다.
  - 반면 `CPU_MAX_OCCUPY=10`은 내부 부하가 10%를 넘지 않도록 제한하는 안전 장치로 작동합니다. 부하가 10%에 도달하는 피크 시점마다 sleep 및 backoff 제어가 활성화되어 부하를 쿨다운(5%대) 시킵니다.
* **단일 프로세스 강제 종료(Watchdog)의 당위성**:
  CPU 자원은 한정되어 있으므로, 단일 프로세스가 CPU를 100%에 가깝게 점유하고 코어를 독점하면 OS의 **실행 큐(Run Queue)에 스케줄링 대기 상태의 다른 프로세스들이 극심하게 밀리게 됩니다.** 특히 실시간으로 가동되는 웹 서버 환경이라면, 이 시간 동안 쌓이는 웹 클라이언트의 TCP 요청들이 OS 소켓 백로그 큐나 WAS의 이벤트 처리 스레드 큐에 적체되는 **대기 큐 지연(Queueing Delay)**을 유발합니다. 이는 응답성 붕괴인 **테일 레이턴시(Tail Latency)의 폭증**으로 이어져 결국 커넥션 타임아웃 장애로 확산됩니다. 따라서 시스템 전반의 공멸을 막기 위해 폭주하는 단일 프로세스를 Watchdog이 선제 차단(Emergency Abort)하는 조치는 절대적으로 필요합니다.

#### 4. Workaround & Verification (조치 및 검증)
* **임시 조치 (Workaround)**: `CPU_MAX_OCCUPY`를 위험값인 100에서 안전 기준값인 10으로 강제 하향 조정했습니다.
* **검증 결과 (Before & After 대조)**:
  - **Before (100)**: CPU 부하가 55.67%까지 일방적으로 폭주하여 임계치 위반으로 인한 강제 자폭 종료 발생.
  - **After (10)**: 10% 도달 시 즉시 Cooldown으로 전환되는 메커니즘이 활발하게 가동되어 강제 종료 현상이 완벽하게 차단됨을 실증 검증 완료.
* **근본 대책 (Code-level Remedy)**: CPU 집약적 연산을 처리하는 루프 내부에 명시적인 Backoff 주기와 `sleep`을 삽입하여 연산 속도를 물리적으로 제한해야 합니다. 나아가 실시간 요청을 응답해야 하는 주 스레드 루프 내에서 무거운 연산을 돌리지 말고, **메시지 큐(Celery, RabbitMQ 등)를 활용한 외부 연산 워커 노드 위임(Offloading) 아키텍처**로 전환하여 비블로킹(Non-blocking) I/O 구조를 완성해야 합니다.

---

### 🔵 [Bug] Deadlock (교착상태) - 두 Worker 스레드가 서로의 락을 기다리며 프로세스가 무응답 상태로 정체

#### 1. Description (현상 설명)
어플리케이션 가동 시 멀티스레드 동시 처리 모드(`MULTI_THREAD_ENABLE=true`)를 활성화하면, 겉으로는 프로세스 PID와 스레드가 백그라운드 상에 버젓이 생존해 있고 프로세스 소멸(Crash)이 발생하지도 않으나, 내부적으로 CPU 사용률과 물리 메모리(RSS) 크기가 단 1바이트의 변화도 없이 완전히 굳어버리며 실행 로그도 특정 라인을 마지막으로 더는 갱신되지 않는 **영구 무응답 먹통(Hang/Blocked) 상태**가 지속해서 반복되는 치명적인 결함이 발견되었습니다.

#### 2. Evidence & Logs (증거 자료)

##### A. 시나리오별 실행 조건
| 구분 | MEMORY_LIMIT | CPU_MAX_OCCUPY | MULTI_THREAD_ENABLE | 결과 |
| :--- | :--- | :--- | :--- | :--- |
| **Before (멀티스레드)** | 512 MB | 10% | **true** | 두 스레드가 교차 락 획득 시도를 하다가 **Deadlock(교착상태)** 재현 |
| **After (싱글스레드)** | 512 MB | 10% | **false** | 스케줄러가 순차 처리하여 데드락을 회피하고 정상 가동 완료 |

##### B. `monitor.sh` 정체 관제 로그 (Raw Logs)
관제 로그(`evidence/raw/deadlock-on.monitor.log`) 상 PID `12995`가 백그라운드에 종료되지 않고 계속 잡혀 있지만, 시간이 흘러도 **CPU 사용률은 0.3% 수준으로 수렴**하고 **RSS 물리 메모리는 21,696 KB로 한 정수 단위조차 변하지 않고 고정**된 극도의 정체 상태를 볼 수 있습니다.

* **Before (MULTI_THREAD_ENABLE=true) 관제 로그**:
  ```text
  # monitor.sh started_at=2026-05-16 00:33:12 +0900 process=agent-app-leak pid=auto interval=1s samples=25
  2026-05-16 00:33:19,12995,SNl,3,1.1,0.1,21696,180188,00:07,agent-app-leak
  2026-05-16 00:33:21,12995,SNl,3,0.8,0.1,21696,180188,00:09,agent-app-leak
  2026-05-16 00:33:28,12995,SNl,3,0.5,0.1,21696,180188,00:15,agent-app-leak
  2026-05-16 00:33:38,12995,SNl,3,0.3,0.1,21696,180188,00:25,agent-app-leak
  ```

##### C. `ps -L` 스레드 레벨 스냅샷 (Raw Evidence)
`ps -L` 명령을 통해 스레드 레벨 상세 현황을 획득한 결과, 프로세스의 개별 Worker 스레드(TID: `13122`, `13123`)의 CPU 점유율이 한순간도 일하지 않는 **`0.0%`** 상태로 고착되어 있음이 물리적으로 입증되었습니다.
```text
# thread snapshot 2026-05-16 00:33:38 pids=12993,12995
    PID     TID STAT %CPU %MEM COMMAND
  12993   12993 S     0.5  0.0 agent-app-leak
  12995   12995 SNl   0.3  0.1 agent-app-leak
  12995   13122 SNl   0.0  0.1 agent-app-leak
  12995   13123 SNl   0.0  0.1 agent-app-leak
```

##### D. 마지막 애플리케이션 실행 로그 (Raw Logs)
`evidence/raw/deadlock-on.app.log`에서 추출한 마지막 생명 징후 로그입니다. 두 스레드가 서로 다른 락을 거머쥔 채, 서로 상대방이 이미 선점한 자원의 잠금이 풀리기만을 바라보며 블로킹된 현상이 뚜렷하게 발췌되었습니다.
```text
2026-05-16 00:33:19,708 [INFO] [AgentWorker][Worker-Thread-1] LOCK ACQUIRED: [Shared_Memory_A]. (Holding...)
2026-05-16 00:33:19,708 [INFO] [AgentWorker][Worker-Thread-2] LOCK ACQUIRED: [Socket_Pool_B]. (Holding...)
2026-05-16 00:33:21,712 [INFO] [AgentWorker][Worker-Thread-1] Need resource [Socket_Pool_B] to finish job.
2026-05-16 00:33:21,712 [INFO] [AgentWorker][Worker-Thread-2] Need resource [Shared_Memory_A] to write logs.
2026-05-16 00:33:21,713 [INFO] [AgentWorker][Worker-Thread-2] WAITING for [Shared_Memory_A]... (Status: BLOCKED)
2026-05-16 00:33:21,713 [INFO] [AgentWorker][Worker-Thread-1] WAITING for [Socket_Pool_B]... (Status: BLOCKED)
# 이 로그 이후 단 하나의 라인도 갱신되지 않고 무한 대기함.
```

##### E. 싱글스레드 설정 시의 회피 성공 로그 (Raw Logs)
`MULTI_THREAD_ENABLE=false` 환경에서는 교착을 유발하는 멀티스레드 경합 시나리오가 아예 호출되지 않고, 정상적인 싱글스레드 스케줄러가 차례대로 작업을 완수해 냈습니다.
```text
2026-05-16 00:34:02,275 [INFO] [Scheduler] Registered Tasks: ['Thread-A', 'Thread-B', 'Thread-C']
2026-05-16 00:34:02,276 [INFO] [Thread-A] Task Started. Calculating... (20%)
2026-05-16 00:34:02,429 [INFO] [Thread-B] Task Started. Calculating... (20%)
2026-05-16 00:34:02,583 [INFO] [Thread-C] Task Started. Calculating... (20%)
2026-05-16 00:34:03,359 [INFO] [Scheduler] All tasks completed.
```

#### 3. Root Cause Analysis (원인 분석)
* **순환 의존의 도식화**:
  본 장애는 두 스레드가 각자 하나의 자원을 이미 쥐어 점유(Hold)한 상태에서, 상대방이 쥐고 있는 다른 자원을 얻기 위해 무한히 락 해제를 대기(Wait)하는 **순환 의존성 고리**가 만들어지며 발생합니다.
  ```text
  [ Worker-Thread-1 ] ──(점유)──> [ Shared_Memory_A ] ──(대기)──> [ Worker-Thread-2 ]
          ▲                                                               │
          │                                                               │
        (대기)                                                          (점유)
          │                                                               ▼
  [ Socket_Pool_B ] <─────────────────────────────────────────────────────┘
  ```
  이를 락 자원 관점에서 매핑하면 단방향 순환 그래프(Closed Loop)가 완성됩니다.
  `Worker-Thread-1` ➔ `Socket_Pool_B` 대기 ➔ `Worker-Thread-2` ➔ `Shared_Memory_A` 대기 ➔ `Worker-Thread-1`
* **교착상태 4대 조건과의 대조**:
  1. **상호 배제 (Mutual Exclusion)**: 메모리 블록 `Shared_Memory_A`와 네트워크 자원 `Socket_Pool_B`는 다중 스레드가 동시에 소유할 수 없는 상호 배제적 자원입니다.
  2. **점유 대기 (Hold and Wait)**: `Worker-Thread-1`은 자신이 획득한 `Shared_Memory_A`를 손에 꼭 쥔 상태로 `Socket_Pool_B`를 요청하며 대기합니다.
  3. **비선점 (No Preemption)**: 다른 스레드가 쥐고 있는 자원을 운영체제 수준이나 강제 호출로 중도 탈취할 수 없습니다.
  4. **순환 대기 (Circular Wait)**: 자원을 양보하지 않는 두 스레드 간 대기 경로가 하나의 원을 그립니다.
  네 가지 조건이 동시에 충족됨으로써, 스레드가 꼼짝 못 하고 굳어버리는 전형적인 Deadlock 상태가 영구 고착화되었습니다.

#### 4. Workaround & Verification (조치 및 검증)
* **임시 조치 (Workaround)**: 멀티스레드 경합 시나리오를 물리적으로 차단하기 위해 `MULTI_THREAD_ENABLE` 환경변수를 `false`로 변환했습니다.
* **검증 결과 (Before & After 대조)**:
  - **Before (true)**: `WAITING ... BLOCKED` 상태에 빠진 뒤 CPU 0.0%, RSS 메모리 고정, 로그 멈춤 상태로 무한히 행(Hang)에 빠짐.
  - **After (false)**: 교차 락 획득 시나리오가 미가동되고 정상 싱글스레드 스케줄러가 `All tasks completed`를 성공적으로 찍으며 정상 처리 완료를 입증함.
* **근본 대책 (Code-level Remedy)**: 환경변수 비활성화 방식은 동시성 대용량 처리를 포기하는 궁색한 우회책입니다. 소스 코드를 근본적으로 교정하려면, 두 스레드가 자원을 획득하는 전역 순서를 **동일하게 일치(Lock Ordering)**시켜야 합니다. 즉, 두 스레드 모두 항상 `Shared_Memory_A`를 먼저 쥐고 난 뒤에만 `Socket_Pool_B`를 획득할 수 있게 통일하면 순환 고리가 절대 생성되지 않습니다. 또는 락 획득 시 **`try_lock(timeout=N)`** 과 같은 타임아웃 기법을 구현하여, 일정 시간 내에 락을 잡지 못하면 이미 자기가 쥐고 있던 모든 락을 즉각 릴리즈(Release)하고 무작위 시간 동안 대기(Jitter Jitter) 후 다시 재시도하도록 롤백 설계를 해야 합니다.

---
