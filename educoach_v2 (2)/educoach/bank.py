"""Builds the full question pool: curated questions + original starter questions + generated aptitude questions."""
import random
from fractions import Fraction
from math import gcd, comb, factorial
from catalog import TECHNICAL, VERBAL, APTITUDE, QUESTION_BANK, GENERIC
from extra_questions import Q as EXTRA

DIFFS = ["Easy", "Medium", "Hard"]

def category_of(subject):
    if subject == "Verbal": return "Verbal"
    if subject == "Aptitude": return "Aptitude"
    return "Technical"

# ---------- option helpers ----------
def fmt(v):
    if isinstance(v, Fraction): return f"{v.numerator}/{v.denominator}" if v.denominator != 1 else str(v.numerator)
    if isinstance(v, float): return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)

def num_opts(ans, rng, suffix="", prefix=""):
    """Correct answer + 3 plausible distinct numeric distractors, shuffled."""
    step = max(1, round(abs(ans) * 0.1)) if float(ans).is_integer() else max(0.5, round(abs(ans) * 0.1, 1))
    cands = [ans + k * step for k in (-3, -2, -1, 1, 2, 3)]
    if ans >= 0: cands = [c for c in cands if c >= 0]
    rng.shuffle(cands)
    out = [ans]
    for c in cands:
        if c not in out: out.append(c)
        if len(out) == 4: break
    k = 4
    while len(out) < 4:
        out.append(ans + k * step); k += 1
    rng.shuffle(out)
    return [f"{prefix}{fmt(x)}{suffix}" for x in out], f"{prefix}{fmt(ans)}{suffix}"

def frac_opts(ans, rng):
    n, d = ans.numerator, ans.denominator
    cands = [Fraction(n + 1, d), Fraction(max(n - 1, 1), d), Fraction(n, d + 1), Fraction(n + 1, d + 2), Fraction(d, n) if n else Fraction(1, 2), Fraction(1, d + 1), Fraction(n + 2, d + 3)]
    out = [ans]
    for c in cands:
        if c != ans and 0 < c <= 1 and c not in out: out.append(c)
        if len(out) == 4: break
    i = 2
    while len(out) < 4:
        f = Fraction(n, d + i)
        if f not in out: out.append(f)
        i += 1
    rng.shuffle(out)
    return [fmt(x) for x in out], fmt(ans)

def ratio_opts(a, b, rng):
    ans = f"{a}:{b}"
    cands = [f"{b}:{a}", f"{a + 1}:{b}", f"{a}:{b + 1}", f"{a * 2 + 1}:{b * 2}", f"{a}:{b * 2 + 1}"]
    out = [ans] + [c for c in dict.fromkeys(cands) if c != ans][:3]
    rng.shuffle(out)
    return out, ans

def reduce(a, b):
    g = gcd(a, b); return a // g, b // g

# ---------- generators: each returns (question, options, answer, explanation) ----------
def g_percentages(d, r):
    if d == 0:
        n = r.choice([120, 150, 200, 250, 300, 360, 400, 500]); p = r.choice([10, 15, 20, 25, 30, 40, 60])
        v = n * p / 100
        o, a = num_opts(v, r); return f"What is {p}% of {n}?", o, a, f"{p}/100 x {n} = {fmt(v)}."
    if d == 1:
        y = r.choice([50, 80, 200, 250, 400, 500]); p = r.choice([10, 20, 25, 40, 60, 75, 80]); x = y * p / 100
        o, a = num_opts(p, r, suffix="%"); return f"{fmt(x)} is what percent of {y}?", o, a, f"({fmt(x)}/{y}) x 100 = {p}%."
    a1 = r.choice([10, 20, 25, 50]); b1 = r.choice([10, 20]); net = a1 - b1 - a1 * b1 / 100
    o, a = num_opts(net, r, suffix="%")
    return f"A price rises by {a1}% and then falls by {b1}%. What is the net change in price?", o, a, f"Net = {a1} - {b1} - ({a1} x {b1})/100 = {fmt(net)}% (positive means increase)."

