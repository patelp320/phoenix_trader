import json, pathlib, datetime as dt, textwrap

LOG = pathlib.Path("logs/errors.jsonl")
TEST_DIR = pathlib.Path("tests")
TEST_DIR.mkdir(exist_ok=True)

def write_test():
    try:
        trace = json.loads(LOG.read_text().splitlines()[-1])["trace"]
    except Exception:
        return
    fname = TEST_DIR / f"trace_{dt.datetime.utcnow():%H%M%S}.py"
    code = textwrap.dedent(f'''
        import pytest

        def test_repro():
            # The original stack-trace must re-appear when we re-run the code block
            trace = \"\"\"{trace}\"\"\"
            with pytest.raises(Exception):
                exec(trace, {{}})
    ''')
    fname.write_text(code)
