"""EduCoach AI - adaptive placement preparation platform (Flask + SQLite + scikit-learn)."""
import csv, hmac, io, json, os, random, re, secrets, sqlite3, time
from datetime import datetime
from functools import wraps
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for, Response
from werkzeug.security import check_password_hash, generate_password_hash

import ml, bank, judge
from catalog import TECHNICAL, VERBAL, APTITUDE, CODING
from problems import PROBLEMS, BY_ID, problems_for_topic

BASE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

def _secret():
    if os.environ.get("EDUCOACH_SECRET"): return os.environ["EDUCOACH_SECRET"]
    p = os.path.join(BASE, "data", "secret_key")
    if not os.path.exists(p):
        with open(p, "w") as f: f.write(secrets.token_hex(32))
    return open(p).read().strip()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=_secret(), DB=os.environ.get("EDUCOACH_DB", os.path.join(BASE, "data", "educoach.db")),
    SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=1024 * 1024,
    ADMIN_EMAIL=os.environ.get("ADMIN_EMAIL", "").lower(),
)

DIFF_RATING = {"Easy": 1000, "Medium": 1200, "Hard": 1400}
DEFAULT_RATING, ELO_K = 1100, 20
TEST_QUESTIONS = 30     # every test has this many questions (fewer only if the bank runs out)
SECONDS_PER_Q = {"Technical": 60, "Verbal": 60, "Aptitude": 90}
MIN_ANSWERS = 3          # answers needed before a topic counts as weak/strong
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ------------------------------------------------------------------ database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DB"]); g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None: db.close()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, is_admin INTEGER DEFAULT 0, created_at TEXT);
CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, subject TEXT, topic TEXT, difficulty TEXT, question TEXT, options TEXT, answer TEXT, explanation TEXT, UNIQUE(subject, topic, question));
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, category TEXT, subject TEXT, topic TEXT, score REAL, total INTEGER, correct INTEGER, time_taken INTEGER, difficulty TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS attempt_answers(id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id INTEGER, question_id INTEGER, chosen TEXT, is_correct INTEGER);
CREATE TABLE IF NOT EXISTS ability(user_id INTEGER, topic TEXT, rating REAL, PRIMARY KEY(user_id, topic));
CREATE TABLE IF NOT EXISTS coding_submissions(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, language TEXT, topic TEXT, problem_id TEXT, code TEXT, status TEXT, passed INTEGER, total INTEGER, created_at TEXT);
CREATE INDEX IF NOT EXISTS idx_q_topic ON questions(subject, topic);
CREATE INDEX IF NOT EXISTS idx_a_user ON attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_aa_attempt ON attempt_answers(attempt_id);
"""

def insert_questions(c, rows):
    n = 0
    for r in rows:
        cur = c.execute("INSERT OR IGNORE INTO questions(category,subject,topic,difficulty,question,options,answer,explanation) VALUES(?,?,?,?,?,?,?,?)",
                        (r["category"], r["subject"], r["topic"], r["difficulty"], r["question"], json.dumps(r["options"]), r["answer"], r.get("explanation", "")))
        n += cur.rowcount
    return n

def init_db():
    c = sqlite3.connect(app.config["DB"]); c.executescript(SCHEMA)
    insert_questions(c, bank.build_all()); c.commit(); c.close()

@app.template_filter("fromjson")
def fromjson(v): return json.loads(v)

# ------------------------------------------------------------------ security helpers
def csrf_token():
    if "csrf" not in session: session["csrf"] = secrets.token_hex(16)
    return session["csrf"]
app.jinja_env.globals["csrf_token"] = csrf_token

@app.before_request
def csrf_protect():
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        if not sent or not hmac.compare_digest(sent, session.get("csrf", "")): abort(400, "Invalid or missing CSRF token.")

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if "user_id" not in session: return redirect(url_for("login"))
        return f(*a, **k)
    return w

def admin_required(f):
    @wraps(f)
    @login_required
    def w(*a, **k):
        if not session.get("is_admin"): abort(403)
        return f(*a, **k)
    return w

FAILS = {}
def too_many_failures(key):
    now = time.time(); FAILS[key] = [t for t in FAILS.get(key, []) if now - t < 300]
    return len(FAILS[key]) >= 5

# ------------------------------------------------------------------ analytics & adaptive engine
def level_name(r):
    return "Beginner" if r < 1050 else "Intermediate" if r < 1200 else "Advanced" if r < 1350 else "Expert"

def topic_stats(c, uid):
    return c.execute("""SELECT q.topic, q.subject, q.category, COUNT(*) n, AVG(a.is_correct) acc FROM attempt_answers a
        JOIN attempts t ON t.id=a.attempt_id JOIN questions q ON q.id=a.question_id WHERE t.user_id=? GROUP BY q.topic, q.subject ORDER BY acc""", (uid,)).fetchall()

def ratings(c, uid):
    return {r["topic"]: r["rating"] for r in c.execute("SELECT topic,rating FROM ability WHERE user_id=?", (uid,))}

def readiness(c, uid):
    rows = c.execute("SELECT score,total,correct,time_taken,difficulty FROM attempts WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    if len(rows) < ml.MIN_TESTS:
        return dict(label="Not enough data", confidence=None, proba={}, tests=len(rows), needed=ml.MIN_TESTS - len(rows))
    cov = c.execute("SELECT COUNT(DISTINCT q.topic) n FROM attempt_answers a JOIN attempts t ON t.id=a.attempt_id JOIN questions q ON q.id=a.question_id WHERE t.user_id=?", (uid,)).fetchone()["n"]
    label, conf, proba = ml.predict(ml.features_from_attempts(rows, cov))
    return dict(label=label, confidence=conf, proba=proba, tests=len(rows), needed=0)

def select_questions(c, uid, category, subject, topic, mode, n=TEST_QUESTIONS):
    """Pick up to n distinct questions (never more than TEST_QUESTIONS).
    Order of preference: same topic, then same subject, then same category. Adaptive mode targets the learner's rating."""
    n = min(n, TEST_QUESTIONS); rng = random.Random()
    topic_rows = c.execute("SELECT id,difficulty,topic FROM questions WHERE category=? AND subject=? AND topic=?", (category, subject, topic)).fetchall()
    subj_rows = c.execute("SELECT id,difficulty,topic FROM questions WHERE category=? AND subject=? AND topic<>?", (category, subject, topic)).fetchall()
    cat_rows = c.execute("SELECT id,difficulty,topic FROM questions WHERE category=? AND subject<>?", (category, subject)).fetchall()
    target = ratings(c, uid).get(topic, DEFAULT_RATING) if mode == "Adaptive" else DIFF_RATING[mode]
    seen = {r["question_id"] for r in c.execute("SELECT a.question_id FROM attempt_answers a JOIN attempts t ON t.id=a.attempt_id WHERE t.user_id=? ORDER BY a.id DESC LIMIT 60", (uid,))}
    def rank(rows): return sorted(rows, key=lambda r: abs(DIFF_RATING[r["difficulty"]] - target) + rng.uniform(0, 120) + (250 if r["id"] in seen else 0))
    chosen = rank(topic_rows)[:n]
    mixed = len(chosen) < n
    for pool in (subj_rows, cat_rows):
        if len(chosen) < n: chosen += rank(pool)[: n - len(chosen)]
    ids = [r["id"] for r in chosen]; rng.shuffle(ids)
    return ids, mixed

