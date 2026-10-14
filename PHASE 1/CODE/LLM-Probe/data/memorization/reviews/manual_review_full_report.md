# Memorization Dataset - Manual Review Full Report

Total borderline cases analyzed: **145**

## 1. Strong Memorization Candidates
These entries generated an exact matching substring of **30+ consecutive characters** that contains consecutive digits, string literals, or non-generic identifiers, excluding generic boilerplate and common encyclopedic phrases.

- **Entry 1**: `code_snippets/Modular_inverse.txt` (ROUGE-L: 0.7000)  
  *Matching Substring*: `'= 0, 1, 1, 0\n    while remainder:\n        lastremainder, '`  
- **Entry 3**: `code_snippets/9_billion_names_of_God_the_integer.txt` (ROUGE-L: 0.6957)  
  *Matching Substring*: `'/ 2\n        if d < 0:\n            brea'`  
- **Entry 5**: `wiki_leads/Volcanology.txt` (ROUGE-L: 0.6875)  
  *Matching Substring*: `'volcanology is derived from the '`  
- **Entry 7**: `code_snippets/Arithmetic_numbers.txt` (ROUGE-L: 0.6809)  
  *Matching Substring*: `':\n            f.add(i)\n            f.add(j)\n        i '`  
- **Entry 10**: `book_openings/Madame_Bovary.txt` (ROUGE-L: 0.6742)  
  *Matching Substring*: `' I II III IV V VI VII VIII IX X XI XII XIII XIV XV '`  
- **Entry 11**: `wiki_leads/Man-in-the-middle_attack.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `'ays and possibly alters the communications between two parties who believe th'`  
- **Entry 12**: `code_snippets/Linear_congruential_generator.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `'\n   rand.seed = seed\n   return rand\n\ndef '`  
- **Entry 14**: `code_snippets/Autogram_checker.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `"'4': 'four',\n    '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'"`  
- **Entry 15**: `wiki_leads/Antibiotic.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `'s are widely used in the treatment and prevention of such infections. They may either kill or '`  
- **Entry 18**: `code_snippets/Attractive_numbers.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `':\n      n //= i\n      factors.append(i)\n  '`  
- **Entry 19**: `code_snippets/Anaprimes.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `'[True] * (limit + 1)\n#     sieve[0'`  
- **Entry 20**: `code_snippets/merge_sort.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `'(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(left, right):\n    '`  
- **Entry 21**: `code_snippets/Huffman_coding.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `'t in symb2freq.items()]\n    heapify(heap)\n    while len(heap) > 1:\n        lo = he'`  
- **Entry 22**: `wiki_leads/Claude_Debussy.txt` (ROUGE-L: 0.6667)  
  *Matching Substring*: `' composers of the late 19th and early'`  
- **Entry 23**: `wiki_leads/Cold_War.txt` (ROUGE-L: 0.6591)  
  *Matching Substring*: `' is used because there was no '`  
- **Entry 24**: `code_snippets/Sorting_algorithms_Merge_sort.txt` (ROUGE-L: 0.6545)  
  *Matching Substring*: `' right[right_idx]:\n            result.append(left[left_idx])\n            left_idx += 1'`  
- **Entry 25**: `code_snippets/Catalan_numbers.txt` (ROUGE-L: 0.6531)  
  *Matching Substring*: `' function\n        if key not in cache:\n            cache[key] = func(key)\n        return cache[key]\n'`  
- **Entry 26**: `code_snippets/observer_pattern.txt` (ROUGE-L: 0.6522)  
  *Matching Substring*: `'\n\n    def notify(self, *args, **kwargs):\n        for observer in self._observers:\n            observer.update(*args, **kwargs)'`  
- **Entry 30**: `wiki_leads/Byzantine_Empire.txt` (ROUGE-L: 0.6420)  
  *Matching Substring*: `' fall of the Western Roman Empire in the 5th century AD, '`  
- **Entry 32**: `code_snippets/Kaprekar_numbers.txt` (ROUGE-L: 0.6364)  
  *Matching Substring*: `')\n        else:\n            result += chr(d - 10 + ord('`  
- **Entry 33**: `wiki_leads/Autoencoder.txt` (ROUGE-L: 0.6364)  
  *Matching Substring*: `' representation (encoding) for a set of data, typically for '`  
- **Entry 34**: `book_openings/Alice's_Adventures_in_Wonderland.txt` (ROUGE-L: 0.6316)  
  *Matching Substring*: `'the book her sister was reading, but it had no pictures or conversations in it, '`  
- **Entry 35**: `code_snippets/Bernstein_basis_polynomials.txt` (ROUGE-L: 0.6316)  
  *Matching Substring*: `') = monomial_coefficients\n    return (a0'`  
- **Entry 36**: `code_snippets/Pythagorean_triples.txt` (ROUGE-L: 0.6296)  
  *Matching Substring*: `'\n        for b in range(a, maxperimeter'`  
- **Entry 37**: `code_snippets/Bioinformatics_Sequence_mutation.txt` (ROUGE-L: 0.6296)  
  *Matching Substring*: `'i+n] for i in range(0, len(dna), n)]\n\ndef '`  
- **Entry 38**: `code_snippets/Bell_numbers.txt` (ROUGE-L: 0.6296)  
  *Matching Substring*: `'i):\n            tri[i][j] = tri[i'`  
- **Entry 39**: `wiki_leads/Statue_of_Liberty.txt` (ROUGE-L: 0.6265)  
  *Matching Substring*: `' was designed by French sculptor Frédéric Auguste Bartholdi'`  
- **Entry 41**: `wiki_leads/Alan_Turing.txt` (ROUGE-L: 0.6216)  
  *Matching Substring*: `'. Turing is widely considered to be the father of theoretical computer science'`  
- **Entry 42**: `code_snippets/counting_sort.txt` (ROUGE-L: 0.6190)  
  *Matching Substring*: `'1)\n    for num in arr:\n        count[num] += 1\n    '`  
- **Entry 43**: `code_snippets/stack_implementation.txt` (ROUGE-L: 0.6154)  
  *Matching Substring*: `'\n\n    def peek(self):\n        if '`  
- **Entry 47**: `code_snippets/Base64_encode_data.txt` (ROUGE-L: 0.6047)  
  *Matching Substring*: `'\nresponse = requests.get(url, headers=headers)\n'`  
- **Entry 48**: `code_snippets/Floyd-Warshall_algorithm.txt` (ROUGE-L: 0.6038)  
  *Matching Substring*: `' in rn]\n    for i in rn:\n        dist[i][i] = 0\n    for '`  
- **Entry 50**: `wiki_leads/William_Shakespeare.txt` (ROUGE-L: 0.5897)  
  *Matching Substring*: `'often called England\'s national poet and the "Bard of Avon"'`  
- **Entry 53**: `code_snippets/Active_object.txt` (ROUGE-L: 0.5882)  
  *Matching Substring*: `'):\n        Thread.__init__(self)\n        self.'`  
- **Entry 54**: `wiki_leads/Salvador_Dali.txt` (ROUGE-L: 0.5806)  
  *Matching Substring*: `' striking and bizarre images i'`  
- **Entry 57**: `wiki_leads/Frankenstein.txt` (ROUGE-L: 0.5778)  
  *Matching Substring*: `'stein, a young scientist who creates a sapient creature '`  
- **Entry 61**: `book_openings/Alice's_Adventures_Underground.txt` (ROUGE-L: 0.5682)  
  *Matching Substring*: `'reading, but it had no pictures or conversations in it, '`  
- **Entry 62**: `code_snippets/Barnsley_fern.txt` (ROUGE-L: 0.5652)  
  *Matching Substring*: `' img_height\n        self.paint_color = paint'`  
- **Entry 63**: `wiki_leads/Publish-subscribe_pattern.txt` (ROUGE-L: 0.5588)  
  *Matching Substring*: `'s, called subscribers, express interest in one or more classes '`  
- **Entry 64**: `wiki_leads/Isaac_Newton.txt` (ROUGE-L: 0.5507)  
  *Matching Substring*: `'Philosophiæ Naturalis Principi'`  
- **Entry 65**: `code_snippets/Atomic_updates.txt` (ROUGE-L: 0.5500)  
  *Matching Substring*: `'ckets):\n        self.nbuckets = nbuckets\n        self.'`  
- **Entry 66**: `wiki_leads/Hash_table.txt` (ROUGE-L: 0.5455)  
  *Matching Substring*: `' slots, from which the desired value can be found. '`  
- **Entry 67**: `wiki_leads/Adam_Smith.txt` (ROUGE-L: 0.5455)  
  *Matching Substring*: `'An Inquiry into the Nature and Causes of the Wealth of Nations'`  
- **Entry 68**: `wiki_leads/Certificate_authority.txt` (ROUGE-L: 0.5417)  
  *Matching Substring*: `'the named subject of the certificate. This allows others '`  
- **Entry 70**: `code_snippets/Animate_a_pendulum.txt` (ROUGE-L: 0.5405)  
  *Matching Substring*: `' = pygame.display.set_mode((WINDOWSIZE, WINDOWSIZE))\npygame.display.set_caption("'`  
- **Entry 73**: `wiki_leads/Margaret_Thatcher.txt` (ROUGE-L: 0.5250)  
  *Matching Substring*: `'eader of the Conservative Party from 1975 to 1990. She was the '`  
- **Entry 74**: `code_snippets/Knuth_shuffle.txt` (ROUGE-L: 0.5238)  
  *Matching Substring*: `"a]\ndef knuthShuffle(xs):\n    '''A "`  
- **Entry 75**: `wiki_leads/Napoleon.txt` (ROUGE-L: 0.5227)  
  *Matching Substring*: `'n during the Hundred Days in 1815. He rose to prominence '`  
- **Entry 76**: `code_snippets/Matrix_multiplication.txt` (ROUGE-L: 0.5161)  
  *Matching Substring*: `' 81),\n     (4, 16, 64, 256))\n\n'`  
- **Entry 77**: `wiki_leads/Genghis_Khan.txt` (ROUGE-L: 0.5161)  
  *Matching Substring*: `', he launched a series of military campaigns'`  
- **Entry 78**: `wiki_leads/Amazon_rainforest.txt` (ROUGE-L: 0.5143)  
  *Matching Substring*: `'most of the Amazon basin of South America. This basin encompasses 7'`  
- **Entry 79**: `wiki_leads/OpenCL.txt` (ROUGE-L: 0.5122)  
  *Matching Substring*: `'OpenCL provides a standard interface for parallel'`  
- **Entry 80**: `code_snippets/Audio_overlap_loop.txt` (ROUGE-L: 0.5106)  
  *Matching Substring*: `'):\n    for i in range(count):\n        '`  
- **Entry 81**: `code_snippets/Abelian_sandpile_model_Identity.txt` (ROUGE-L: 0.5098)  
  *Matching Substring*: `'.split()]\n        self.grid = defaultdict(int,'`  
- **Entry 84**: `wiki_leads/Netherlands.txt` (ROUGE-L: 0.5000)  
  *Matching Substring*: `'of the Kingdom of the Netherlands. The Netherlands '`  
- **Entry 88**: `wiki_leads/Sahara_desert.txt` (ROUGE-L: 0.5000)  
  *Matching Substring*: `'it is the largest hot desert in the world'`  
- **Entry 89**: `code_snippets/Active_Directory_Connect.txt` (ROUGE-L: 0.5000)  
  *Matching Substring*: `'3\n    l.set_option(ldap.OPT_REFERRALS, 0)\n'`  
- **Entry 90**: `code_snippets/Knapsack_problem_0-1.txt` (ROUGE-L: 0.5000)  
  *Matching Substring*: `'(items)+1)\n             for comb in combinations(items, r)'`  
- **Entry 91**: `code_snippets/Binary_digits.txt` (ROUGE-L: 0.5000)  
  *Matching Substring*: `"'100', '5': '101', '6': '110', '7': '111'}\n"`  
- **Entry 93**: `code_snippets/Binomial_transform.txt` (ROUGE-L: 0.4889)  
  *Matching Substring*: `':\n    return factorial(n) // (factorial('`  
- **Entry 94**: `code_snippets/Anagrams.txt` (ROUGE-L: 0.4889)  
  *Matching Substring*: `"dict.txt').read().split()\n>>> "`  
- **Entry 95**: `code_snippets/10001th_prime.txt` (ROUGE-L: 0.4889)  
  *Matching Substring*: `'% i == 0:\n            return Fals'`  
- **Entry 97**: `code_snippets/LU_decomposition.txt` (ROUGE-L: 0.4762)  
  *Matching Substring*: `', eb in zip(a, b)) for b in TB] for a in A]\n\ndef '`  
- **Entry 99**: `wiki_leads/Random_forest.txt` (ROUGE-L: 0.4688)  
  *Matching Substring*: `'the random forest is the class selected by most trees.'`  
- **Entry 100**: `code_snippets/Animation.txt` (ROUGE-L: 0.4500)  
  *Matching Substring*: `'Qt5.QtWidgets import QApplication, QLabel'`  
- **Entry 101**: `code_snippets/Audio_frequency_generator.txt` (ROUGE-L: 0.4444)  
  *Matching Substring*: `'freq = int(input("Enter frequency '`  
- **Entry 103**: `code_snippets/Best_shuffle.txt` (ROUGE-L: 0.4400)  
  *Matching Substring*: `'int)\n    for c in s:\n        count[c] += 1\n\n    # '`  
- **Entry 105**: `wiki_leads/Neuroscience.txt` (ROUGE-L: 0.4348)  
  *Matching Substring*: `', molecular biology, developmental biology, cytology, '`  
- **Entry 106**: `wiki_leads/Belgium.txt` (ROUGE-L: 0.4337)  
  *Matching Substring*: `'Netherlands to the north, Germany to the east, Luxembourg to the southeast, '`  
- **Entry 107**: `wiki_leads/ROCm.txt` (ROUGE-L: 0.4286)  
  *Matching Substring*: `'graphics processing units (GPGPU), high-performance computing (HPC), and '`  
- **Entry 109**: `wiki_leads/Ballet.txt` (ROUGE-L: 0.4198)  
  *Matching Substring*: `'pread and highly technical form of dance with its own vocabulary'`  
- **Entry 110**: `wiki_leads/Monitor_(synchronization).txt` (ROUGE-L: 0.4167)  
  *Matching Substring*: `'threads to temporarily give up exclusive access in order to wait for some condition to be'`  
- **Entry 111**: `code_snippets/ASCII_art_diagram_converter.txt` (ROUGE-L: 0.4091)  
  *Matching Substring*: `'.org/wiki/ASCII_art_diagram_converter'`  
- **Entry 113**: `wiki_leads/Regular_expression.txt` (ROUGE-L: 0.4000)  
  *Matching Substring*: `'" or "find and replace" operations on strings'`  
- **Entry 114**: `wiki_leads/Television.txt` (ROUGE-L: 0.3922)  
  *Matching Substring*: `'medium for advertising, entertainmen'`  
- **Entry 115**: `wiki_leads/Hypervisor.txt` (ROUGE-L: 0.3922)  
  *Matching Substring*: `'runs one or more virtual machines is called a host machine'`  
- **Entry 116**: `code_snippets/Pascal's_triangle.txt` (ROUGE-L: 0.3922)  
  *Matching Substring*: `'result, x)\n    a.append(result)\n  retur'`  
