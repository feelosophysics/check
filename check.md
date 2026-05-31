

## 🌟 1. 이 프로젝트의 탁월한 부분 (Best Practices)

* **자체 CPU 차분 계산 및 MemAvailable 활용**
  * `top`이나 `free` 같은 외부 명령어의 가변적 포맷에 의존하지 않고, `/proc/stat`의 idle 타임을 1초 간격으로 직접 차분 계산하여 CPU를 측정했으며, 리눅스 커널이 보장하는 실질 가용 메모리 지표인 `MemAvailable`을 파싱한 것은 운영체제(OS)에 대한 깊은 이해를 보여줍니다.

---

## ⚠️ 2. 핵심 보안 취약점 및 오작동 위험 요소 (Critical Issues)
이 프로젝트의 핵심은 **서버 보안**과 **정확한 장애 모니터링**입니다. 그러나 실제 프로덕션 환경 관점에서 피평가자의 구현 방식에는 몇 가지 **치명적인 맹점(Vulnerability & Bug)**이 존재합니다. 

### ① 프로세스 위장 및 오진 취약점 (Process Masquerading)
* **현상**: `monitor.sh` 내부 프로세스 체크 로직:
  ```bash
  pid=$(pgrep -f "${APP_NAME}" | head -n1 || true)
  ```
* **문제점**: `pgrep -f`는 프로세스의 이름뿐만 아니라 **전체 명령행 아규먼트(Command Line)**까지 검사합니다. 만약 다른 일반 사용자(예: 보안 수준이 낮은 `agent-test` 계정)나 악의적인 해커가 단순히 `cat agent_app`, `vi agent_app` 혹은 `python3 -m agent_app` 같은 텍스트나 프로세스를 실행해 두면, 관제 스크립트는 이를 정상적인 백엔드 서비스로 인지하고 `[OK]` 판정을 내립니다.
* **해결 방안**: 실행 소유자 필터를 반드시 걸거나 exact match를 지향해야 합니다.
  ```bash
  # agent-admin 사용자가 실행한 정확한 프로세스만 추적
  pid=$(pgrep -u agent-admin -x "agent_app" | head -n1 || true)
  ```

### ② 방화벽(UFW) 모니터링의 심각한 탐지 우회 오류 (False Positive Firewall Status)
* **현상**: `monitor.sh` 내부 UFW 감시 로직:
  ```bash
  if ! systemctl is-active --quiet ufw; then ...
  ```
* **문제점**: Ubuntu 환경에서 `ufw.service`는 **`oneshot`** 형태의 systemd 서비스입니다. 이는 부팅 시점에 UFW 방화벽 규칙을 커널(netfilter)에 올린 뒤 프로세스 자체는 바로 종료(Exited)됩니다.
  만약 관리자가 실수나 악의적 목적으로 `sudo ufw disable` 명령을 통해 방화벽을 꺼버려도, systemd 유닛 상태는 여전히 `active (exited)`로 남아있습니다. 즉, **방화벽이 완전히 해제되어 외부 포트가 전부 노출된 상황에서도 관제 스크립트는 `[WARNING] UFW is not active` 경고를 뿜지 못하고 통과**합니다.
* **해결 방안**: 실제 UFW 런타임 룰 엔진 상태를 확인해야 합니다.
  ```bash
  # ufw status 결과를 통해 실제 활성화 상태 파악 (단, 일반 권한 실행 시 sudo 처리 필요)
  if ufw status | grep -q "Status: inactive"; then
      echo "[WARNING] UFW is disabled"
  fi
  ```

