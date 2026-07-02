#!/usr/bin/env python3
"""
AI 기반 Git 커밋 & PR 자동 생성기
- 노트북 마지막 줄의 prompt 변수에 자연어를 입력하면 git 작업을 자동 수행
- SAKANA(Fugu) API로 커밋 메시지 / PR 초안 생성
- SAKANA API 실패 시 IBM BOB API로 자동 폴백
- gh CLI로 GitHub PR 생성
"""

import os
import sys
import subprocess
import argparse
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# 환경변수 로드 (.env)
# ─────────────────────────────────────────────
def load_env(env_path: Optional[str] = None) -> None:
    """현재 스크립트 위치의 .env 파일을 로드한다""" #.삭제함
    if env_path is None:
        env_path = Path(__file__).parent / ".env"
    else:
        env_path = Path(env_path)

    if not env_path.exists():
        return

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

load_env()

# ─────────────────────────────────────────────
# 설정 상수
# ─────────────────────────────────────────────
SAKANA_API_KEY = os.environ.get("SAKANA_API_KEY", "")
SAKANA_API_URL = os.environ.get("SAKANA_API_URL", "https://api.sakana.ai/v1/chat/completions")
FUGU_MODEL     = os.environ.get("FUGU_MODEL", "fugu")

# 로컬 Ollama 폴백 (Sakana 실패 시)
# Ollama는 OpenAI 호환 API를 localhost:11434/v1 로 제공
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/v1/chat/completions")
OLLAMA_MODEL   = os.environ.get("OLLAMA_MODEL", "gpt-oss:20b")

DEFAULT_MODEL       = FUGU_MODEL
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS  = 512

SAFE_MODE_PATTERNS = [
    r"(?i)(password|passwd|pwd)\s*=\s*\S+",
    r"(?i)(api[_-]?key|apikey|secret|token)\s*=\s*\S+",
    r"(?i)(auth|credential)\s*=\s*\S+",
    r"[A-Za-z0-9+/]{40,}={0,2}",          # base64-like 긴 문자열
    r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*",
]

# ─────────────────────────────────────────────
# 민감정보 마스킹
# ─────────────────────────────────────────────
def mask_sensitive(text: str) -> str:
    """safe-mode: diff/status에서 민감 정보를 마스킹한다."""
    for pattern in SAFE_MODE_PATTERNS:
        text = re.sub(pattern, "[MASKED]", text)
    return text