def g_profit(d, r):
    cp = r.choice([200, 250, 400, 500, 800, 1000]); p = r.choice([10, 20, 25, 40]); sp = cp * (100 + p) // 100
    if cp * (100 + p) % 100: sp = cp * (100 + p) / 100
    if d == 0:
        o, a = num_opts(p, r, suffix="%"); return f"An article bought for {cp} is sold for {fmt(sp)}. Profit percentage?", o, a, f"Profit = {fmt(sp - cp)}; ({fmt(sp - cp)}/{cp}) x 100 = {p}%."
    if d == 1:
        o, a = num_opts(sp, r); return f"The cost price is {cp} and the profit is {p}%. What is the selling price?", o, a, f"SP = {cp} x (100+{p})/100 = {fmt(sp)}."
    o, a = num_opts(cp, r); return f"After a {p}% profit an item sells for {fmt(sp)}. What was the cost price?", o, a, f"CP = SP x 100/(100+{p}) = {cp}."

def g_si(d, r):
    P = r.choice([1000, 2000, 4000, 5000]); R = r.choice([5, 8, 10, 12]); T = r.choice([2, 3, 4]); si = P * R * T // 100
    if d == 0:
        o, a = num_opts(si, r); return f"Find the simple interest on {P} at {R}% per annum for {T} years.", o, a, f"SI = PRT/100 = {P} x {R} x {T}/100 = {si}."
    if d == 1:
        o, a = num_opts(R, r, suffix="%"); return f"A sum of {P} earns simple interest {si} in {T} years. What is the annual rate?", o, a, f"R = SI x 100/(P x T) = {R}%."
    o, a = num_opts(P + si, r); return f"What is the total amount on {P} after {T} years at {R}% simple interest?", o, a, f"Amount = P + SI = {P} + {si} = {P + si}."

def g_ci(d, r):
    while True:
        P = r.choice([4000, 8000, 10000, 20000]); R = r.choice([5, 10, 20]); ci = P * ((100 + R) ** 2 - 10000) / 10000
        if float(ci).is_integer(): ci = int(ci); break
    if d == 0:
        o, a = num_opts(ci, r); return f"Compound interest on {P} for 2 years at {R}% p.a. (compounded yearly)?", o, a, f"A = {P} x (1+{R}/100)^2 = {P + ci}; CI = A - P = {ci}."
    if d == 1:
        o, a = num_opts(P + ci, r); return f"Amount of {P} after 2 years at {R}% compound interest?", o, a, f"A = P(1+R/100)^2 = {P + ci}."
    diff = P * R * R / 10000
    if not float(diff).is_integer(): diff = P * R * R // 10000
    o, a = num_opts(int(diff), r); return f"Find the difference between CI and SI on {P} for 2 years at {R}% p.a.", o, a, f"Difference = P(R/100)^2 = {int(diff)}."

def g_avg(d, r):
    if d == 0:
        nums = [r.randint(5, 60) for _ in range(5)]; nums[-1] += (5 - sum(nums) % 5) % 5; v = sum(nums) // 5
        o, a = num_opts(v, r); return f"Find the average of {', '.join(map(str, nums))}.", o, a, f"Sum = {sum(nums)}; average = {sum(nums)}/5 = {v}."
    if d == 1:
        a5 = r.randint(20, 50); b6 = a5 + r.randint(1, 5); six = 6 * b6 - 5 * a5
        o, a = num_opts(six, r); return f"The average of 5 numbers is {a5}. When a sixth number is added the average becomes {b6}. What is the sixth number?", o, a, f"6 x {b6} - 5 x {a5} = {six}."
    n = r.choice([19, 24, 29, 34]); avg = r.randint(14, 18); k = r.choice([1, 2]); t = avg + k * (n + 1)
    o, a = num_opts(t, r); return f"The average age of {n} students is {avg}. Including the teacher the average rises by {k}. Find the teacher's age.", o, a, f"Teacher = {avg} + {k} x ({n}+1) = {t}."

