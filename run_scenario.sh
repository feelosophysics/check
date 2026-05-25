#!/usr/bin/env bash

# ==============================================================================
# [run_scenario.sh] 장애 재현 및 환경변수 조정을 위한 대화식 시나리오 제어 컨트롤러
# ==============================================================================
# 이 스크립트는 3가지 필수 장애 시나리오(OOM, CPU Spike, Deadlock)의 환경변수를 조정하고,
# 대상 바이너리(agent-app-leak)와 관제 도구(monitor.sh)를 정밀하게 시작/중단/청소해 줍니다.
# 
# 사용자가 메뉴 입력 한 번으로 모든 트러블슈팅을 손쉽게 수행할 수 있도록 돕습니다.
# 초심자가 쉘의 입출력 제어, 백그라운드 프로세스 관리(nohup, &), 시그널 제어(kill)를
# 막힘없이 학습할 수 있도록 "매우 상세한 한글 해설 주석"을 매 줄마다 채웠습니다.
# ==============================================================================

# 1. 공통 환경 변수 및 설정 정의
# ------------------------------------------------------------------------------
DEFAULT_HOME="/Users/f22losophysics1091/Desktop/260525work/agent_home"
export AGENT_HOME="${AGENT_HOME:-$DEFAULT_HOME}"
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
export AGENT_KEY_PATH="$AGENT_HOME/api_keys"
export AGENT_LOG_DIR="$AGENT_HOME/logs"

# 앱 실행 바이너리의 로컬 경로 지정
# 현재 디렉토리에 있는 'agent-app-leak' 실행 파일을 타겟팅합니다.
APP_BIN="./agent-app-leak"

# 2. 실행 권한 및 초기 환경 검증
# ------------------------------------------------------------------------------
# -x 검사는 '해당 파일이 존재하고 실행 권한이 부여되었는지' 확인하는 구문입니다.
if [ ! -x "$APP_BIN" ]; then
    echo "[안내] $APP_BIN 바이너리에 실행 권한이 부여되지 않았습니다. 권한을 부여합니다 (chmod +x)."
    # chmod +x 명령어는 해당 파일에 '실행 가능(Executable)' 플래그를 추가로 부여합니다.
    chmod +x "$APP_BIN"
fi

# 실시간 모니터링 스크립트 실행 권한 확인
if [ -f "./monitor.sh" ] && [ ! -x "./monitor.sh" ]; then
    chmod +x "./monitor.sh"
fi

# setup_env.sh를 활용해 기초 폴더 구성과 secret.key 검증을 선제적으로 완수합니다.
# 'source' 또는 '.' 명령어는 서브 쉘이 아닌 '현재 쉘 환경'에서 해당 스크립트를 직접 실행(Include)합니다.
if [ -f "./setup_env.sh" ]; then
    source ./setup_env.sh
else
    echo "[경고] setup_env.sh가 존재하지 않아 기본 구성 요소를 자동 생성합니다."
    mkdir -p "$AGENT_UPLOAD_DIR" "$AGENT_KEY_PATH" "$AGENT_LOG_DIR"
    echo -n "agent_api_key_test" > "$AGENT_KEY_PATH/secret.key"
fi

# 3. 헬퍼 기능: 실행 중인 프로세스 안전 청소 (Cleanup)
# ------------------------------------------------------------------------------
# 새로운 장애 실험을 시작하기 전, 기존에 백그라운드에서 실행되고 있던 앱과 모니터링 툴을
# 완전히 깨끗하게 종료(Kill)시켜 리소스를 확보하고 로그 중복 오염을 방지하는 핵심 서브루틴입니다.
cleanup_processes() {
    echo "----------------------------------------------------------------------"
    echo "🧹 [프로세스 초기화] 잔존 프로세스(앱 및 관제 툴)가 있는지 조회하고 종료합니다."
    
    # 3.1 monitor.sh 백그라운드 종료
    # - pgrep -f를 사용해 monitor.sh의 PID들을 가져옵니다.
    MON_PIDS=$(pgrep -f "monitor.sh")
    if [ -n "$MON_PIDS" ]; then
        # kill 명령어는 실행 중인 프로세스에 시그널(Signal)을 보냅니다. 기본값은 안전한 종료를 의미하는 SIGTERM(15)입니다.
        # 여러 PID가 줄바꿈으로 넘어올 수 있으므로 echo로 일렬 배치하여 kill에 주입합니다.
        kill $MON_PIDS 2>/dev/null
        echo "✔ 백그라운드 관제 스크립트(monitor.sh)를 성공적으로 종료했습니다."
    fi

    # 3.2 agent-app-leak 백그라운드 종료
    APP_PIDS=$(pgrep -f "agent-app-leak")
    if [ -n "$APP_PIDS" ]; then
        # 교착상태(Deadlock)에 빠진 스레드는 일반 SIGTERM(15) 시그널에 무응답할 수 있으므로,
        # 확실한 자원 해제를 위해 강제 종료 시그널인 SIGKILL(-9)을 동시 주입합니다.
        kill -9 $APP_PIDS 2>/dev/null
        echo "✔ 백그라운드 애플리케이션(agent-app-leak)을 강제 종료 처리했습니다."
    fi
    echo "----------------------------------------------------------------------"
}

