# Oktatói értékelés (generálva: tdk/elemzes/oktatoi.py)

Értékelők: ['rater_A', 'rater_B', 'rater_C', 'rater_C2', 'rater_C3']; értékelések (kitöltött): {'rater_A': 72, 'rater_B': 72, 'rater_C': 72, 'rater_C2': 72, 'rater_C3': 34}

## Tanárok egymás közt (Krippendorff-α; ordinális, a felhasználnám nominális)

| szempont | 60 kérdés | 95% CI | 72 (kalibrációval) | 12 kalibrációs |
|---|---|---|---|---|
| correctness | 0.693 | [0.581, 0.786] | 0.679 | 0.578 |
| clarity | 0.589 | [0.444, 0.703] | 0.567 | 0.413 |
| distractor_quality | 0.472 | [0.325, 0.585] | 0.466 | 0.366 |
| bloom_fit | 0.39 | [0.249, 0.515] | 0.38 | 0.322 |
| would_use | 0.454 | [0.314, 0.579] | 0.459 | 0.485 |

Leave-one-out α: {"rater_A": {"correctness": 0.643, "clarity": 0.561, "distractor_quality": 0.403, "bloom_fit": 0.344, "would_use": 0.554}, "rater_B": {"correctness": 0.607, "clarity": 0.481, "distractor_quality": 0.356, "bloom_fit": 0.259, "would_use": 0.359}, "rater_C": {"correctness": 0.624, "clarity": 0.486, "distractor_quality": 0.41, "bloom_fit": 0.321, "would_use": 0.394}, "rater_C2": {"correctness": 0.81, "clarity": 0.77, "distractor_quality": 0.607, "bloom_fit": 0.483, "would_use": 0.463}, "rater_C3": {"correctness": 0.769, "clarity": 0.616, "distractor_quality": 0.551, "bloom_fit": 0.503, "would_use": 0.485}}

Páronkénti α: {"correctness": {"rater_A-rater_B": 0.938, "rater_A-rater_C": 0.883, "rater_A-rater_C2": 0.56, "rater_A-rater_C3": 0.46, "rater_B-rater_C": 0.949, "rater_B-rater_C2": 0.629, "rater_B-rater_C3": 0.527, "rater_C-rater_C2": 0.639, "rater_C-rater_C3": 0.511, "rater_C2-rater_C3": 0.274}, "clarity": {"rater_A-rater_B": 0.925, "rater_A-rater_C": 0.841, "rater_A-rater_C2": 0.142, "rater_A-rater_C3": 0.293, "rater_B-rater_C": 0.951, "rater_B-rater_C2": 0.297, "rater_B-rater_C3": 0.495, "rater_C-rater_C2": 0.341, "rater_C-rater_C3": 0.573, "rater_C2-rater_C3": 0.527}, "distractor_quality": {"rater_A-rater_B": 0.844, "rater_A-rater_C": 0.556, "rater_A-rater_C2": 0.298, "rater_A-rater_C3": 0.213, "rater_B-rater_C": 0.78, "rater_B-rater_C2": 0.332, "rater_B-rater_C3": 0.306, "rater_C-rater_C2": 0.384, "rater_C-rater_C3": 0.313, "rater_C2-rater_C3": 0.025}, "bloom_fit": {"rater_A-rater_B": 0.869, "rater_A-rater_C": 0.477, "rater_A-rater_C2": 0.142, "rater_A-rater_C3": -0.23, "rater_B-rater_C": 0.697, "rater_B-rater_C2": 0.326, "rater_B-rater_C3": -0.032, "rater_C-rater_C2": 0.381, "rater_C-rater_C3": 0.12, "rater_C2-rater_C3": 0.044}, "would_use": {"rater_A-rater_B": 0.533, "rater_A-rater_C": 0.32, "rater_A-rater_C2": 0.192, "rater_A-rater_C3": -0.1, "rater_B-rater_C": 0.768, "rater_B-rater_C2": 0.501, "rater_B-rater_C3": 0.321, "rater_C-rater_C2": 0.518, "rater_C-rater_C3": 0.387, "rater_C2-rater_C3": 0.581}}

Értékelőnkénti átlagok: {"rater_A": {"correctness": 3.45, "clarity": 3.05, "distractor_quality": 2.733, "bloom_fit": 2.767, "would_use": 0.25, "n": 60}, "rater_B": {"correctness": 3.633, "clarity": 3.383, "distractor_quality": 3.233, "bloom_fit": 3.25, "would_use": 0.467, "n": 60}, "rater_C": {"correctness": 3.8, "clarity": 3.567, "distractor_quality": 3.733, "bloom_fit": 3.967, "would_use": 0.583, "n": 60}, "rater_C2": {"correctness": 3.8, "clarity": 4.45, "distractor_quality": 3.367, "bloom_fit": 3.95, "would_use": 0.617, "n": 60}, "rater_C3": {"correctness": 3.931, "clarity": 3.759, "distractor_quality": 3.31, "bloom_fit": 4.241, "would_use": 0.621, "n": 29}}

## Bíró és tanárok