def g_ratio(d, r):
    if d == 0:
        a, b = r.choice([(2, 3), (3, 5), (4, 5), (3, 7), (5, 7)]); N = (a + b) * r.choice([10, 20, 30, 40]); big = N * max(a, b) // (a + b)
        o, ans = num_opts(big, r); return f"Divide {N} in the ratio {a}:{b}. What is the larger share?", o, ans, f"Larger part = {N} x {max(a, b)}/{a + b} = {big}."
    if d == 1:
        a, b, c = r.choice([2, 3, 4]), r.choice([3, 5, 6]), r.choice([5, 7, 8])
        x, y = reduce(a * b, b * c)
        o, ans = ratio_opts(x, y, r); return f"If A:B = {a}:{b} and B:C = {b}:{c}, find A:C.", o, ans, f"A:C = ({a} x {b}) : ({b} x {c}) = {x}:{y} after simplification."
    a, b = r.choice([(3, 5), (4, 7), (5, 9), (2, 7)]); S = (a + b) * r.choice([6, 8, 9, 12]); diff = S * abs(b - a) // (a + b)
    o, ans = num_opts(diff, r); return f"Two numbers are in the ratio {a}:{b} and their sum is {S}. What is their difference?", o, ans, f"Difference = {S} x {abs(b - a)}/{a + b} = {diff}."

def g_work(d, r):
    pairs = [(12, 24, 8), (10, 15, 6), (20, 30, 12), (6, 12, 4), (15, 30, 10), (30, 60, 20), (12, 12, 6)]
    a, b, t = r.choice(pairs)
    if d == 0:
        o, ans = num_opts(t, r, suffix=" days"); return f"A can finish a job in {a} days and B in {b} days. Working together, how long will they take?", o, ans, f"1/{a} + 1/{b} = 1/{t}, so {t} days."
    if d == 1:
        o, ans = num_opts(b, r, suffix=" days"); return f"A alone takes {a} days. A and B together take {t} days. How long would B take alone?", o, ans, f"1/B = 1/{t} - 1/{a} = 1/{b}, so {b} days."
    k = r.choice([2, 3, 4]); done = Fraction(k, t); rem = 1 - done
    if rem <= 0: k, done = 2, Fraction(2, t); rem = 1 - done
    o, ans = frac_opts(rem, r); return f"A and B ({a} and {b} days alone) work together for {k} days. What fraction of the work is left?", o, ans, f"Work done = {k}/{t}; left = 1 - {fmt(done)} = {fmt(rem)}."

def g_speed(d, r):
    if d == 0:
        s = r.choice([40, 45, 50, 60, 72]); t = r.choice([2, 3, 4, 5]); o, a = num_opts(s * t, r, suffix=" km")
        return f"A car travels at {s} km/h for {t} hours. How far does it go?", o, a, f"Distance = speed x time = {s * t} km."
    if d == 1:
        s = r.choice([36, 54, 72, 90, 108]); v = s * 5 // 18; o, a = num_opts(v, r, suffix=" m/s")
        return f"Convert {s} km/h to m/s.", o, a, f"Multiply by 5/18: {s} x 5/18 = {v} m/s."
    s1, s2, v = r.choice([(40, 60, 48), (30, 60, 40), (60, 90, 72), (20, 30, 24), (50, 75, 60)])
    o, a = num_opts(v, r, suffix=" km/h"); return f"A man covers equal distances at {s1} km/h and {s2} km/h. What is his average speed?", o, a, f"Average speed = 2ab/(a+b) = {v} km/h."

def g_lcm(d, r):
    g = r.choice([2, 3, 4, 5, 6, 7]); x, y = r.choice([(2, 3), (3, 4), (3, 5), (4, 5), (2, 5), (5, 7)]); a, b = g * x, g * y
    if d == 0:
        o, ans = num_opts(g, r); return f"Find the HCF of {a} and {b}.", o, ans, f"Both numbers are multiples of {g} and {x}, {y} are co-prime, so HCF = {g}."
    if d == 1:
        l = g * x * y; o, ans = num_opts(l, r); return f"Find the LCM of {a} and {b}.", o, ans, f"LCM = {g} x {x} x {y} = {l}."
    l = g * x * y; o, ans = num_opts(b, r); return f"The HCF of two numbers is {g} and their LCM is {l}. One number is {a}. Find the other.", o, ans, f"Other = (HCF x LCM)/{a} = {b}."

