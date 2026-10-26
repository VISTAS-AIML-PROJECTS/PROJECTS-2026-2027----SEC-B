import os, sys, tempfile, unittest, io, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
_tmp = tempfile.mkdtemp(); os.environ["EDUCOACH_DB"] = os.path.join(_tmp, "t.db"); os.environ["EDUCOACH_SECRET"] = "test-secret"
import app as A, bank, judge, ml
from problems import BY_ID, PROBLEMS

class BankTests(unittest.TestCase):
    def test_all_questions_valid(self): self.assertEqual(bank.validate(bank.build_all()), [])
    def test_no_duplicate_questions(self):
        rows = bank.build_all(); keys = [(r["subject"], r["topic"], r["question"]) for r in rows]; self.assertEqual(len(keys), len(set(keys)))
    def test_every_topic_has_a_question(self):
        have = {(r["subject"], r["topic"]) for r in bank.build_all()}
        want = {(s, t) for s, ts in bank.TECHNICAL.items() for t in ts} | {("Verbal", t) for t in bank.VERBAL} | {("Aptitude", t) for t in bank.APTITUDE}
        self.assertEqual(want - have, set())
    def test_generated_answers_are_correct(self):
        rows = {r["question"]: r for r in bank.generated_for("Percentages")}
        r = next(x for x in rows.values() if x["question"].startswith("What is") and "% of" in x["question"])
        p, n = [float(s) for s in r["question"].replace("What is ", "").replace("?", "").split("% of ")]
        self.assertEqual(float(r["answer"]), n * p / 100)

class JudgeTests(unittest.TestCase):
    def test_accepted(self): self.assertEqual(judge.run_python("a,b=map(int,input().split());print(a+b)", BY_ID["sum2"]["tests"])[0], "Accepted")
    def test_wrong(self): self.assertEqual(judge.run_python("print(0)", BY_ID["sum2"]["tests"])[0], "Wrong Answer")
    def test_runtime_error(self): self.assertEqual(judge.run_python("1/0", BY_ID["sum2"]["tests"])[0], "Runtime Error")
    def test_timeout(self):
        judge.TIME_LIMIT = 1
        try: self.assertEqual(judge.run_python("while True: pass", BY_ID["sum2"]["tests"][:1])[0], "Time Limit Exceeded")
        finally: judge.TIME_LIMIT = 3
    def test_problem_reference_solutions_self_consistent(self):
        for p in PROBLEMS: self.assertTrue(p["tests"] and p["sample_out"].strip() == dict(p["tests"]).get(p["sample_in"], p["sample_out"]).strip(), p["id"])

class MLTests(unittest.TestCase):
    def test_model_quality(self):
        _, r = ml.get_model(); self.assertGreater(r["holdout_accuracy"], 0.6)
    def test_needs_min_tests(self): self.assertIsNone(ml.features_from_attempts([], 0))
    def test_strong_beats_weak(self):
        strong = [dict(score=92, total=10, correct=9, time_taken=250, difficulty="Hard")] * 8
        weak = [dict(score=30, total=10, correct=3, time_taken=900, difficulty="Easy")] * 8
        ls, _, _ = ml.predict(ml.features_from_attempts(strong, 10)); lw, _, _ = ml.predict(ml.features_from_attempts(weak, 4))
        self.assertEqual((ls, lw), ("High", "Low"))