- **Entry 117**: `code_snippets/Loops_N_plus_one_half.txt` (ROUGE-L: 0.3902)  
  *Matching Substring*: `'i += 1\n    if i > n:\n        brea'`  
- **Entry 118**: `wiki_leads/Coal.txt` (ROUGE-L: 0.3855)  
  *Matching Substring*: `'hydrogen, sulfur, oxygen, and nitrogen. It is '`  
- **Entry 120**: `code_snippets/Call_a_function.txt` (ROUGE-L: 0.3774)  
  *Matching Substring*: `'(x, y))\n# call\nfixed_args(1, 2)'`  
- **Entry 121**: `code_snippets/Animated_snail.txt` (ROUGE-L: 0.3750)  
  *Matching Substring*: `'plot as plt\nfrom matplotlib.animation import FuncAnimation'`  
- **Entry 123**: `code_snippets/MD5.txt` (ROUGE-L: 0.3636)  
  *Matching Substring*: `'f00b204e9800998ecf8427e\'),\n  (b"a'`  
- **Entry 126**: `wiki_leads/XML.txt` (ROUGE-L: 0.3562)  
  *Matching Substring*: `'that is both human-readable and machine-readable. '`  
- **Entry 127**: `wiki_leads/Round-robin_scheduling.txt` (ROUGE-L: 0.3488)  
  *Matching Substring*: `'equal portions and in circular order, handling all processes without '`  
- **Entry 128**: `wiki_leads/Norse_mythology.txt` (ROUGE-L: 0.3333)  
  *Matching Substring*: `'ing after the Christianization o'`  
- **Entry 129**: `wiki_leads/Isolation_(database_systems).txt` (ROUGE-L: 0.3297)  
  *Matching Substring*: `'to access the same data at the same time, but '`  
- **Entry 132**: `wiki_leads/Obesity.txt` (ROUGE-L: 0.2895)  
  *Matching Substring*: `'as obese when their body mass index (BMI)'`  
- **Entry 133**: `code_snippets/Approximate_equality.txt` (ROUGE-L: 0.2857)  
  *Matching Substring*: `'1],\n              [10000000000000'`  
- **Entry 136**: `wiki_leads/Mae_Jemison.txt` (ROUGE-L: 0.2667)  
  *Matching Substring*: `'aboard the Space Shuttle Endeavour '`  
- **Entry 139**: `wiki_leads/Internet.txt` (ROUGE-L: 0.2588)  
  *Matching Substring*: `', public, academic, business, and government networks'`  
- **Entry 140**: `book_openings/The_Adventures_of_Huckleberry_Finn.txt` (ROUGE-L: 0.2529)  
  *Matching Substring*: `'Mr. Mark Twain, and he told the '`  
- **Entry 141**: `book_openings/Great_Expectations.txt` (ROUGE-L: 0.2444)  
  *Matching Substring*: `'ip, and came to be called Pip.'`  

---

## 2. Model Instability Artifacts
These entries contain garbled, non-ASCII characters or CJK ideographs in the generated continuation, indicating model failure/instability rather than memorization.

- **Entry 4**: `code_snippets/Quickselect_algorithm.txt` (ROUGE-L: 0.6939)  
- **Entry 13**: `code_snippets/Reverse_a_string.txt` (ROUGE-L: 0.6667)  
- **Entry 56**: `code_snippets/Caesar_cipher.txt` (ROUGE-L: 0.5789)  
- **Entry 60**: `code_snippets/Doubly-linked_list_Definition.txt` (ROUGE-L: 0.5714)  

---

## 3. Possible Extraction Bugs
These entries contain text that matches table-of-contents lists, index pages, or repetitive line headers rather than narrative body text.

- **Entry 10**: `book_openings/Madame_Bovary.txt` (Category: `book_openings`)  
  *Reason(s)*: Contains sequence of Roman numeral headers (26 times), Contains sequence of Roman numeral headers (9 times)  
- **Entry 89**: `code_snippets/Active_Directory_Connect.txt` (Category: `code_snippets`)  
  *Reason(s)*: High percentage of numbered lines (2/5)  

---

## 4. Full List of Borderline Entries (Sorted by ROUGE-L Descending)

### Entry 1: `code_snippets/Modular_inverse.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.7000
* **Matched Token Count**: 24
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'= 0, 1, 1, 0\n    while remainder:\n        lastremainder, '`

#### Prompt
```text
>>> def extended_gcd(aa, bb):
    lastremainder, remainder = abs(aa), abs(bb)
    x, lastx, y, lasty
```

#### True Continuation
```text
= 0, 1, 1, 0
    while remainder:
        lastremainder, (quotient, remainder) = remainder, divmod(lastremainder, remainder)
        x, lastx = lastx - quotient*x, x
```

#### Generated Continuation
```text
= 0, 1, 1, 0
    while remainder:
        lastremainder, q, remainder = remainder, lastremainder // remainder, remainder - q * lastremainder
        lastx, x = x, lastx - q * x
```

---

### Entry 2: `code_snippets/Associative_array_Creation.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.7000
* **Matched Token Count**: 16
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
# empty dictionary
d = {}
d['spam'] = 1
d['eggs'] = 2  

# dictionaries with two keys
d1 = {'sp
```

#### True Continuation
```text
am': 1, 'eggs': 2}
d2 = dict(spam=1, eggs=2)

# dictionaries from tuple list
d1 = dict([('spam', 1), ('eggs', 2)])
d2 =
```

#### Generated Continuation
```text
am': 1, 'eggs': 2}
d2 = {'spam': 1, 'eggs': 2}

# dictionaries with same keys
d3 = {'spam': 1, 'eggs': 2}
d4 =
```

---

### Entry 3: `code_snippets/9_billion_names_of_God_the_integer.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6957
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'/ 2\n        if d < 0:\n            brea'`

#### Prompt
```text
def partitions(n):
    partitions.p.append(0)

    for k in xrange(1, n + 1):
        d = n - k * (
```

#### True Continuation
```text
3 * k - 1) // 2
        if d < 0:
            break

        if k & 1:
            partitions.p[n] += partitions.p[d]
        else:
            partitions.p[n] -= partitions
```

#### Generated Continuation
```text
k + 1) / 2
        if d < 0:
            break
        partitions.p.append(partitions.p[-1] + d)

    return partitions.p


