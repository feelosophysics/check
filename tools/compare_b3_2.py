"""두 B3-2 소스의 경계 사례 재현. 실제 API, 원본 수정, 실제 커밋 없음.

python tools/compare_b3_2.py --friend ../codyssey_b3-2 --mine ../codsaid/01_Basic/b3-2
의존성: python-dotenv, PyYAML. 임시 저장소는 실행 폴더 아래 생성 후 삭제한다.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--friend', type=Path, required=True)
    parser.add_argument('--mine', type=Path, required=True)
    args = parser.parse_args()
    friend = load('friend_core', args.friend.resolve() / 'gitgen/core.py')
    mine = args.mine.resolve()
    helper = load('mine_git', mine / 'gitgen/git_helper.py')
    safety = load('mine_safety', mine / 'gitgen/safe_mode.py')
    config = load('mine_config', mine / 'gitgen/config.py')
    api = load('mine_api', mine / 'gitgen/gemini_client.py')
    results = {}
    old = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='b3-2-probe-', dir=old) as directory:
        try:
            os.chdir(directory)
            subprocess.run(['git', 'init', '-q'], check=True, capture_output=True)
            Path('sample.txt').write_text('STAGED_FIRST\n', encoding='utf-8')
            subprocess.run(['git', 'add', 'sample.txt'], check=True, capture_output=True)
            Path('sample.txt').write_text('UNSTAGED_SECOND\n', encoding='utf-8')
            _, their_diff = friend.collect_changes()
            my_diff = helper.get_git_diff()
            my_staged_diff = helper.get_git_diff(staged_only=True)
            results['mixed_changes'] = {
                'friend_contains_both_additions': '+STAGED_FIRST' in their_diff and '+UNSTAGED_SECOND' in their_diff,
                'mine_default_contains_staged_addition': '+STAGED_FIRST' in my_diff,
                'mine_default_contains_unstaged_addition': '+UNSTAGED_SECOND' in my_diff,
                'mine_staged_only_contains_staged_addition': '+STAGED_FIRST' in my_staged_diff,
            }
            with contextlib.redirect_stdout(io.StringIO()):
                Path('.ai-gitgen.yml').write_text('commit: {}\n', encoding='utf-8')
                dotted = config.load_convention()
                Path('ai-gitgen.yml').write_text('commit: {}\n', encoding='utf-8')
                plain = config.load_convention()
            results['config_filename'] = {'dotted_loaded': dotted is not None, 'plain_loaded': plain is not None}
        finally:
            os.chdir(old)
    raw = 'email=demo@example.com\nAPI_KEY="synthetic-demo-key"\npassword="demopassword"\nip=192.0.2.1'
    with patch.dict(os.environ, {'AI_API_KEY': 'synthetic-demo-key'}, clear=True):
        with contextlib.redirect_stdout(io.StringIO()):
            my_mask = safety.apply_safe_mode(raw)
        results['mask'] = {'friend': friend.mask(raw), 'mine': my_mask}
    invalid_style = {'summary': 'English', 'title': 'No prefix', 'body': '- one\n- two\n- three'}
    results['friend_style_validation_accepts'] = friend.validate(json.dumps(invalid_style), 'commit') == invalid_style
    with patch.dict(os.environ, {'AI_API_KEY': 'demo123'}, clear=True), patch(
        'urllib.request.urlopen', return_value=io.BytesIO(b'{"candidates":[]}')
    ), contextlib.redirect_stdout(io.StringIO()):
        results['mine_empty_candidates_result'] = api.call_gemini_api('demo', 'demo-model', 0.3, 100)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