# 4. 헬퍼 기능: 시나리오 기동기 (Launcher)
# ------------------------------------------------------------------------------
# 설정된 환경변수 세트를 터미널에 공지한 뒤, 
# 관제 도구(monitor.sh)와 앱(agent-app-leak)을 백그라운드로 기동(nohup ... &)합니다.
launch_scenario() {
    # 4.1 기존 프로세스 완벽 클리닝
    cleanup_processes

    echo "======================================================================"
    echo "🚀 [시나리오 기동] 프로세스를 백그라운드 모드로 가동합니다."
    echo "   - MEMORY_LIMIT        : $MEMORY_LIMIT MB"
    echo "   - CPU_MAX_OCCUPY      : $CPU_MAX_OCCUPY %"
    echo "   - MULTI_THREAD_ENABLE : $MULTI_THREAD_ENABLE"
    echo "======================================================================"

    # 4.2 환경변수를 현재 쉘 환경에 확실히 등록(export)합니다.
    export MEMORY_LIMIT
    export CPU_MAX_OCCUPY
    export MULTI_THREAD_ENABLE

    # 4.3 백그라운드 로그 파일 초기화
    # - '>' 기호를 통해 기존 로그 파일 내용을 완전히 깨끗이 비워 비행 데이터가 꼬이지 않게 만듭니다.
    > "$AGENT_LOG_DIR/app.log"
    > "$AGENT_LOG_DIR/monitor.log"

    # 4.4 관제 스크립트(monitor.sh) 백그라운드 실행
    # - nohup 명령어는 터미널이 닫히거나 연결이 끊어져도 백그라운드 프로세스가 계속 생존(No Hang Up)하도록 방어합니다.
    # - '> /dev/null 2>&1' 구문은 표준 출력(1)과 에러 출력(2)을 화면에 띄우지 않고 쓰레기통(/dev/null)으로 조용히 리다이렉트합니다.
    # - 맨 끝의 '&' 기호는 명령어를 포그라운드가 아닌 '백그라운드'로 즉시 밀어넣어 프롬프트 제어권을 보존합니다.
    nohup ./monitor.sh > /dev/null 2>&1 &

    # 4.5 애플리케이션(agent-app-leak) 백그라운드 실행
    # - 앱 실행 표준 출력 및 표준 에러를 '$AGENT_LOG_DIR/app.log'로 몰아서 로깅하도록 매핑해 둡니다.
    # - 맨 끝의 '&'를 통해 백그라운드 실행을 확보합니다.
    nohup "$APP_BIN" > "$AGENT_LOG_DIR/app.log" 2>&1 &

    # 백그라운드로 밀려난 프로세스들의 PID를 다시 확인해 공지합니다.
    sleep 0.5
    NEW_APP_PID=$(pgrep -f "agent-app-leak" | head -n 1)
    NEW_MON_PID=$(pgrep -f "monitor.sh" | head -n 1)

    echo "✔ 기동 성공!"
    echo "  - 애플리케이션 PID   : $NEW_APP_PID"
    echo "  - 관제 스크립트 PID  : $NEW_MON_PID"
    echo "----------------------------------------------------------------------"
    echo "💡 [팁] 실시간 데이터 스트리밍 모니터링을 하려면 터미널을 열고 아래 명령을 구동해 주세요:"
    echo "   - 앱 로그 보기     : tail -f $AGENT_LOG_DIR/app.log"
    echo "   - 실시간 관제 보기 : tail -f $AGENT_LOG_DIR/monitor.log"
    echo "======================================================================"
}