| szempont | ρ | p | n | bíró átlag | tanár átlag | α bíró–medián | α tanárok+bíró | α bíró–tanár pár (átl.) | α tanár–tanár pár (átl.) |
|---|---|---|---|---|---|---|---|---|---|
| correctness | 0.655 | 0.0 | 60 | 4.1 | 3.711 | 0.621 [0.384, 0.796] | 0.646 | 0.528 | 0.637 |
| clarity | 0.436 | 0.0 | 60 | 4.65 | 3.688 | 0.164 [-0.081, 0.407] | 0.479 | 0.22 | 0.539 |
| distractor_quality | 0.408 | 0.001 | 60 | 3.9 | 3.29 | 0.366 [0.132, 0.544] | 0.397 | 0.216 | 0.405 |
| bloom_fit | 0.283 | 0.028 | 60 | 4.45 | 3.584 | 0.105 [-0.162, 0.352] | 0.277 | 0.07 | 0.279 |
| mean | 0.635 | 0.0 | 60 | 4.275 | 3.568 |   |  |  |  |

κ: {"grounded_vs_teacher_correct": 0.486, "would_use_judge_vs_teachers": 0.455, "judge_would_use_rate": 0.7, "teacher_majority_would_use_rate": 0.45, "judge_grounded_rate": 0.833, "teacher_majority_correct_rate": 0.667, "confusion_would_use": {"judge_True_teacher_True": 26, "judge_True_teacher_False": 16, "judge_False_teacher_True": 1, "judge_False_teacher_False": 17}, "confusion_correct": {"judge_True_teacher_True": 39, "judge_True_teacher_False": 11, "judge_False_teacher_True": 1, "judge_False_teacher_False": 9}, "would_use_teacher_pairs_mean": 0.447}

## Konfigurációnként (tanári átlag [átlag, CI], felhasználnám-arány; bíró)

- Gemma B-doc-L: {"n": 10, "teacher_mean": [4.178, 3.77, 4.514], "teacher_would_use": 0.72, "t_correctness": 4.465, "t_clarity": 4.35, "t_distractor_quality": 3.74, "t_bloom_fit": 4.155, "judge_mean": 4.55, "judge_would_use": 0.8, "judge_grounded": 0.9}
- Gemma E2: {"n": 10, "teacher_mean": [4.259, 3.815, 4.64], "teacher_would_use": 0.78, "t_correctness": 4.52, "t_clarity": 4.42, "t_distractor_quality": 3.905, "t_bloom_fit": 4.19, "judge_mean": 4.675, "judge_would_use": 0.9, "judge_grounded": 1.0}
- PULI B-doc-L: {"n": 10, "teacher_mean": [2.425, 1.898, 3.028], "teacher_would_use": 0.2, "t_correctness": 2.275, "t_clarity": 2.65, "t_distractor_quality": 2.415, "t_bloom_fit": 2.36, "judge_mean": 3.825, "judge_would_use": 0.6, "judge_grounded": 0.7}
- PULI E2: {"n": 10, "teacher_mean": [2.666, 2.062, 3.263], "teacher_would_use": 0.165, "t_correctness": 2.455, "t_clarity": 2.98, "t_distractor_quality": 2.605, "t_bloom_fit": 2.625, "judge_mean": 3.725, "judge_would_use": 0.4, "judge_grounded": 0.6}
- Qwen B-doc-L: {"n": 10, "teacher_mean": [3.815, 3.39, 4.239], "teacher_would_use": 0.535, "t_correctness": 3.99, "t_clarity": 3.93, "t_distractor_quality": 3.375, "t_bloom_fit": 3.965, "judge_mean": 4.15, "judge_would_use": 0.6, "judge_grounded": 0.8}
- Qwen E2: {"n": 10, "teacher_mean": [4.066, 3.596, 4.508], "teacher_would_use": 0.625, "t_correctness": 4.56, "t_clarity": 3.795, "t_distractor_quality": 3.7, "t_bloom_fit": 4.21, "judge_mean": 4.725, "judge_would_use": 0.9, "judge_grounded": 1.0}

Karonként: {"B-doc-L": {"n": 30, "teacher_mean": [3.472, 3.088, 3.848], "teacher_would_use": 0.485, "judge_mean": 4.175}, "E2": {"n": 30, "teacher_mean": [3.664, 3.262, 4.061], "teacher_would_use": 0.523, "judge_mean": 4.375}}

Generátoronként: {"Gemma": {"n": 20, "teacher_mean": [4.218, 3.923, 4.482], "teacher_would_use": 0.75, "judge_mean": 4.612}, "PULI": {"n": 20, "teacher_mean": [2.546, 2.131, 2.977], "teacher_would_use": 0.183, "judge_mean": 3.775}, "Qwen": {"n": 20, "teacher_mean": [3.941, 3.615, 4.249], "teacher_would_use": 0.58, "judge_mean": 4.438}}

Nyelvenként: {"en": {"n": 31, "teacher_mean": 3.804, "teacher_would_use": 0.589, "judge_mean": 4.411, "rho_mean": 0.592}, "hu": {"n": 29, "teacher_mean": 3.316, "teacher_would_use": 0.414, "judge_mean": 4.129, "rho_mean": 0.62}}

E2 vs B-doc-L (Mann–Whitney): {"all": {"E2": 3.664, "B-doc-L": 3.472, "n": [30, 30], "p": 0.473}, "Gemma": {"E2": 4.259, "B-doc-L": 4.178, "n": [10, 10], "p": 0.82}, "PULI": {"E2": 2.666, "B-doc-L": 2.425, "n": [10, 10], "p": 0.623}, "Qwen": {"E2": 4.066, "B-doc-L": 3.815, "n": [10, 10], "p": 0.496}}

Konfiguráció-rangsor ρ (bíró vs tanár, 6 konf.): 0.771

Legalább egy tanár szerint hibás (helyesség ≤ 2): 24; többség szerint nem helyes (< 4): 20; ebből a bíró alátámasztottnak tartja / felhasználná: {'n': 20, 'judge_grounded': 11, 'judge_would_use': 6}
