#!/usr/bin/env bash

# ==============================================================================
# [run_custom.sh] 사용자 정의 옵션 기반 실시간 장애 분석 애플리케이션 기동 스크립트
# ==============================================================================
# 이 스크립트는 기존 run_scenario.sh의 고정된 시나리오 선택에서 벗어나,
# 사용자가 직접 MEMORY_LIMIT, CPU_MAX_OCCUPY, MULTI_THREAD_ENABLE 등의 
# 시스템 자원 임계 옵션을 제어하여 agent-app-leak을 유연하게 구동할 수 있게 돕는
# 실전 실습용 커스텀 기동기입니다.
#
# 특히, 기존 백그라운드 관제기(monitor.sh)를 절대 강제 종료하지 않음으로써,
# 터미널 창 하나에는 monitor.sh를 계속 켜놓은 상태로, 다른 터미널에서 이 스크립트를
# 통해 프로세스 인자값을 변경해가며 자원 상태를 실시간 관측할 수 있습니다.
# ==============================================================================

# 1. 공통 환경 변수 및 설정 정의
# ------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_HOME="$SCRIPT_DIR/agent_home"
export AGENT_HOME="${AGENT_HOME:-$DEFAULT_HOME}"
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
export AGENT_KEY_PATH="$AGENT_HOME/api_keys"
export AGENT_LOG_DIR="$AGENT_HOME/logs"

# 앱 실행 바이너리의 로컬 경로 지정
APP_BIN="./agent-app-leak"

# 2. 도움말 출력 함수
# ------------------------------------------------------------------------------
show_help() {
    echo -e "\033[1;34m======================================================================\033[0m"
    echo -e "💡 \033[1;36m[run_custom.sh] 사용 가이드 - 직접 제어하는 리소스 실습 환경\033[0m"
    echo -e "\033[1;34m======================================================================\033[0m"
    echo "사용법: $0 [옵션]"
    echo ""
    echo "지원하는 옵션:"
    echo "  -m, --memory <MB>      메모리 제한 설정 (정수, 범위: 50 ~ 512 MB)"
    echo "  -c, --cpu <%>          CPU 최대 허용률 설정 (정수, 범위: 10 ~ 100 %)"
    echo "  -t, --thread <bool>    멀티스레드 활성화 여부 (true / false)"
    echo "  -d, --daemon           백그라운드(Daemon) 모드로 실행 (실습 추적 모드)"
    echo "  -h, --help             이 도움말을 화면에 출력합니다."
    echo ""
    echo "예시:"
    echo "  ./run_custom.sh -m 128 -c 50 -t false"
    echo "  ./run_custom.sh --memory 256 --cpu 80 --thread true --daemon"
    echo "  (아무 인자 없이 실행 시 대화식 터미널 프롬프트 모드로 진입합니다.)"
    echo -e "\033[1;34m======================================================================\033[0m"
}

# 3. 명령줄 인수 파싱 (Arguments Parsing)
# ------------------------------------------------------------------------------
DAEMON_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--memory)
            MEMORY_LIMIT="$2"
            shift 2
            ;;
        -c|--cpu)
            CPU_MAX_OCCUPY="$2"
            shift 2
            ;;
        -t|--thread)
            MULTI_THREAD_ENABLE="$2"
            shift 2
            ;;
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "\033[1;31m❌ [오류] 알 수 없는 인수입니다: $1\033[0m"
            show_help
            exit 1
            ;;
    esac
done

# 4. 입력 부재 시 대화식 입력 프롬프트 제공 (Interactive Fallback with Smart Defaults)
# ------------------------------------------------------------------------------
echo -e "\033[1;35m======================================================================\033[0m"
echo -e "🚀 \033[1;35m[옵션 빌딩] 리소스 분석용 커스텀 환경 구성을 빌드합니다.\033[0m"
echo -e "\033[1;35m======================================================================\033[0m"

# 4.1 MEMORY_LIMIT 입력 및 검증
if [ -z "$MEMORY_LIMIT" ]; then
    read -p "👉 MEMORY_LIMIT 설정 (50~512 MB) [기본값: 256]: " USER_MEM
    MEMORY_LIMIT="${USER_MEM:-256}"
fi

if ! [[ "$MEMORY_LIMIT" =~ ^[0-9]+$ ]] || [ "$MEMORY_LIMIT" -lt 50 ] || [ "$MEMORY_LIMIT" -gt 512 ]; then
    echo -e "\033[1;31m❌ [오류] MEMORY_LIMIT는 50에서 512 사이의 정수여야 합니다. (입력값: $MEMORY_LIMIT)\033[0m"
    exit 1