class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        A.app.config.update(DB=os.path.join(_tmp, "app.db"), TESTING=True); A.init_db()
    def setUp(self): self.c = A.app.test_client()
    def tok(self):
        self.c.get("/login")
        with self.c.session_transaction() as s: return s["csrf"]
    def post(self, url, data=None, **kw):
        d = dict(data or {}); d["csrf_token"] = self.tok(); return self.c.post(url, data=d, **kw)
    def register_login(self, email, pw="Passw0rd!"):
        self.post("/register", dict(name="T", email=email, password=pw)); return self.post("/login", dict(email=email, password=pw))

    def test_csrf_required(self): self.assertEqual(self.c.post("/login", data=dict(email="a@b.co", password="x")).status_code, 400)
    def test_password_rules_and_hashing(self):
        r = self.post("/register", dict(name="X", email="weak@x.com", password="short"), follow_redirects=True); self.assertIn(b"Password must be", r.data)
        self.post("/register", dict(name="X", email="hash@x.com", password="Passw0rd!"))
        stored = A.sqlite3.connect(A.app.config["DB"]).execute("SELECT password FROM users WHERE email='hash@x.com'").fetchone()[0]
        self.assertTrue(stored.startswith(("scrypt:", "pbkdf2:"))); self.assertNotIn("Passw0rd!", stored)
    def test_login_required(self): self.assertEqual(self.c.get("/dashboard").status_code, 302)
    def test_bad_login(self):
        r = self.post("/login", dict(email="nobody@x.com", password="Passw0rd!"), follow_redirects=True); self.assertIn(b"Invalid email or password", r.data)

    def test_full_learning_flow(self):
        self.register_login("flow@x.com")
        self.assertEqual(self.c.get("/dashboard").status_code, 200)
        for _ in range(3):
            r = self.post("/start-test", dict(category="Technical", subject="Python", topic="Lists", difficulty="Adaptive")); self.assertEqual(r.status_code, 302)
            page = self.c.get("/test"); self.assertEqual(page.status_code, 200)
            with self.c.session_transaction() as s: ids = s["test"]["ids"]
            self.assertEqual(len(ids), len(set(ids)))  # distinct questions
            self.assertEqual(len(ids), 30)
            db = A.sqlite3.connect(A.app.config["DB"]); ans = {i: db.execute("SELECT answer FROM questions WHERE id=?", (i,)).fetchone()[0] for i in ids}
            form = {f"q{i}": a for i, a in list(ans.items())[:3]}   # answer 3 correctly, leave the rest blank
            r = self.post("/submit-test", form); self.assertEqual(r.status_code, 302)
            self.assertIn(b"Review", self.c.get(r.headers["Location"]).data)
        for url in ("/dashboard", "/performance", "/mentor", "/mistakes", "/model", "/category/Technical", "/category/Coding"):
            self.assertEqual(self.c.get(url).status_code, 200, url)
        db = A.sqlite3.connect(A.app.config["DB"]); self.assertGreater(db.execute("SELECT COUNT(*) FROM ability").fetchone()[0], 0)
        self.assertIn(b"Placement readiness", self.c.get("/dashboard").data)

    def test_adaptive_prefers_matching_difficulty(self):
        self.register_login("adapt@x.com")
        with A.app.app_context():
            c = A.get_db(); uid = c.execute("SELECT id FROM users WHERE email='adapt@x.com'").fetchone()["id"]
            c.execute("INSERT INTO ability VALUES(?,?,?)", (uid, "Percentages", 1500)); c.commit()
            ids, _ = A.select_questions(c, uid, "Aptitude", "Aptitude", "Percentages", "Adaptive", 4)
            diffs = [c.execute("SELECT difficulty FROM questions WHERE id=?", (i,)).fetchone()[0] for i in ids]
        self.assertEqual(diffs.count("Hard"), 4)
    def test_never_more_than_30_questions(self):
        with A.app.app_context():
            c = A.get_db()
            for cat, sub, top in (("Aptitude", "Aptitude", "Percentages"), ("Technical", "DBMS", "SQL"), ("Verbal", "Verbal", "Grammar")):
                ids, _ = A.select_questions(c, 1, cat, sub, top, "Adaptive", 99)
                self.assertLessEqual(len(ids), 30); self.assertEqual(len(ids), len(set(ids)))
    def test_every_topic_gets_exactly_30(self):
        with A.app.app_context():
            c = A.get_db()
            for r in c.execute("SELECT DISTINCT category,subject,topic FROM questions").fetchall():
                ids, _ = A.select_questions(c, 1, r["category"], r["subject"], r["topic"], "Adaptive")
                self.assertEqual(len(ids), 30, (r["subject"], r["topic"]))
    def test_elo_moves_in_right_direction(self):
        with A.app.app_context():
            c = A.get_db(); A.update_ratings(c, 9001, [("T", "Hard", True)]); up = A.ratings(c, 9001)["T"]
            A.update_ratings(c, 9002, [("T", "Easy", False)]); down = A.ratings(c, 9002)["T"]
        self.assertGreater(up, A.DEFAULT_RATING); self.assertLess(down, A.DEFAULT_RATING)

    def test_coding_judge_route(self):
        self.register_login("code@x.com")
        r = self.post("/coding/Python/Basics/sum2", dict(code="a,b=map(int,input().split())\nprint(a+b)")); self.assertIn(b"Accepted", r.data)
        r = self.post("/coding/Java/Basics/sum2", dict(code="class A{}")); self.assertIn(b"Python only", r.data)

    def test_admin_import_and_access(self):
        self.register_login("admin-first@x.com")   # not necessarily first user
        with A.app.app_context():
            c = A.get_db(); c.execute("UPDATE users SET is_admin=1 WHERE email='admin-first@x.com'"); c.commit()
        self.post("/login", dict(email="admin-first@x.com", password="Passw0rd!"))
        csv_data = "category,subject,topic,difficulty,question,option_a,option_b,option_c,option_d,answer,explanation\nTechnical,Python,Lists,Easy,CSV test question?,a,b,c,d,B,because\n"
        d = {"csrf_token": self.tok(), "file": (io.BytesIO(csv_data.encode()), "q.csv")}
        r = self.c.post("/admin/import", data=d, content_type="multipart/form-data", follow_redirects=True); self.assertIn(b"Imported 1 new", r.data)
        db = A.sqlite3.connect(A.app.config["DB"]); self.assertEqual(db.execute("SELECT answer FROM questions WHERE question='CSV test question?'").fetchone()[0], "b")
    def test_non_admin_forbidden(self):
        self.register_login("plain@x.com")
        with A.app.app_context():
            c = A.get_db(); c.execute("UPDATE users SET is_admin=0 WHERE email='plain@x.com'"); c.commit()
        self.post("/login", dict(email="plain@x.com", password="Passw0rd!")); self.assertEqual(self.c.get("/admin").status_code, 403)

if __name__ == "__main__": unittest.main()
