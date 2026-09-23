"""
constants.py — Mini Git 상수 및 메시지 모음
============================================

이 모듈은 Mini Git 전반에서 사용되는 모든 상수, 매직 스트링,
에러 메시지 등을 중앙 집중식으로 관리합니다.

# 💡 파이썬 현미경 해설
# '모듈(Module)'이란 파이썬 파일(.py) 하나하나를 부르는 말입니다.
# 여기서는 프로그램 곳곳에서 쓰이는 고정된 텍스트(상수)들을 한 곳에 모아두었습니다.
# 이렇게 하면 나중에 오타를 줄이고, 텍스트를 수정할 때 이 파일 하나만 고치면 되기 때문에 아주 편리합니다!
"""

# Enum(열거형)은 관련된 상수들을 묶어서 관리할 때 사용하는 파이썬 내장 기능입니다.
from enum import Enum


class CommandType(Enum):
    """CLI 명령어의 종류를 정의하는 Enum 클래스"""
    # 💡 파이썬 현미경 해설
    # Enum을 사용하면 `CommandType.INIT` 처럼 접근할 수 있습니다.
    # 단순 문자열 "INIT"을 그냥 쓰는 것보다, 오타를 냈을 때 파이썬이 바로 에러로 알려주기 때문에 훨씬 안전합니다.
    INIT = "INIT"
    COMMIT = "COMMIT"
    BRANCH = "BRANCH"
    SWITCH = "SWITCH"
    LOG = "LOG"
    PATH = "PATH"
    ANCESTORS = "ANCESTORS"
    SEARCH = "SEARCH"
    MERGE = "MERGE"
    DIFF = "DIFF"
    BENCHMARK = "BENCHMARK"
    STATUS = "STATUS"
    HELP = "HELP"
    EXIT = "EXIT"
    QUIT = "QUIT"


class ConfigConstants:
    """시스템 기본 설정값들을 관리하는 클래스"""
    # 💡 파이썬 현미경 해설
    # 여기 있는 변수들은 클래스 바로 아래에 정의된 '클래스 변수(Class Variable)'입니다.
    # 객체를 굳이 생성하지 않아도 `ConfigConstants.DEFAULT_BRANCH`처럼 이름만으로 바로 가져다 쓸 수 있습니다.
    DEFAULT_BRANCH = "main"
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # 연-월-일 시:분:초 형태로 시간을 표시하겠다는 포맷 문자열입니다.


class ErrorMessages:
    """모든 에러 메시지를 관리하는 텍스트 클래스"""
    # 💡 파이썬 현미경 해설
    # 오류가 났을 때 화면에 띄워줄 문구들입니다.
    # 문자열 안에 중괄호 `{name}` 부분이 보이시나요?
    # 나중에 사용할 때 `.format(name="main")` 처럼 써주면, 저 중괄호 부분에 "main"이라는 글자가 쏙 들어갑니다. (문자열 포매팅)
    REPO_NOT_INIT = "Error: Repository not initialized. Use INIT first."
    BRANCH_ALREADY_EXISTS = "Error: Branch '{name}' already exists."
    UNKNOWN_BRANCH = "Error: Unknown branch: {name}"
    UNKNOWN_COMMIT = "Error: Unknown commit: {hash}"
    MERGE_SELF = "Error: Cannot merge a branch into itself."
    MERGE_NO_COMMITS = "Error: Cannot merge branches without commits."
    INVALID_INIT = "Error: Invalid args: INIT <user_name>"
    INVALID_COMMIT = "Error: Invalid args: COMMIT <message>"
    INVALID_BRANCH = "Error: Invalid args: BRANCH <branch_name>"
    INVALID_SWITCH = "Error: Invalid args: SWITCH <branch_name>"
    INVALID_PATH = "Error: Invalid args: PATH <commit1> <commit2>"
    INVALID_ANCESTORS = "Error: Invalid args: ANCESTORS <commit_hash>"
    INVALID_SEARCH = "Error: Invalid args: SEARCH <keyword> or SEARCH --author=<name>"
    INVALID_MERGE = "Error: Invalid args: MERGE <branch_name>"
    INVALID_DIFF = "Error: Invalid args: DIFF <file1> <file2>"
    INVALID_SORT_KEY = "Error: Invalid sort key: {key}. Use 'date' or 'author'."
    FILE_NOT_FOUND = "Error: File not found: {path}"
    FILE_READ_ERROR = "Error: Error reading {path}: {error}"