fi

# 4.2 CPU_MAX_OCCUPY 입력 및 검증
if [ -z "$CPU_MAX_OCCUPY" ]; then
    read -p "👉 CPU_MAX_OCCUPY 설정 (10~100 %) [기본값: 80]: " USER_CPU
    CPU_MAX_OCCUPY="${USER_CPU:-80}"
fi

if ! [[ "$CPU_MAX_OCCUPY" =~ ^[0-9]+$ ]] || [ "$CPU_MAX_OCCUPY" -lt 10 ] || [ "$CPU_MAX_OCCUPY" -gt 100 ]; then
    echo -e "\033[1;31m❌ [오류] CPU_MAX_OCCUPY는 10에서 100 사이의 정수여야 합니다. (입력값: $CPU_MAX_OCCUPY)\033[0m"
    exit 1
fi

# 4.3 MULTI_THREAD_ENABLE 입력 및 검증
if [ -z "$MULTI_THREAD_ENABLE" ]; then
    read -p "👉 MULTI_THREAD_ENABLE 여부 (true/false) [기본값: false]: " USER_THREAD
    MULTI_THREAD_ENABLE="${USER_THREAD:-false}"
fi

# 입력값을 소문자로 변환하여 변이 검사 방어
MULTI_THREAD_ENABLE=$(echo "$MULTI_THREAD_ENABLE" | tr '[:upper:]' '[:lower:]')
if [ "$MULTI_THREAD_ENABLE" != "true" ] && [ "$MULTI_THREAD_ENABLE" != "false" ]; then
    echo -e "\033[1;31m❌ [오류] MULTI_THREAD_ENABLE은 'true' 또는 'false' 여야 합니다. (입력값: $MULTI_THREAD_ENABLE)\033[0m"
    exit 1
fi

export MEMORY_LIMIT
export CPU_MAX_OCCUPY
export MULTI_THREAD_ENABLE

# 5. 실행 권한 및 초기 환경 검증
# ------------------------------------------------------------------------------
if [ ! -x "$APP_BIN" ]; then
    echo -e "\033[1;33m[안내] $APP_BIN 바이너리에 실행 권한이 부여되지 않았습니다. 권한을 부여합니다 (chmod +x).\033[0m"
    chmod +x "$APP_BIN"
fi

if [ -f "./setup_env.sh" ]; then
    # setup_env.sh를 활용해 기초 폴더 구성과 secret.key 검증을 선제적으로 완수합니다.
    source ./setup_env.sh
else
    echo -e "\033[1;33m[경고] setup_env.sh가 존재하지 않아 기본 구성 요소를 자동 생성합니다.\033[0m"
    mkdir -p "$AGENT_UPLOAD_DIR" "$AGENT_KEY_PATH" "$AGENT_LOG_DIR"
    echo -n "agent_api_key_test" > "$AGENT_KEY_PATH/secret.key"
fi

# 6. 프로세스 청소 및 관제 스크립트 체크
# ------------------------------------------------------------------------------
cleanup_previous_app() {
    echo "----------------------------------------------------------------------"
    echo -e "\033[1;36m🧹 [애플리케이션 초기화] 포트 충돌 방지를 위해 기존 agent-app-leak 인스턴스를 찾아 종료합니다.\033[0m"
    
    APP_PIDS=$(pgrep -f "agent-app-leak")
    if [ -n "$APP_PIDS" ]; then
        # 포트 바인딩 중복 및 데드락 상태의 완벽한 정리를 위해 확실한 강제 종료 시그널(-9)을 보냅니다.
        kill -9 $APP_PIDS 2>/dev/null
        echo "✔ 기존에 실행 중이던 백그라운드 애플리케이션(agent-app-leak, PID: $APP_PIDS)을 강제 종료했습니다."
    else
        echo "✔ 충돌되는 기존 애플리케이션 프로세스가 없습니다. 깨끗한 상태입니다."
    fi
    echo "----------------------------------------------------------------------"
}

