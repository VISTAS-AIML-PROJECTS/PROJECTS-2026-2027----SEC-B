# LLM Probe - Merged Borderline Rows Spot-Check Sample

This file contains a representative sample of 20 newly merged borderline rows
(10 labeled 'memorized', 10 labeled 'novel') for manual verification.

## Merged Rows Summary statistics
- **Total Merged Rows**: 139
- **Label Breakdown**:
  - `NOVEL`: 109
  - `MEMORIZED`: 30
- **Category Breakdown**:
  - `code_snippets`: 76
  - `wiki_leads`: 58
  - `book_openings`: 5

---

## Sampled Rows for Review

### Row 1: wiki_leads/Vladimir_Lenin.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.4923`
- **Matched Token Count**: `11`
- **Longest Common N-gram Len**: `6`

**Prompt**:
```text
Vladimir Ilyich Ulyanov, better known as Vladimir Lenin, was a Russian revolutionary, politician and political theorist. He was the first head of government of Soviet Russia from
```

**Generated Continuation**:
```text
1917 to 1922 and of the Soviet Union from 1922 to 1923. Lenin was a key political leader of the Bolsheviks, the party that led the October Revolution in Russia in 1917.
```

**True Continuation**:
```text
1917 to 1922, and the first head of government of the Soviet Union from 1922 until his death in 1924. As the Bolsheviks' founder, Lenin led the October Revolution, which established the world'
```

---

### Row 2: wiki_leads/Random_forest.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.4688`
- **Matched Token Count**: `11`
- **Longest Common N-gram Len**: `10`

**Prompt**:
```text
Random forests or random decision forests is an ensemble learning method for classification, regression and other tasks that works by creating a multitude of decision trees during training. For classification tasks, the output of
```

**Generated Continuation**:
```text
the random forest is the class selected by most trees.

Here' explanation of the process:

1. **Bootstrap Aggregating (Bagging):** Random forests use the bagging technique to create
```

**True Continuation**:
```text
the random forest is the class selected by most trees. For regression tasks, the output is the average of the predictions of the trees. Random forests correct for decision trees' habit of overfitting to their training set.
```

---

### Row 3: wiki_leads/Internet.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.2588`
- **Matched Token Count**: `10`
- **Longest Common N-gram Len**: `6`

**Prompt**:
```text
The Internet is the global system of interconnected computer networks that uses the Internet protocol suite (TCP/IP) to communicate between networks and devices. It is a network of networks that comprises private
```

**Generated Continuation**:
```text
, public, academic, business, and government networks.

The Internet has a hierarchical structure, with the largest networks (like the NSFNET in the United States) interconnected to form the backbone, which in turn connects to regional networks, which then connect to local networks
```

**True Continuation**:
```text
, public, academic, business, and government networks of local to global scope, linked by electronic, wireless, and optical networking technologies. The Internet carries a vast range of information services and resources, such as the interlinked hypertext documents and applications of the World Wide Web (W
```

---

### Row 4: wiki_leads/Immune_system.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.4267`
- **Matched Token Count**: `13`
- **Longest Common N-gram Len**: `7`

**Prompt**:
```text
The immune system is a network of biological systems that protects an organism from diseases. It detects and responds to a wide variety of pathogens, such as viruses
```

**Generated Continuation**:
```text
, bacteria, and parasites, as well as the body'ieves that are foreign to the body, such as transplanted organs and tissues.

The immune system is composed of two main parts: the innate immune system and the adaptive immune
```

**True Continuation**:
```text
, bacteria, and parasites, as well as cancer cells and foreign objects, such as wood splinters—distinguishing them from the organism's own healthy tissue. Many species have two major subsystems of the immune system. The innate imm
```

---

### Row 5: wiki_leads/Ballet.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.4198`
- **Matched Token Count**: `15`
- **Longest Common N-gram Len**: `10`

**Prompt**:
```text
Ballet is a type of performance dance that originated during the Italian Renaissance in the fifteenth century and later developed into a concert dance form in France and Russia. It has since become a wides
```

**Generated Continuation**:
```text
pread and highly technical form of dance with its own vocabulary, performance techniques, and aesthetic standards.

The term "ballet" comes from the Italian word "balletto," which means "little dance." Ballet was initially performed as part of a
```

**True Continuation**:
```text
pread and highly technical form of dance with its own vocabulary. Ballet has been influential globally and has defined the foundational techniques which are used in many other dance genres and cultures. Various schools around the world have incorporated their own cultures. As a
```

---

### Row 6: wiki_leads/Amazon_rainforest.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.5143`
- **Matched Token Count**: `19`
- **Longest Common N-gram Len**: `11`

**Prompt**:
```text
The Amazon rainforest, also called the Amazon jungle, Amazonia, or simply the Amazon, is a moist broadleaf tropical rainforest in the Amazon biome that covers
```

**Generated Continuation**:
```text
most of the Amazon basin of South America. This basin encompasses 7,000,000 square kilometers (2,700,000 sq mi), of which 5,500,000 square kilometers (2
```