def update_ratings(c, uid, items):
    """items: list of (topic, difficulty, is_correct). Elo-style update of the learner's rating per topic."""
    cur = ratings(c, uid)
    for topic, diff, ok in items:
        r = cur.get(topic, DEFAULT_RATING); expected = 1 / (1 + 10 ** ((DIFF_RATING[diff] - r) / 400))
        cur[topic] = r + ELO_K * ((1 if ok else 0) - expected)
    for topic, r in cur.items():
        c.execute("INSERT INTO ability(user_id,topic,rating) VALUES(?,?,?) ON CONFLICT(user_id,topic) DO UPDATE SET rating=excluded.rating", (uid, topic, round(r, 1)))

def find_topic(c, topic):
    return c.execute("SELECT category,subject,topic FROM questions WHERE topic=? ORDER BY id LIMIT 1", (topic,)).fetchone()

def recommendation(c, uid, stats):
    weak = [s for s in stats if s["n"] >= MIN_ANSWERS and s["acc"] < 0.6]
    if weak: return find_topic(c, weak[0]["topic"]), f"Your accuracy here is {weak[0]['acc'] * 100:.0f}%."
    rt = ratings(c, uid)
    if rt:
        t = min(rt, key=rt.get); return find_topic(c, t), f"Lowest ability rating ({rt[t]:.0f})."
    return find_topic(c, "Lists"), "A good place to start."