# ─────────────────────────────────────────────
# Git 유틸리티
# ─────────────────────────────────────────────
def run_git(args: list[str], cwd: Optional[str] = None) -> tuple[str, str, int]:
    """git 명령을 실행하고 (stdout, stderr, returncode)를 반환한다."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_repo_root(path: str = ".") -> Optional[str]:
    path = os.path.expanduser(path)  # ~ 경로 확장
    out, _, code = run_git(["rev-parse", "--show-toplevel"], cwd=path)
    return out if code == 0 else None


def get_git_status(repo: str) -> str:
    out, _, _ = run_git(["status", "--short"], cwd=repo)
    return out


def get_git_diff(repo: str, staged: bool = False) -> str:
    args = ["diff", "--stat", "--patch"]
    if staged:
        args.insert(1, "--cached")
    out, _, _ = run_git(args, cwd=repo)
    return out


def get_branch_diff(repo: str, base: str = "main") -> str:
    """현재 브랜치가 base 이후로 가진 커밋의 diff를 반환한다."""
    out, _, _ = run_git(["diff", "--stat", "--patch", f"{base}...HEAD"], cwd=repo)
    return out


def has_commits_since_base(repo: str, base: str = "main") -> bool:
    """현재 브랜치에 base에는 없는 커밋이 있는지 확인한다."""
    out, _, code = run_git(["rev-list", "--count", f"{base}..HEAD"], cwd=repo)
    if code != 0:
        return False
    return int(out or "0") > 0


def get_current_branch(repo: str) -> str:
    out, _, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo)
    return out or "main"


def get_recent_log(repo: str, n: int = 5) -> str:
    out, _, _ = run_git(["log", f"-{n}", "--oneline"], cwd=repo)
    return out


def is_branch_pushed(repo: str, branch: str) -> bool:
    """브랜치가 origin에 이미 존재하는지 확인한다."""
    out, _, code = run_git(["ls-remote", "--exit-code", "--heads", "origin", branch], cwd=repo)
    return code == 0 and bool(out.strip())

# ─────────────────────────────────────────────
# SAKANA API 호출
# ─────────────────────────────────────────────
def call_sakana_api(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """SAKANA API를 호출하고 응답 텍스트를 반환한다. 실패 시 RuntimeError."""
    if not SAKANA_API_KEY:
        raise RuntimeError("SAKANA_API_KEY가 설정되지 않았습니다.")

    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SAKANA_API_URL,
        data=data,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {SAKANA_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SAKANA HTTP {e.code}: {e.reason} / {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"SAKANA 네트워크 오류: {e.reason}") from e


# ─────────────────────────────────────────────
# 로컬 Ollama 호출 (폴백)
# ─────────────────────────────────────────────
def call_ollama_api(
    system_prompt: str,
    user_message: str,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """로컬 Ollama의 OpenAI 호환 엔드포인트를 호출한다. API key 불필요."""
    payload = {
        "model": OLLAMA_MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama 연결 실패: {e.reason}\n"
            "Ollama가 실행 중인지 확인하세요: ollama serve"
        ) from e


# ─────────────────────────────────────────────
# 통합 AI 호출 (Sakana → Ollama 자동 폴백)
# ─────────────────────────────────────────────
def call_ai(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    SAKANA API를 먼저 시도하고, 실패하면 로컬 Ollama(gpt-oss:20b)로 자동 폴백한다.
    둘 다 실패하면 RuntimeError를 발생시킨다.
    """
    sakana_err_msg = ""

    # 1차: Sakana API
    try:
        result = call_sakana_api(system_prompt, user_message,
                                 model=model, temperature=temperature, max_tokens=max_tokens)
        return result
    except RuntimeError as e:
        sakana_err_msg = str(e)
        print(f"  [WARN] Sakana API 실패: {sakana_err_msg}")
        print(f"  [INFO] 로컬 Ollama ({OLLAMA_MODEL})로 폴백합니다...")

    # 2차: 로컬 Ollama
    try:
        result = call_ollama_api(system_prompt, user_message,
                                 temperature=temperature, max_tokens=max_tokens)
        print(f"  [INFO] Ollama ({OLLAMA_MODEL}) 응답 수신 완료")
        return result
    except RuntimeError as ollama_err:
        raise RuntimeError(
            f"Sakana와 Ollama 모두 실패했습니다.\n"
            f"  - Sakana:  {sakana_err_msg}\n"
            f"  - Ollama:  {ollama_err}\n"
            "hint: 'ollama serve' 로 Ollama를 먼저 실행하세요."
        ) from ollama_err

# ─────────────────────────────────────────────
# AI 생성: 커밋 메시지
# ─────────────────────────────────────────────
def generate_commit_message(
    status: str,
    diff: str,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    safe_mode: bool = False,
) -> tuple[str, str]:
    """(title, body) 형태의 커밋 메시지를 생성한다."""
    if safe_mode:
        status = mask_sensitive(status)
        diff   = mask_sensitive(diff)

    system = (
        "당신은 Git 커밋 메시지를 작성하는 전문가입니다. "
        "git status와 diff를 보고 간결한 커밋 메시지를 작성하세요. "
        "제목은 Conventional Commits 형식(type: 한글 설명)을 따르세요. "
        "제목은 72자 이내로 작성하세요. "
        "body는 반드시 한국어로 작성하세요. "
        "Respond ONLY with JSON: {\"title\": \"...\", \"body\": \"...\"}"
    )
    user = f"## git status\n{status}\n\n## git diff\n{diff[:3000]}"

    raw = call_ai(system, user, model=model,
                  temperature=temperature, max_tokens=max_tokens)

    # JSON 파싱 시도
    try:
        # 마크다운 코드블록 제거
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        obj = json.loads(clean)
        title = obj.get("title", "").strip()[:72]
        body  = obj.get("body", "").strip()
        return title, body
    except json.JSONDecodeError:
        # 파싱 실패 시 첫 줄을 title로
        lines = raw.strip().splitlines()
        title = lines[0][:72] if lines else "chore: update"
        body  = "\n".join(lines[1:]).strip()
        return title, body