def g_series(d, r):
    if d == 0:
        a, df = r.randint(2, 15), r.randint(2, 9); t = [a + i * df for i in range(5)]; nxt = a + 5 * df
        o, ans = num_opts(nxt, r); return f"Find the next term: {', '.join(map(str, t))}, ?", o, ans, f"Common difference {df}, so next = {nxt}."
    if d == 1:
        a, q = r.randint(1, 4), r.choice([2, 3]); t = [a * q ** i for i in range(5)]; nxt = a * q ** 5
        o, ans = num_opts(nxt, r); return f"Find the next term: {', '.join(map(str, t))}, ?", o, ans, f"Each term is multiplied by {q}, so next = {nxt}."
    a, df = r.randint(1, 8), r.randint(1, 4); t = [a]; inc = df
    for _ in range(4): t.append(t[-1] + inc); inc += 2
    nxt = t[-1] + inc; o, ans = num_opts(nxt, r); return f"Find the next term: {', '.join(map(str, t))}, ?", o, ans, f"Differences grow by 2 ({df}, {df + 2}, ...), so the next difference is {inc} and the term is {nxt}."

def g_ages(d, r):
    if d == 0:
        b = r.randint(10, 30); df = r.randint(3, 12); k = r.randint(3, 8); o, a = num_opts(b + df + k, r)
        return f"A is {df} years older than B. B is {b} now. What will A's age be after {k} years?", o, a, f"A now = {b + df}; after {k} years = {b + df + k}."
    if d == 1:
        s = r.randint(8, 20); m = r.choice([3, 4, 5]); S = s * (m + 1); o, a = num_opts(s, r)
        return f"A father is {m} times as old as his son. The sum of their ages is {S}. How old is the son?", o, a, f"Son = {S}/({m}+1) = {s}."
    s = r.randint(10, 20); S = 4 * s - 10; o, a = num_opts(s, r)
    return f"Five years ago a father was 3 times as old as his son. Now the sum of their ages is {S}. Find the son's present age.", o, a, f"Let son = x: father = 3x - 10, so 4x - 10 = {S} and x = {s}."

def g_algebra(d, r):
    if d == 0:
        x = r.randint(2, 15); a = r.randint(2, 7); b = r.randint(1, 15); c = a * x + b; o, ans = num_opts(x, r)
        return f"Solve for x: {a}x + {b} = {c}.", o, ans, f"x = ({c} - {b})/{a} = {x}."
    if d == 1:
        p, q = r.sample(range(1, 9), 2); big = max(p, q); o, ans = num_opts(big, r)
        return f"Find the larger root of x^2 - {p + q}x + {p * q} = 0.", o, ans, f"The equation factors as (x-{p})(x-{q}) = 0, so the roots are {p} and {q}."
    x, y = r.sample(range(2, 15), 2); o, ans = num_opts(x * y, r)
    return f"If x + y = {x + y} and x - y = {x - y}, find xy.", o, ans, f"Adding gives x = {x}, so y = {y} and xy = {x * y}."

def g_mens(d, r):
    if d == 0:
        l, b = r.randint(5, 20), r.randint(3, 12); o, a = num_opts(l * b, r)
        return f"Area of a rectangle of length {l} and breadth {b}?", o, a, f"Area = {l} x {b} = {l * b}."
    if d == 1:
        rad = r.choice([7, 14, 21]); v = 22 * rad * rad // 7; o, a = num_opts(v, r)
        return f"Area of a circle of radius {rad} (use pi = 22/7)?", o, a, f"Area = 22/7 x {rad}^2 = {v}."
    rad = 7; h = r.choice([4, 5, 6, 10]); v = 22 * rad * rad * h // 7; o, a = num_opts(v, r)
    return f"Volume of a cylinder with radius {rad} and height {h} (pi = 22/7)?", o, a, f"V = pi r^2 h = 22/7 x 49 x {h} = {v}."

def g_prob(d, r):
    if d == 0:
        red, blue = r.randint(2, 8), r.randint(2, 8); f = Fraction(red, red + blue); o, a = frac_opts(f, r)
        return f"A bag has {red} red and {blue} blue balls. Probability of drawing a red ball?", o, a, f"{red}/{red + blue} = {fmt(f)}."
    if d == 1:
        k = r.randint(1, 4); f = Fraction(6 - k, 6); o, a = frac_opts(f, r)
        return f"A fair die is rolled. Probability that the number is greater than {k}?", o, a, f"Favourable outcomes: {6 - k} out of 6 = {fmt(f)}."
    s = r.randint(4, 10); ways = sum(1 for i in range(1, 7) for j in range(1, 7) if i + j == s); f = Fraction(ways, 36); o, a = frac_opts(f, r)
    return f"Two dice are rolled. Probability that the sum is {s}?", o, a, f"There are {ways} favourable outcomes out of 36 = {fmt(f)}."