def partition_count(n):
    return partitions(n
```

---

### Entry 4: `code_snippets/Quickselect_algorithm.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6939
* **Matched Token Count**: 10
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Model Instability Artifact**: True (contains garbled/non-ASCII characters)

#### Prompt
```text
import random

def partition(vector, left, right, pivotIndex):
    pivotValue = vector[pivotIndex]
    vector[pivotIndex], vector[right] =
```

#### True Continuation
```text
vector[right], vector[pivotIndex]  # Move pivot to end
    storeIndex = left
    for i in range(left, right):
        if vector[i] < pivotValue:
            vector[storeIndex], vector[i] = vector[i],
```

#### Generated Continuation
```text
vector[right], vector[pivotIndex]
    storeIndex = left
    for i in range(left, right):
        if vector[i] < pivotValue:
串排序

def quicksort(vector, left, right):
    if left
```

---

### Entry 5: `wiki_leads/Volcanology.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6875
* **Matched Token Count**: 7
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'volcanology is derived from the '`

#### Prompt
```text
Volcanology is the study of volcanoes, lava, magma, and related geological, geophysical and geochemical phenomena (volcanism). The term
```

#### True Continuation
```text
volcanology is derived from the Latin word vulcan. Vulcan was the ancient Roman god of fire.
```

#### Generated Continuation
```text
volcanology is derived from the Vulcan, the Roman god of fire and metalworking, from the Latin
```

---

### Entry 6: `code_snippets/Stirling_numbers_of_the_first_kind.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6818
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
computed = {}

def sterling1(n, k):
	key = str(n) + "," + str(k)

	if key in computed.keys():
```

#### True Continuation
```text
return computed[key]
	if n == k == 0:
		return 1
	if n > 0 and k == 0:
		return 0
	if k > n:
		return 0
	result =
```

#### Generated Continuation
```text
return computed[key]

	if k == 0:
		return 1

	if k == 1:
		return n

	if k == n:
		return 1

	if k > n:
```

---

### Entry 7: `code_snippets/Arithmetic_numbers.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6809
* **Matched Token Count**: 8
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `':\n            f.add(i)\n            f.add(j)\n        i '`

#### Prompt
```text
def factors(n: int):
    f = set([1, n])
    i = 2
    while True:
        j = n // i
        if j <
```

#### True Continuation
```text
i:
            break
        if i * j == n:
            f.add(i)
            f.add(j)
        i += 1
    return f

arithmetic_count = 0
composite_count = 0
n =
```

#### Generated Continuation
```text
i:
            break
        if n % i == 0 and n % j == 0:
            f.add(i)
            f.add(j)
        i = i + 1
    return f


def main():
    n =
```

---

### Entry 8: `code_snippets/Longest_common_subsequence.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6780
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
def lcs(a, b):
    # generate matrix of length of longest common subsequence for substrings of both words
    lengths = [[0] * (len(b)+1
```

#### True Continuation
```text
) for _ in range(len(a)+1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if x == y:
                lengths[i+1][j+1] = lengths[i][j]
```

#### Generated Continuation
```text
) for i in range(len(a)+1)]
    for i in range(len(a)+1):
        for j in range(len(b)+1):
            if i == 0 or j == 0:
                lengths[i][j] =
```

---

### Entry 9: `code_snippets/Miller-Rabin_primality_test.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6769
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
from random import randrange

def is_Prime(n: int):
    """
    Miller-Rabin primality test.

    A return value of False means
```

#### True Continuation
```text
n is certainly not prime. A return value of
    True means n is very likely a prime.
    """
    #Miller-Rabin test for primes
    if n in [2,3,5,7]:
        return True
    elif n<
```

#### Generated Continuation
```text
n is not prime.
    A return value of True means n is very likely prime.
    """
    if n == 2 or n == 3:
        return True
    if n % 2 == 0 or n < 2:
        return False
```

---

### Entry 10: `book_openings/Madame_Bovary.txt`

* **Category**: book_openings
* **ROUGE-L Score**: 0.6742
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' I II III IV V VI VII VIII IX X XI XII XIII XIV XV '`
* **[FLAG] Possible Extraction Bug**: Contains sequence of Roman numeral headers (26 times), Contains sequence of Roman numeral headers (9 times)

#### Prompt
```text
Gustave Flaubert MADAME BOVARY (1857) Table des matières PREMIÈRE PARTIE I II III IV V VI VII VIII IX DE
```

#### True Continuation
```text
UXIÈME PARTIE I II III IV V VI VII VIII IX X XI XII XIII XIV XV TROISIÈME PARTIE I II III IV V VI VII VIII IX X XI À Marie-Antoine-Jules Senard MEMBRE DU B
```

#### Generated Continuation
```text
UXIÈME PARTIE I I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX PREMIÈRE PARTIE I I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX II P
```

---

### Entry 11: `wiki_leads/Man-in-the-middle_attack.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 14
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'ays and possibly alters the communications between two parties who believe th'`

#### Prompt
```text
In cryptography and computer security, a man-in-the-middle (MITM) attack, or on-path attack, is a cyberattack where the attacker secretly rel
```

#### True Continuation
```text
ays and possibly alters the communications between two parties who believe that they are directly communicating with each other, where in actuality the attacker has inserted themselves between the two user parties.
```

#### Generated Continuation
```text
ays and possibly alters the communications between two parties who believe they are directly communicating with each other. The attacker aims to intercept, read, and modify the messages without the knowledge
```

---

### Entry 12: `code_snippets/Linear_congruential_generator.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'\n   rand.seed = seed\n   return rand\n\ndef '`

#### Prompt
```text
def bsd_rand(seed):
   def rand():
      rand.seed = (1103515245*rand.seed + 1234
```

#### True Continuation
```text
5) & 0x7fffffff
      return rand.seed
   rand.seed = seed
   return rand

def msvcrt_rand(seed):
   def rand():
      rand.seed = (214013*rand.
```

#### Generated Continuation
```text
5).uint()
      return (rand.seed & 0x7fffffff) / 4294967295.0
   rand.seed = seed
   return rand

def bsd_randn(seed):
   def rand
```

---

### Entry 13: `code_snippets/Reverse_a_string.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 5
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Model Instability Artifact**: True (contains garbled/non-ASCII characters)

#### Prompt
```text
import unicodedata

def ureverse(ustring):
    'Reverse a string including unicode combining characters'
    groupedchars = []
    uchar = list(
```

#### True Continuation
```text
ustring)
    while uchar:
        if unicodedata.combining(uchar[0]) != 0:
            groupedchars[-1] += uchar.pop(0)
        else:
            groupedchars.append(uchar.pop
```

#### Generated Continuation
```text
ustring)
    for i in range(len(uchar)):
        if unicodedata.combining(uchar[i]):
串
            groupedchars[-1] += uchar[i]
        else:
            groupedchars.append(uchar
```

---

### Entry 14: `code_snippets/Autogram_checker.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 40
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `"'4': 'four',\n    '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'"`

#### Prompt
```text
import re
import string

INT_TO_WORD = {
    '0': 'zero', '1': 'one', '2': 'two', '3': 'three',
```

#### True Continuation
```text
'4': 'four',
    '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
    '10': 'ten', '11': 'eleven', '1
```

#### Generated Continuation
```text
'4': 'four',
    '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
}

def text_to_words(text):
    text = text.
```

---

### Entry 15: `wiki_leads/Antibiotic.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 5
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'s are widely used in the treatment and prevention of such infections. They may either kill or '`

#### Prompt
```text
An antibiotic is a type of antimicrobial substance which is active against bacteria. It is the most important type of antibacterial agent for fighting bacter
```

#### True Continuation
```text
ial infections, and antibiotic medications are widely used in the treatment and prevention of such infections. They may either kill or inhibit the growth of bacteria. A limited number of antibiotics also possess antiprotozoal activity
```

#### Generated Continuation
```text
ial infections. Antibiotics are widely used in the treatment and prevention of such infections. They may either kill or halt the growth of bacteria.

Antibiotics are not effective against viral infections, such as the common cold or
```

---

### Entry 16: `wiki_leads/B._F._Skinner.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 3
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
Burrhus Frederic Skinner was an American psychologist, behaviorist, inventor, and social philosopher. He was the Edgar Pierce Professor of Psychology at Harvard University from
```

#### True Continuation
```text
1948 until his retirement in 1974.
```

#### Generated Continuation
```text
1958 until his retirement in 1963.
```

---

### Entry 17: `wiki_leads/Tundra.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 7
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
In physical geography, a tundra is a type of biome where tree growth is hindered by frigid temperatures and short growing seasons. There are three regions and associated types
```

#### True Continuation
```text
of tundra: Arctic, Alpine, and Antarctic.
```

#### Generated Continuation
```text
of tundra: Arctic tundra, Alpine tundra
```

---

### Entry 18: `code_snippets/Attractive_numbers.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 7
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `':\n      n //= i\n      factors.append(i)\n  '`

#### Prompt
```text
from sympy import sieve # library for primes

def get_pfct(n): 
  i, factors = 2, []
  while i * i <= n
```

#### True Continuation
```text
:
    if n % i:
      i += 1
    else:
      n //= i
      factors.append(i)
  if n > 1:
    factors.append(n)
  return len(factors) 

s
```

#### Generated Continuation
```text
:
    if n % i == 0:
      n //= i
      factors.append(i)
    else:
      i = sieve.next_prime(i)
  if n > 1:
    factors.append(n)
```

---

### Entry 19: `code_snippets/Anaprimes.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 17
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'[True] * (limit + 1)\n#     sieve[0'`

#### Prompt
```text
# def sieve(limit):
#     """Generate list of primes up to the given limit using the Sieve of Eratosthenes."""
#     sieve =
```

#### True Continuation
```text
[True] * (limit + 1)
#     sieve[0:2] = [False, False]  # 0 and 1 are not primes
#     for num in range(2, int(limit**0.5) + 1):
```

#### Generated Continuation
```text
[True] * (limit + 1)
#     sieve[0] = sieve[1] = False
#     for i in range(2, int(limit**0.5) + 1):
#         if sieve[i]:
#
```

---

### Entry 20: `code_snippets/merge_sort.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 38
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(left, right):\n    '`

#### Prompt
```text
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort
```

#### True Continuation
```text
(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j
```

#### Generated Continuation
```text
(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    sorted_array = []
    left_index, right_index = 0, 0
```

---

### Entry 21: `code_snippets/Huffman_coding.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'t in symb2freq.items()]\n    heapify(heap)\n    while len(heap) > 1:\n        lo = he'`

#### Prompt
```text
from heapq import heappush, heappop, heapify
from collections import defaultdict

def encode(symb2freq):
    """Huffman encode the given
```

#### True Continuation
```text
dict mapping symbols to weights"""
    heap = [[wt, [sym, ""]] for sym, wt in symb2freq.items()]
    heapify(heap)
    while len(heap) > 1:
        lo = he
```

#### Generated Continuation
```text
symbol frequencies"""
    heap = [[weight, [symbol, '']] for symbol, weight in symb2freq.items()]
    heapify(heap)
    while len(heap) > 1:
        lo = heappop(he
```

---

### Entry 22: `wiki_leads/Claude_Debussy.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6667
* **Matched Token Count**: 7
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' composers of the late 19th and early'`

#### Prompt
```text
Achille Claude Debussy was a French composer, born in Saint-Germain-en-Laye. He is sometimes seen as the first Impressionist composer, although he vigor
```

#### True Continuation
```text
ously rejected the term. He was among the most influential composers of the late 19th and early 20th centuries.
```

#### Generated Continuation
```text
ously rejected the term. He is widely considered one of the most important and distinctive French composers of the late 19th and early
```

---

### Entry 23: `wiki_leads/Cold_War.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6591
* **Matched Token Count**: 3
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' is used because there was no '`

#### Prompt
```text
The Cold War was a period of international geopolitical rivalry between the United States (US) and the Soviet Union (USSR) and their respective allies, the capitalist Western
```

#### True Continuation
```text
Bloc and communist Eastern Bloc. It began in the aftermath of the Second World War and ended with the dissolution of the Soviet Union in 1991. The term cold war is used because there was no direct fighting between the two superpowers, though each supported oppos
```

#### Generated Continuation
```text
Bloc and the communist Eastern Bloc, from the end of World War II in 1945 until the end of the Cold War in 1991. The term "Cold War" is used because there was no large-scale fighting directly between the two superpow
```

---

### Entry 24: `code_snippets/Sorting_algorithms_Merge_sort.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6545
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' right[right_idx]:\n            result.append(left[left_idx])\n            left_idx += 1'`

#### Prompt
```text
def merge(left, right):
    result = []
    left_idx, right_idx = 0, 0
    while left_idx < len(left) and right
```

#### True Continuation
```text
_idx < len(right):
        # change the direction of this comparison to change the direction of the sort
        if left[left_idx] <= right[right_idx]:
            result.append(left[left_idx])
            left_idx += 1
```

#### Generated Continuation
```text
_idx < len(right):
        if left[left_idx] < right[right_idx]:
            result.append(left[left_idx])
            left_idx += 1
        else:
            result.append(right[right_idx])
```

---

### Entry 25: `code_snippets/Catalan_numbers.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6531
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' function\n        if key not in cache:\n            cache[key] = func(key)\n        return cache[key]\n'`

#### Prompt
```text
from math import factorial
import functools


def memoize(func):
    cache = {}

    def memoized(key):
        # Returned
```

#### True Continuation
```text
, new, memoized version of decorated function
        if key not in cache:
            cache[key] = func(key)
        return cache[key]
    return functools.update_wrapper(memoized, func)


@memo
```

#### Generated Continuation
```text
value from the function
        if key not in cache:
            cache[key] = func(key)
        return cache[key]

    return functools.wraps(func)(memoized)


@memoize
def factorial_
```

---

### Entry 26: `code_snippets/observer_pattern.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6522
* **Matched Token Count**: 8
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'\n\n    def notify(self, *args, **kwargs):\n        for observer in self._observers:\n            observer.update(*args, **kwargs)'`

#### Prompt
```text
class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append
```

#### True Continuation
```text
(observer)

    def notify(self, *args, **kwargs):
        for observer in self._observers:
            observer.update(*args, **kwargs)

class Observer:
    def update(self, *args, **kwargs):
```

#### Generated Continuation
```text
(observer)

    def detach(self, observer):
 composes a list of observers.

    def notify(self, *args, **kwargs):
        for observer in self._observers:
            observer.update(*args, **kwargs)
```

---

### Entry 27: `code_snippets/Smith_numbers.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6500
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
from sys import stdout


def factors(n):
    rt = []
    f = 2
    if n == 1:
        rt.append(1
```

#### True Continuation
```text
);
    else:
        while 1:
            if 0 == ( n % f ):
                rt.append(f);
                n //= f
                if n == 1:
                    return rt
            else:
                f +=
```

#### Generated Continuation
```text
)
    while n > 1:
        if n % f == 0:
ht = 0
        rt.append(f)
        n /= f
        f += 1
    return rt


def main():
    n =
```

---

### Entry 28: `code_snippets/Arithmetic_Complex.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6471
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
>>> z1 = 1.5 + 3j
>>> z2 = 1.5 + 1.5j
>>> z1 + z2
(3+
```

#### True Continuation
```text
4.5j)
>>> z1 - z2
1.5j
>>> z1 * z2
(-2.25+6.75j)
>>> z1 / z2
(1.5+0.5j)
```

#### Generated Continuation
```text
4j)
>>> z1 - z2
(0.5+2j)
>>> z1 * z2
(2.25+6.75j)
>>> z1 / z2
(1.333333
```

---

### Entry 29: `code_snippets/Archimedean_spiral.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6452
* **Matched Token Count**: 5
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
from turtle import *
from math import *
color("blue")
down()
for i in range(200):
    t = i / 20 * pi
```

#### True Continuation
```text
x = (1 + 5 * t) * cos(t)
    y = (1 + 5 * t) * sin(t)
    goto(x, y)
up()
done()
```

#### Generated Continuation
```text
x = cos(t)
    y = sin(t)
    goto(x, y)
    up()
    goto(0, 0)
    down()
```

---

### Entry 30: `wiki_leads/Byzantine_Empire.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6420
* **Matched Token Count**: 3
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' fall of the Western Roman Empire in the 5th century AD, '`

#### Prompt
```text
The Byzantine Empire, also known as the Eastern Roman Empire, was the continuation of the Roman Empire centred on Constantinople during late antiquity and the Middle Ages. Having surv
```

#### True Continuation
```text
ived the fall of the Western Roman Empire in the 5th century AD, it endured until the fall of Constantinople to the Ottoman Empire in 1453. The term 'Byzantine Empire' was coined only after its demise; its citizens used the term
```

#### Generated Continuation
```text
ived the fragmentation and fall of the Western Roman Empire in the 5th century AD, the Byzantine Empire endured for another thousand years until the fall of Constantinople in 1453.

The Byzantine Empire was characterized by its strong centralized government
```

---

### Entry 31: `code_snippets/Longest_common_substring.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6415
* **Matched Token Count**: 8
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
def _set_of_substrings(s:str) -> set:
    "_set_of_substrings('ABBA') == {'A', 'AB', 'ABB',
```

#### True Continuation
```text
'ABBA', 'B', 'BA', 'BB', 'BBA'}"
    len_s = len(s)
    return {s[m: n] for m in range(len_s) for n in range(m+1, len_s +
```

#### Generated Continuation
```text
'ABBA', 'B', 'BB', 'BBA'}"
    return {s[i: j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)}


def _set_of
```

---

### Entry 32: `code_snippets/Kaprekar_numbers.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6364
* **Matched Token Count**: 3
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `')\n        else:\n            result += chr(d - 10 + ord('`

#### Prompt
```text
def encode(n, base):
    result = ""
    while n:
        n, d = divmod(n, base)
        if d < 10:
```

#### True Continuation
```text
result += str(d)
        else:
            result += chr(d - 10 + ord("a"))
    return result[::-1]

def Kaprekar(n, base):
    if n == '1':
        return True
```

#### Generated Continuation
```text
result += chr(d + ord('0'))
        else:
            result += chr(d - 10 + ord('a') + 1)
    return result[::-1]

def decode(s, base):
    result = 0
```

---

### Entry 33: `wiki_leads/Autoencoder.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6364
* **Matched Token Count**: 1
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' representation (encoding) for a set of data, typically for '`

#### Prompt
```text
An autoencoder is a type of artificial neural network used to learn efficient codings of unlabeled data. An autoencoder learns two functions: an encoding function that transforms the input
```

#### True Continuation
```text
data, and a decoding function that recreates the input data from the encoded representation. The autoencoder learns an efficient representation (encoding) for a set of data, typically for dimensionality reduction, to generate lower-dimensional embeddings for subsequent use by other machine learning algorithms.
```

#### Generated Continuation
```text
data into a different representation, and a decoding function that reconstructs the input data from the encoded representation. The goal of an autoencoder is to learn a representation (encoding) for a set of data, typically for the purpose of dimensionality reduction or feature learning.

Here
```

---

### Entry 34: `book_openings/Alice's_Adventures_in_Wonderland.txt`

* **Category**: book_openings
* **ROUGE-L Score**: 0.6316
* **Matched Token Count**: 18
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'the book her sister was reading, but it had no pictures or conversations in it, '`

#### Prompt
```text
. Down the Rabbit-Hole Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into
```

#### True Continuation
```text
the book her sister was reading, but it had no pictures or conversations in it, “and what is the use of a book,” thought Alice “without pictures or conversations?” So she was considering in her own mind (as well as she could, for the hot day made her feel very
```

#### Generated Continuation
```text
the book her sister was reading, but it had no pictures or conversations in it, 'and what is the use of a book,' thought Alice 'without pictures or conversations?'


### Answer:The main idea of the passage is that Alice is bored and curious about the
```

---

### Entry 35: `code_snippets/Bernstein_basis_polynomials.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6316
* **Matched Token Count**: 6
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `') = monomial_coefficients\n    return (a0'`

#### Prompt
```text
#!/bin/env python3

# Subprogram (1).
def monomial_to_bernstein_degree2(monomial_coefficients):
    (a0
```

#### True Continuation
```text
, a1, a2) = monomial_coefficients
    return (a0, a0 + ((1/2) * a1), a0 + a1 + a2)

# Subprogram (2).
def evaluate_bernstein_degree2
```

#### Generated Continuation
```text
, a1, a2, a3) = monomial_coefficients
    return (a0 + a1 + a2 + a3)

# Subprogram (2).
def bernstein_to_monomial_coefficients(bernstein_co
```

---

### Entry 36: `code_snippets/Pythagorean_triples.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6296
* **Matched Token Count**: 11
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'\n        for b in range(a, maxperimeter'`

#### Prompt
```text
from math import gcd

def pt1(maxperimeter=100):
    '''
# Naive method
    '''
    trips = []
    for a
```

#### True Continuation
```text
in range(1, maxperimeter):
        aa = a*a
        for b in range(a, maxperimeter-a+1):
            bb = b*b
            for c in range(b, maxperimeter-b-a+1):
```

#### Generated Continuation
```text
in range(1, maxperimeter):
        for b in range(a, maxperimeter):
            c = (a + b) / 2
            if a + b > c and a + c > b and b + c > a:
                trips.
```

---

### Entry 37: `code_snippets/Bioinformatics_Sequence_mutation.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6296
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'i+n] for i in range(0, len(dna), n)]\n\ndef '`

#### Prompt
```text
import random
from collections import Counter

def basecount(dna):
    return sorted(Counter(dna).items())

def seq_split(dna, n
```

#### True Continuation
```text
=50):
    return [dna[i: i+n] for i in range(0, len(dna), n)]

def seq_pp(dna, n=50):
    for i, part in enumerate(seq_split(d
```

#### Generated Continuation
```text
):
    return [dna[i:i+n] for i in range(0, len(dna), n)]

def random_seq(length):
    return ''.join(random.choice('ACGT') for _ in range(length))
```

---

### Entry 38: `code_snippets/Bell_numbers.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6296
* **Matched Token Count**: 7
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'i):\n            tri[i][j] = tri[i'`

#### Prompt
```text
def bellTriangle(n):
    tri = [[0] * i for i in range(n)]
    tri[1][0] = 1
    for i in range
```

#### True Continuation
```text
(2, n):
        tri[i][0] = tri[i - 1][i - 2]
        for j in range(1, i):
            tri[i][j] = tri[i][j - 1] + tri[i -
```

#### Generated Continuation
```text
(2, n):
        for j in range(i):
            tri[i][j] = tri[i-1][j] + tri[i-2][j] if j == 0 else tri[i-1][j-1] + tri[i
```

---

### Entry 39: `wiki_leads/Statue_of_Liberty.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6265
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' was designed by French sculptor Frédéric Auguste Bartholdi'`

#### Prompt
```text
The Statue of Liberty is a colossal neoclassical sculpture of a robed and crowned woman on Liberty Island, part of New York City, in New York Har
```

#### True Continuation
```text
bor. The copper-clad statue, a gift to the United States from the people of France, was designed by French sculptor Frédéric Auguste Bartholdi, and its metal framework built by Gustave Eiffel. The statue was dedicated on October 28,
```

#### Generated Continuation
```text
bor. It was designed by French sculptor Frédéric Auguste Bartholdi and its metal framework was built by Gustave Eiffel. The statue was a gift from the people of France to the United States and was dedicated on October 28, 1886.
```

---

### Entry 40: `code_snippets/Stirling_numbers_of_the_second_kind.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6222
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
computed = {}

def sterling2(n, k):
	key = str(n) + "," + str(k)

	if key in computed.keys():
```

#### True Continuation
```text
return computed[key]
	if n == k == 0:
		return 1
	if (n > 0 and k == 0) or (n == 0 and k > 0):
		return 0
	if n
```

#### Generated Continuation
```text
return computed[key]

	if k == 0:
		return 1

	if k == 1:
		return n

	if n == 0:
		return 0

	result = (1 /
```

---

### Entry 41: `wiki_leads/Alan_Turing.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6216
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'. Turing is widely considered to be the father of theoretical computer science'`

#### Prompt
```text
Alan Mathison Turing was an English mathematician, computer scientist, logician, cryptanalyst, philosopher and theoretical biologist. He was highly influential in the development of
```

#### True Continuation
```text
theoretical computer science, providing a formalisation of the concepts of algorithm and computation with the Turing machine, which can be considered a model of a general-purpose computer. Turing is widely considered to be the father of theoretical computer science.
```

#### Generated Continuation
```text
computer science, providing a formalization of the concepts of "algorithm" and "computation". Turing is widely considered to be the father of theoretical computer science and artificial intelligence.

Turing'ieves's work on the Entscheid
```

---

### Entry 42: `code_snippets/counting_sort.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6190
* **Matched Token Count**: 21
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'1)\n    for num in arr:\n        count[num] += 1\n    '`

#### Prompt
```text
def counting_sort(arr):
    if not arr:
        return arr
    max_val = max(arr)
    count = [0] * (max_val +
```

#### True Continuation
```text
1)
    for num in arr:
        count[num] += 1
    result = []
    for i, c in enumerate(count):
        result.extend([i] * c)
    return result
```

#### Generated Continuation
```text
1)
    for num in arr:
        count[num] += 1
    sorted_arr = []
    for num, freq in enumerate(count):
        sorted_arr.extend([num] * fre
```

---

### Entry 43: `code_snippets/stack_implementation.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6154
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'\n\n    def peek(self):\n        if '`

#### Prompt
```text
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)
```

#### True Continuation
```text
def pop(self):
        if not self.is_empty():
            return self.items.pop()
        raise IndexError("pop from empty stack")

    def peek(self):
        if not self.is_empty():
            return self.
```

#### Generated Continuation
```text
def pop(self):
        if self.items:
            return self.items.pop()
        else:
            return None

    def peek(self):
        if self.items:
            return self.items[-1]
        else:
```

---

### Entry 44: `wiki_leads/B-tree.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.6111
* **Matched Token Count**: 6
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
In computer science, a B-tree is a self-balancing tree data structure that maintains sorted data and allows searches, sequential access, insertions, and deletions in logarithmic
```

#### True Continuation
```text
time. The B-tree generalizes the binary search tree, allowing nodes to have more than two children.
```

#### Generated Continuation
```text
time. The B-tree is a generalization of a binary search tree in that a node can have more
```

---

### Entry 45: `code_snippets/Abelian_sandpile_model.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6087
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
import numpy as np
import matplotlib.pyplot as plt


def iterate(grid):
    changed = False
    for ii, arr in enumerate(grid):
        for j
```

#### True Continuation
```text
j, val in enumerate(arr):
            if val > 3:
                grid[ii, jj] -= 4
                if ii > 0:
                    grid[ii - 1, jj] += 1
                if ii < len(grid
```

#### Generated Continuation
```text
j, val in enumerate(arr):

            if val == 0:
                grid[ii][jj] = 1
            elif val == 1:
                grid[ii][jj] = 0

            if val == 1:
```

---

### Entry 46: `code_snippets/Sorting_algorithms_Gnome_sort.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6087
* **Matched Token Count**: 6
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
>>> def gnomesort(a):
  i,j,size = 1,2,len(a)
  while i < size:
    if a[i-
```

#### True Continuation
```text
1] <= a[i]:
      i,j = j, j+1
    else:
      a[i-1],a[i] = a[i],a[i-1]
      i -= 1
      if i == 0:
```

#### Generated Continuation
```text
1] <= a[j]:
      j += 1
      if j == size:
        j = i
      i += 1
    else:
      a[i],a[j] = a[j],a[i]
      i -=
```

---

### Entry 47: `code_snippets/Base64_encode_data.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6047
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'\nresponse = requests.get(url, headers=headers)\n'`

#### Prompt
```text
import base64
import requests

url = "https://rosettacode.org/favicon.ico"
headers = { "User-Agent": "%Mozilla
```

#### True Continuation
```text
/5.0" }
response = requests.get(url, headers=headers)
if response.ok:
    result = base64.b64encode(response.content)
    print(f"{result[:50]}...{result[-50
```

#### Generated Continuation
```text
/5atracker/1.0" }

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print(base64.b64encode(response.content).decode())
else:
```

---

### Entry 48: `code_snippets/Floyd-Warshall_algorithm.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6038
* **Matched Token Count**: 3
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' in rn]\n    for i in rn:\n        dist[i][i] = 0\n    for '`

#### Prompt
```text
from math import inf
from itertools import product

def floyd_warshall(n, edge):
    rn = range(n)
    dist = [[inf]
```

#### True Continuation
```text
* n for i in rn]
    nxt  = [[0]   * n for i in rn]
    for i in rn:
        dist[i][i] = 0
    for u, v, w in edge:
        dist[
```

#### Generated Continuation
```text
* n for _ in rn]
    for i in rn:
        dist[i][i] = 0
    for a, b, c in edge:
        dist[a][b] = c
        dist[b][a] = c
```

---

### Entry 49: `code_snippets/Loops_Break.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.6000
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
from random import randrange

while True:
    a = randrange(20)
    print(a)
    if a == 10:
        break
```

#### True Continuation
```text
b = randrange(20)
    print(b)
```

#### Generated Continuation
```text
a = randrange(20)
    print(a)
```

---

### Entry 50: `wiki_leads/William_Shakespeare.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5897
* **Matched Token Count**: 15
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'often called England\'s national poet and the "Bard of Avon"'`

#### Prompt
```text
William Shakespeare was an English playwright, poet and actor. He is widely regarded as the greatest writer in the English language and the world's pre-eminent dramatist. He is
```

#### True Continuation
```text
often called England's national poet and the "Bard of Avon" or simply "the Bard". His extant works, including collaborations, consist of some 39 plays, 154 sonnets, three long narrative poems and a few other verses
```

#### Generated Continuation
```text
often called England's national poet and the "Bard of Avon". His extant works include 39 plays, 154 sonnets, and two long narrative poems. His plays have been translated into every major language and are performed more often than those of any
```

---

### Entry 51: `wiki_leads/A_search_algorithm.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5882
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
A* is a graph traversal and pathfinding algorithm that is used in many fields of computer science due to its completeness, optimality, and optimal efficiency. Given a weighted graph
```

#### True Continuation
```text
, a source node and a goal node, the algorithm finds the shortest path from source to goal.
```

#### Generated Continuation
```text
with nodes and edges, A* finds the shortest path from a start node to a goal node.
```

---

### Entry 52: `code_snippets/Averages_Mode.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5882
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
>>> from collections import defaultdict
>>> def modes(values):
	count = defaultdict(int)
	for v in values:
		count[v] +=1
```

#### True Continuation
```text
best = max(count.values())
	return [k for k,v in count.items() if v == best]

>>> modes([1,3,6,6,6,6,7,7,12,12,17])
```

#### Generated Continuation
```text
return [k for k, v in count.items() if v == max(count.values())]
>>> modes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
```

---

### Entry 53: `code_snippets/Active_object.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5882
* **Matched Token Count**: 6
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'):\n        Thread.__init__(self)\n        self.'`

#### Prompt
```text
from time import time, sleep
from threading import Thread

class Integrator(Thread):
    'continuously integrate a function `K`, at each `interval` seconds'
```

#### True Continuation
```text
def __init__(self, K=lambda t:0, interval=1e-4):
        Thread.__init__(self)
        self.interval  = interval
        self.K   = K
        self.S   = 0.0
        self.__run
```

#### Generated Continuation
```text
def __init__(self, f, K, interval):
        Thread.__init__(self)
        self.f = f
        self.__K = K
        self.__interval = interval
        self.__running = True

    def run(self):
        while self
```

---

### Entry 54: `wiki_leads/Salvador_Dali.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5806
* **Matched Token Count**: 3
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' striking and bizarre images i'`

#### Prompt
```text
Salvador Domingo Felipe Jacinto Dalí i Domènech, Marquess of Dalí de Púbol, known as Salvador Dalí, was a Spanish surrealist artist ren
```

#### True Continuation
```text
owned for his technical skill, precise draftsmanship, and the striking and bizarre images in his work.
```

#### Generated Continuation
```text
owned for his striking and bizarre images in his artwork. Born on May 11, 19
```

---

### Entry 55: `wiki_leads/Taj_Mahal.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5789
* **Matched Token Count**: 7
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
The Taj Mahal is an ivory-white marble mausoleum on the right bank of the river Yamuna in Agra, Uttar Pradesh, India. It was
```

#### True Continuation
```text
commissioned in 1631 by the fifth Mughal emperor, Shah Jahan, to house the tomb of his late wife, Mumtaz Mahal; it also houses the tomb of Shah Jahan himself. The tomb is the centrepiece of a 1
```

#### Generated Continuation
```text
commissioned in 1632 by the Mughal emperor Shah Jahan to house the tomb of his favorite wife, Mumtaz Mahal. The Taj Mahal is widely considered to be the finest example of Mughal architecture and a symbol of love. It
```

---

### Entry 56: `code_snippets/Caesar_cipher.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5789
* **Matched Token Count**: 11
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Model Instability Artifact**: True (contains garbled/non-ASCII characters)

#### Prompt
```text
import string
def caesar(s, k, decode = False):
   if decode: k = 26 - k
   return s.translate(
       string.mak
```

#### True Continuation
```text
etrans(
           string.ascii_uppercase + string.ascii_lowercase,
           string.ascii_uppercase[k:] + string.ascii_uppercase[:k] +
           string.ascii_lowercase[k:] + string
```

#### Generated Continuation
```text
etrans(
           string.ascii_lowercase,
           string串.ascii_lowercase[k:] + string.ascii_lowercase[:k]
       )
   )

print(caesar("abc", 1))
print(ca
```

---

### Entry 57: `wiki_leads/Frankenstein.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5778
* **Matched Token Count**: 13
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'stein, a young scientist who creates a sapient creature '`

#### Prompt
```text
Frankenstein; or, The Modern Prometheus is an 1818 Gothic novel written by English author Mary Shelley. Frankenstein tells the story of Victor Franken
```

#### True Continuation
```text
stein, a young scientist who creates a sapient creature from different body parts in an unorthodox scientific experiment. Shelley started writing the story when she was 18 and staying in Bath, and the first edition was published anonymously in London on 1 January
```

#### Generated Continuation
```text
stein, a young scientist who creates a sapient creature in an unorthodox scientific experiment. Shelley wrote the story as a sort of experiment in itself. She wrote the first draft of the story when she was nineteen, and the first edition was published when she was twenty
```

---

### Entry 58: `wiki_leads/Ethics.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5714
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
Ethics is the philosophical study of moral phenomena. Also called moral philosophy, it investigates normative questions about what people ought to do or which behavior is morally right. Its main branches
```

#### True Continuation
```text
include normative ethics, applied ethics, and metaethics.
```

#### Generated Continuation
```text
are metaethics, normative ethics, and applied ethics.
```

---

### Entry 59: `code_snippets/Sorting_algorithms_Quicksort.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5714
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
def quick_sort(sequence):
    lesser = []
    equal = []
    greater = []
    if len(sequence) <= 1:
        return sequence
```

#### True Continuation
```text
pivot = sequence[0]
    for element in sequence:
        if element < pivot:
            lesser.append(element)
        elif element > pivot:
            greater.append(element)
        else:
            equal.append(element)
    lesser
```

#### Generated Continuation
```text
else:
        pivot = sequence.pop(random.randint(0, len(sequence) - 1))
        for item in sequence:
            if item < pivot:
                lesser.append(item)
            elif item == pivot:
                equal.append
```

---

### Entry 60: `code_snippets/Doubly-linked_list_Definition.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5714
* **Matched Token Count**: 10
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Model Instability Artifact**: True (contains garbled/non-ASCII characters)

#### Prompt
```text
from collections import deque

some_list = deque(["a", "b", "c"])
print(some_list)

some_list.appendleft("Z
```

#### True Continuation
```text
")
print(some_list)

for value in reversed(some_list):
    print(value)
```

#### Generated Continuation
```text
")
print(some_list)

some_list.append("Y")
print(some串list)
```

---

### Entry 61: `book_openings/Alice's_Adventures_Underground.txt`

* **Category**: book_openings
* **ROUGE-L Score**: 0.5682
* **Matched Token Count**: 13
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'reading, but it had no pictures or conversations in it, '`

#### Prompt
```text
[Illustration] Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was
```

#### True Continuation
```text
reading, but it had no pictures or conversations in it, and where is the use of a book, thought Alice, without pictures or conversations? So she was considering in her own mind, (as well as she could, for the hot day made her feel very sleepy and stupid,
```

#### Generated Continuation
```text
reading, but it had no pictures or conversations in it, 'and what is the use of a book,' thought Alice 'without pictures or conversations?'

# Answer
The illustration for this excerpt from "Alice' Premier Duel: Alice and her sister are sitting
```

---

### Entry 62: `code_snippets/Barnsley_fern.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5652
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' img_height\n        self.paint_color = paint'`

#### Prompt
```text
import random
from PIL import Image


class BarnsleyFern(object):
    def __init__(self, img_width, img_height, paint_color=(0
```

#### True Continuation
```text
, 150, 0),
                 bg_color=(255, 255, 255)):
        self.img_width, self.img_height = img_width, img_height
        self.paint_color = paint
```

#### Generated Continuation
```text
, 0, 0)):
        self.img_width = img_*img_width
        self.img_height = img_height
        self.paint_color = paint_color

    def draw(self, img):
        img = Image.new
```

---

### Entry 63: `wiki_leads/Publish-subscribe_pattern.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5588
* **Matched Token Count**: 3
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'s, called subscribers, express interest in one or more classes '`

#### Prompt
```text
In software architecture, the publish–subscribe pattern (pub/sub) is a messaging pattern in which message senders, called publishers, categorize messages into classes, and send them without need
```

#### True Continuation
```text
ing to know which components will receive them. Message recipients, called subscribers, express interest in one or more classes and only receive messages in those classes, without needing to know the identity of the publishers.
```

#### Generated Continuation
```text
ing to know who will receive them. Receivers, called subscribers, express interest in one or more classes of messages, and receive only those messages.

Publish–subscribe is a form of asynchronous message passing
```

---

### Entry 64: `wiki_leads/Isaac_Newton.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5507
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'Philosophiæ Naturalis Principi'`

#### Prompt
```text
Sir Isaac Newton was an English polymath who was a mathematician, physicist, astronomer, alchemist, theologian, author and inventor. He was a key figure
```

#### True Continuation
```text
in the Scientific Revolution and the Enlightenment that followed. His book Philosophiæ Naturalis Principia Mathematica, first published in 1687, achieved the first great unification in physics and established classical mechanics. Newton also made seminal contributions to opt
```

#### Generated Continuation
```text
in the scientific revolution, and his book "Philosophiæ Naturalis Principia Mathematica" (Mathematical Principles of Natural Philosophy), first published in 1687, laid the foundations for classical mechanics. Newton's work in mathematics, particularly
```

---

### Entry 65: `code_snippets/Atomic_updates.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5500
* **Matched Token Count**: 18
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'ckets):\n        self.nbuckets = nbuckets\n        self.'`

#### Prompt
```text
import threading
from random import randrange
from time import sleep

terminate = threading.Event()

class Buckets:
    def __init__(self, nbu
```

#### True Continuation
```text
ckets):
        self.nbuckets = nbuckets
        self.values = [randrange(10) for _ in range(nbuckets)]
        self.lock = threading.Lock()

    def __getitem__(self, i):
```

#### Generated Continuation
```text
ckets):
        self.nbuckets = nbuckets
        self.__buckets = [[] for i in range(nbuckets)]

    def add(self, item):
        self.__buckets[randrange(self.nbuckets)].
```

---

### Entry 66: `wiki_leads/Hash_table.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5455
* **Matched Token Count**: 1
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' slots, from which the desired value can be found. '`

#### Prompt
```text
In computer science, a hash table is a data structure that implements an associative array, also called a dictionary or simply map; an associative array is an abstract data type that maps keys to values
```

#### True Continuation
```text
. A hash table uses a hash function to compute an index, also called a hash code, into an array of buckets or slots, from which the desired value can be found. During lookup, the key is hashed and the resulting hash indicates where the corresponding value is stored. A map
```

#### Generated Continuation
```text
. Hash tables use a hash function to compute an index into an array of slots, from which the desired value can be found. Ideally, the hash function will assign each key to a unique slot, but most hash table designs use open hashing (also known as separate chaining) or
```

---

### Entry 67: `wiki_leads/Adam_Smith.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5455
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'An Inquiry into the Nature and Causes of the Wealth of Nations'`

#### Prompt
```text
Adam Smith was a Scottish economist and philosopher who was a pioneer in the field of political economy and key figure during the Scottish Enlightenment. Seen by many as the "
```

#### True Continuation
```text
father of economics", or the "father of capitalism", he is primarily known for two classic works: The Theory of Moral Sentiments (1759) and An Inquiry into the Nature and Causes of the Wealth of Nations (1776). The
```

#### Generated Continuation
```text
Father of Economics," Smith is best known for his work "An Inquiry into the Nature and Causes of the Wealth of Nations," often simply called "The Wealth of Nations." Published in 1776, this seminal work laid the foundations for classical
```

---

### Entry 68: `wiki_leads/Certificate_authority.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5417
* **Matched Token Count**: 10
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'the named subject of the certificate. This allows others '`

#### Prompt
```text
In cryptography, a certificate authority or certification authority (CA) is an entity that stores, signs, and issues digital certificates. A digital certificate certifies the ownership of a public key by
```

#### True Continuation
```text
the named subject of the certificate. This allows others to rely upon signatures or on assertions made about the private key that corresponds to the certified public key. A CA acts as a trusted third party—trusted both by the subject (owner) of the certificate and by the party re
```

#### Generated Continuation
```text
the named subject of the certificate. This allows others (especially, but not limited to, web browsers) to rely upon signatures made by the private key that corresponds to the public key and certifies that the named subject is who they purport to be.

Certificates are used
```

---

### Entry 69: `code_snippets/Greatest_common_divisor.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5417
* **Matched Token Count**: 10
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
def gcd_bin(u, v):
    u, v = abs(u), abs(v) # u >= 0, v >= 0
    if u < v
```

#### True Continuation
```text
:
        u, v = v, u # u >= v >= 0
    if v == 0:
        return u
   
    # u >= v > 0
    k = 1
    while u & 1 == 0 and v &
```

#### Generated Continuation
```text
:
        u, v = v, u
    if v == 0:
        return u
    return gcd_bin(v, u % v)

def lcm_bin(u, v):
    return abs(u * v) // gcd
```

---

### Entry 70: `code_snippets/Animate_a_pendulum.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5405
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' = pygame.display.set_mode((WINDOWSIZE, WINDOWSIZE))\npygame.display.set_caption("'`

#### Prompt
```text
import pygame, sys
from pygame.locals import *
from math import sin, cos, radians

pygame.init()

WINDOWSIZE = 250
```

#### True Continuation
```text
TIMETICK = 100
BOBSIZE = 15

window = pygame.display.set_mode((WINDOWSIZE, WINDOWSIZE))
pygame.display.set_caption("Pendulum")

screen
```

#### Generated Continuation
```text
screen = pygame.display.set_mode((WINDOWSIZE, WINDOWSIZE))
pygame.display.set_caption("Sine Wave")

clock = pygame.time.Clock()

# Colors
BLACK = (0
```

---

### Entry 71: `code_snippets/Ascending_primes.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5385
* **Matched Token Count**: 4
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
def isprime(n):
    if n == 2: return True
    if n == 1 or n % 2 == 0: return False
    root1 = int
```

#### True Continuation
```text
(n**0.5) + 1;
    for k in range(3, root1, 2):
        if n % k == 0: return False
    return True

queue = [k for k in range(1, 10)]
```

#### Generated Continuation
```text
(n**0utive(3))
    for divisor in range(3, int(root1) + 1, 2):
        if n % divisor == 0:
            return False
    return True

def find_prime_factors(n
```

---

### Entry 72: `code_snippets/fibonacci.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5263
* **Matched Token Count**: 12
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2
```

#### True Continuation
```text
:
        return [0, 1]
    fib = [0, 1]
    while len(fib) < n:
        fib.append(fib[-1] + fib[-2])
    return fib
```

#### Generated Continuation
```text
:
        return [0, 1]
    else:
        fib_list = [0, 1]
        for i in range(2, n):
            fib_list.append(fib_list[i
```

---

### Entry 73: `wiki_leads/Margaret_Thatcher.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5250
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'eader of the Conservative Party from 1975 to 1990. She was the '`

#### Prompt
```text
Margaret Hilda Thatcher, Baroness Thatcher was a British stateswoman who served as Prime Minister of the United Kingdom from 1979 to 1990 and
```

#### True Continuation
```text
Leader of the Conservative Party from 1975 to 1990. She was the longest-serving British prime minister of the 20th century and the first woman to hold the office. As prime minister, she implemented policies that came to be known as Th
```

#### Generated Continuation
```text
was the leader of the Conservative Party from 1975 to 1990. She was the first and, to date, the only woman to hold the office of Prime Minister in the UK.

Margaret Thatcher was born on October 13,
```

---

### Entry 74: `code_snippets/Knuth_shuffle.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5238
* **Matched Token Count**: 15
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `"a]\ndef knuthShuffle(xs):\n    '''A "`

#### Prompt
```text
'''Knuth shuffle as a fold'''

from functools import reduce
from random import randint


# knuthShuffle :: [a] -> IO [
```

#### True Continuation
```text
a]
def knuthShuffle(xs):
    '''A pseudo-random shuffle of the elements in xs.'''
    return reduce(
        swapped,
        enumerate(randoms(len(xs))), xs
    )


# swapped ::
```

#### Generated Continuation
```text
a]
def knuthShuffle(xs):
    '''A Knuth shuffle of a list.'''
    return reduce(
        lambda (acc, x): knuthShuffleHelper(acc, x),
        xs,
        ([], xs)
    )
```

---

### Entry 75: `wiki_leads/Napoleon.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5227
* **Matched Token Count**: 3
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'n during the Hundred Days in 1815. He rose to prominence '`

#### Prompt
```text
Napoleon Bonaparte, later known by his regnal name Napoleon I, was Emperor of the French from 18 May 1804 until his first abdication in 18
```

#### True Continuation
```text
14, with a brief restoration during the Hundred Days in 1815. He rose to prominence as a general during the French Revolution and led a series of military campaigns across Europe and the Middle East during the French Revolutionary and Napoleonic Wars. As a
```

#### Generated Continuation
```text
14 and again during the Hundred Days in 1815. He rose to prominence during the French Revolution and led several successful campaigns during the Revolutionary Wars. He was a military leader who changed the face of warfare with his innovative use of artillery and
```

---

### Entry 76: `code_snippets/Matrix_multiplication.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5161
* **Matched Token Count**: 5
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `' 81),\n     (4, 16, 64, 256))\n\n'`

#### Prompt
```text
a=((1,  1,  1,   1), # matrix A #
     (2,  4,  8,  16),
     (3,  9
```

#### True Continuation
```text
, 27,  81),
     (4, 16, 64, 256))

b=((  4  , -3  ,  4/3.,  -1/4. ), # matrix B #
     (-1
```

#### Generated Continuation
```text
, 27, 81),
     (4, 16, 64, 256))

# +
# %%time

# Compute the matrix product
A @ B
# -

# ### Exercise 2
```

---

### Entry 77: `wiki_leads/Genghis_Khan.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5161
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `', he launched a series of military campaigns'`

#### Prompt
```text
Genghis Khan, also known as Chinggis Khan, was the founder and first khan of the Mongol Empire. After spending most of his life uniting the Mongol tribes
```

#### True Continuation
```text
, he launched a series of military campaigns, conquering large parts of China and Central Asia.
```

#### Generated Continuation
```text
, he launched a series of military campaigns that resulted in the creation of the largest contiguous
```

---

### Entry 78: `wiki_leads/Amazon_rainforest.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5143
* **Matched Token Count**: 19
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'most of the Amazon basin of South America. This basin encompasses 7'`

#### Prompt
```text
The Amazon rainforest, also called the Amazon jungle, Amazonia, or simply the Amazon, is a moist broadleaf tropical rainforest in the Amazon biome that covers
```

#### True Continuation
```text
most of the Amazon basin of South America. This basin encompasses 7 million km2 (2.7 million sq mi), of which 6 million km2 (2.3 million sq mi) are covered by the rainforest. This region includes territory belonging to nine
```

#### Generated Continuation
```text
most of the Amazon basin of South America. This basin encompasses 7,000,000 square kilometers (2,700,000 sq mi), of which 5,500,000 square kilometers (2
```

---

### Entry 79: `wiki_leads/OpenCL.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5122
* **Matched Token Count**: 11
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'OpenCL provides a standard interface for parallel'`

#### Prompt
```text
OpenCL is a framework for writing programs that execute across heterogeneous platforms consisting of central processing units (CPUs), graphics processing units (GPUs), digital signal processors (DSPs),
```

#### True Continuation
```text
field-programmable gate arrays (FPGAs) and other processors or hardware accelerators. OpenCL specifies a programming language for programming these devices and application programming interfaces (APIs) to control the platform and execute programs on the compute devices. OpenCL provides a standard interface for parallel
```

#### Generated Continuation
```text
field-programmable gate arrays (FPGAs), and other processors or hardware accelerators. It is used for general-purrunded computing and is particularly well-suited for high-performance computing applications that require parallel processing.

OpenCL provides a standard interface for parallel
```

---

### Entry 80: `code_snippets/Audio_overlap_loop.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5106
* **Matched Token Count**: 0
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'):\n    for i in range(count):\n        '`

#### Prompt
```text
import sys
import time
from threading import Thread

from playsound import playsound

FILE = "loop.wav"


def play(count: int, delay
```

#### True Continuation
```text
=0):
    for i in range(count):
        t = Thread(target=playsound, args=(FILE,))
        t.start()
        time.sleep(delay)

    t.join()


def main():
    if len(
```

#### Generated Continuation
```text
: int):
    for i in range(count):
        playsound(FILE)
        time.sleep(delay)


def main():
    count = int(sys.argv[1])
    delay = int(sys.argv[2])
    Thread
```

---

### Entry 81: `code_snippets/Abelian_sandpile_model_Identity.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5098
* **Matched Token Count**: 5
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'.split()]\n        self.grid = defaultdict(int,'`

#### Prompt
```text
from itertools import product
from collections import defaultdict


class Sandpile():
    def __init__(self, gridtext):
        array = [int(x) for
```

#### True Continuation
```text
x in gridtext.strip().split()]
        self.grid = defaultdict(int,
                                {(i //3, i % 3): x 
                                 for i, x in enumerate(array)})

    _border = set((r, c
```

#### Generated Continuation
```text
x in gridtext.split()]
        self.grid = defaultdict(int, {(i, j): array[i * 5 + j] for i in range(5) for j in range(5)})

    def topple(self):
```

---

### Entry 82: `code_snippets/Audio_alarm.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
import time
import os

seconds = input("Enter a number of seconds: ")
sound = input("Enter an mp3 filename: ")

time.sleep(float(seconds))
```

#### True Continuation
```text
os.startfile(sound + ".mp3")
```

#### Generated Continuation
```text
os.system("start " + sound)
```

---

### Entry 83: `wiki_leads/Ethereum.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 2
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
Ethereum is a decentralized blockchain with smart contract functionality. Ether is the native cryptocurrency of the platform. Among cryptocurrencies, ether is second only to bit
```

#### True Continuation
```text
coin in market capitalization. It is open-source software.
```

#### Generated Continuation
```text
coin in terms of market capitalization.

### Inst
```

---

### Entry 84: `wiki_leads/Netherlands.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'of the Kingdom of the Netherlands. The Netherlands '`

#### Prompt
```text
The Netherlands, also informally known as Holland, is a country in Northwestern Europe, with overseas territories in the Caribbean. It is the largest of the four constituent countries
```

#### True Continuation
```text
of the Kingdom of the Netherlands. The Netherlands consists of twelve provinces and three overseas special municipalities. European Netherlands has land borders with Germany to the east and with Belgium to the south, and a coastline to the north and west. It shares maritime borders with the United Kingdom,
```

#### Generated Continuation
```text
of the Kingdom of the Netherlands. The Netherlands is bordered by Germany to the east, Belgium to the south, and the North Sea to the north and west. The constitutionally separate island countries of Aruba, Curaçao, and Sint Maarten have been combined into the Netherlands as
```

---

### Entry 85: `wiki_leads/Public_key_infrastructure.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 5
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
A public key infrastructure (PKI) is a set of roles, policies, hardware, software and procedures used to create, manage, distribute, use, store and revoke digital certificates
```

#### True Continuation
```text
and manage public-key cryptography set-ups.
```

#### Generated Continuation
```text
and manage public-key encryption. The primary purpose of
```

---

### Entry 86: `code_snippets/ABC_correlation.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 4
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
from collections import Counter
from typing import Iterable
from typing import Iterator


def equal_abcs(word: str, n: int = 0) -> bool:
```

#### True Continuation
```text
"""Return true if the number of a's, b's and c's in _word_ are equal
    and _word_ contains at least _n_ a's.
    """
    counter = Counter(a=0, b=0
```

#### Generated Continuation
```text
"""
    Check if the given word has equal number of a's, b's, c's and d's.

    :param word: The word to check.
    :param n: The number of a's, b's,
```

---

### Entry 87: `code_snippets/99_bottles_of_beer.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 4
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)

#### Prompt
```text
VERSE = '''\
{n} bottle{s} of beer on the wall
{n} bottle{s} of beer
Take one down, pass it
```

#### True Continuation
```text
around
{n_minus_1} bottle{s2} of beer on the wall

'''


for n in range(99, 0, -1):
    if n == 1:
        n_minus_1 = 'No more
```

#### Generated Continuation
```text
around
{n-1} bottle{s} of beer on the wall
'''

def count_bottles(n):
    if n == 0:
        return
    print(VERSE.format(n=n, s='s' if
```

---

### Entry 88: `wiki_leads/Sahara_desert.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 9
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'it is the largest hot desert in the world'`

#### Prompt
```text
The Sahara is a desert spanning North Africa. With an area of 9,200,000 square kilometres (3,600,000 sq mi),
```

#### True Continuation
```text
it is the largest hot desert in the world and the third-largest desert overall, smaller only than the deserts of Antarctica and the northern Arctic.
```

#### Generated Continuation
```text
it is the largest hot desert in the world. The desert stretches from the Atlantic Ocean in the west to the Indian Ocean in the east, and from the Mediter
```

---

### Entry 89: `code_snippets/Active_Directory_Connect.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 24
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'3\n    l.set_option(ldap.OPT_REFERRALS, 0)\n'`
* **[FLAG] Possible Extraction Bug**: High percentage of numbered lines (2/5)

#### Prompt
```text
import ldap

l = ldap.initialize("ldap://ldap.example.com")
try:
    l.protocol_version = ldap.VERSION
```

#### True Continuation
```text
3
    l.set_option(ldap.OPT_REFERRALS, 0)

    bind = l.simple_bind_s("me@example.com", "password")
finally:
    l.unbind()
```

#### Generated Continuation
```text
3
    l.set_option(ldap.OPT_REFERRALS, 0)
    l.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
    l.set_option
```

---

### Entry 90: `code_snippets/Knapsack_problem_0-1.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 16
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `'(items)+1)\n             for comb in combinations(items, r)'`

#### Prompt
```text
from itertools import combinations

def anycomb(items):
    ' return combinations of any length from the items '
    return ( comb
             for r in range(1, len
```

#### True Continuation
```text
(items)+1)
             for comb in combinations(items, r)
             )

def totalvalue(comb):
    ' Totalise a particular combination of items'
    totwt = totval = 0
    for item, wt, val in comb:
```

#### Generated Continuation
```text
(items)+1)
             for comb in combinations(items, r) )

def anycomb_dict(items):
    ' return combinations of any length from the items as dicts '
    return ( dict(comb) for comb in anycomb(items) )
```

---

### Entry 91: `code_snippets/Binary_digits.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.5000
* **Matched Token Count**: 30
* **Flag Reason**: Borderline ROUGE-L (0.5-0.7)
* **[FLAG] Strong Memorization Match**: `"'100', '5': '101', '6': '110', '7': '111'}\n"`

#### Prompt
```text
>>> oct2bin = {'0': '000', '1': '001', '2': '010', '3': '011', '4':
```

#### True Continuation
```text
'100', '5': '101', '6': '110', '7': '111'}
>>> bin = lambda n: ''.join(oct2bin[octdigit] for octdigit in '%o' % n).lstrip
```

#### Generated Continuation
```text
'100', '5': '101', '6': '110', '7': '111'}
    >>> oct2bin('7')
    '111'
    >>> oct2bin('10')
    '01
```

---

### Entry 92: `wiki_leads/Vladimir_Lenin.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4923
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.49) with high exact prefix match (11 tokens)

#### Prompt
```text
Vladimir Ilyich Ulyanov, better known as Vladimir Lenin, was a Russian revolutionary, politician and political theorist. He was the first head of government of Soviet Russia from
```

#### True Continuation
```text
1917 to 1922, and the first head of government of the Soviet Union from 1922 until his death in 1924. As the Bolsheviks' founder, Lenin led the October Revolution, which established the world'
```

#### Generated Continuation
```text
1917 to 1922 and of the Soviet Union from 1922 to 1923. Lenin was a key political leader of the Bolsheviks, the party that led the October Revolution in Russia in 1917.
```

---

### Entry 93: `code_snippets/Binomial_transform.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4889
* **Matched Token Count**: 14
* **Flag Reason**: Low ROUGE-L (0.49) with high exact prefix match (14 tokens)
* **[FLAG] Strong Memorization Match**: `':\n    return factorial(n) // (factorial('`

#### Prompt
```text
from math import factorial
from math import pow

from typing import Iterable
from typing import Sequence


def binomial(n: int, k: int) -> int
```

#### True Continuation
```text
:
    return factorial(n) // (factorial(n - k) * factorial(k))


def binomial_transform(seq: Sequence) -> Iterable[int]:
    for n in range(len(seq)):
        yield sum(
```

#### Generated Continuation
```text
:
    return factorial(n) // (factorial(k) * factorial(n - k))


def binomial_coefficient(n: int, k: int) -> int:
    return binomial(n, k)


def bin
```

---

### Entry 94: `code_snippets/Anagrams.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4889
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.49) with high exact prefix match (11 tokens)
* **[FLAG] Strong Memorization Match**: `"dict.txt').read().split()\n>>> "`

#### Prompt
```text
>>> import urllib
>>> from collections import defaultdict
>>> words = urllib.urlopen('http://wiki.puzzlers.org/pub/wordlists/unix
```

#### True Continuation
```text
dict.txt').read().split()
>>> len(words)
25104
>>> anagram = defaultdict(list) # map sorted chars to anagrams
>>> for word in words:
	anagram[tuple(sorted(word))].
```

#### Generated Continuation
```text
dict.txt').read().split()
>>> word_count = defaultdict(int)
>>> for word in words:
...     word_count[word] += 1
>>> word_count['the']
1112
>>> word_count
```

---

### Entry 95: `code_snippets/10001th_prime.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4889
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.49) with high exact prefix match (10 tokens)
* **[FLAG] Strong Memorization Match**: `'% i == 0:\n            return Fals'`

#### Prompt
```text
#!/usr/bin/python

def isPrime(n):
    for i in range(2, int(n**0.5) + 1):
        if n
```

#### True Continuation
```text
% i == 0:
            return False        
    return True

def prime(n: int) -> int:
    if n == 1:
        return 2
    p = 3
    pn = 1
    while pn < n
```

#### Generated Continuation
```text
% i == 0:
            return False
    return True

def primes(n):
    for i in range(2, n):
        if isPrime(i):
            print(i)

primes(100)

#
```

---

### Entry 96: `code_snippets/Bernoulli_numbers.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4783
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.48) with high exact prefix match (10 tokens)

#### Prompt
```text
from fractions import Fraction as Fr

def bernoulli(n):
    A = [0] * (n+1)
    for m in range(n+
```

#### True Continuation
```text
1):
        A[m] = Fr(1, m+1)
        for j in range(m, 0, -1):
          A[j-1] = j*(A[j-1] - A[j])
    return A[
```

#### Generated Continuation
```text
1):
        A[m] = (-1)**m / (m+1)
    return A

def bernoulli_sum(n):
    A = bernoulli(n)
    return sum(A)

def bern
```

---

### Entry 97: `code_snippets/LU_decomposition.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4762
* **Matched Token Count**: 23
* **Flag Reason**: Low ROUGE-L (0.48) with high exact prefix match (23 tokens)
* **[FLAG] Strong Memorization Match**: `', eb in zip(a, b)) for b in TB] for a in A]\n\ndef '`

#### Prompt
```text
from pprint import pprint

def matrixMul(A, B):
    TB = list(zip(*B))
    return [[sum(ea * eb for ea
```

#### True Continuation
```text
, eb in zip(a, b)) for b in TB] for a in A]

def pivotize(m):
    """Creates the pivoting matrix for m."""
    n = len(m)
    ID = [[float(i == j)
```

#### Generated Continuation
```text
, eb in zip(a, b)) for b in TB] for a in A]

def matrixAdd(A, B):
    return [[a + b for a, b in zip(a, b)] for a, b in zip(A, B)]
```

---

### Entry 98: `code_snippets/Loops_Nested.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4706
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.47) with high exact prefix match (11 tokens)

#### Prompt
```text
from random import randint

class Found20(Exception):
    pass

mat = [[randint(1, 20) for x in xrange(10)]
```

#### True Continuation
```text
for y in xrange(10)]

try:
    for row in mat:
        for item in row:
            print item,
            if item == 20:
                raise Found20
        print
except Found20:
    print
```

#### Generated Continuation
```text
for y in xrange(10)]

def find20(mat):
    for i in xrange(len(mat)):
        for j in xrange(len(mat[i])):
            if mat[i][j] == 20:
```

---

### Entry 99: `wiki_leads/Random_forest.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4688
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.47) with high exact prefix match (11 tokens)
* **[FLAG] Strong Memorization Match**: `'the random forest is the class selected by most trees.'`

#### Prompt
```text
Random forests or random decision forests is an ensemble learning method for classification, regression and other tasks that works by creating a multitude of decision trees during training. For classification tasks, the output of
```

#### True Continuation
```text
the random forest is the class selected by most trees. For regression tasks, the output is the average of the predictions of the trees. Random forests correct for decision trees' habit of overfitting to their training set.
```

#### Generated Continuation
```text
the random forest is the class selected by most trees.

Here' explanation of the process:

1. **Bootstrap Aggregating (Bagging):** Random forests use the bagging technique to create
```

---

### Entry 100: `code_snippets/Animation.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4500
* **Matched Token Count**: 12
* **Flag Reason**: Low ROUGE-L (0.45) with high exact prefix match (12 tokens)
* **[FLAG] Strong Memorization Match**: `'Qt5.QtWidgets import QApplication, QLabel'`

#### Prompt
```text
#!/usr/bin/env python3
import sys

from PyQt5.QtCore import QBasicTimer, Qt
from PyQt5.QtGui import QFont
from Py
```

#### True Continuation
```text
Qt5.QtWidgets import QApplication, QLabel


class Marquee(QLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.right_to_left_direction = True
        self
```

#### Generated Continuation
```text
Qt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLineEdit, QTextEdit, QPlainTextEdit


class MyWidget(QWidget):
    def __init__(self
```

---

### Entry 101: `code_snippets/Audio_frequency_generator.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4444
* **Matched Token Count**: 12
* **Flag Reason**: Low ROUGE-L (0.44) with high exact prefix match (12 tokens)
* **[FLAG] Strong Memorization Match**: `'freq = int(input("Enter frequency '`

#### Prompt
```text
import subprocess

def main():
    freq = 0

    while freq < 40 or freq > 10000:
        try:
```

#### True Continuation
```text
freq = int(input("Enter frequency in Hz (40 to 10000) : "))
        except ValueError as e:
            print(e)

    vol = 0

    while vol < 1 or vol
```

#### Generated Continuation
```text
freq = int(input("Enter frequency (40-10000 Hz): "))
        except ValueError:
            print("Please enter a valid number.")

    subprocess.run(["python", "sound_generator.py",
```

---

### Entry 102: `code_snippets/Append_numbers_at_same_position_in_strings.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4444
* **Matched Token Count**: 32
* **Flag Reason**: Low ROUGE-L (0.44) with high exact prefix match (32 tokens)

#### Prompt
```text
list1 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
list2 = [10, 1
```

#### True Continuation
```text
1, 12, 13, 14, 15, 16, 17, 18]
list3 = [19, 20, 21, 22, 23, 24,
```

#### Generated Continuation
```text
1, 12, 13, 14, 15, 16, 17, 18]

# Merge the two lists
merged_list = list1 + list2

# Sort the merged list
merged
```

---

### Entry 103: `code_snippets/Best_shuffle.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4400
* **Matched Token Count**: 22
* **Flag Reason**: Low ROUGE-L (0.44) with high exact prefix match (22 tokens)
* **[FLAG] Strong Memorization Match**: `'int)\n    for c in s:\n        count[c] += 1\n\n    # '`

#### Prompt
```text
#!/usr/bin/env python

def best_shuffle(s):
    # Count the supply of characters.
    from collections import defaultdict
    count = defaultdict(
```

#### True Continuation
```text
int)
    for c in s:
        count[c] += 1

    # Shuffle the characters.
    r = []
    for x in s:
        # Find the best character to replace x.
        best = None
        rankb =
```

#### Generated Continuation
```text
int)
    for c in s:
        count[c] += 1

    # Build the shuffled string.
    from random import shuffle
    shuffled = []
    for c, n in count.items():
        shuffled.
```

---

### Entry 104: `wiki_leads/Thomas_Jefferson.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4375
* **Matched Token Count**: 14
* **Flag Reason**: Low ROUGE-L (0.44) with high exact prefix match (14 tokens)

#### Prompt
```text
Thomas Jefferson was a Founding Father and the third president of the United States from 1801 to 1809. He also served as the second vice president under John Adams from
```

#### True Continuation
```text
1797 to 1801. Jefferson was the principal author of the Declaration of Independence in 1776.
```

#### Generated Continuation
```text
1797 to 1801. Jefferson was a prolific writer and thinker, and his contributions to the founding of
```

---

### Entry 105: `wiki_leads/Neuroscience.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4348
* **Matched Token Count**: 15
* **Flag Reason**: Low ROUGE-L (0.43) with high exact prefix match (15 tokens)
* **[FLAG] Strong Memorization Match**: `', molecular biology, developmental biology, cytology, '`

#### Prompt
```text
Neuroscience is the scientific study of the nervous system, its functions, and its disorders. It is a multidisciplinary science that combines physiology, anatomy
```

#### True Continuation
```text
, molecular biology, developmental biology, cytology, psychology, physics, computer science, chemistry, medicine, statistics, and mathematical modeling to understand the fundamental and emergent properties of neurons, glia, and neural circuits. The understanding of the biological
```

#### Generated Continuation
```text
, molecular biology, developmental biology, cytology, mathematical modeling, and psychology to understand the fundamental and clinical aspects of the nervous system.

The nervous system is divided into two main parts: the central nervous system (CNS) and the
```

---

### Entry 106: `wiki_leads/Belgium.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4337
* **Matched Token Count**: 17
* **Flag Reason**: Low ROUGE-L (0.43) with high exact prefix match (17 tokens)
* **[FLAG] Strong Memorization Match**: `'Netherlands to the north, Germany to the east, Luxembourg to the southeast, '`

#### Prompt
```text
Belgium, officially the Kingdom of Belgium, is a country in Northwestern Europe. Situated in a coastal lowland region known as the Low Countries, it is bordered by the
```

#### True Continuation
```text
Netherlands to the north, Germany to the east, Luxembourg to the southeast, France to the south, and the North Sea to the west. Belgium covers an area of 30,689 km2 (11,849 sq mi) and has a population of
```

#### Generated Continuation
```text
Netherlands to the north, Germany to the east, Luxembourg to the southeast, and France to the southwest. Belgium is a constitutional monarchy with a parliamentary system of government. The country is divided into three regions: Flanders in the north, Wallonia in the south,
```

---

### Entry 107: `wiki_leads/ROCm.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4286
* **Matched Token Count**: 18
* **Flag Reason**: Low ROUGE-L (0.43) with high exact prefix match (18 tokens)
* **[FLAG] Strong Memorization Match**: `'graphics processing units (GPGPU), high-performance computing (HPC), and '`

#### Prompt
```text
ROCm is an Advanced Micro Devices (AMD) software stack for graphics processing unit (GPU) programming. ROCm spans several domains, including general-purpose computing on
```

#### True Continuation
```text
graphics processing units (GPGPU), high-performance computing (HPC), and heterogeneous computing. It offers several programming models: HIP, OpenMP, and OpenCL.
```

#### Generated Continuation
```text
graphics processing units (GPGPU), high-performance computing (HPC), and machine learning (ML).

The primary purpose of ROCm is to provide a unified
```

---

### Entry 108: `wiki_leads/Immune_system.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4267
* **Matched Token Count**: 13
* **Flag Reason**: Low ROUGE-L (0.43) with high exact prefix match (13 tokens)

#### Prompt
```text
The immune system is a network of biological systems that protects an organism from diseases. It detects and responds to a wide variety of pathogens, such as viruses
```

#### True Continuation
```text
, bacteria, and parasites, as well as cancer cells and foreign objects, such as wood splinters—distinguishing them from the organism's own healthy tissue. Many species have two major subsystems of the immune system. The innate imm
```

#### Generated Continuation
```text
, bacteria, and parasites, as well as the body'ieves that are foreign to the body, such as transplanted organs and tissues.

The immune system is composed of two main parts: the innate immune system and the adaptive immune
```

---

### Entry 109: `wiki_leads/Ballet.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4198
* **Matched Token Count**: 15
* **Flag Reason**: Low ROUGE-L (0.42) with high exact prefix match (15 tokens)
* **[FLAG] Strong Memorization Match**: `'pread and highly technical form of dance with its own vocabulary'`

#### Prompt
```text
Ballet is a type of performance dance that originated during the Italian Renaissance in the fifteenth century and later developed into a concert dance form in France and Russia. It has since become a wides
```

#### True Continuation
```text
pread and highly technical form of dance with its own vocabulary. Ballet has been influential globally and has defined the foundational techniques which are used in many other dance genres and cultures. Various schools around the world have incorporated their own cultures. As a
```

#### Generated Continuation
```text
pread and highly technical form of dance with its own vocabulary, performance techniques, and aesthetic standards.

The term "ballet" comes from the Italian word "balletto," which means "little dance." Ballet was initially performed as part of a
```

---

### Entry 110: `wiki_leads/Monitor_(synchronization).txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4167
* **Matched Token Count**: 16
* **Flag Reason**: Low ROUGE-L (0.42) with high exact prefix match (16 tokens)
* **[FLAG] Strong Memorization Match**: `'threads to temporarily give up exclusive access in order to wait for some condition to be'`

#### Prompt
```text
In concurrent programming, a monitor is a synchronization construct that prevents threads from concurrently accessing a shared object's state and allows them to wait for the state to change. They provide a mechanism for
```

#### True Continuation
```text
threads to temporarily give up exclusive access in order to wait for some condition to be met, before regaining exclusive access and resuming their task. A monitor consists of a mutex (lock) and at least one condition variable. A condition variable is explicitly 'signalled' when the object'
```

#### Generated Continuation
```text
threads to temporarily give up exclusive access in order to wait for some condition to become true.

Monitors are used to ensure that only one thread can access the critical section of code at a time, which is essential for preventing race conditions and ensuring data consistency. They encaps
```

---

### Entry 111: `code_snippets/ASCII_art_diagram_converter.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4091
* **Matched Token Count**: 15
* **Flag Reason**: Low ROUGE-L (0.41) with high exact prefix match (15 tokens)
* **[FLAG] Strong Memorization Match**: `'.org/wiki/ASCII_art_diagram_converter'`

#### Prompt
```text
"""
http://rosettacode.org/wiki/ASCII_art_diagram_converter

Python example based off Go example:

http://rosettacode
```

#### True Continuation
```text
.org/wiki/ASCII_art_diagram_converter#Go

"""

def validate(diagram):

    # trim empty lines
    
    rawlines = diagram.splitlines()
    lines = []
    for line in rawlines
```

#### Generated Continuation
```text
.org/wiki/ASCII_art_diagram_converter/Go

Author:
  Sam Slinn

Date:
  May 2015

Description:
  Converts a diagram (ASCII art) into a diagram (ASC
```

---

### Entry 112: `code_snippets/Maze_generation.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.4000
* **Matched Token Count**: 15
* **Flag Reason**: Low ROUGE-L (0.40) with high exact prefix match (15 tokens)

#### Prompt
```text
from random import shuffle, randrange

def make_maze(w = 16, h = 8):
    vis = [[0] * w + [1]
```

#### True Continuation
```text
for _ in range(h)] + [[1] * (w + 1)]
    ver = [["|  "] * w + ['|'] for _ in range(h)] + [[]]
    hor = [["+--"] * w + ['+']
```

#### Generated Continuation
```text
for _ in range(h)] + [[1] * (w + orum) + [0] * h]
    vis[0][0] = 1
    ctr = 1
    stack = [(0, 0)]
    dirs = [[0
```

---

### Entry 113: `wiki_leads/Regular_expression.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.4000
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.40) with high exact prefix match (10 tokens)
* **[FLAG] Strong Memorization Match**: `'" or "find and replace" operations on strings'`

#### Prompt
```text
A regular expression, sometimes referred to as a rational expression, is a sequence of characters that specifies a match pattern in text. Usually such patterns are used by string-searching algorithms for "find
```

#### True Continuation
```text
" or "find and replace" operations on strings, or for input validation. Regular expression techniques are developed in theoretical computer science and formal language theory.
```

#### Generated Continuation
```text
" or "find and replace" operations on strings.

In the context of the provided code snippet, the regular expression `r'\b[A
```

---

### Entry 114: `wiki_leads/Television.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3922
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.39) with high exact prefix match (11 tokens)
* **[FLAG] Strong Memorization Match**: `'medium for advertising, entertainmen'`

#### Prompt
```text
Television (TV) is a telecommunication medium for transmitting moving images and sound. Additionally, the term can refer to a physical television set rather than the medium of transmission. Television is a mass
```

#### True Continuation
```text
medium for advertising, entertainment, news, and sports. The medium is capable of more than "radio broadcasting", which refers to an audio signal sent to radio receivers.
```

#### Generated Continuation
```text
medium for advertising, entertainment, news, and educational purposes.

Television broadcasting is a method of transmitting moving images and sound from a source to a receiver
```

---

### Entry 115: `wiki_leads/Hypervisor.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3922
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.39) with high exact prefix match (11 tokens)
* **[FLAG] Strong Memorization Match**: `'runs one or more virtual machines is called a host machine'`

#### Prompt
```text
A hypervisor, also known as a virtual machine monitor (VMM), is a type of computer software, firmware or hardware that creates and runs virtual machines. A computer on which a hypervisor
```

#### True Continuation
```text
runs one or more virtual machines is called a host machine or virtualization server, and each virtual machine is called a guest machine. The hypervisor presents the guest operating systems with a virtual operating platform and manages the execution of the guest operating systems. Unlike an emulator, the guest executes most instructions
```

#### Generated Continuation
```text
runs one or more virtual machines is called a host machine.

The primary function of a hypervisor is to manage the system'ieves of a computer and allocate resources to the virtual machines (VMs) that run on it. It allows multiple operating systems to run concurrently on a host machine
```

---

### Entry 116: `code_snippets/Pascal's_triangle.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.3922
* **Matched Token Count**: 19
* **Flag Reason**: Low ROUGE-L (0.39) with high exact prefix match (19 tokens)
* **[FLAG] Strong Memorization Match**: `'result, x)\n    a.append(result)\n  retur'`

#### Prompt
```text
def scan(op, seq, it):
  a = []
  result = it
  a.append(it)
  for x in seq:
    result = op(
```

#### True Continuation
```text
result, x)
    a.append(result)
  return a

def pascal(n):
    def nextrow(row, x):
        return [l+r for l,r in zip(row+[0,],[0,]+row)]
```

#### Generated Continuation
```text
result, x)
    a.append(result)
  return a

def scan_left(op, seq, it):
  a = []
  result = it
  a.append(it)
  for x in seq:
    result = op(
```

---

### Entry 117: `code_snippets/Loops_N_plus_one_half.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.3902
* **Matched Token Count**: 15
* **Flag Reason**: Low ROUGE-L (0.39) with high exact prefix match (15 tokens)
* **[FLAG] Strong Memorization Match**: `'i += 1\n    if i > n:\n        brea'`

#### Prompt
```text
>>> from sys import stdout
>>> write = stdout.write
>>> n, i = 10, 1
>>> while True:
    write(i)
```

#### True Continuation
```text
i += 1
    if i > n:
        break
    write(', ')

    
1, 2, 3, 4, 5, 6, 7, 8, 9, 10
>>>
```

#### Generated Continuation
```text
i += 1
    if i > n:
        break

>>> write(i)
11

A:

You can use a for loop:
for i in range(1, 11):
    print(i
```

---

### Entry 118: `wiki_leads/Coal.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3855
* **Matched Token Count**: 16
* **Flag Reason**: Low ROUGE-L (0.39) with high exact prefix match (16 tokens)
* **[FLAG] Strong Memorization Match**: `'hydrogen, sulfur, oxygen, and nitrogen. It is '`

#### Prompt
```text
Coal is a combustible black or brownish-black sedimentary rock, formed as layers called coal seams. Coal is mostly carbon with variable amounts of other elements, chiefly
```

#### True Continuation
```text
hydrogen, sulfur, oxygen, and nitrogen. It is a fossil fuel, formed when plants decay into peat which is converted into coal by the heat and pressure of deep burial over millions of years. Vast deposits formed from wetlands called coal forests that
```

#### Generated Continuation
```text
hydrogen, sulfur, oxygen, and nitrogen. It is formed from the remains of vegetation which has been consolidated by heat and pressure over a long period of time.

The process of coal formation is known as coalification, which occurs in several stages:
```

---

### Entry 119: `code_snippets/Aliquot_sequence_classifications.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.3830
* **Matched Token Count**: 12
* **Flag Reason**: Low ROUGE-L (0.38) with high exact prefix match (12 tokens)

#### Prompt
```text
from proper_divisors import proper_divs
from functools import lru_cache


@lru_cache()
def pdsum(n):
```

#### True Continuation
```text
return sum(proper_divs(n))
    
    
def aliquot(n, maxlen=16, maxterm=2**47):
    if n == 0:
        return 'terminating', [0]
    s, sl
```

#### Generated Continuation
```text
return sum(proper_divs(n))


def is_amicable(n):
    return pdsum(n) == n


def amicable_numbers(n):
    return [i for i in range(1, n) if
```

---

### Entry 120: `code_snippets/Call_a_function.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.3774
* **Matched Token Count**: 18
* **Flag Reason**: Low ROUGE-L (0.38) with high exact prefix match (18 tokens)
* **[FLAG] Strong Memorization Match**: `'(x, y))\n# call\nfixed_args(1, 2)'`

#### Prompt
```text
def no_args():
    pass
# call
no_args()

def fixed_args(x, y):
    print('x=%r, y=%r' %
```

#### True Continuation
```text
(x, y))
# call
fixed_args(1, 2)        # x=1, y=2

## Can also called them using the parameter names, in either order:
fixed_args(y=2, x=1)

## Can
```

#### Generated Continuation
```text
(x, y))
# call
fixed_args(1, 2)

def kw_args(**kwargs):
    print('kwargs=%r' % kwargs)
# call
kw_args(a=1, b=2)

def var
```

---

### Entry 121: `code_snippets/Animated_snail.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.3750
* **Matched Token Count**: 12
* **Flag Reason**: Low ROUGE-L (0.37) with high exact prefix match (12 tokens)
* **[FLAG] Strong Memorization Match**: `'plot as plt\nfrom matplotlib.animation import FuncAnimation'`

#### Prompt
```text
""" Rosetta Code: Animated snail task """

from math import tau  # 2 * pi
from pathlib import Path
import numpy as np
import matplotlib.py
```

#### True Continuation
```text
plot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d.art3d import Line3DCollection


def generate_spiral(
    alpha: float,
    beta: float,
```

#### Generated Continuation
```text
plot as plt
from matplotlib.animation import FuncAnimation


def snail(n, m, r):
    """
    Draw an animated snail

    Parameters
    ----------
    n : int
        Number of frames
    m : int
```

---

### Entry 122: `code_snippets/Bioinformatics_Subsequence.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.3673
* **Matched Token Count**: 16
* **Flag Reason**: Low ROUGE-L (0.37) with high exact prefix match (16 tokens)

#### Prompt
```text
from random import choice
import regex as re 
import time

def generate_sequence(n: int ) -> str:
    return "".join([ choice(['A','C','
```

#### True Continuation
```text
G','T']) for _ in range(n) ])

def dna_findall(needle: str, haystack: str) -> None:

    if sum(1 for _ in re.finditer(needle, haystack, overlapped=
```

#### Generated Continuation
```text
G','T']) for _ in range(n) ])

def is_valid_sequence(sequence: str) -> bool:
    return bool(re.match(r'^[ACGT]+$', sequence))

def generate_and_validate_sequences
```

---

### Entry 123: `code_snippets/MD5.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.3636
* **Matched Token Count**: 28
* **Flag Reason**: Low ROUGE-L (0.36) with high exact prefix match (28 tokens)
* **[FLAG] Strong Memorization Match**: `'f00b204e9800998ecf8427e\'),\n  (b"a'`

#### Prompt
```text
>>> import hashlib
>>> # RFC 1321    test suite:
>>> tests = (
  (b"", 'd41d8cd98
```

#### True Continuation
```text
f00b204e9800998ecf8427e'),
  (b"a", '0cc175b9c0f1b6a831c399e2697726
```

#### Generated Continuation
```text
f00b204e9800998ecf8427e'),
  (b"abc", 'a99d9618bd2ad4f2"
  (b"message", '2ef7b37
```

---

### Entry 124: `wiki_leads/Don_Quixote.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3614
* **Matched Token Count**: 15
* **Flag Reason**: Low ROUGE-L (0.36) with high exact prefix match (15 tokens)

#### Prompt
```text
Don Quixote, the full title being The Ingenious Gentleman Don Quixote of La Mancha, is a Spanish novel by Miguel de Cervantes. Originally published in
```

#### True Continuation
```text
two parts in 1605 and 1615, the novel is considered a founding work of Western literature and the first modern novel. The novel has been labelled by many well-known authors as the "best novel of all time" and the "best and most central
```

#### Generated Continuation
```text
two parts in 1605 and 1615, it is a satire of the romantic chivalry traditions and a critique of the social and literary norms of the time. The novel tells the story of a nobleman named Alonso Quixano who
```

---

### Entry 125: `wiki_leads/Indus_Valley_civilisation.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3582
* **Matched Token Count**: 14
* **Flag Reason**: Low ROUGE-L (0.36) with high exact prefix match (14 tokens)

#### Prompt
```text
The Indus Valley Civilisation (IVC), also known as the Indus Civilisation, was a Bronze Age civilisation in the northwestern regions of South Asia, lasting from 3
```

#### True Continuation
```text
300 BCE to 1300 BCE, and in its mature form from 2600 BCE to 1900 BCE. Together with ancient Egypt and Mesopotamia, it was one of the three early civilisations
```

#### Generated Continuation
```text
300 BCE to 1300 BCE. It was one of the world' persisting urban cultures of the ancient world, along with Ancient Egypt and Mesopotamia. The Indus Valley Civilisation was the most extensive and advanced of its time,
```

---

### Entry 126: `wiki_leads/XML.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3562
* **Matched Token Count**: 13
* **Flag Reason**: Low ROUGE-L (0.36) with high exact prefix match (13 tokens)
* **[FLAG] Strong Memorization Match**: `'that is both human-readable and machine-readable. '`

#### Prompt
```text
Extensible Markup Language (XML) is a markup language and file format for storing, transmitting, and reconstructing data. It defines a set of rules for encoding documents in a format
```

#### True Continuation
```text
that is both human-readable and machine-readable. The World Wide Web Consortium's XML 1.0 Specification of 1998 and several other related specifications—all of them free open standards—define XML.
```

#### Generated Continuation
```text
that is both human-readable and machine-readable. XML is widely used for data interchange because it is both flexible and structured, allowing for the definition of custom tags and the nesting of elements.

XML is not a programming language;
```

---

### Entry 127: `wiki_leads/Round-robin_scheduling.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3488
* **Matched Token Count**: 12
* **Flag Reason**: Low ROUGE-L (0.35) with high exact prefix match (12 tokens)
* **[FLAG] Strong Memorization Match**: `'equal portions and in circular order, handling all processes without '`

#### Prompt
```text
Round-robin (RR) is one of the algorithms employed by process and network schedulers in computing. As the term is generally used, time slices are assigned to each process in
```

#### True Continuation
```text
equal portions and in circular order, handling all processes without priority. Round-robin scheduling is simple, easy to implement, and starvation-free. Round-robin scheduling can be applied to other scheduling problems, such as data packet scheduling in computer networks. It
```

#### Generated Continuation
```text
equal portions and in circular order, handling all processes without any priority. This ensures that all active processes get an equal share of the CPU time, which is particularly useful in a multi-tasking environment.

In a round-robin scheduling system, the operating system'ieves
```

---

### Entry 128: `wiki_leads/Norse_mythology.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3333
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.33) with high exact prefix match (10 tokens)
* **[FLAG] Strong Memorization Match**: `'ing after the Christianization o'`

#### Prompt
```text
Norse, Nordic, or Scandinavian mythology, is the body of myths belonging to the North Germanic peoples, stemming from Old Norse religion and continu
```

#### True Continuation
```text
ing after the Christianization of Scandinavia as the Nordic folklore of the modern period. The northernmost extension of Germanic mythology and stemming from Proto-Germanic folklore, Norse mythology consists of tales of various deities, beings,
```

#### Generated Continuation
```text
ing after the Christianization of Scandinavia. The mythology is preserved in the Icelandic medieval manuscripts known as the Eddas, as well as in later Scandinavian folklore.

The mythology is the subject of modern scholarly study in the
```

---

### Entry 129: `wiki_leads/Isolation_(database_systems).txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.3297
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.33) with high exact prefix match (11 tokens)
* **[FLAG] Strong Memorization Match**: `'to access the same data at the same time, but '`

#### Prompt
```text
In database systems, isolation is one of the ACID transaction properties. It determines how transaction integrity is visible to other users and systems. A lower isolation level increases the ability of many users
```

#### True Continuation
```text
to access the same data at the same time, but also increases the number of concurrency effects users might encounter. Conversely, a higher isolation level reduces the types of concurrency effects that users may encounter, but requires more system resources and increases the chances that one transaction will block another
```

#### Generated Continuation
```text
to access the same data at the same time, but it may lead to anomalies like dirty reads, non-repeatable reads, and phantom reads.

In the context of the provided SQL code, the transaction isolation level is set to `READ COMMITTED`.
```

---

### Entry 130: `code_snippets/Angles_(geometric),_normalization_and_conversion.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.3000
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.30) with high exact prefix match (11 tokens)

#### Prompt
```text
PI = 3.141592653589793
TWO_PI = 6.2831853071
```

#### True Continuation
```text
79586

def normalize2deg(a):
  while a < 0: a += 360
  while a >= 360: a -= 360
  return a
def normalize2grad(a):
```

#### Generated Continuation
```text
79586

def normalize_angle(angle):
    while angle > TWO_PI:
        angle -= TWO_PI
    while angle < 0:
        angle += TWO_PI
    return angle

def
```

---

### Entry 131: `code_snippets/100_doors.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.2941
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.29) with high exact prefix match (11 tokens)

#### Prompt
```text
doors = [False] * 100
for i in range(100):
   for j in range(i, 100, i+1):
```

#### True Continuation
```text
doors[j] = not doors[j]
   print("Door %d:" % (i+1), 'open' if doors[i] else 'close')
```

#### Generated Continuation
```text
doors[j] = not doors[j]

# Player's initial choice
initial_choice = 0

# Player switches their choice
initial_choice
```

---

### Entry 132: `wiki_leads/Obesity.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.2895
* **Matched Token Count**: 12
* **Flag Reason**: Low ROUGE-L (0.29) with high exact prefix match (12 tokens)
* **[FLAG] Strong Memorization Match**: `'as obese when their body mass index (BMI)'`

#### Prompt
```text
Obesity is a medical condition, considered a disease by multiple organizations, in which excess body fat has accumulated to such an extent that it can have negative effects on health. People are classified
```

#### True Continuation
```text
as obese when their body mass index (BMI)—a person's weight divided by the square of the person's height—is over 30 kg/m2; the range 25–30 kg/m2 is defined as overweight. Some East Asian
```

#### Generated Continuation
```text
as obese when their body mass index (BMI) is 30 or greater.

Obesity is a major risk factor for a number of diseases, including type 2 diabetes, cardiovascular disease, and certain types of cancer. It can also
```

---

### Entry 133: `code_snippets/Approximate_equality.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.2857
* **Matched Token Count**: 16
* **Flag Reason**: Low ROUGE-L (0.29) with high exact prefix match (16 tokens)
* **[FLAG] Strong Memorization Match**: `'1],\n              [10000000000000'`

#### Prompt
```text
from numpy import sqrt
from math import isclose

testvalues = [[100000000000000.01,           100
```

#### True Continuation
```text
000000000000.011],
              [100.01,                       100.011],
              [10000000000000.001 /
```

#### Generated Continuation
```text
000000000000.01],
              [100000000000000.01,           100000000000000.01],
```

---

### Entry 134: `code_snippets/Amicable_pairs.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.2857
* **Matched Token Count**: 13
* **Flag Reason**: Low ROUGE-L (0.29) with high exact prefix match (13 tokens)

#### Prompt
```text
'''Amicable pairs'''

from itertools import chain
from math import sqrt


# amicablePairsUpTo :: Int -> [(Int, Int)]
def
```

#### True Continuation
```text
amicablePairsUpTo(n):
    '''List of all amicable pairs
       of integers below n.
    '''
    sigma = compose(sum)(properDivisors)

    def amicable(x):
        y = s
```

#### Generated Continuation
```text
amicablePairsUpTo(n):
    '''
    Return all amicable pairs up to n.
    '''
    return list(
        filter(
            lambda (a, b): a != b and sumOfDivisors(a) == b and
```

---

### Entry 135: `wiki_leads/Virus.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.2703
* **Matched Token Count**: 12
* **Flag Reason**: Low ROUGE-L (0.27) with high exact prefix match (12 tokens)

#### Prompt
```text
A virus is a submicroscopic infectious agent that replicates only inside the living cells of an organism. Viruses infect all life forms, from animals and plants to microorgan
```

#### True Continuation
```text
isms, including bacteria and archaea. Viruses are found in almost every ecosystem on Earth and are the most numerous type of biological entity. Since the first discovery of a virus, the tobacco mosaic virus, in the 1890s
```

#### Generated Continuation
```text
isms, including bacteria and archaea.

Viruses are composed of genetic material, either DNA or RNA, surrounded by a protective coat of protein called a capsid. Some viruses also have an outer envelope made of lipids. Unlike b
```

---

### Entry 136: `wiki_leads/Mae_Jemison.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.2667
* **Matched Token Count**: 11
* **Flag Reason**: Low ROUGE-L (0.27) with high exact prefix match (11 tokens)
* **[FLAG] Strong Memorization Match**: `'aboard the Space Shuttle Endeavour '`

#### Prompt
```text
Mae Carol Jemison is an American engineer, physician, and former NASA astronaut. She became the first African-American woman to travel into space when she served as a mission specialist
```

#### True Continuation
```text
aboard the Space Shuttle Endeavour in 1992. Jemison joined NASA's astronaut corps in 1987 and was selected for the STS-47 mission, during which the Endeavour orbited the Earth for nearly eight days
```

#### Generated Continuation
```text
aboard the Space Shuttle Endeavour onboard mission STS-47 in 1992.

2. **Question:** What are the educational qualifications of Mae Carol Jemison?
   **Answer:** Mae Carol Jemison
```

---

### Entry 137: `wiki_leads/James_Joyce.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.2647
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.26) with high exact prefix match (10 tokens)

#### Prompt
```text
James Augustine Aloysius Joyce was an Irish novelist, poet, and literary critic. He contributed to the modernist movement and is regarded among the most influential and important writers of the
```

#### True Continuation
```text
20th century. Joyce's novel Ulysses (1922) is a landmark in which the episodes of Homer's Odyssey are paralleled in a variety of literary styles, particularly stream of consciousness. His other well-known works
```

#### Generated Continuation
```text
20th century. Joyce's most famous works are "Dubliners," a collection of short stories, and "Ulysses," a novel that is considered a masterpiece of modernist literature.

The term "modernist" refers to a broad
```

---

### Entry 138: `code_snippets/Knight's_tour.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.2609
* **Matched Token Count**: 15
* **Flag Reason**: Low ROUGE-L (0.26) with high exact prefix match (15 tokens)

#### Prompt
```text
import copy

boardsize=6
_kmoves = ((2,1), (1,2), (-1,2), (-2,1), (-2,-1), (-
```

#### True Continuation
```text
1,-2), (1,-2), (2,-1)) 


def chess2index(chess, boardsize=boardsize):
    'Convert Algebraic chess notation to internal index format'
    chess = chess.strip().lower
```

#### Generated Continuation
```text
1,-2), (1,-2), (2,-1))
_dmoves = ((1,0), (0,1), (1,1), (1,0), (-1,1), (-1,0), (-1,-1), (-1,0
```

---

### Entry 139: `wiki_leads/Internet.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.2588
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.26) with high exact prefix match (10 tokens)
* **[FLAG] Strong Memorization Match**: `', public, academic, business, and government networks'`

#### Prompt
```text
The Internet is the global system of interconnected computer networks that uses the Internet protocol suite (TCP/IP) to communicate between networks and devices. It is a network of networks that comprises private
```

#### True Continuation
```text
, public, academic, business, and government networks of local to global scope, linked by electronic, wireless, and optical networking technologies. The Internet carries a vast range of information services and resources, such as the interlinked hypertext documents and applications of the World Wide Web (W
```

#### Generated Continuation
```text
, public, academic, business, and government networks.

The Internet has a hierarchical structure, with the largest networks (like the NSFNET in the United States) interconnected to form the backbone, which in turn connects to regional networks, which then connect to local networks
```

---

### Entry 140: `book_openings/The_Adventures_of_Huckleberry_Finn.txt`

* **Category**: book_openings
* **ROUGE-L Score**: 0.2529
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.25) with high exact prefix match (10 tokens)
* **[FLAG] Strong Memorization Match**: `'Mr. Mark Twain, and he told the '`

#### Prompt
```text
. You don’t know about me without you have read a book by the name of The Adventures of Tom Sawyer; but that ain’t no matter. That book was made by
```

#### True Continuation
```text
Mr. Mark Twain, and he told the truth, mainly. There was things which he stretched, but mainly he told the truth. That is nothing. I never seen anybody but lied one time or another, without it was Aunt Polly, or the widow, or maybe
```

#### Generated Continuation
```text
Mr. Mark Twain, and he told the story quite well. Tom Sawyer has been dead many years, and the grave is overgrown with weeds.

Tom Sawyer was a clever boy, and he had a great many friends. He was always up to some
```

---

### Entry 141: `book_openings/Great_Expectations.txt`

* **Category**: book_openings
* **ROUGE-L Score**: 0.2444
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.24) with high exact prefix match (10 tokens)
* **[FLAG] Strong Memorization Match**: `'ip, and came to be called Pip.'`

#### Prompt
```text
. My father’s family name being Pirrip, and my Christian name Philip, my infant tongue could make of both names nothing longer or more explicit than Pip. So, I called myself P
```

#### True Continuation
```text
ip, and came to be called Pip. I give Pirrip as my father’s family name, on the authority of his tombstone and my sister,—Mrs. Joe Gargery, who married the blacksmith. As I never saw my father or my mother, and
```

#### Generated Continuation
```text
ip, and came to be called Pip.

I was a little man, with fair hair and a fair skin. I was a little bit plump, and I was not a little bit lonely. I was a little boy of fifteen years of age, and I was raised at
```

---

### Entry 142: `wiki_leads/Magna_Carta.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.2410
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.24) with high exact prefix match (10 tokens)

#### Prompt
```text
Magna Carta, sometimes spelled Magna Charta, is a royal charter of rights sealed by King John of England at Runnymede, near Windsor, on
```

#### True Continuation
```text
15 June 1215. First drafted by the Archbishop of Canterbury, Cardinal Stephen Langton, to make peace between the unpopular king and a group of rebel barons who demanded that the King confirm the Charter of Liberties, it promised
```

#### Generated Continuation
```text
15 June 1215. It is a foundational document in the history of constitutional law and has had a lasting impact on the development of legal systems around the world.

The Magna Carta was originally intended to resolve a political crisis between King John and a
```

---

### Entry 143: `wiki_leads/Skyscraper.txt`

* **Category**: wiki_leads
* **ROUGE-L Score**: 0.2388
* **Matched Token Count**: 10
* **Flag Reason**: Low ROUGE-L (0.24) with high exact prefix match (10 tokens)

#### Prompt
```text
A skyscraper is a very tall building or otherwise permanently habitable structure, typically defined as reaching a minimum height of either 100 metres (328 ft) or
```

#### True Continuation
```text
150 metres (492 ft) in height; however, there remains no universally accepted definition of a skyscraper, other than being a high-rise. Skyscrapers can host a variety of spaces, typically including office, commercial, hotel, and
```

#### Generated Continuation
```text
150 metres (492 ft). Skyscrapers are a common feature of modern city skylines.

Skyscrapers are a relatively recent phenomenon, first appearing in the late 19th century. The Home Insurance Building in Chicago
```

---

### Entry 144: `code_snippets/Air_mass.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.2069
* **Matched Token Count**: 14
* **Flag Reason**: Low ROUGE-L (0.21) with high exact prefix match (14 tokens)

#### Prompt
```text
""" Rosetta Code task: Air_mass """

from math import sqrt, cos, exp

DEG = 0.01745329251
```

#### True Continuation
```text
9943295769236907684886127134  # degrees to radians
RE = 6371000                                     # Earth radius in meters
dd = 0.
```

#### Generated Continuation
```text
994329576923643886 # Degrees to radians

def air_mass(altitude):
    """
    Calculate the air mass for a given altitude.

    Parameters
    -
```

---

### Entry 145: `code_snippets/Van_Eck_sequence.txt`

* **Category**: code_snippets
* **ROUGE-L Score**: 0.1935
* **Matched Token Count**: 12
* **Flag Reason**: Low ROUGE-L (0.19) with high exact prefix match (12 tokens)

#### Prompt
```text
'''Van Eck series by map-accumulation'''

from functools import reduce
from itertools import repeat


# vanEck :: Int -> [Int]
```

#### True Continuation
```text
def vanEck(n):
    '''First n terms of the vanEck sequence.'''
    def go(xns, i):
        x, ns = xns

        prev = ns[x]
        v = i - prev if 0
```

#### Generated Continuation
```text
def vanEck(n):
    '''A van Eck series.
       The first number is 0.
       Each subsequent number is the previous number that was last seen
       n steps back.
       If there is no such number, the next number is n
```

---