check_monitor_status() {
    MON_PIDS=$(pgrep -f "monitor.sh" | grep -v grep)
    if [ -z "$MON_PIDS" ]; then
        echo -e "\033[1;33m💡 [안내] 현재 관제 스크립트(monitor.sh)가 실행되고 있지 않습니다!\033[0m"
        echo "   실시간 관제 분석 실습을 위해, 다른 터미널 창을 열고 아래 명령어로 관제를 먼저 실행해 주세요:"
        echo -e "   \033[1;36m./monitor.sh\033[0m"
    else
        echo -e "\033[1;32m✔ [안내] 관제 스크립트(monitor.sh)가 이미 동작 중입니다!\033[0m (PID: $MON_PIDS)"
        echo "   다른 터미널 창에서 실시간 관제 로그 스트리밍을 볼 수 있습니다:"
        echo -e "   \033[1;36mtail -f \"$AGENT_LOG_DIR/monitor.log\"\033[0m"
    fi
    echo "----------------------------------------------------------------------"
}

cleanup_previous_app
check_monitor_status

# 7. 애플리케이션 기동 연산
# ------------------------------------------------------------------------------
echo -e "\033[1;32m⚙ [기동 구성 요약]"
echo "   - MEMORY_LIMIT        : $MEMORY_LIMIT MB"
echo "   - CPU_MAX_OCCUPY      : $CPU_MAX_OCCUPY %"
echo "   - MULTI_THREAD_ENABLE : $MULTI_THREAD_ENABLE"
echo -e "   - RUN_MODE            : $( [ "$DAEMON_MODE" = true ] && echo "Background (Daemon)" || echo "Foreground (Live Console)" )\033[0m"
echo "----------------------------------------------------------------------"

# 백그라운드 로그 파일 초기화
> "$AGENT_LOG_DIR/app.log"

if [ "$DAEMON_MODE" = true ]; then
    # 백그라운드(Daemon) 실행 모드
    echo -e "\033[1;32m🚀 애플리케이션을 백그라운드 모드로 구동합니다.\033[0m"
    
    nohup "$APP_BIN" > "$AGENT_LOG_DIR/app.log" 2>&1 &
    
    # 찰나의 기동 대기 시간 후 PID 확인
    sleep 0.3
    NEW_APP_PID=$(pgrep -f "agent-app-leak" | head -n 1)
    
    if [ -n "$NEW_APP_PID" ]; then
        echo -e "  - 애플리케이션 PID   : \033[1;36m$NEW_APP_PID\033[0m"
        echo "  - 애플리케이션 로그  : $AGENT_LOG_DIR/app.log"
        echo ""
        echo -e "\033[1;33m📚 [학습 미션 - 다음 명령어들을 다른 터미널에서 입력하여 직접 상태를 진단해 보세요!]\033[0m"
        echo "  1. 프로세스가 가상 메모리 테이블에 살아있는지 증명하기:"
        echo -e "     \033[1;36mps -ef | grep agent-app-leak\033[0m"
        echo "  2. 실시간 CPU 및 메모리 소모 수치 개별 필터링 조회하기 (헤더 생략 옵션):"
        echo -e "     \033[1;36mps -p $NEW_APP_PID -o %cpu=,%%mem=\033[0m"
        echo "  3. 애플리케이션 내부 실행 스레드(LWP) 테이블 전개 관측하기 (데드락 진단 필수):"
        echo -e "     \033[1;36mps -L -p $NEW_APP_PID\033[0m"
        echo "  4. 실시간으로 수집되는 monitor.sh 관제 데이터 로그 스트리밍하기:"
        echo -e "     \033[1;36mtail -f \"$AGENT_LOG_DIR/monitor.log\"\033[0m"
        echo "  5. 프로세스를 직접 강제 사멸시키는 시그널 실험해보기:"
        echo -e "     \033[1;36mkill -9 $NEW_APP_PID\033[0m"
    else
        echo -e "\033[1;31m❌ [오류] 백그라운드 애플리케이션 기동에 실패했습니다. 로그를 점검하세요 ($AGENT_LOG_DIR/app.log).\033[0m"
        exit 1
    fi
else
    # 포그라운드(Live Console) 실행 모드
    echo -e "\033[1;32m🚀 애플리케이션을 포그라운드 모드로 구동합니다. 콘솔 로그가 스트리밍됩니다.\033[0m"
    echo -e "\033[1;33m👉 실행을 중단하고 프로세스를 종료하려면 터미널에서 [Ctrl + C]를 누르세요.\033[0m"
    echo "----------------------------------------------------------------------"
    
    # stdout을 터미널로 실시간 내보내며 동시에 파일(app.log)에도 써지도록 tee 명령어 활용
    "$APP_BIN" 2>&1 | tee "$AGENT_LOG_DIR/app.log"
fi

echo -e "\033[1;34m======================================================================\033[0m"