# ─────────────────────────────────────────────
# AI 생성: PR 초안
# ─────────────────────────────────────────────
def generate_pr_draft(
    status: str,
    diff: str,
    branch: str,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    safe_mode: bool = False,
) -> tuple[str, str]:
    """(pr_title, pr_body) 형태의 PR 초안을 생성한다."""
    if safe_mode:
        status = mask_sensitive(status)
        diff   = mask_sensitive(diff)

    system = (
        "당신은 GitHub Pull Request 초안을 작성하는 전문가입니다. "
        "git 변경사항과 브랜치 이름을 보고 PR 제목과 본문을 작성하세요. "
        "PR 제목은 80자 이내의 한국어로 작성하세요. "
        "PR 본문은 반드시 한국어로 작성하고, 섹션 제목도 다음 한국어 형식을 사용하세요: "
        "## 변경 이유, ## 변경 내용, ## 테스트 방법. "
        "각 섹션은 bullet point로 작성하세요. "
        "Respond ONLY with JSON: {\"title\": \"...\", \"body\": \"...\"}"
    )
    user = (
        f"## Branch\n{branch}\n\n"
        f"## git status\n{status}\n\n"
        f"## git diff\n{diff[:3000]}"
    )

    raw = call_ai(system, user, model=model,
                  temperature=temperature, max_tokens=max_tokens)

    try:
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        obj = json.loads(clean)
        title = obj.get("title", "").strip()[:80]
        body  = obj.get("body", "").strip()
        return title, body
    except json.JSONDecodeError:
        lines = raw.strip().splitlines()
        title = lines[0][:80] if lines else "feat: update"
        body  = "\n".join(lines[1:]).strip()
        return title, body

# ─────────────────────────────────────────────
# Git 작업 실행 함수들
# ─────────────────────────────────────────────
def do_stage_all(repo: str) -> None:
    _, err, code = run_git(["add", "-A"], cwd=repo)
    if code != 0:
        raise RuntimeError(f"git add 실패: {err}")
    print("  ✓ 변경 파일 스테이징 완료 (git add -A)")


def do_commit(repo: str, title: str, body: str = "") -> None:
    message = title if not body else f"{title}\n\n{body}"
    _, err, code = run_git(["commit", "-m", message], cwd=repo)
    if code != 0:
        raise RuntimeError(f"git commit 실패: {err}")
    print(f"  ✓ 커밋 완료: {title}")


def do_push(repo: str, branch: str, set_upstream: bool = True) -> None:
    args = ["push"]
    if set_upstream:
        args += ["-u", "origin", branch]
    _, err, code = run_git(args, cwd=repo)
    if code != 0:
        raise RuntimeError(f"git push 실패: {err}")
    print(f"  ✓ 푸시 완료: origin/{branch}")


def do_create_branch(repo: str, branch: str) -> None:
    _, err, code = run_git(["checkout", "-b", branch], cwd=repo)
    if code != 0:
        raise RuntimeError(f"브랜치 생성 실패: {err}")
    print(f"  ✓ 브랜치 생성 및 전환: {branch}")


