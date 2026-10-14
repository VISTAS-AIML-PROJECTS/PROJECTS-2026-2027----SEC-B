# LLM Probe - Teacher-Forcing Memorization Score Verification

This file compares the memorization probe's token-by-token risk scores during teacher-forcing
(where the true continuation is forced) versus the model's free-generation path.

## Alice in Wonderland (Side-by-Side Comparison)
| Token Index | Token (Free Gen) | Score (Free Gen) | Token (Forced) | Score (Forced) |
|---|---|---|---|---|
| 1 | `and` | 0.6500 | `the` | 0.8275 |
| 2 | `of` | 0.9500 | `book` | 0.9997 |
| 3 | `having` | 0.9900 | `her` | 0.9982 |
| 4 | `to` | 0.9800 | `sister` | 0.9923 |
| 5 | `entertain` | 0.9900 | `was` | 0.9751 |
| 6 | `herself` | 0.9800 | `reading` | 0.9757 |
| 7 | `.` | 0.9500 | `,` | 0.9251 |
| 8 | `\n` | 0.8500 | `but` | 0.9267 |
| 9 | `\n` | 0.7300 | `it` | 0.8977 |
| 10 | `\n` | 0.5900 | `had` | 0.8736 |
| 11 | `"` | 0.7000 | `no` | 0.8994 |
| 12 | `I` | 0.5900 | `pictures` | 0.8759 |
| 13 | `'` | 0.5100 | `or` | 0.8562 |
| 14 | `ll` | 0.4500 | `convers` | 0.8825 |
| 15 | `be` | 0.4000 | `ations` | 0.8796 |
| 16 | `going` | 0.3500 | `in` | 0.8846 |
| 17 | `_` | 0.2900 | `it` | 0.8634 |
| 18 | `____` | 0.1900 | `,` | 0.8272 |
| 19 | `__` | 0.1200 | `“` | 0.8879 |
| 20 | `",` | 0.1000 | `and` | 0.8322 |
| 21 | `said` | 0.0800 | `what` | 0.8140 |
| 22 | `Alice` | 0.0800 | `is` | 0.7210 |
| 23 | `,` | 0.0600 | `the` | 0.7094 |
| 24 | `trying` | 0.0400 | `use` | 0.6700 |
| 25 | `to` | 0.0400 | `of` | 0.6806 |
| 26 | `decide` | 0.0300 | `a` | 0.6905 |
| 27 | `what` | 0.0200 | `book` | 0.8067 |
| 28 | `to` | 0.0200 | `,”` | 0.8184 |
| 29 | `say` | 0.0200 | `thought` | 0.8101 |
| 30 | `next` | 0.0200 | `Alice` | 0.7829 |
| 31 | `.` | 0.0200 | `“` | 0.8214 |
| 32 | `` |  | `without` | 0.8511 |
| 33 | `` |  | `pictures` | 0.8440 |
| 34 | `` |  | `or` | 0.8308 |
| 35 | `` |  | `convers` | 0.8428 |
| 36 | `` |  | `ations` | 0.8356 |
| 37 | `` |  | `?”` | 0.8164 |
| 38 | `` |  | `So` | 0.8148 |
| 39 | `` |  | `she` | 0.7892 |
| 40 | `` |  | `was` | 0.7541 |

---

## Moby Dick (Side-by-Side Comparison)
| Token Index | Token (Free Gen) | Score (Free Gen) | Token (Forced) | Score (Forced) |
|---|---|---|---|---|
| 1 | `when` | 0.0100 | `I` | 0.5186 |
| 2 | `I` | 0.0700 | `would` | 0.2442 |
| 3 | `was` | 0.0100 | `sail` | 0.2640 |
| 4 | `in` | 0.0100 | `about` | 0.1597 |
| 5 | `the` | 0.0100 | `a` | 0.1742 |
| 6 | `high` | 0.0200 | `little` | 0.0852 |
| 7 | `school` | 0.0100 | `and` | 0.0457 |
| 8 | `` |  | `see` | 0.0304 |
| 9 | `` |  | `the` | 0.0349 |
| 10 | `` |  | `wat` | 0.0261 |
| 11 | `` |  | `ery` | 0.0161 |
| 12 | `` |  | `part` | 0.0162 |
| 13 | `` |  | `of` | 0.0249 |
| 14 | `` |  | `the` | 0.0378 |
| 15 | `` |  | `world` | 0.0555 |
| 16 | `` |  | `.` | 0.0527 |
| 17 | `` |  | `It` | 0.0326 |
| 18 | `` |  | `is` | 0.0265 |
| 19 | `` |  | `a` | 0.0359 |
| 20 | `` |  | `way` | 0.0328 |
| 21 | `` |  | `I` | 0.0487 |
| 22 | `` |  | `have` | 0.0585 |
| 23 | `` |  | `of` | 0.0789 |
| 24 | `` |  | `driving` | 0.0721 |
| 25 | `` |  | `off` | 0.0807 |
| 26 | `` |  | `the` | 0.0747 |
| 27 | `` |  | `s` | 0.0359 |
| 28 | `` |  | `ple` | 0.0226 |
| 29 | `` |  | `en` | 0.0168 |
| 30 | `` |  | `and` | 0.0142 |
| 31 | `` |  | `reg` | 0.0112 |
| 32 | `` |  | `ulating` | 0.0106 |
| 33 | `` |  | `the` | 0.0114 |
| 34 | `` |  | `circul` | 0.0113 |
| 35 | `` |  | `ation` | 0.0121 |
| 36 | `` |  | `.` | 0.0131 |

---

## Verification Statistics Summary
| Target Name | Label | Avg Score (Forced) | Max Score (Forced) | Last Token Score (Forced) |
|---|---|---|---|---|
| Pride & Prejudice (Memorized) | MEMORIZED | 0.9968 | 0.9999 | 0.9999 |
| Alice in Wonderland (Memorized) | MEMORIZED | 0.8446 | 0.9997 | 0.7541 |
| Moby Dick (Novel Control) | NOVEL | 0.0691 | 0.5186 | 0.0131 |
| Adam Bede (Novel Control) | NOVEL | 0.0000 | 0.0001 | 0.0000 |


### Final Verdict
- **Pride & Prejudice (Memorized)** (Forced): Avg=0.9968, Sustained High: YES
- **Alice in Wonderland (Memorized)** (Forced): Avg=0.8446, Sustained High: YES
- **Moby Dick (Novel Control)** (Forced): Avg=0.0691, Stayed Low: NO
- **Adam Bede (Novel Control)** (Forced): Avg=0.0000, Stayed Low: YES