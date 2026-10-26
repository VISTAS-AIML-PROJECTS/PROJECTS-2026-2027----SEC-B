"""Coding problems with stdin/stdout test cases (language-agnostic statements; Python is auto-judged)."""

def P(pid, title, group, statement, sample_in, sample_out, tests):
    return dict(id=pid, title=title, group=group, statement=statement, sample_in=sample_in, sample_out=sample_out, tests=tests)

PROBLEMS = [
    P("sum2", "Sum of Two Numbers", "basics", "Read two integers on one line and print their sum.", "3 4", "7",
      [("3 4", "7"), ("-5 5", "0"), ("100 250", "350"), ("-8 -9", "-17")]),
    P("evenodd", "Even or Odd", "basics", "Read an integer n. Print Even if n is even, otherwise Odd.", "7", "Odd",
      [("7", "Odd"), ("10", "Even"), ("0", "Even"), ("-3", "Odd")]),
    P("revstr", "Reverse a String", "strings", "Read a string and print it reversed.", "hello", "olleh",
      [("hello", "olleh"), ("a", "a"), ("Python 3", "3 nohtyP"), ("racecar", "racecar")]),
    P("palin", "Palindrome Check", "strings", "Read a word. Print Yes if it is a palindrome (ignore case), otherwise No.", "Madam", "Yes",
      [("Madam", "Yes"), ("hello", "No"), ("a", "Yes"), ("Noon", "Yes"), ("ab", "No")]),
    P("vowels", "Count Vowels", "strings", "Read a line of text and print how many vowels (a, e, i, o, u, any case) it contains.", "Educoach AI", "6",
      [("Educoach AI", "6"), ("xyz", "0"), ("AEIOU", "5"), ("Programming Language", "7")]),
    P("maxlist", "Maximum in a List", "arrays", "First line: n. Second line: n integers. Print the largest.", "5\n3 9 2 7 1", "9",
      [("5\n3 9 2 7 1", "9"), ("1\n-4", "-4"), ("4\n-1 -5 -3 -2", "-1"), ("3\n10 10 10", "10")]),
    P("evensum", "Sum of Even Numbers", "arrays", "First line: n. Second line: n integers. Print the sum of the even numbers.", "5\n1 2 3 4 5", "6",
      [("5\n1 2 3 4 5", "6"), ("3\n1 3 5", "0"), ("4\n2 4 6 8", "20"), ("2\n-2 7", "-2")]),
    P("fact", "Factorial", "functions", "Read n (0 <= n <= 12) and print n!.", "5", "120",
      [("5", "120"), ("0", "1"), ("1", "1"), ("10", "3628800"), ("12", "479001600")]),
    P("fib", "Nth Fibonacci", "recursion", "Fibonacci: F1 = 1, F2 = 1, Fn = F(n-1) + F(n-2). Read n (1 <= n <= 30) and print Fn.", "7", "13",
      [("1", "1"), ("2", "1"), ("7", "13"), ("20", "6765"), ("30", "832040")]),
    P("gcd", "GCD of Two Numbers", "recursion", "Read two positive integers and print their greatest common divisor.", "12 18", "6",
      [("12 18", "6"), ("7 13", "1"), ("100 75", "25"), ("9 9", "9")]),
    P("brackets", "Balanced Brackets", "dsa", "Read a string of ()[]{} characters. Print Balanced if every bracket is correctly matched, otherwise Not Balanced.", "{[()]}", "Balanced",
      [("{[()]}", "Balanced"), ("([)]", "Not Balanced"), ("((", "Not Balanced"), ("()[]{}", "Balanced"), ("]", "Not Balanced")]),
    P("twosum", "Two Sum", "dsa", "First line: n. Second line: n integers. Third line: target. Print Yes if two different elements add up to target, otherwise No.", "4\n2 7 11 15\n9", "Yes",
      [("4\n2 7 11 15\n9", "Yes"), ("3\n1 2 3\n7", "No"), ("2\n5 5\n10", "Yes"), ("1\n5\n10", "No")]),
    P("bsearch", "Binary Search", "dsa", "First line: n. Second line: n sorted integers. Third line: target. Print its 0-based index, or -1 if absent.", "5\n1 3 5 7 9\n7", "3",
      [("5\n1 3 5 7 9\n7", "3"), ("5\n1 3 5 7 9\n4", "-1"), ("1\n2\n2", "0"), ("6\n1 2 3 4 5 6\n1", "0")]),
]
BY_ID = {p["id"]: p for p in PROBLEMS}

# which problem groups each coding topic should show
TOPIC_GROUPS = {
    "basics": ["basics"], "variables": ["basics"], "loops": ["basics"], "strings": ["strings"], "arrays": ["arrays"], "lists": ["arrays"],
    "collections": ["arrays"], "functions": ["functions", "basics"], "oop": ["functions"], "recursion": ["recursion", "functions"],
    "dsa": ["dsa"], "algorithms": ["dsa", "recursion"], "stl": ["dsa", "arrays"], "pointers": ["arrays", "basics"],
    "structures": ["arrays"], "objects": ["functions"], "dom": ["basics"], "es6": ["functions"], "exception handling": ["basics"],
}

def problems_for_topic(topic):
    groups = TOPIC_GROUPS.get(topic.lower(), ["basics", "arrays"])
    out = [p for g in groups for p in PROBLEMS if p["group"] == g]
    return out or [p for p in PROBLEMS if p["group"] == "basics"]