def do_create_pr(repo: str, title: str, body: str, base: str = "main") -> None:
    result = subprocess.run(
        ["gh", "pr", "create",
         "--title", title,
         "--body",  body,
         "--base",  base],
        capture_output=True, text=True, cwd=repo,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        # 이미 PR이 존재하는 경우 → 에러 대신 URL 안내 후 머지 시도
        url_match = re.search(r"https://github\.com/\S+/pull/\d+", stderr)
        if url_match:
            pr_url = url_match.group(0)
            print(f"  [INFO] 이 브랜치의 PR이 이미 존재합니다: {pr_url}")
            _auto_merge_pr(repo, pr_url, base)
            return
        # base와 head 사이에 커밋 차이가 없는 경우 → 에러 대신 안내만 출력
        if "No commits between" in stderr:
            print(f"  [INFO] '{base}'와(과) 비교했을 때 새로운 변경사항이 없어 PR을 생성하지 않습니다.")
            return
        raise RuntimeError(f"PR 생성 실패: {stderr}")

    pr_url = result.stdout.strip()
    print(f"  ✓ PR 생성 완료 → {pr_url}")
    _auto_merge_pr(repo, pr_url, base)


def _auto_merge_pr(repo: str, pr_url: str, base: str = "main") -> None:
    """PR을 머지하고 로컬 main을 최신화한다."""
    # PR 번호 추출
    pr_num = pr_url.rstrip("/").split("/")[-1]

    print(f"  [INFO] PR #{pr_num} 자동 머지 중...")
    merge_result = subprocess.run(
        ["gh", "pr", "merge", pr_num, "--merge", "--delete-branch"],
        capture_output=True, text=True, cwd=repo,
    )
    if merge_result.returncode != 0:
        stderr = merge_result.stderr.strip()
        # 이미 머지된 경우는 무시
        if "already been merged" in stderr or "already merged" in stderr:
            print(f"  [INFO] PR #{pr_num}은 이미 머지되어 있습니다.")
        else:
            print(f"  [WARN] 자동 머지 실패: {stderr}")
            print(f"         수동으로 머지하세요: gh pr merge {pr_num} --merge")
        return

    print(f"  ✓ PR #{pr_num} 머지 완료 (feature 브랜치 삭제됨)")

    # 로컬 main 최신화
    _, err, code = run_git(["checkout", base], cwd=repo)
    if code == 0:
        run_git(["pull", "origin", base], cwd=repo)
        print(f"  ✓ 로컬 {base} 브랜치 최신화 완료")

# ─────────────────────────────────────────────
# 자연어 의도 분석
# ─────────────────────────────────────────────
INTENT_KEYWORDS = {
    "commit": [
        "커밋", "commit", "저장", "변경사항 저장", "변경 저장",
    ],
    "push": [
        "푸시", "push", "올려", "원격", "업로드", "remote",
    ],
    "pr": [
        "pr", "pull request", "풀리퀘", "풀 리퀘스트", "머지 요청",
        "merge request", "pr 만들어", "pr 생성", "pr해줘",
    ],
    "branch": [
        "브랜치", "branch", "브랜치 만들어", "새 브랜치",
    ],
    "stage": [
        "스테이징", "stage", "add", "추가",
    ],
    "full": [
        "전부", "모두", "다", "전체", "all", "한번에",
        "commit push pr", "커밋 푸시 pr", "끝까지",
    ],
}

def detect_intents(prompt: str) -> list[str]:
    """
    자연어 프롬프트에서 수행할 git 작업 목록을 순서대로 반환한다.
    예: ["stage", "commit", "push", "pr"]
    """
    p = prompt.lower()
    intents: list[str] = []

    # full 키워드가 있으면 전체 플로우
    for kw in INTENT_KEYWORDS["full"]:
        if kw in p:
            return ["stage", "commit", "push", "pr"]

    for action in ["branch", "stage", "commit", "push", "pr"]:
        for kw in INTENT_KEYWORDS[action]:
            if kw in p:
                if action not in intents:
                    intents.append(action)
                break

    # commit이 있으면 stage도 자동 포함 (앞에)
    if "commit" in intents and "stage" not in intents:
        intents.insert(intents.index("commit"), "stage")

    return intents


def extract_branch_name(prompt: str) -> Optional[str]:
    """프롬프트에서 브랜치 이름을 추출한다."""
    patterns = [
        r"브랜치\s+['\"]?([a-zA-Z0-9/_\-]+)['\"]?",
        r"branch\s+['\"]?([a-zA-Z0-9/_\-]+)['\"]?",
        r"['\"]([a-zA-Z0-9/_\-]+)['\"]",
    ]
    for pat in patterns:
        m = re.search(pat, prompt, re.IGNORECASE)
        if m:
            return m.group(1)
    return None

# ─────────────────────────────────────────────
# 핵심 실행 엔진
# ─────────────────────────────────────────────
def run_auto_git(
    prompt: str,
    repo: str = ".",
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    safe_mode: bool = False,
    base_branch: str = "main",
    dry_run: bool = False,
) -> None:
    """
    자연어 prompt를 해석해 git 작업을 자동 수행한다.

    Parameters
    ----------
    prompt       : 사용자가 작성한 자연어 명령
    repo         : 로컬 git 저장소 경로
    model        : 사용할 AI 모델명
    temperature  : 생성 다양성 (0.0 ~ 1.0)
    max_tokens   : 최대 생성 토큰 수
    safe_mode    : True면 민감정보 마스킹 후 API 전송
    base_branch  : PR 대상 base 브랜치
    dry_run      : True면 실제 git 명령 없이 미리보기만 출력
    """
    print(f"\n{'='*55}")
    print(f"  AI Git 자동화 시작")
    print(f"  프롬프트: {prompt}")
    print(f"  저장소:   {repo}")
    print(f"  safe_mode: {safe_mode} | dry_run: {dry_run}")
    print(f"{'='*55}\n")

    # 저장소 확인: "." 이면 스크립트 위치로 해석
    if repo == ".":
        repo = str(Path(__file__).parent)
    repo = os.path.expanduser(repo)
    repo_root = get_repo_root(repo)
    if not repo_root:
        print(f"[ERROR] '{repo}'는 git 저장소가 아닙니다.")
        sys.exit(1)

    # 현재 상태 수집
    status = get_git_status(repo_root)
    staged_diff  = get_git_diff(repo_root, staged=True)
    working_diff = get_git_diff(repo_root, staged=False)
    branch = get_current_branch(repo_root)
    branch_diff = get_branch_diff(repo_root, base_branch) if branch != base_branch else ""
    diff = staged_diff or working_diff or branch_diff

    # 의도 파악
    intents = detect_intents(prompt)
    if not intents:
        print("[INFO] 인식된 git 작업이 없습니다.")
        print("       hint: '커밋', '푸시', 'PR', '브랜치' 등 키워드를 포함해 주세요.")
        return

    print(f"  인식된 작업: {' → '.join(intents)}\n")

    # 변경사항 없으면 commit/stage만 건너뜀
    has_changes = bool(status.strip())
    has_pr_commits = branch != base_branch and has_commits_since_base(repo_root, base_branch)

    if "pr" in intents and not has_changes and not has_pr_commits:
        print(f"[INFO] PR로 보낼 변경사항이 없습니다.")
        print(f"       작업트리 변경사항: 없음")
        print(f"       {base_branch} 이후 새 커밋: 없음")
        print("       먼저 저장소 안의 파일을 수정한 뒤 저장하거나, 새 커밋을 만든 뒤 다시 실행하세요.")
        return

    if not has_changes and any(x in intents for x in ["stage", "commit"]):
        print("[INFO] 변경사항이 없어 commit/stage 작업을 건너뜁니다.")
        intents = [x for x in intents if x not in ("stage", "commit")]

    # pr 포함 시: 변경사항이 있으면 stage/commit/push를 자동으로 앞에 추가
    if "pr" in intents and has_changes:
        for step in ["push", "commit", "stage"]:
            if step not in intents:
                intents.insert(0, step)

    if not intents:
        print("[INFO] 수행할 작업이 없습니다.")
        return

    # AI 생성 (commit 또는 pr 포함 시)
    commit_title = commit_body = pr_title = pr_body = ""

    if "commit" in intents and has_changes:
        print("  [AI] 커밋 메시지 생성 중...")
        commit_title, commit_body = generate_commit_message(
            status, diff,
            model=model, temperature=temperature,
            max_tokens=max_tokens, safe_mode=safe_mode,
        )
        print(f"  커밋 제목: {commit_title}")
        if commit_body:
            print(f"  커밋 본문:\n{commit_body}\n")

    if "pr" in intents:
        print("  [AI] PR 초안 생성 중...")
        pr_title, pr_body = generate_pr_draft(
            status, diff, branch,
            model=model, temperature=temperature,
            max_tokens=max_tokens, safe_mode=safe_mode,
        )
        print(f"  PR 제목: {pr_title}")
        print(f"  PR 본문:\n{pr_body}\n")

    if dry_run:
        print("\n[DRY-RUN] 실제 git 명령은 실행하지 않습니다.")
        return

    # PR 포함 시: main→main PR은 불가 → feature 브랜치 자동 생성
    import time as _time
    _auto_branch_name = f"feature/auto-{_time.strftime('%Y%m%d-%H%M%S')}"
    if "pr" in intents and branch == base_branch:
        if "branch" not in intents:
            intents.insert(0, "branch")

    # 작업 순서대로 실행
    for intent in intents:
        if intent == "branch":
            new_branch = extract_branch_name(prompt) or _auto_branch_name
            do_create_branch(repo_root, new_branch)
            branch = new_branch

        elif intent == "stage":
            do_stage_all(repo_root)

        elif intent == "commit":
            if commit_title:
                do_commit(repo_root, commit_title, commit_body)

        elif intent == "push":
            do_push(repo_root, branch)

        elif intent == "pr":
            if branch == base_branch:
                print(f"  [WARN] 브랜치({branch})가 base({base_branch})와 같아 PR을 건너뜁니다.")
                print("         hint: feature 브랜치로 전환 후 시도하세요.")
            elif pr_title:
                if not is_branch_pushed(repo_root, branch):
                    print(f"  [INFO] 브랜치 '{branch}'가 원격(origin)에 없어 먼저 push합니다...")
                    do_push(repo_root, branch)
                do_create_pr(repo_root, pr_title, pr_body, base=base_branch)

    print(f"\n{'='*55}")
    print("  완료!")
    print(f"{'='*55}\n")

# ─────────────────────────────────────────────
# CLI 인터페이스 (argparse)
# ─────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="6-2",
        description="AI 기반 Git 커밋 & PR 자동 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python 6-2.py commit
  python 6-2.py pr
  python 6-2.py commit --repo /path/to/repo
  python 6-2.py commit --safe-mode --dry-run
  python 6-2.py commit --model fugu --temperature 0.5
  python 6-2.py push --repo /path/to/repo
  python 6-2.py prompt "변경사항 커밋하고 푸시해줘"
  python 6-2.py prompt "커밋 푸시 PR 다 해줘" --repo /path/to/repo
        """,
    )

    sub = parser.add_subparsers(dest="command")

    # 공통 옵션 부모
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo",        default=".", help="git 저장소 경로 (기본: 현재 디렉토리)")
    common.add_argument("--model",       default=DEFAULT_MODEL, help=f"AI 모델명 (기본: {DEFAULT_MODEL})")
    common.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE, help="생성 temperature (기본: 0.3)")
    common.add_argument("--max-tokens",  type=int,   default=DEFAULT_MAX_TOKENS,  help="최대 토큰 수 (기본: 512)")
    common.add_argument("--safe-mode",   action="store_true", help="민감정보 마스킹 후 API 전송")
    common.add_argument("--dry-run",     action="store_true", help="실제 명령 없이 미리보기만 출력")
    common.add_argument("--base",        default="main", help="PR base 브랜치 (기본: main)")

    # commit 명령
    sub.add_parser("commit", parents=[common], help="AI 커밋 메시지 생성 후 커밋")

    # pr 명령
    sub.add_parser("pr", parents=[common], help="AI PR 초안 생성 후 PR 생성")

    # push 명령
    sub.add_parser("push", parents=[common], help="현재 브랜치를 원격에 푸시")

    # prompt 명령 (자연어) — 텍스트가 옵션보다 먼저 올 수도 있어 nargs='?' 유지
    p_prompt = sub.add_parser("prompt", parents=[common], help="자연어 프롬프트로 git 작업 자동화")
    p_prompt.add_argument("text", nargs="?", default="", help="자연어 명령 문자열")

    return parser


def cli_main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    kwargs = dict(
        model       = getattr(args, "model",       DEFAULT_MODEL),
        temperature = getattr(args, "temperature", DEFAULT_TEMPERATURE),
        max_tokens  = getattr(args, "max_tokens",  DEFAULT_MAX_TOKENS),
        safe_mode   = getattr(args, "safe_mode",   False),
        dry_run     = getattr(args, "dry_run",     False),
        repo        = getattr(args, "repo",        "."),
        base_branch = getattr(args, "base",        "main"),
    )

    if args.command == "commit":
        run_auto_git("커밋해줘", **kwargs)
    elif args.command == "pr":
        run_auto_git("PR 만들어줘", **kwargs)
    elif args.command == "push":
        run_auto_git("푸시해줘", **kwargs)
    elif args.command == "prompt":
        text = args.text.strip() if args.text else ""
        if not text:
            text = input("자연어 명령 입력: ").strip()
        run_auto_git(text, **kwargs)
    else:
        parser.print_help()

# ─────────────────────────────────────────────
# 노트북 인터페이스 (맨 마지막 줄에서 사용)
# ─────────────────────────────────────────────
# 여기서 변수를 설정해서 실행하면 자동으로 git 작업이 수행됩니다.
#
# 사용법:
#   repo   = "저장소 절대경로 또는 상대경로"  (기본: 현재 디렉토리)
#   prompt = "자연어 명령"
#
# 예시:
#   repo   = "/Users/kangsikseo/my_project"
#   prompt = "변경사항 커밋하고 푸시까지 해줘"
#
# 지원 자연어 표현:
#   "커밋해줘"                  → stage + commit
#   "푸시해줘"                  → push
#   "PR 만들어줘"               → PR 생성
#   "커밋하고 푸시해줘"          → stage + commit + push
#   "커밋 푸시 PR 다 해줘"      → stage + commit + push + pr
#   "feature/login 브랜치 만들어" → 브랜치 생성
#
# 옵션 (기본값 사용해도 됩니다):
#   model        = "fugu"     # AI 모델
#   temperature  = 0.3        # 생성 다양성
#   max_tokens   = 512        # 최대 토큰
#   safe_mode    = False      # 민감정보 마스킹
#   dry_run      = False      # 미리보기 모드
#   base_branch  = "main"     # PR base 브랜치

repo        = str(Path(__file__).parent)  # 이 파일이 있는 폴더 = 동료평가
model       = FUGU_MODEL
temperature = DEFAULT_TEMPERATURE
max_tokens  = DEFAULT_MAX_TOKENS
safe_mode   = False
dry_run     = False
base_branch = "main"

prompt = ""  # ← 이 줄에 자연어 명령을 입력하세요

# ─────────────────────────────────────────────
# 엔트리 포
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # CLI 모드: python 6-2.py commit / pr / push / prompt "..."
    if len(sys.argv) > 1:
        cli_main()
    # 노트북/직접 실행 모드
    elif prompt.strip():
        run_auto_git(
            prompt      = prompt,
            repo        = repo,
            model       = model,
            temperature = temperature,
            max_tokens  = max_tokens,
            safe_mode   = safe_mode,
            dry_run     = dry_run,
            base_branch = base_branch,
        )
    else:
        print("사용법 (CLI):")
        print("  python 6-2.py commit              # AI 커밋 메시지 생성 후 커밋")
        print("  python 6-2.py push                # 현재 브랜치 푸시")
        print("  python 6-2.py pr                  # AI PR 초안 생성 후 PR 생성")
        print("  python 6-2.py prompt '커밋하고 푸시해줘'")
        print()
        print("사용법 (노트북/직접 실행):")
        print("  이 파일 맨 아래 prompt = \"...\" 에 자연어 명령을 입력 후 실행")
        print("  예: prompt = \"변경사항 모두 커밋하고 푸시한 뒤 PR 만들어줘\"")