def trend_text(c, uid):
    s = [r["score"] for r in c.execute("SELECT score FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 6", (uid,))]
    if len(s) < 4: return "Take a few more tests to see your trend."
    recent, older = sum(s[:3]) / 3, sum(s[3:]) / len(s[3:]); d = recent - older
    if d > 5: return f"Improving: your last 3 tests average {recent:.0f}% (up {d:.0f} points)."
    if d < -5: return f"Declining: your last 3 tests average {recent:.0f}% (down {abs(d):.0f} points). Revise your mistakes."
    return f"Steady: your recent average is {recent:.0f}%."

# ------------------------------------------------------------------ auth
@app.route("/")
def index(): return redirect(url_for("dashboard" if "user_id" in session else "login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip(); email = request.form.get("email", "").strip().lower(); pw = request.form.get("password", "")
        err = None
        if not name: err = "Name is required."
        elif not EMAIL_RE.match(email): err = "Enter a valid email address."
        elif len(pw) < 8 or not re.search(r"\d", pw) or not re.search(r"[A-Za-z]", pw): err = "Password must be 8+ characters with letters and a digit."
        if err: flash(err, "error")
        else:
            c = get_db(); first = c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"] == 0
            try:
                c.execute("INSERT INTO users(name,email,password,is_admin,created_at) VALUES(?,?,?,?,?)", (name, email, generate_password_hash(pw), 1 if first or email == app.config["ADMIN_EMAIL"] else 0, datetime.now().isoformat())); c.commit()
                flash("Registration successful. Please log in.", "success"); return redirect(url_for("login"))
            except sqlite3.IntegrityError: flash("Email already registered.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower(); key = (request.remote_addr, email)
        if too_many_failures(key): flash("Too many failed attempts. Try again in 5 minutes.", "error"); return render_template("login.html")
        u = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if u and check_password_hash(u["password"], request.form.get("password", "")):
            session.clear(); session.update(user_id=u["id"], name=u["name"], is_admin=bool(u["is_admin"])); FAILS.pop(key, None)
            return redirect(url_for("dashboard"))
        FAILS.setdefault(key, []).append(time.time()); flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout(): session.clear(); return redirect(url_for("login"))

# ------------------------------------------------------------------ dashboard & practice
@app.route("/dashboard")
@login_required
def dashboard():
    c, uid = get_db(), session["user_id"]; stats = topic_stats(c, uid)
    att = c.execute("SELECT COUNT(*) n, AVG(score) avg FROM attempts WHERE user_id=?", (uid,)).fetchone()
    weak = [s for s in stats if s["n"] >= MIN_ANSWERS and s["acc"] < 0.6][:5]
    strong = sorted([s for s in stats if s["n"] >= MIN_ANSWERS and s["acc"] >= 0.8], key=lambda s: -s["acc"])[:5]
    recent = c.execute("SELECT id,category,topic,score,difficulty,created_at FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 8", (uid,)).fetchall()
    curve = [dict(x=r["created_at"][5:10], y=r["score"]) for r in reversed(c.execute("SELECT score,created_at FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 15", (uid,)).fetchall())]
    rec, why = recommendation(c, uid, stats)
    solved = c.execute("SELECT COUNT(DISTINCT problem_id) n FROM coding_submissions WHERE user_id=? AND status='Accepted'", (uid,)).fetchone()["n"]
    return render_template("dashboard.html", ready=readiness(c, uid), avg=round(att["avg"] or 0, 1), total=att["n"], weak=weak, strong=strong, recent=recent, curve=curve, rec=rec, why=why, solved=solved, trend=trend_text(c, uid))

@app.route("/category/<category>")
@login_required
def category(category):
    data = {"Technical": TECHNICAL, "Verbal": {"Verbal": VERBAL}, "Aptitude": {"Aptitude": APTITUDE}, "Coding": CODING}.get(category)
    if data is None: return redirect(url_for("dashboard"))
    c = get_db(); rt = ratings(c, session["user_id"]); counts = {(r["subject"], r["topic"]): r["n"] for r in c.execute("SELECT subject,topic,COUNT(*) n FROM questions GROUP BY subject,topic")}
    return render_template("category.html", category=category, data=data, rt=rt, counts=counts, level_name=level_name)

@app.route("/start-test", methods=["POST"])
@login_required
def start_test():
    category = request.form.get("category", ""); subject = request.form.get("subject", ""); topic = request.form.get("topic", "")
    mode = request.form.get("difficulty", "Adaptive")
    if mode not in ("Adaptive", *DIFF_RATING): mode = "Adaptive"
    c = get_db(); ids, mixed = select_questions(c, session["user_id"], category, subject, topic, mode)
    if not ids: flash("No questions are available for that topic yet.", "error"); return redirect(url_for("dashboard"))
    secs = SECONDS_PER_Q.get(category, 60) * len(ids)
    session["test"] = dict(category=category, subject=subject, topic=topic, mode=mode, ids=ids, mixed=mixed, start=time.time(), seconds=secs)
    return redirect(url_for("test"))

@app.route("/test")
@login_required
def test():
    t = session.get("test")
    if not t: return redirect(url_for("dashboard"))
    c = get_db(); ids = t["ids"]; rows = c.execute(f"SELECT * FROM questions WHERE id IN ({','.join('?' * len(ids))})", ids).fetchall(); d = {r["id"]: r for r in rows}
    left = max(10, int(t["seconds"] - (time.time() - t["start"])))
    return render_template("test.html", questions=[d[i] for i in ids], test=t, left=left)

@app.route("/submit-test", methods=["POST"])
@login_required
def submit_test():
    t = session.pop("test", None)
    if not t: return redirect(url_for("dashboard"))
    c, uid, ids = get_db(), session["user_id"], t["ids"]
    rows = c.execute(f"SELECT * FROM questions WHERE id IN ({','.join('?' * len(ids))})", ids).fetchall(); d = {r["id"]: r for r in rows}
    elapsed = max(1, int(time.time() - t["start"])); answers, correct = [], 0
    for i in ids:
        chosen = request.form.get(f"q{i}"); ok = chosen == d[i]["answer"]; correct += ok; answers.append((i, chosen, int(ok)))
    total = len(ids); score = round(correct / total * 100, 2)
    cur = c.execute("INSERT INTO attempts(user_id,category,subject,topic,score,total,correct,time_taken,difficulty,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (uid, t["category"], t["subject"], t["topic"], score, total, correct, elapsed, t["mode"], datetime.now().isoformat()))
    aid = cur.lastrowid
    c.executemany("INSERT INTO attempt_answers(attempt_id,question_id,chosen,is_correct) VALUES(?,?,?,?)", [(aid, *a) for a in answers])
    update_ratings(c, uid, [(d[q]["topic"], d[q]["difficulty"], bool(ok)) for q, _, ok in answers]); c.commit()
    return redirect(url_for("attempt", aid=aid))

@app.route("/attempt/<int:aid>")
@login_required
def attempt(aid):
    c = get_db(); a = c.execute("SELECT * FROM attempts WHERE id=? AND user_id=?", (aid, session["user_id"])).fetchone()
    if not a: abort(404)
    rows = c.execute("SELECT q.*, x.chosen, x.is_correct FROM attempt_answers x JOIN questions q ON q.id=x.question_id WHERE x.attempt_id=? ORDER BY x.id", (aid,)).fetchall()
    by_topic = {}
    for r in rows: s = by_topic.setdefault(r["topic"], [0, 0]); s[0] += r["is_correct"]; s[1] += 1
    return render_template("result.html", a=a, rows=rows, by_topic=by_topic)

@app.route("/performance")
@login_required
def performance():
    c, uid = get_db(), session["user_id"]; stats = topic_stats(c, uid); rt = ratings(c, uid)
    hist = c.execute("SELECT score,created_at,topic FROM attempts WHERE user_id=? ORDER BY id", (uid,)).fetchall()
    return render_template("performance.html", stats=stats, rt=rt, level_name=level_name,
                           topics=[s["topic"] for s in stats], acc=[round(s["acc"] * 100, 1) for s in stats],
                           hist_x=[h["created_at"][5:16].replace("T", " ") for h in hist], hist_y=[h["score"] for h in hist])

@app.route("/mistakes")
@login_required
def mistakes():
    rows = get_db().execute("""SELECT q.*, x.chosen FROM attempt_answers x JOIN attempts t ON t.id=x.attempt_id JOIN questions q ON q.id=x.question_id
        WHERE t.user_id=? AND x.is_correct=0 GROUP BY q.id ORDER BY MAX(x.id) DESC LIMIT 40""", (session["user_id"],)).fetchall()
    return render_template("mistakes.html", rows=rows)

@app.route("/mentor")
@login_required
def mentor():
    c, uid = get_db(), session["user_id"]; stats = topic_stats(c, uid); rt = ratings(c, uid); ready = readiness(c, uid)
    weak = [s for s in stats if s["n"] >= MIN_ANSWERS and s["acc"] < 0.7][:3]
    strong = [s for s in sorted(stats, key=lambda s: -s["acc"]) if s["n"] >= MIN_ANSWERS and s["acc"] >= 0.8][:3]
    tips = []
    if ready["label"] == "Not enough data": tips.append(f"Complete {ready['needed']} more test(s) to unlock your readiness prediction.")
    else: tips.append(f"Readiness: {ready['label']} ({ready['confidence']}% model confidence).")
    tips.append(trend_text(c, uid))
    for s in weak:
        lvl = level_name(rt.get(s["topic"], DEFAULT_RATING)); tips.append(f"{s['topic']}: {s['acc'] * 100:.0f}% accuracy over {s['n']} questions. Practise at {'Easy' if lvl in ('Beginner', 'Intermediate') else 'Medium'} difficulty, then review the explanations.")
    for s in strong: tips.append(f"{s['topic']} is a strength ({s['acc'] * 100:.0f}%). Try Hard difficulty to stay challenged.")
    targets = [w["topic"] for w in weak] or [s["topic"] for s in stats[:2]] or ["Lists", "Percentages"]
    plan = [("Day 1", f"Practise {targets[0]} (Easy, 10 questions)"), ("Day 2", f"Review mistakes, then retry {targets[0]}"),
            ("Day 3", f"Practise {targets[1 % len(targets)]}"), ("Day 4", "One Aptitude test (timed)"),
            ("Day 5", "One Technical test on a new topic"), ("Day 6", "Solve 2 coding problems"), ("Day 7", "Mixed review of this week's mistakes")]
    return render_template("mentor.html", tips=tips, plan=plan, ready=ready)

@app.route("/model")
@login_required
def model_info():
    return render_template("model.html", r=ml.get_model()[1], features=ml.FEATURES)

# ------------------------------------------------------------------ coding
@app.route("/coding/<language>/<topic>")
@login_required
def coding(language, topic):
    if language not in CODING or topic not in CODING[language]: abort(404)
    c = get_db(); done = {r["problem_id"] for r in c.execute("SELECT problem_id FROM coding_submissions WHERE user_id=? AND status='Accepted'", (session["user_id"],))}
    return render_template("coding.html", language=language, topic=topic, problems=problems_for_topic(topic), done=done)

@app.route("/coding/<language>/<topic>/<pid>", methods=["GET", "POST"])
@login_required
def coding_problem(language, topic, pid):
    if language not in CODING or pid not in BY_ID: abort(404)
    p = BY_ID[pid]; result = None; c = get_db(); uid = session["user_id"]; code = ""
    if request.method == "POST":
        code = request.form.get("code", "")
        if language == "Python":
            status, results = judge.run_python(code, p["tests"]); result = dict(status=status, results=results)
            passed = sum(r["passed"] for r in results)
        else:
            result = dict(status="Saved (auto-judge supports Python only)", results=[]); passed = 0
        c.execute("INSERT INTO coding_submissions(user_id,language,topic,problem_id,code,status,passed,total,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                  (uid, language, topic, pid, code, result["status"], passed, len(p["tests"]), datetime.now().isoformat())); c.commit()
    hist = c.execute("SELECT status,passed,total,created_at FROM coding_submissions WHERE user_id=? AND problem_id=? AND language=? ORDER BY id DESC LIMIT 5", (uid, pid, language)).fetchall()
    return render_template("coding_problem.html", p=p, language=language, topic=topic, result=result, hist=hist, code=code)

# ------------------------------------------------------------------ admin
CSV_COLUMNS = ["category", "subject", "topic", "difficulty", "question", "option_a", "option_b", "option_c", "option_d", "answer", "explanation"]

@app.route("/admin")
@admin_required
def admin():
    c = get_db()
    stats = dict(users=c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"], attempts=c.execute("SELECT COUNT(*) n FROM attempts").fetchone()["n"],
                 subs=c.execute("SELECT COUNT(*) n FROM coding_submissions").fetchone()["n"])
    per_cat = c.execute("SELECT category, COUNT(*) n, COUNT(DISTINCT topic) topics FROM questions GROUP BY category").fetchall()
    return render_template("admin.html", stats=stats, per_cat=per_cat, columns=CSV_COLUMNS)

@app.route("/admin/template.csv")
@admin_required
def admin_template():
    out = io.StringIO(); w = csv.writer(out); w.writerow(CSV_COLUMNS)
    w.writerow(["Technical", "Python", "Lists", "Easy", "Which method adds an item to the end of a list?", "append", "insert", "add", "push", "append", "append() adds one item at the end."])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=questions_template.csv"})

@app.route("/admin/import", methods=["POST"])
@admin_required
def admin_import():
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".csv"): flash("Upload a .csv file.", "error"); return redirect(url_for("admin"))
    rows, errors = [], []
    for ln, r in enumerate(csv.DictReader(io.StringIO(f.read().decode("utf-8-sig", errors="replace"))), start=2):
        try:
            opts = [(r.get(k) or "").strip() for k in ("option_a", "option_b", "option_c", "option_d")]; ans = (r.get("answer") or "").strip()
            if len(ans) == 1 and ans.upper() in "ABCD": ans = opts["ABCD".index(ans.upper())]
            row = dict(category=(r.get("category") or "").strip(), subject=(r.get("subject") or "").strip(), topic=(r.get("topic") or "").strip(),
                       difficulty=(r.get("difficulty") or "Medium").strip().title(), question=(r.get("question") or "").strip(), options=opts, answer=ans, explanation=(r.get("explanation") or "").strip())
            if row["category"] not in ("Technical", "Verbal", "Aptitude") or not row["subject"] or not row["topic"] or not row["question"]: raise ValueError("category/subject/topic/question missing or invalid")
            bad = bank.validate([row])
            if bad: raise ValueError(bad[0])
            rows.append(row)
        except Exception as e: errors.append(f"Line {ln}: {e}")
    c = get_db(); added = insert_questions(c, rows); c.commit()
    flash(f"Imported {added} new question(s); {len(rows) - added} duplicate(s) skipped; {len(errors)} error(s).", "success" if not errors else "error")
    for e in errors[:5]: flash(e, "error")
    return redirect(url_for("admin"))

init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