class SystemMessages:
    """일반 출력 및 상태 메시지를 관리하는 텍스트 클래스"""
    PROMPT = "mini-git> "
    
    # 💡 파이썬 현미경 해설
    # 문자열이 길어질 때는 괄호 `()` 로 묶고 한 줄씩 따옴표를 쓰면, 
    # 파이썬이 알아서 하나의 긴 문자열로 이어 붙여줍니다. 
    # `\n`은 줄바꿈(엔터)을 의미하는 특수 기호입니다.
    WELCOME = (
        "==================================================\n"
        "  Welcome to Mini Git!\n"
        "  Type 'help' for available commands.\n"
        "=================================================="
    )
    # 💡 파이썬 현미경 해설
    # 프로그램 종료 및 일반적인 예외 상황 안내 메시지들입니다.
    GOODBYE = "Goodbye!"
    UNKNOWN_COMMAND = "Unknown command: {command}. Type 'help' for available commands."
    ALREADY_UP_TO_DATE = "Already up to date."
    NO_COMMITS_YET = "No commits yet."
    NO_PATH = "No path"

    # 💡 파이썬 현미경 해설
    # 터미널에 보여질 성공 안내 메시지들입니다.
    # 문자열 중간에 `\n`을 쓰면 화면에 출력될 때 그 부분에서 줄이 바뀝니다(엔터 효과).
    # `{branch}`, `{user}` 등의 빈칸은 다른 파일에서 `.format(branch="main", user="alice")` 형태로 채워집니다.
    INIT_SUCCESS = "Initialized repository.\nCurrent branch: {branch}\nCurrent user: {user}"
    COMMIT_SUCCESS = "[{branch} {hash}] {message}"
    BRANCH_CREATED = "Created branch: {name}"
    SWITCHED_BRANCH = "Switched to branch: {name}"
    MERGE_SUCCESS = "Merged '{branch}' into '{head}'.\n[{head} {hash}] {message}"
    
    # 💡 파이썬 현미경 해설
    # 검색 결과를 보여주는 메시지입니다.
    SEARCH_NO_RESULTS = "No commits found for {search_type}."
    SEARCH_FOUND = "Found {count} commit(s) for {search_type}:"
    
    # 💡 파이썬 현미경 해설
    # 따옴표 3개(`"""`)를 연달아 쓰면 여러 줄(Multi-line)에 걸친 긴 문자열을 아주 쉽게 작성할 수 있습니다.
    # 매 줄마다 엔터 표시(\n)를 넣지 않아도, 여기서 엔터를 치면 그대로 화면에 출력됩니다!
    HELP_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║                    Mini Git — Command Help                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  INIT <user_name>         Initialize repository              ║
║  COMMIT <message>         Create a new commit                ║
║  BRANCH <name>            Create a new branch                ║
║  SWITCH <name>            Switch to a branch                 ║
║  LOG                      Show commits (topological order)   ║
║  LOG --sort-by=date       Show commits sorted by date        ║
║  LOG --sort-by=author     Show commits sorted by author      ║
║  PATH <hash1> <hash2>     Find shortest path between commits ║
║  ANCESTORS <hash>         Find all ancestors of a commit     ║
║  SEARCH <keyword>         Search commits by keyword          ║
║  SEARCH --author=<name>   Search commits by author           ║
║  STATUS                   Show repository status             ║
║                                                              ║
║  ── Bonus Commands ──                                        ║
║  MERGE <branch_name>      Merge a branch into current        ║
║  DIFF <file1> <file2>     Compare two text files (LCS)       ║
║  BENCHMARK                Compare sorting algorithms         ║
║                                                              ║
║  HELP                     Show this help message             ║
║  EXIT / QUIT              Exit Mini Git                      ║
╚══════════════════════════════════════════════════════════════╝
"""

    # 💡 파이썬 현미경 해설
    # 문자열 앞에 `f`가 붙어있는 것을 'f-string'이라고 부릅니다. 
    # 중괄호 `{}` 안에 변수 이름이나 식을 넣으면 그 결과가 바로 문자열에 포함됩니다.
    # `{Size:>8}`는 "총 8칸을 확보한 다음 오른쪽(>) 정렬해서 Size라는 글자를 채워라"라는 뜻의 깔끔한 표 그리기 마법입니다.
    BENCHMARK_HEADER = (
        "=================================================================\n"
        "  Sorting Algorithm Benchmark: Merge Sort vs Quick Sort\n"
        "=================================================================\n"
        f"{'Size':>8} | {'Merge Sort (s)':>16} | {'Quick Sort (s)':>16} | {'Winner':>8}\n"
        "-----------------------------------------------------------------"
    )
    # 💡 파이썬 현미경 해설
    # `{merge:>16.6f}`의 의미: 
    # `>16`: 16칸을 잡고 오른쪽으로 정렬해라
    # `.6f`: 소수점 아래 6자리까지 보여주는 실수(Float)로 출력해라
    BENCHMARK_ROW = "{size:>8} | {merge:>16.6f} | {quick:>16.6f} | {winner:>8}"
    BENCHMARK_FOOTER = (
        "-----------------------------------------------------------------\n\n"
        "Notes:\n"
        "  - Merge Sort: Stable, O(n log n) guaranteed\n"
        "  - Quick Sort: Unstable, O(n log n) avg, O(n^2) worst\n"
        "  - Merge Sort uses O(n) extra space\n"
        "  - Quick Sort (this impl) also uses O(n) extra space\n"
        "    (due to list creation; in-place version uses O(log n))\n"
        "================================================================="
    )