def g_pnc(d, r):
    if d == 0:
        n = r.randint(5, 9); k = r.randint(2, 3); v = comb(n, k); o, a = num_opts(v, r)
        return f"Find the value of {n}C{k}.", o, a, f"{n}C{k} = {v}."
    if d == 1:
        w = r.choice(["PLANET", "FLOWER", "BRIGHT", "MASTER"]); n = len(set(w)); v = factorial(n) if n == len(w) else None
        if v is None: w = "PLANET"; v = 720
        o, a = num_opts(v, r); return f"In how many ways can the letters of the word {w} be arranged?", o, a, f"All {len(w)} letters are distinct: {len(w)}! = {v}."
    n, m = r.randint(5, 7), r.randint(4, 6); a_, b_ = 3, 2; v = comb(n, a_) * comb(m, b_); o, a = num_opts(v, r)
    return f"A committee of {a_ + b_} is formed from {n} men and {m} women with exactly {b_} women. In how many ways?", o, a, f"{n}C{a_} x {m}C{b_} = {v}."

GENERATORS = {
    "Percentages": g_percentages, "Profit & Loss": g_profit, "Simple Interest": g_si, "Compound Interest": g_ci,
    "Averages": g_avg, "Ratio & Proportion": g_ratio, "Time & Work": g_work, "Time, Speed & Distance": g_speed,
    "LCM & HCF": g_lcm, "Number Series": g_series, "Problems on Ages": g_ages, "Algebra": g_algebra,
    "Mensuration": g_mens, "Probability": g_prob, "Permutation & Combination": g_pnc,
}

def generated_for(topic, per_level=4):
    rng = random.Random(f"edu-{topic}"); gen = GENERATORS[topic]; seen = set(); rows = []
    for d, diff in enumerate(DIFFS):
        tries = 0
        while sum(1 for x in rows if x["difficulty"] == diff) < per_level and tries < 200:
            tries += 1
            q, opts, ans, exp = gen(d, rng)
            if q in seen or len(set(opts)) != 4: continue
            seen.add(q); rows.append(dict(category="Aptitude", subject="Aptitude", topic=topic, difficulty=diff, question=q, options=opts, answer=ans, explanation=exp))
    return rows

def build_all():
    """Return every question as a dict (idempotent seed data)."""
    rows = []
    def base(topic):
        return QUESTION_BANK.get(topic) or GENERIC.get(topic)
    # original one-per-topic starter questions (Easy)
    for subject, topics in TECHNICAL.items():
        for t in topics:
            b = base(t)
            if b: rows.append(dict(category="Technical", subject=subject, topic=t, difficulty="Easy", question=b[0], options=list(b[1]), answer=b[2], explanation=f"Correct answer: {b[2]}."))
    for t in VERBAL:
        b = base(t)
        if b: rows.append(dict(category="Verbal", subject="Verbal", topic=t, difficulty="Easy", question=b[0], options=list(b[1]), answer=b[2], explanation=f"Correct answer: {b[2]}."))
    for t in APTITUDE:
        if t in GENERATORS: rows.extend(generated_for(t))
        else:
            b = base(t)
            if b: rows.append(dict(category="Aptitude", subject="Aptitude", topic=t, difficulty="Easy", question=b[0], options=list(b[1]), answer=b[2], explanation=f"Correct answer: {b[2]}."))
    for subject, topic, diff, q, opts, ans, exp in EXTRA:
        rows.append(dict(category=category_of(subject), subject=subject, topic=topic, difficulty=diff, question=q, options=list(opts), answer=ans, explanation=exp))
    # shuffle option order deterministically so the answer position varies
    for i, r in enumerate(rows):
        random.Random(f"{r['topic']}-{r['question']}").shuffle(r["options"])
    return rows

def validate(rows):
    """Return a list of problems found in a question list (used by tests and CSV import)."""
    errs = []
    for r in rows:
        if len(r["options"]) != 4 or len(set(r["options"])) != 4: errs.append(f"4 distinct options required: {r['question'][:50]}")
        if r["answer"] not in r["options"]: errs.append(f"answer not in options: {r['question'][:50]}")
        if r["difficulty"] not in DIFFS: errs.append(f"bad difficulty: {r['question'][:50]}")
    return errs
