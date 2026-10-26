"""Tiny code judge for Python submissions (stdin/stdout test cases).

SECURITY NOTE: this runs user code in a separate process with a timeout and (on Linux/macOS) CPU and memory limits.
It is NOT a full sandbox. For a public deployment run it inside a container or an isolated service.
"""
import os, subprocess, sys, tempfile

TIME_LIMIT = float(os.environ.get("JUDGE_TIME_LIMIT", "3"))
MEMORY_MB = int(os.environ.get("JUDGE_MEMORY_MB", "256"))
MAX_CODE = 20000

def _limits():  # POSIX only
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_MB * 1024 * 1024,) * 2)
        resource.setrlimit(resource.RLIMIT_CPU, (int(TIME_LIMIT) + 1,) * 2)
    except Exception:
        pass

def run_python(code, tests):
    """Return (overall_status, results). Each result: dict(n, hidden, verdict, passed, input, expected, got)."""
    if len(code) > MAX_CODE: return "Rejected", [dict(n=1, hidden=False, verdict="Code too long", passed=False, input="", expected="", got="")]
    results = []
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "solution.py")
        with open(path, "w", encoding="utf-8") as f: f.write(code)
        for i, (inp, exp) in enumerate(tests, 1):
            hidden = i > 2  # first two tests are visible, the rest hidden
            kw = dict(input=inp + "\n", capture_output=True, text=True, timeout=TIME_LIMIT, cwd=d)
            if os.name == "posix": kw["preexec_fn"] = _limits
            try:
                p = subprocess.run([sys.executable, "-I", path], **kw)
                out = p.stdout.strip()
                if p.returncode != 0: verdict, ok, got = "Runtime Error", False, (p.stderr.strip().splitlines() or [""])[-1][:200]
                elif out == exp.strip(): verdict, ok, got = "Passed", True, out
                else: verdict, ok, got = "Wrong Answer", False, out[:200]
            except subprocess.TimeoutExpired:
                verdict, ok, got = "Time Limit Exceeded", False, ""
            results.append(dict(n=i, hidden=hidden, verdict=verdict, passed=ok, input=inp, expected=exp, got=got))
    if all(r["passed"] for r in results): status = "Accepted"
    else: status = next(r["verdict"] for r in results if not r["passed"])
    return status, results