**True Continuation**:
```text
most of the Amazon basin of South America. This basin encompasses 7 million km2 (2.7 million sq mi), of which 6 million km2 (2.3 million sq mi) are covered by the rainforest. This region includes territory belonging to nine
```

---

### Row 7: book_openings/Alice's_Adventures_Underground.txt
- **Category**: `book_openings`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.5682`
- **Matched Token Count**: `13`
- **Longest Common N-gram Len**: `10`

**Prompt**:
```text
[Illustration] Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was
```

**Generated Continuation**:
```text
reading, but it had no pictures or conversations in it, 'and what is the use of a book,' thought Alice 'without pictures or conversations?'

# Answer
The illustration for this excerpt from "Alice' Premier Duel: Alice and her sister are sitting
```

**True Continuation**:
```text
reading, but it had no pictures or conversations in it, and where is the use of a book, thought Alice, without pictures or conversations? So she was considering in her own mind, (as well as she could, for the hot day made her feel very sleepy and stupid,
```

---

### Row 8: wiki_leads/Man-in-the-middle_attack.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.6667`
- **Matched Token Count**: `14`
- **Longest Common N-gram Len**: `11`

**Prompt**:
```text
In cryptography and computer security, a man-in-the-middle (MITM) attack, or on-path attack, is a cyberattack where the attacker secretly rel
```

**Generated Continuation**:
```text
ays and possibly alters the communications between two parties who believe they are directly communicating with each other. The attacker aims to intercept, read, and modify the messages without the knowledge
```

**True Continuation**:
```text
ays and possibly alters the communications between two parties who believe that they are directly communicating with each other, where in actuality the attacker has inserted themselves between the two user parties.
```

---

### Row 9: wiki_leads/William_Shakespeare.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.5897`
- **Matched Token Count**: `15`
- **Longest Common N-gram Len**: `9`

**Prompt**:
```text
William Shakespeare was an English playwright, poet and actor. He is widely regarded as the greatest writer in the English language and the world's pre-eminent dramatist. He is
```

**Generated Continuation**:
```text
often called England's national poet and the "Bard of Avon". His extant works include 39 plays, 154 sonnets, and two long narrative poems. His plays have been translated into every major language and are performed more often than those of any
```

**True Continuation**:
```text
often called England's national poet and the "Bard of Avon" or simply "the Bard". His extant works, including collaborations, consist of some 39 plays, 154 sonnets, three long narrative poems and a few other verses
```

---

### Row 10: wiki_leads/Neuroscience.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`MEMORIZED`**
- **ROUGE-L Score**: `0.4348`
- **Matched Token Count**: `15`
- **Longest Common N-gram Len**: `6`

**Prompt**:
```text
Neuroscience is the scientific study of the nervous system, its functions, and its disorders. It is a multidisciplinary science that combines physiology, anatomy
```

**Generated Continuation**:
```text
, molecular biology, developmental biology, cytology, mathematical modeling, and psychology to understand the fundamental and clinical aspects of the nervous system.

The nervous system is divided into two main parts: the central nervous system (CNS) and the
```

**True Continuation**:
```text
, molecular biology, developmental biology, cytology, psychology, physics, computer science, chemistry, medicine, statistics, and mathematical modeling to understand the fundamental and emergent properties of neurons, glia, and neural circuits. The understanding of the biological
```

---

### Row 11: wiki_leads/Isaac_Newton.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.5507`
- **Matched Token Count**: `2`
- **Longest Common N-gram Len**: `4`

**Prompt**:
```text
Sir Isaac Newton was an English polymath who was a mathematician, physicist, astronomer, alchemist, theologian, author and inventor. He was a key figure
```

**Generated Continuation**:
```text
in the scientific revolution, and his book "Philosophiæ Naturalis Principia Mathematica" (Mathematical Principles of Natural Philosophy), first published in 1687, laid the foundations for classical mechanics. Newton's work in mathematics, particularly
```

**True Continuation**:
```text
in the Scientific Revolution and the Enlightenment that followed. His book Philosophiæ Naturalis Principia Mathematica, first published in 1687, achieved the first great unification in physics and established classical mechanics. Newton also made seminal contributions to opt
```

---

### Row 12: code_snippets/Reverse_a_string.txt
- **Category**: `code_snippets`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.6667`
- **Matched Token Count**: `5`
- **Longest Common N-gram Len**: `2`

**Prompt**:
```text
import unicodedata

def ureverse(ustring):
    'Reverse a string including unicode combining characters'
    groupedchars = []
    uchar = list(
```

**Generated Continuation**:
```text
ustring)
    for i in range(len(uchar)):
        if unicodedata.combining(uchar[i]):
串
            groupedchars[-1] += uchar[i]
        else:
            groupedchars.append(uchar
```

**True Continuation**:
```text
ustring)
    while uchar:
        if unicodedata.combining(uchar[0]) != 0:
            groupedchars[-1] += uchar.pop(0)
        else:
            groupedchars.append(uchar.pop
```

---

### Row 13: code_snippets/Pythagorean_triples.txt
- **Category**: `code_snippets`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.6296`
- **Matched Token Count**: `11`
- **Longest Common N-gram Len**: `4`

**Prompt**:
```text
from math import gcd

def pt1(maxperimeter=100):
    '''
# Naive method
    '''
    trips = []
    for a
```

**Generated Continuation**:
```text
in range(1, maxperimeter):
        for b in range(a, maxperimeter):
            c = (a + b) / 2
            if a + b > c and a + c > b and b + c > a:
                trips.
```

**True Continuation**:
```text
in range(1, maxperimeter):
        aa = a*a
        for b in range(a, maxperimeter-a+1):
            bb = b*b
            for c in range(b, maxperimeter-b-a+1):
```

---

### Row 14: code_snippets/9_billion_names_of_God_the_integer.txt
- **Category**: `code_snippets`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.6957`
- **Matched Token Count**: `0`
- **Longest Common N-gram Len**: `6`

**Prompt**:
```text
def partitions(n):
    partitions.p.append(0)

    for k in xrange(1, n + 1):
        d = n - k * (
```

**Generated Continuation**:
```text
k + 1) / 2
        if d < 0:
            break
        partitions.p.append(partitions.p[-1] + d)

    return partitions.p


def partition_count(n):
    return partitions(n
```

**True Continuation**:
```text
3 * k - 1) // 2
        if d < 0:
            break

        if k & 1:
            partitions.p[n] += partitions.p[d]
        else:
            partitions.p[n] -= partitions
```

---

### Row 15: wiki_leads/Tundra.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.6667`
- **Matched Token Count**: `7`
- **Longest Common N-gram Len**: `2`

**Prompt**:
```text
In physical geography, a tundra is a type of biome where tree growth is hindered by frigid temperatures and short growing seasons. There are three regions and associated types
```

**Generated Continuation**:
```text
of tundra: Arctic tundra, Alpine tundra
```

**True Continuation**:
```text
of tundra: Arctic, Alpine, and Antarctic.
```

---

### Row 16: code_snippets/Active_object.txt
- **Category**: `code_snippets`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.5882`
- **Matched Token Count**: `6`
- **Longest Common N-gram Len**: `2`

**Prompt**:
```text
from time import time, sleep
from threading import Thread

class Integrator(Thread):
    'continuously integrate a function `K`, at each `interval` seconds'
   
```

**Generated Continuation**:
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

**True Continuation**:
```text
def __init__(self, K=lambda t:0, interval=1e-4):
        Thread.__init__(self)
        self.interval  = interval
        self.K   = K
        self.S   = 0.0
        self.__run
```

---

### Row 17: wiki_leads/Salvador_Dali.txt
- **Category**: `wiki_leads`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.5806`
- **Matched Token Count**: `3`
- **Longest Common N-gram Len**: `6`

**Prompt**:
```text
Salvador Domingo Felipe Jacinto Dalí i Domènech, Marquess of Dalí de Púbol, known as Salvador Dalí, was a Spanish surrealist artist ren
```

**Generated Continuation**:
```text
owned for his striking and bizarre images in his artwork. Born on May 11, 19
```

**True Continuation**:
```text
owned for his technical skill, precise draftsmanship, and the striking and bizarre images in his work.
```

---

### Row 18: code_snippets/Bernoulli_numbers.txt
- **Category**: `code_snippets`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.4783`
- **Matched Token Count**: `10`
- **Longest Common N-gram Len**: `3`

**Prompt**:
```text
from fractions import Fraction as Fr

def bernoulli(n):
    A = [0] * (n+1)
    for m in range(n+
```

**Generated Continuation**:
```text
1):
        A[m] = (-1)**m / (m+1)
    return A

def bernoulli_sum(n):
    A = bernoulli(n)
    return sum(A)

def bern
```

**True Continuation**:
```text
1):
        A[m] = Fr(1, m+1)
        for j in range(m, 0, -1):
          A[j-1] = j*(A[j-1] - A[j])
    return A[
```

---

### Row 19: code_snippets/fibonacci.txt
- **Category**: `code_snippets`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.5263`
- **Matched Token Count**: `12`
- **Longest Common N-gram Len**: `4`

**Prompt**:
```text
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2
```

**Generated Continuation**:
```text
:
        return [0, 1]
    else:
        fib_list = [0, 1]
        for i in range(2, n):
            fib_list.append(fib_list[i
```

**True Continuation**:
```text
:
        return [0, 1]
    fib = [0, 1]
    while len(fib) < n:
        fib.append(fib[-1] + fib[-2])
    return fib
```

---

### Row 20: code_snippets/Audio_alarm.txt
- **Category**: `code_snippets`
- **Assigned Label**: **`NOVEL`**
- **ROUGE-L Score**: `0.5000`
- **Matched Token Count**: `2`
- **Longest Common N-gram Len**: `1`

**Prompt**:
```text
import time
import os

seconds = input("Enter a number of seconds: ")
sound = input("Enter an mp3 filename: ")

time.sleep(float(seconds))
```

**Generated Continuation**:
```text


os.system("start " + sound)

```

**True Continuation**:
```text

os.startfile(sound + ".mp3")
```

---
