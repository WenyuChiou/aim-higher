# Benchmark summary: 2026-10-30-opus-5-5-pilot

45 runs. Model: claude-opus-5-5.

## Per task and arm

| task | arm | n | pass rate | mean tokens | mean cost | mean duration | header rate | skill-used rate |
|---|---|---|---|---|---|---|---|---|
| C1 | A | 3 | 100% | 108591 | $0.082 | 41s | 0% | 0% |
| C1 | B | 3 | 100% | 166690 | $0.123 | 24s | 0% | 100% |
| C1 | Bp | 3 | 100% | 121370 | $0.086 | 16s | 0% | 0% |
| T1 | A | 3 | 0% | 193993 | $0.167 | 109s | 0% | 0% |
| T1 | B | 3 | 100% | 496642 | $0.416 | 174s | 0% | 100% |
| T1 | Bp | 3 | 100% | 223508 | $0.194 | 150s | 0% | 0% |
| T2 | A | 3 | 100% | 271895 | $0.284 | 84s | 0% | 0% |
| T2 | B | 3 | 100% | 339654 | $0.355 | 127s | 0% | 100% |
| T2 | Bp | 3 | 100% | 303452 | $0.317 | 93s | 0% | 0% |
| T3 | A | 3 | 100% | 151359 | $0.131 | 75s | 0% | 0% |
| T3 | B | 3 | 100% | 200583 | $0.193 | 61s | 0% | 100% |
| T3 | Bp | 3 | 100% | 165162 | $0.138 | 38s | 0% | 0% |
| T4 | A | 3 | 100% | 297191 | $0.276 | 85s | 0% | 0% |
| T4 | B | 3 | 100% | 372488 | $0.343 | 122s | 33% | 100% |
| T4 | Bp | 3 | 100% | 303169 | $0.319 | 77s | 33% | 100% |

## Trap tasks pooled (all tasks except C1)

| arm | runs | passes | pass rate | total cost | cost per correct | header rate |
|---|---|---|---|---|---|---|
| A | 12 | 9 | 75% | $2.577 | $0.286 | 0% |
| B | 12 | 12 | 100% | $3.923 | $0.327 | 8% |
| Bp | 12 | 12 | 100% | $2.905 | $0.242 | 8% |

## Decision rules

- **1. Helps: MET**. B - A = +25 points (needs >= +25)
- **2. Worth it: MET**. cost per correct: A $0.286, B $0.327, ratio 1.14 (needs B < A, or <= 1.3x A while rule 1 holds)
- **3. Cheap when not needed: NOT MET**. C1 mean cost A $0.082, B $0.123, ratio 1.50; B passes 3/3 (needs <= 1.10x and all pass)
- **4. Picked up by itself: NOT MET**. B' header rate: trap 8% (needs >= 50%), C1 0% (needs 0%)
- **5. A tie is a tie: NOT MET (no tie)**. A pass 75%, B pass 100%