### ③ Modular SSH 설정 충돌에 따른 루트 접속 허용 위험 (Modular SSH Conflict)
* **현상**: `docs/IMPLEMENTATION_GUIDE.md`에서 `/etc/ssh/sshd_config` 파일만 직접 수정하여 `PermitRootLogin no`를 적용했습니다.
* **문제점**: Ubuntu 22.04 LTS를 포함한 최신 리눅스 배포판은 `/etc/ssh/sshd_config` 상단에 `Include /etc/ssh/sshd_config.d/*.conf`가 활성화되어 있습니다. 클라우드 이미지(AWS, Azure 등)의 경우 기본 포트나 루트 로그인 권한 설정을 `/etc/ssh/sshd_config.d/50-cloud-init.conf` 등 모듈형 설정 파일에 우선 정의해 두는 경우가 많습니다.
  이 경우, 메인 설정 파일을 수정하더라도 **하위 `.d/` 설정이 우선 적용되어 Root 원격 접속 제한 규칙이 무력화**될 위험이 있습니다.
* **해결 방안**: `sshd_config.d/` 디렉토리 내부의 설정 파일들까지 일관되게 덮어쓰거나 불필요한 modular 설정을 차단하는 지침을 가이드라인에 보완해야 합니다.

---

## 🛠️ 3. 운영 효율성 및 스크립트 안정성 개선점 (Improvements)

### ① 로그 파일 보관 개수 제한 요구사항 오차 (Off-by-One Error)
* **현상**: 미션 요구사항은 **"최대 10MB / 10개 파일 유지"**입니다.
* **문제점**: `rotate_log()` 함수는 `monitor.log` (현재 활성화된 파일) 외에 `monitor.log.1`부터 `monitor.log.10`까지 백업 파일을 순회(Shift)하도록 구성되어 있습니다. 결과적으로 디렉토리에 **총 11개**의 로그 파일이 상존하게 됩니다.
* **해결 방안**: 요구사항을 엄격하게 만족하기 위해서는 `LOG_MAX_FILES` 값을 `9`로 선언하거나, 총합 개수가 10개가 되도록 파라미터를 수정해야 합니다.

### ② 로그 디렉토리 권한 및 존재 사전 검증 부재 (Defensive Coding)
* **현상**: `monitor.sh`는 실행 극초기에 로그 쓰기 목적지(`/var/log/agent-app/`)가 유효한지, 실행 주체에게 실질적인 쓰기 권한(`-w`)이 있는지 점검하지 않습니다.
* **문제점**: 모종의 이유로 디렉토리가 지워지거나 권한이 손실된 상태에서 cron이 작동하면, 스크립트는 쉘 에러 메시지를 다수 출력하고 비정상 상태로 매분 돌게 됩니다.
* **해결 방안**: `main` 도입부에 사전 환경 디렉토리 체크 로직을 추가하는 방어적 코딩 기법이 권장됩니다.
  ```bash
  if [[ ! -w "${AGENT_LOG_DIR}" ]]; then
      echo "Error: Log directory is not writable. Exiting." >&2
      exit 1
  fi
  ```

### ③ `set -u`와 `/proc` 파싱 구문 분석 에러 위험
* **현상**: 스크립트 상단에 `set -u`(정의되지 않은 변수 참조 시 즉시 종료)를 설정하여 높은 코드 안정성을 지향했습니다.
* **문제점**: 그러나 만약 스크립트가 리소스 수집 과정에서 예외적인 리눅스 커널 환경(Docker 컨테이너 내부나 `/proc` 마운트가 제한된 샌드박스 등)에서 동작하여 `/proc/stat` 또는 `/proc/meminfo` 필드가 정상 파싱되지 않으면, `cpu`, `mem`, `disk` 변수가 정의는 되었으나 비어 있는(Null/Empty) 상태가 될 수 있습니다.
  이후 `(( disk > DISK_THRESHOLD ))`와 같은 Bash 산술 표현식을 거칠 때, 빈 값에 대한 연산 에러(`syntax error in expression`)가 발생하여 관제 스크립트 전체가 붕괴됩니다.
* **해결 방안**: 수집된 변수가 실제 '숫자 포맷'인지 정규식 검증 과정을 추가해야 합니다.
  ```bash
  if [[ ! "${disk}" =~ ^[0-9]+$ ]]; then
      disk=0 # 안전한 기본값 대입 또는 경고 출력 후 무시
  fi
  ```