# 5. 인터랙티브 대화형 메뉴 루프
# ------------------------------------------------------------------------------
# 사용자가 스크립트를 끄지 않고 연속적인 테스트를 매끄럽게 할 수 있도록 대화식 루프를 설계합니다.
while true; do
    echo ""
    echo "======================================================================"
    echo "   🚨 리눅스 리소스 장애 분석 및 트러블슈팅 컨트롤러 (Interactive CLI)"
    echo "======================================================================"
    echo " [1] OOM Crash 재현 (Before: MEMORY_LIMIT=50MB)"
    echo " [2] OOM Crash 조치 & 검증 (After: MEMORY_LIMIT=256MB)"
    echo "----------------------------------------------------------------------"
    echo " [3] CPU Spike & Watchdog 재현 (Before: CPU_MAX_OCCUPY=15%)"
    echo " [4] CPU Spike 조치 & 검증 (After: CPU_MAX_OCCUPY=90%)"
    echo "----------------------------------------------------------------------"
    echo " [5] Deadlock 재현 (Before: MULTI_THREAD_ENABLE=true)"
    echo " [6] Deadlock 회피 & 검증 (After: MULTI_THREAD_ENABLE=false)"
    echo "----------------------------------------------------------------------"
    echo " [7] 현재 실행 중인 모든 백그라운드 프로세스 강제 종료 및 청소"
    echo " [8] 컨트롤러 종료"
    echo "======================================================================"
    # read -p 명령어는 사용자로부터 입력을 한 줄(String) 받아 지정한 변수(CHOICE)에 할당합니다.
    read -p "▶ 실행할 시나리오 번호를 입력하세요 (1-8): " CHOICE

    case "$CHOICE" in
        1)
            # OOM Crash 재현 (제약: MEMORY_LIMIT 50~512)
            # - 메모리를 50MB로 대폭 억제하고 스레드를 꺼서 순수 메모리 릭 증가를 선명히 유도합니다.
            MEMORY_LIMIT=50
            CPU_MAX_OCCUPY=100
            MULTI_THREAD_ENABLE="false"
            launch_scenario
            ;;
        2)
            # OOM Crash 조치 (MEMORY_LIMIT 256MB로 상향)
            # - 가용 메모리 확장을 통해 동일 시간 대비 생존 시간 증대 및 Before & After 추이를 비교합니다.
            MEMORY_LIMIT=256
            CPU_MAX_OCCUPY=100
            MULTI_THREAD_ENABLE="false"
            launch_scenario
            ;;
        3)
            # CPU Spike 재현 (CPU 임계치를 15%로 억제)
            # - 과점유 방지용 내장 Watchdog 정책을 동작시켜 SIGTERM으로 강제 사멸을 유도합니다.
            MEMORY_LIMIT=512
            CPU_MAX_OCCUPY=15
            MULTI_THREAD_ENABLE="false"
            launch_scenario
            ;;
        4)
            # CPU Spike 조치 (CPU 임계치를 90%로 대폭 상향)
            # - Watchdog 임계 상승을 통해 프로세스가 중단되지 않고 영구 생존하는 Before & After를 증명합니다.
            MEMORY_LIMIT=512
            CPU_MAX_OCCUPY=90
            MULTI_THREAD_ENABLE="false"
            launch_scenario
            ;;
        5)
            # Deadlock 재현 (MULTI_THREAD_ENABLE=true)
            # - 식사하는 철학자들의 순환 자원 락 대기가 유발되어 CPU 0% 정체 및 무응답 상태를 검사합니다.
            MEMORY_LIMIT=512
            CPU_MAX_OCCUPY=100
            MULTI_THREAD_ENABLE="true"
            launch_scenario
            ;;
        6)
            # Deadlock 회피 (MULTI_THREAD_ENABLE=false)
            # - 싱글 스레드 혹은 안전한 순차 처리 모드로 실행되어 데드락 없이 안정적으로 비즈니스 로직을 마칩니다.
            MEMORY_LIMIT=512
            CPU_MAX_OCCUPY=100
            MULTI_THREAD_ENABLE="false"
            launch_scenario
            ;;
        7)
            # 프로세스 일시 정리
            cleanup_processes
            ;;
        8)
            # 종료 인사 및 스크립트 탈출
            echo "👋 컨트롤러를 종료합니다. 백그라운드 모니터링은 별도 종료 처리까지 계속될 수 있습니다."
            exit 0
            ;;
        *)
            # 1-8 범위를 벗어난 예외 입력 처리
            echo "[경고] 잘못된 선택입니다. 1번부터 8번 사이의 숫자를 입력해 주십시오."
            ;;
    esac
done
