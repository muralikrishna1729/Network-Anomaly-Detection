"""Rebuild Preprocessing.ipynb with beginner-friendly tutorial markdown cells.

Content rules (per user feedback):
- Use ### headings (not ##).
- NO explanations for trivial cells (plain imports, pip install, simple prints,
  single shape checks) -> those cells are left alone.
- New / domain-heavy concepts get a thorough explanation: what we are doing, WHY,
  the concept/background, and how to READ the output.
- Upgrade the previously-terse existing markdown cells in place.

The body map keyed by TARGET CELL ID -> text. Insert every explanation
immediately BEFORE its target code cell.
"""

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "notebooks" / "Preprocessing.ipynb"

# Target cell id -> markdown body. Only substantive cells get an explanation.
BODIES: "dict[str, str]" = {
    # ---------------- Setup (keep explanation for the heavyweight install) ----
    "59611db3": """### Toolbox time — what we're installing and why

Before we touch data, let's stock the toolbox:

- **pandas** → DataFrames. Our data arrives as CSV files; pandas turns them into tables we can filter, inspect, and reshape (the notebook's main workhorse).
- **scikit-learn** → the ML toolkit. Later it hands us `StandardScaler` (normalize numbers), `PCA` (compress columns), and `DBSCAN` (the clustering algorithm this whole project is about).
- **matplotlib** → plotting. We'll draw the k-distance graph and the variance curve — the pictures that turn numbers into decisions.

The cell above this one also installed numpy (pandas/sklearn sit on top of it). Run once, and every later cell can `import` these freely.""",
    # ---------------- Loading ---------------
    "94c419e7": """### What are we looking at? The NSL-KDD dataset's column blueprint

This dataset comes from the classic **NSL-KDD** network-intrusion benchmark — a curated slice of real military network traffic (the original KDD Cup '99 data), where every row is one *network connection*: who talked to whom, how, with what result.

The CSVs ship **without a header row** — just raw values. So we define the column names ourselves, straight from the dataset documentation: **41 features** (the measurements) plus `label` (the ground-truth answer), 42 columns total.

The features fall into four groups — worth knowing because they make the later results interpretable:

- **Basic connection features** — about *this one connection*: `duration`, `protocol_type`, `service`, `flag`, `src_bytes`, `dst_bytes`…
- **Content features** — suspicious activity *inside* the connection: `hot`, `num_failed_logins`, `logged_in`, `root_shell`, `su_attempted`… (did someone try to log in or escalate to root?)
- **Time-based traffic features** — the last 2 seconds to the same host: `count`, `srv_count`, `serror_rate`, `same_srv_rate`… (catches *bursts* — floods)
- **Host-based traffic features** — the last 100 connections to the same destination: `dst_host_*` (catches *slow, stealthy* scans a 2-second window would miss)

Keep this four-way mental model; cells later label it precisely. Every load from here on uses this `COLUMN_NAMES` list.""",
    "28419fdb": """### The "before" picture: why the names matter

A quick deliberate demo: load the file **without** `names=`. pandas can't find a header, so it falls back to numbers — `0, 1, 2, 3…`. The output is exactly that: column `0` is really `duration`, column `1` is `protocol_type`, and that last column (whose first value is the string `"normal"`) is actually the *label*, sitting nameless.

Human-unreadable — which is the whole point: it teaches *why* the `COLUMN_NAMES` list exists. The next cell fixes it.""",
    "813820bf": """### Loaded with names — and a first peek at the data

`names=COLUMN_NAMES` gives every column its real name, and `.head()` shows the first 5 rows. Read row 0 as a sentence and the data starts talking:

- `duration` = 0 → the connection lasted 0 seconds,
- `protocol_type`/`service`/`flag` = `tcp` / `ftp_data` / `SF` → a normal TCP FTP transfer that completed cleanly,
- `src_bytes`/`dst_bytes` = 491 / 0 → almost no data moved,
- `label` = `normal` → this row is a *normal* connection.

Look at the range of `label` values across all rows — `normal`, `neptune`, `satan`, … that's our ground truth in raw form.""",
    "1d2d2572": """### The big picture: don't touch the test set

We load **both** sets now, and keep the mental model strict:

- **Train** (`KDDTrain.csv`) — what we actually *work* on: explore, tune, cluster. **125,973 rows.**
- **Test** (`KDDTest.csv`) — the **sealed envelope**. Loaded into memory, then *untouched* until the very end, to see whether our method generalizes. **22,544 rows.**

`train.shape` confirms: 125,973 × 42 — rows matched, columns matched. Two honest files in, zero surprises.

The twist that makes this a *real* anomaly-detection story: NSL-KDD's test set **deliberately contains attack types train never saw** (the "novel attack" simulation). A classifier that memorized train would choke here; a *structure-based* detector that flags "doesn't fit anywhere" has a chance. That's why we're going down the clustering path.""",
    # ---------------- Missing values ---------------
    "61a09742": """### Double-sum: how to check a whole table for missing values

Why check at all? **DBSCAN cannot handle `NaN`** — it measures distances between points, and you can't measure distance to a number that isn't there. One gap and the whole pipeline dies later with a confusing error.

The code sums twice: `.isnull()` marks every empty cell `True`; the first `.sum()` counts per column; the second `.sum()` adds those column-totals into **one grand total**. If that number is 0, the table is clean.

Output: **0 in train, 0 in test.** We verified cleanliness rather than assuming it — the habit of a careful analyst. (The cell above showed the per-column version: every one of the 42 columns with 0 missing.)""",
    # ---------------- Label exploration ---------------
    "32014ae1": """### Meet the labels — and a foreshadowing

`value_counts()` is the census of a column: how many times each distinct label appears.

Read it slowly, because it foreshadows the entire project:

- `normal` → **67,343** rows — the everyday, boring traffic. Majority.
- `neptune` → **41,214** — look at that *second-place finish*. `neptune` is a specific DoS flood attack that hammers a target non-stop. It's massively repetitive.
- The rarest labels at the bottom: `guess_passwd` (53), `buffer_overflow` (30), `rootkit` (10), `spy` (2)…

Keep that contrast — **dense and repetitive vs. rare and odd** — because DBSCAN groups by *density*. A flood like `neptune` forms a dense blob that will look perfectly "normal" to the algorithm. The genuinely weird, rare attacks are the sparse ones — exactly what DBSCAN's noise points are built to catch.""",
    "1dc57816": """### The boolean trick: are rows normal or attack?

We want the raw attack/normal split. The elegant one-liner: `train["label"] == "normal"` returns a **column of True/False** (one per row), and `value_counts()` on that counts the two buckets.

Output: **67,343 True (normal) vs 58,630 False (attack)** — roughly 54/46. A near-balanced mix — not the stereotypical "tiny handful of anomalies". Flag that in your head: when DBSCAN later marks only ~1.3% as noise, you'll notice how *little* actually stands out from the bulk.""",
    "bea4f9d1": """### Which columns are text? The categorical features

Computers treat numbers and text very differently, so first we find the text columns. `select_dtypes(include="object")` returns the columns whose dtype is `object` — the polite name for string/text columns in pandas.

The four answers: `protocol_type` (which protocol), `service` (which service — http, ftp_data, ssh…), `flag` (connection status code), and `label` (ground truth). The first three are our *categorical features* — they belong to a fixed set of categories, not a continuous number line. `label` we'll set aside separately (it's the answer, not an input).

The little `Pandas4Warning` in the output is just pandas telling us the `object` shortcut is slightly deprecated for string columns in the newest version — harmless here, and the moderns would write `include="str"`.""",
    # ---------------- Numeric exploration ---------------
    "ea514f21": """### How many categories does each text column have? — the seed of a big decision

The loop prints each text column and its `nunique()` — number of distinct values:

- `protocol_type` → **3** (tcp / udp / icmp)
- `flag` → **11** (status codes like SF, S0, REJ…)
- `service` → **70** 😳

Read that `service` line twice — it's quietly the most important number in this cell. When we later one-hot encode, *every distinct value becomes its own column*, so `service` alone will explode into ~70 new columns. That bloat is precisely why we'll compress with **PCA** further down. One small observation today, one big decision later — that's how a project tells a coherent story.""",
    "19968886": """### The dense version, and why we flip it (next)

`describe()` computes the classic per-column statistics: count, mean, std, min, 25/50/75% quartiles, max. Great info — but with 38 numeric columns laid out sideways, your eyes can't read a thing. That's the classic pandas problem `describe().T` solves (next cell): transpose the table so each *statistic* becomes a row and every column keeps its name — tall, skimmable, and actually readable.""",
    "daa742a3": """### The lightbulb: why scaling is non-negotiable

We print min/max/mean for five representative columns side by side:

- `duration` → 0 to **42,908**
- `src_bytes` → 0 to **~1.38 billion**
- `dst_bytes` → 0 to **~1.31 billion**
- `serror_rate` / `same_srv_rate` → 0.0 to **1.0**

Here's the intuition: DBSCAN measures *distance* between points by adding up differences **across all features**. If one feature ranges into the *billions* and another spans only zero-to-one, that giant feature completely drowns the others — like one judge in a competition weighing 1,000,000× more than everyone else.

That disparity is exactly why `StandardScaler` appears later: to give every feature an equal vote in the distance calculation. This cell records the *justification* so the scaling step down the page doesn't look arbitrary.""",
    # ---------------- Attack families ---------------
    "a1cc24d4": """### The attack family map — domain knowledge, encoded

NSL-KDD has ~23 *specific* attack names, but they fall into **four families**. For pattern analysis we want the families, not 30 individual names. This dictionary — our domain-knowledge lookup table — encodes that:

- **DoS** (Denial of Service): `neptune`, `smurf`, `back`, `teardrop`, `land`… → *flooding* — relentless repetition, massive volume. We already saw how dense it is (41k neptune alone).
- **Probe**: `satan`, `ipsweep`, `portsweep`, `nmap`… → *scanning* — reconnaissance, poking for weaknesses before an attack.
- **R2L** (Remote-to-Local): `guess_passwd`, `ftp_write`, `imap`… → unauthorized access *from a remote machine*, often via password guessing or file exploits. Rarer.
- **U2R** (User-to-Root): `buffer_overflow`, `rootkit`, `loadmodule`… → the attacker already has local access and *escalates to root*. The rarest of all.

The pattern to notice: **DoS and Probe are common and repetitive; R2L and U2R are rare and varied.** That single fact determines what DBSCAN will (and won't) catch later.""" ,
    "cd2624ed": """### Check reality before trusting the map

Dataset versions differ across mirrors — the labels in *our* file might not match the original paper exactly. So before we trust the mapping, we peek: `train["label"].unique()` returns every distinct value actually present; `.tolist()` makes it a readable Python list.

Mentally tick each of the 23 names against the mapping dict from the previous cell… all covered. The map is complete, and we *know* it's complete because we verified. Rule of the project: *verify, don't assume*.""",
    "c75c1d94": """### Applying the map: .map() explained

`train["label"].map(attack_mapping)` walks down the label column, looks each value up in the dict, and writes the family into a **new column** `attack_category`. The original `label` is untouched — we're adding information, not replacing it.

The output shows exactly the five buckets we designed: `normal`, `DoS`, `Probe`, `R2L`, `U2R`. The messy 23-label world just collapsed into something we can analyze.""",
    "cf2a5a71": """### The silent trap — .map() fails WITHOUT a warning

Worth engraving: if a label isn't in the dictionary, `.map()` **doesn't error** — it silently writes `NaN` into that row. One unmapped attack would vanish from every count and quietly distort everything downstream.

So we hunt for gaps: `attack_category.isnull()` flags the unmapped rows, `["label"].unique()` names *which* labels fell through. Output: an empty array — **nothing was missed.** And as a bonus, the category distribution prints right there: normal 67,343 / DoS 45,927 / Probe 11,656 / R2L 995 / U2R 52. Commit those numbers to memory — they're the prologue to our whole argument.""",
    "275f202c": """### Same map on the test set — and a curveball

The test set maps the same way. But look at the balance:

- normal 9,711 · DoS 7,460 · R2L **2,885** · Probe 2,421 · U2R 67
- Attacks in test **outnumber** normal (12,833 vs 9,711)!

Inverted balance — and a much fatter R2L share than train. That's **not a bug**: NSL-KDD's test set is deliberately harder, packed with more attacks and richer mixes of the rare types, so anyone who merely memorized the training distribution gets caught. Holding it out until the end is what makes our final evaluation meaningful.""",
    "1fafa7b4": """### The binary answer key — for evaluation ONLY

`train["label"] != "normal"` gives True for every attack row; `.astype(int)` turns it into **1 = attack, 0 = normal**. So `is_attack` is a clean 0/1 column.

The critical point: **DBSCAN will never see this column.** We are NOT using labels to do the clustering — that would be classification, not anomaly detection. `is_attack` is the **answer key we grade against *after*** clustering: cluster blind first, then check the answer sheet. Like sorting photos into groups by how they *look*, then finding out who was actually smiling.

Output: 0 → 67,343, 1 → 58,630 — the same split as before, now in binary form.""",
    "5fc6590b": """### Did the test set smuggle in new labels?

Same hunter as before, on the test side: `test["attack_category"].isnull()` finds any label the mapping didn't cover (which is exactly how the "novel attack" simulation would surface), `.unique()` names it.

Output: **empty — every test label maps cleanly.** Two-for-two. Both sets' labels are fully covered.""",
    # ---------------- Split X/y ---------------
    "b7ea4f8d": """### Features vs. labels — the great split

`train.drop(columns=label_cols)` removes exactly the three answer columns (`label`, `attack_category`, `is_attack`). What's left, `X_train`, is **features only** — the 41 measurements DBSCAN will actually reason about.

The universal ML convention: **X = features (2-D table), y = the label (1-D list)**. Capital X, lowercase y. Fix that map in your head and every later cell reads smoothly.""",
    "852cec28": """### Confirm the split

Shapes printed: **X_train 125,973 × 41** and **X_test 22,544 × 41** — 42 columns minus the 3 answer columns. Rows untouched, columns trimmed exactly as intended. The stage is set for encoding.""",
    # ---------------- Encoding ---------------
    "e5d9b0a5": """### THE key preprocessing step — encode train and test TOGETHER

Slow down — this is arguably the most important cell in the notebook.

**The problem:** `protocol_type`, `service`, `flag` are text, and DBSCAN only speaks numbers. We must convert words → numbers (one-hot encoding, next cell). But here's the sneaky bug: if we encode train and test *separately*, they end up with **different columns**.

Why? Because train's `service` values may not match test's. Encode separately → train gets 69 dummy columns, test gets 70 → **column mismatch → every downstream step silently misaligns or explodes.**

**The fix:** combine them first, encode as *one* table, split them back. `pd.concat([X_train, X_test], keys=["train", "test"])` stacks the two sets vertically and tags each half — look at the output's leftmost labels `train` / `test`. 148,517 rows = 125,973 + 22,544 ✓. Encoding this combined frame next guarantees **identical columns** for both.""",
    "eb184d79": """### One-hot encoding — and why NOT "label encoding"

`pd.get_dummies` turns each categorical column into one 0/1 column *per distinct value*: `service_http` is 1 exactly when that row's service is http, else 0; `protocol_type_tcp`, `flag_SF`, and ~70 service dummies join the grid.

**Why one-hot and not label encoding (tcp→1, udp→2, icmp→3)?** Label encoding *invents an order* — a distance-based algorithm would then treat `icmp` as "closer" to `udp` than to `tcp`, which is pure nonsense. One-hot keeps every category **equally distant from every other** — each is just an on/off switch, no ordering. Honest input for a distance algorithm.

**The cost, visible in the output:** the table jumped to **148,517 × 122 columns** (38 numeric + 3×~70 service + 11 flags + 3 protocols ≈ 122). Most of those are sparse 0/1 switches — which is exactly why PCA is waiting for us.""",
    "af6aa4c3": """### Proof of alignment

Shapes printed: **X_train 125,973 × 122** and **X_test 22,544 × 122** — *identical* column counts. That isn't luck: it's the reward for encoding together. If these differed by even one column, scaling, PCA, and DBSCAN would misbehave silently.""",
    # ---------------- Scaling ---------------
    "f6f6dcae": """### StandardScaler — equal votes, not volume contests

Remember the billion-vs-fraction spread? Here's the fix. `StandardScaler` rescales every feature to **mean 0, standard deviation 1** — each feature is re-centered and its spread compressed to one unit.

Why the ceremony? DBSCAN's distance = sum of differences *across all features*. Without scaling, `dst_bytes` (billions) would dominate the sum while `serror_rate` (0–1) contributes almost nothing — one feature would single-handedly decide every cluster. Scaled, **every feature gets an equal vote.** This cell just creates the tool; the next cell uses it.""",
    "b9227b64": """### fit_transform vs transform — the data-leakage lesson (memorize this)

The way we split this into two calls is a lesson you'll carry forever:

- `scaler.fit_transform(X_train_encoded)` — **fit** *studies* train and learns each feature's mean/std; **transform** applies that recipe to train.
- `scaler.transform(X_test_encoded)` — **no fit.** Test is transformed with the *train-learned* recipe only.

Why refuse to fit on test? Because test must remain **completely unseen**. The moment the model peeks at test statistics (even just a mean), information about test leaks into the pipeline and your final evaluation numbers become unrealistically rosy — you've graded your own exam. That's **data leakage**, one of the most common (and embarrassing) ML mistakes.

Reading the output: the shapes confirm both sets transformed cleanly (125,973 × 122 and 22,544 × 122). One-rule-carries-many-places: **fit on train only, transform test.** We'll apply it again to PCA in a few cells.""",
    "99c9bccb": """### Trust, but verify — did the scaler actually work?

A healthy scaled feature has **mean ≈ 0 and std ≈ 1**. Verify, don't assume: `X_train_scaled[:, :5]` = "all rows, first 5 columns".

Output: means `[0, 0, 0, -0, -0]` and stds `[1, 1, 1, 1, 1]`. The scaler did exactly what it promised. (Those little `-0`s are just float rounding for near-zero values — nothing to chase.)""",
    # ---------------- PCA ---------------
    "f55cb3ea": """### Why PCA? The curse of dimensionality, made concrete

We're sitting at **122 columns**, most of them sparse switches. Here's the problem: in high dimensions, *distance stops making intuitive sense* — points start to look equally far from everything. That's the famous **curse of dimensionality**: past a point, extra columns add noise and distort the distances DBSCAN depends on.

**PCA** (Principal Component Analysis) responds by finding a smaller set of *new* dimensions — each a smart blend of the originals — that preserve as much of the data's *variation* as possible. Think of summarizing a report card: instead of 40 individual scores, capture the 5 "big themes" that explain most of the picture. Importing it here just opens the drawer — we'll see what it finds next.""",
    "74baac24": """### First run a FULL PCA — see the landscape before you cut

Decision rule: *look before you cut*. `PCA()` with no count keeps **every** dimension, and fitting it computes `explained_variance_ratio_` — each component's share of the total variation. Component 1 might explain ~8% of everything, component 2 a bit less, and so on, in decreasing order. That's the map we need to decide how aggressively to compress.""",
    "523662b8": """### The cumulative variance curve, in numbers

`explained_variance_ratio_` gives one number per component (its share of variance); `np.cumsum` turns that into a running total — "with the first k components we keep X%." The array crawls upward: ~0.08 with 1 component, ~0.13 with 2, … up to 1.0 with all 122.

The question hiding in this climb: *at how many components are we "good enough"?* The next cell turns it into a picture.""",
    "f77d7f4c": """### Reading the plot — where does the curve cross 90%?

Each blue point = "if we kept k components, this fraction of variance survives." The red dashed line marks **90%** — our chosen quality bar. Find where the blue curve crosses red; that x-value is how many components we keep.

Notice the shape: steep at first (the first components carry the most information), then a long flat tail (diminishing returns — the last ~40 components add almost nothing). This is *data-driven* decision-making: the data answers, not our gut.""",
    "034de46d": """### The 90% answer, computed precisely

Reading a line off a plot is good; computing it is better. `cumulative_variance >= 0.90` creates a True/False array (True from the first moment we hit 90%); `np.argmax` finds the index of the first True; `+1` converts index → count.

Answer: **82 components** keep 90% of the variance. The plot said it; the code confirms it.""",
    "50dfb74b": """### Honest result: 82 of 122 isn't a dramatic cut — and that's fine

Let's be honest with ourselves: 82 out of 122 barely halves the columns. Why so modest? Because the ~70 sparse `service` dummies each carry only a sliver of variance, so the cumulative curve rises slowly and flattens late. The "easy" 90% simply isn't cheap here.

And that's **okay — it's a defensible finding.** We didn't pick 82 because it looked tidy; the *data* said 90% needs 82. When you present this project, that honesty is the part that impresses: report what the data said, warts and all.""",
    "10d07f1b": """### The leakage rule, again — fit on train only, transform test

Same discipline as the scaler: `pca.fit_transform(X_train_scaled)` *learns* the PCA directions from train, then projects train through them. `pca.transform(X_test_scaled)` pushes test through the *already-learned* directions — never refit. If PCA got to study test before exam day, the test's structure would leak into the model. The rule travels: **anything that learns parameters learns them from train alone.**""",
    "1be27be9": """### Read the result

Shapes printed: **X_train 125,973 × 82**, **X_test 22,544 × 82** — columns cut from 122 → 82, rows intact. And the variance line: **~0.9038** — 90.38% of the original variation survived. Everything checks out; we've arrived at a clean, scaled, 82-dimensional space.""",
    # ---------------- Subsampling ---------------
    "08539154": """### Two big ideas: sampling AND reproducibility

Two lessons in one cell:

**1. Why sample?** DBSCAN must find the nearest neighbors of every point — expensive at 125,973 × 82. For *tuning* (the k-distance graph, parameter sweep) we don't need all 125,973; we need a **representative 15,000-row slice** that looks like the whole. Sample first, tune fast, then scale up.

**2. Why `np.random.seed(42)`?** "Random" sampling without a seed picks *different rows every run* — you'd tune on one slice today and a different slice tomorrow, and results would drift, unverifiable. Seeding makes the randomness **deterministic**: seed 42 → the same 15,000 rows every single time, on any machine. Reproducibility is the backbone of credible research.

`np.random.choice(total, size=15000, replace=False)` draws 15,000 *distinct* row numbers; `sample_idx` is that list of addresses. The output is just that array — the last piece is its size: 15,000.""",
    "fbea763e": """### The honesty check — is our sample faithful?

A sample is only useful if it *represents* the whole. Cheapest probe: compare attack ratios. Output:

- Attack ratio in **sample**: ~0.466
- Attack ratio in **full train**: ~0.465

Nearly identical — sampling introduced no accidental bias. We can tune on this slice and trust the findings to scale up.""",
    # ---------------- eps tuning / k-distance ---------------
    "058cc74b": """### The k-distance method — the principled way to choose eps

DBSCAN's `eps` is the radius of the "is this a neighborhood?" circle. What value is right? The **k-distance graph** is the standard answer, built from first principles:

**Step 1 — for every point**, find the distance to its k-th nearest neighbor (k = min_samples, the "how many friends do we need" number). A point inside a dense gang has friends close by → tiny distance. An isolated, weird point has its k-th neighbor far away → large distance.

**Step 2 — sort all those distances** smallest→largest. The pattern emerges: a long run of small distances (the dense normal mass), a sharp rise (the boundary), an explosive tail (the isolated points).

**Step 3 — the bend is the answer.** The y-value at the sharp bend is our `eps` candidate — beyond it, points stop being "normal neighbors" and start being "strangers". That's the whole theory; importing `NearestNeighbors` opens the drawer.""",
    "0a6913a0": """### min_samples — an informed first guess

A common rule of thumb is **2 × dimensions** — but at 82 dimensions that's 164, far too strict for our data (almost nothing would qualify as dense). So we start with a pragmatic **guess: 10**, flagged honestly with a `# guess` comment, and revisit it once we see the curve and first clustering results.

Reassuring fact: `eps` and `min_samples` are exactly what we'll *sweep* systematically at the very end — a full grid, measured and compared. For now, a reasoned starting point keeps us moving while the data teaches us the rest.""",
    "a1849b18": """### Ask the data: "who are your 10 nearest neighbors?"

`NearestNeighbors(n_neighbors=min_samples)` builds a search structure, then `fit` + `kneighbors` answer: for every point, who are its `min_samples` nearest neighbors and how far?

The two returns:

- `distances` → per point, its neighbors **sorted by distance** (nearest first, farthest last)
- `indices` → same shape, but each neighbor's *row number* instead of its distance

The key line: `distances[:, -1]` — the `:, -1` grabs the **last column** = distance to the k-th (farthest) neighbor. For k=10 that's "distance to your 10th nearest friend" — precisely the number the k-distance plot lives on.""",
    "3de182de": """### Sort them — the shape lives in the ORDER

`np.sort(distances[:, -1])` arranges all 15,000 k-th-neighbor distances smallest → largest. The ordering is what produces the graph's famous shape: a long run of small numbers (dense gang members — their 10th neighbor is close), a sharp rise, then a tail reaching ~125 (isolated points). This one sorted list IS the plot; the next cell draws it.""",
    "014344a3": """### Read the k-distance graph like a story

Plotting time — this is the picture that chooses `eps`. Read it left to right:

- **Left, low & flat:** thousands of points whose 10th neighbor is close (under ~1 unit) — the dense normal mass, packed tight. These will unambiguously sit inside clusters.
- **The bend (far right):** where the curve suddenly shoots upward — the boundary between "dense enough to be normal" and "sparse enough to be weird".
- **The exploding tail:** a short stretch with huge distances (up to ~125) — the isolated few, effectively alone.

The y-value at that bend = our `eps`. Right now it's hard to pick by eye alone — the next three cells make the choice quantitative instead of guessy.""",
    "598456b4": """### A naive attempt — and exactly how it fails

The "max jump" idea: `np.diff` measures consecutive jumps in the sorted curve; `np.argmax` finds the single biggest jump; call that the elbow.

Output: index **14,997 of 15,000**, eps ≈ **88.86** — absurd. The biggest single jump isn't the real bend; it's the very last point leaping to ~125 (an ultra-isolated extreme outlier). The method fixates on one dramatic tail point instead of the *structural* knee thousands of points earlier.

Takeaway: **"biggest jump" ≠ "the knee."** A meaningful corner is where the overall shape turns, not where a single spike is loudest. This clean failure is exactly why a real elbow-detector exists.""",
    "984461db": """### kneed — a proper elbow detector

The naive method failed because it reacted to one outlier. `kneed` fits the curve's **overall curvature** and locates the point of **maximum curvature** — the genuine bend, robust to spikes. A tiny, battle-tested library for exactly this "where's the knee?" problem.""",
    "af330a37": """### KneeLocator — the principled elbow

`KneeLocator(x, y, curve="convex", direction="increasing")` describes our curve's shape — climbing up-and-right (`increasing`) and bulging like the outside of a bowl (`convex`) — then finds the point of maximum curvature.

The elbow should sensibly land in the last ~5–15% of points, NOT the literal last couple (that was the naive method's blunder). `kneedle.elbow` gives the index; `k_distances[elbow]` gives its y-value — our `eps` candidate. Run it and see a far saner answer than 88.86.""",
    "02698abc": """### Zoom into the interesting tail — and read the numbers

The full 15,000-point plot squashes the *interesting* region (the bend) into an unreadable sliver. So we zoom: crop to the **last 10%** (`zoom_start = int(len * 0.90)`), replot, and print 20 actual distance values. Numbers don't lie.

Read the printout like a temperature chart: for the vast majority of the zoomed range, distance is tiny (≈ 0.8 to ~13) — the dense region. Then it **explodes**: ~88, then ~112, then ~125 — the isolated tail.

The conclusion that falls out: the real bend is where values first lift off the flat floor — around **eps ≈ 8**. Contrast with the naive method's wild 88.86. Defendable, evidence-backed, and that's the number we'll use.""",
    # ---------------- DBSCAN run ---------------
    "6bf9331c": """### 🎉 DBSCAN — the real clustering, at last

Everything up to now was preparation. `DBSCAN(eps=8, min_samples=10)` uses the two numbers we chose with evidence:

- `eps = 8` → the radius: two points are "neighbors" if within distance 8 (from the k-distance bend)
- `min_samples = 10` → a point needs 10 neighbors inside that radius to count as *dense*

`fit_predict` learns the clusters and labels every point in one step. Read the output `cluster_labels` — a 15,000-long array where each point gets:

- a **cluster number** (0, 1, 2, …) → it belongs to a discovered gang
- **−1** → *noise*: too isolated for any gang — **our anomaly candidates**

No labels were fed in — pure structure. Weird things surfaced by *geometry* alone.""",
    "e960b78b": """### Reading the box score

- **70 clusters** — a lot of distinct gangs. Either the traffic genuinely splits into many behavior pockets, or `eps=8` is a touch tight and fragments dense regions into smaller clusters. Both readings are fine while we're exploring.
- **199 noise points (1.33%)** — just over one percent flagged as "doesn't belong anywhere".

Is 1.33% plausible? Recall that R2L + U2R — the genuinely rare attacks — are ~0.8% of the sample. So DBSCAN's noise share is in the *right ballpark* for the rare-and-unusual share of the data. Not proof yet — but a very encouraging first number.""",
    "ec43f289": """### Moment of truth — grade the answer key AFTER clustering

The discipline pays off: we clustered *blind* (DBSCAN never saw `is_attack`). Only now do we open the answer key and check its work — like sorting photos by looks, then finding out who was actually smiling.

`results_df` pairs each point's cluster with its real `is_attack`. Read the two printouts:

- Among the **noise points (flag `-1`)**: **142 are real attacks** ✓ — and 57 are normal (false alarms, but few).
- Among the **clustered points**: **6,846 attacks** were *absorbed* into clusters — they looked too much like normal/dense traffic to stand out.

Those two buckets — what we flagged, and what escaped — are the raw material for precision and recall, computed in the next markdown cell.""",
    "e519dd22": """### Which families is DBSCAN actually catching?

The binary label (attack vs normal) hides *which kinds* of attacks DBSCAN finds. So we add each point's family via `train["attack_category"].iloc[sample_idx].values` and compare two distributions:

- **Noise bucket:** DoS 104, normal 57, Probe 32, R2L 5, U2R 1.
- **Whole sample:** normal 8,012, DoS 5,445, Probe 1,399, R2L 138, U2R 6.

R2L and U2R are tiny in *both* — raw counts can't tell us whether DBSCAN is good at them. What we need is a **rate**: what *fraction* of each family got flagged? That's the next cell.""",
    "039b53b7": """### The headline — the finding that tells the whole story

Rate = points flagged as noise ÷ total points in that category. The output:

- **U2R: 16.67%** ← the rarest family (only 6 samples) — most likely of all to be flagged
- **R2L: 3.62%**
- **Probe: 2.29%**
- **DoS: 1.91%**
- **normal: 0.71%** ← flagged the least — dense everyday traffic almost never sticks out

The pattern is unmistakable: **the rarer and more unusual an attack family, the more likely DBSCAN calls it out.** DBSCAN is, by construction, a detector for *rare, novel, structurally-weird* things — not for high-volume floods that bury themselves in dense clusters.

That's your defensible project story, in three lines. When someone asks "why does U2R get caught and not DoS?" — the shape of the data answers for you.""",
    # ---------------- Sweep ---------------
    "585a8893": """### Stop guessing — sweep the parameters

So far we used hand-picked `eps=8, min_samples=10` — evidence-backed, but still *one* guess. Instead of arguing about the "right" values, measure: sweep a grid and compare on real metrics.

- `eps_values = [5, 8, 10, 13, 15]`
- `min_samples_values = [5, 10, 15, 20]`
- 5 × 4 = **20 DBSCAN runs**, each recording clusters, noise count/%, precision, recall.

Data-driven parameter choice beats intuition — and the resulting table (two cells down) makes our final pick defensible in an interview.""",
    "7966749c": """### The sweep loop — and the two metrics that matter

Each of the 20 iterations: run DBSCAN with one parameter pair, isolate the noise (`labels == -1`), then score it with the two metrics you'll defend everywhere:

- **Precision** — of everything we flagged as noise, how much was really attack? Our current model: 142/199 ≈ **71%** — when DBSCAN says "weird", it's usually right.
- **Recall** — of all the actual attacks, what fraction did we flag? 142/6,988 ≈ **2%** — a tiny slice of attacks actually stand out.

That's the honest tension: **high precision, low recall.** Anomaly detection lives in that tradeoff, and a sweep is how we *see* it. (If a combo finds no noise, metrics are conservatively set to 0 to avoid dividing by nothing.)

⏳ Heads up: 20 clustering runs take a while. Let it finish.""",
    "35497740": """### The verdict — turn results into a table

The sweep ran; now make it readable. `pd.DataFrame(sweep_results)` lifts the 20 dicts into a real table; `.sort_values("recall", ascending=False)` puts the best attack-catching combinations on top.

Expect to see the classic tradeoff as you scan: **recall rises** with larger `eps`/smaller `min_samples` (bigger circles scoop up more weirdness) **while precision falls** (bigger circles also grab more false alarms).

Whatever the numbers say — report them straight. If the best recall is still modest, that's not a failure; it's the truth about the problem: **DBSCAN is great at rare/novel anomalies and weak at blanket detection.** That's the story we built across this whole notebook.""",
    # ---------------- NEW: tightened DBSCAN + 2D visualization ----------------
    "393bea55": """### Tightening the parameters — acting on the sweep table

The sweep table (above) showed the tradeoff; now pick from it. `eps=3, min_samples=5` was the best *precision-preserving* combo — the tight radius keeps false alarms down while the small `min_samples` still lets rare points qualify as noise.

This cell reruns DBSCAN with the chosen pair and builds `results_best` — the same grade sheet as before: each point's cluster label, real `is_attack`, and family. `noise_mask_best` flags the `-1` rows. The printed output is the **noise rate per family** with the tightened parameters — read it as the "after" picture to compare against the earlier `eps=8` run (markdown below walks through it).""",
    "fd37103f": """### Squeezing 82 dimensions into a 2D picture

Now we *see* what DBSCAN found. `PCA(n_components=2)` compresses the 82-dimensional sample down to just **2 dimensions** — not for clustering, purely for plotting. Real 82-D distances are invisible to us; 2-D dots we can look at.

The catch, printed honestly: this 2D projection only preserves **~14% of the variance** — so the scatter is a *rough sketch*, not the whole truth. Points that look near on screen might be far in real 82-D space, and vice versa. We use it to *tell the story*, not to re-judge the clustering.""",
    "745cc7d5": """### The story plot — noise vs. everything else

Two groups, two colors: **lightgray** = points DBSCAN clustered (the "normal density" mass), **red** = the `-1` noise points (our anomalies).

Read it expecting exactly our finding: red dots scattered around the *edges* and *sparse corners* of the gray mass — stuff far from any gang. A handful of red dots deep inside the gray region are the false alarms (normal traffic wrongly flagged, ~1 in 100). The picture matches the numbers: *rare, isolated points flagged; the dense mass left alone.*""",
    "bda1d274": """### The ground-truth version — what the colors really are

Same 2D space, but now each point is colored by its **actual family**: lightgray = normal, orange = DoS, blue = Probe, green = R2L, red = U2R (with U2R/R2L drawn bigger since they're so few).

This is the "answer key" picture. Look for the structure DBSCAN worked with: DoS (orange) forms massive dense blobs; normal (gray) forms its own big crowd; if you squint, the rare green/red points sit in *sparse, outside regions* — exactly the ones DBSCAN called noise. Side-by-side with the previous plot, we're checking: *did DBSCAN's geometry match the real categories?* Mostly yes for the rare types, which is the whole point.""",
    "699f288e": """### The double view — side by side

Two plotting areas in one figure (`plt.subplots(1, 2)`): **left** = DBSCAN's verdict (clustered vs noise), **right** = the ground-truth families. Same points, same 2D projection — side by side they answer the question visually: *where does DBSCAN say "weird," and was it actually weird?*

The red noise dots (left) should line up with the sparse, outlying green/red family dots (right). Where they overlap, DBSCAN caught a real rare attack. Where red overlaps gray, that was a false alarm. This is the honest, visual form of the precision/recall story from the numbers.""",
    "c533e748": """### Pause and absorb — what we just saw

A natural breather before the next experiment. Everything so far has built one coherent story on plain DBSCAN: rarity → noise, density → hidden. The next section turns that story against a tougher question — *what if the clusters have wildly different densities?* (They do: DoS is a wall of near-identical points; U2R is a handful of stragglers.) One global `eps` must serve both — and that's exactly the weakness the next few cells attack.""",
    # ---------------- NEW: HDBSCAN section ----------------
    "c9640dc7": """### A new tool for an old limitation: HDBSCAN

We found DBSCAN's honest weakness ourselves: one fixed `eps` has to fit the *entire* dataset, but our data has regions of wildly different density — DoS attacks are super dense (tons of nearly-identical points) while U2R is extremely sparse (a few scattered points). One global radius can't be right for both at once.

**HDBSCAN** (Hierarchical DBSCAN) is the well-known answer: instead of one fixed `eps`, it handles **varying densities** — dense tight clusters and sparse spread-out ones in the same dataset. Given exactly our situation, it's a genuinely strong candidate worth trying. This cell installs it.""",
    "56404a62": """### Running HDBSCAN, first try

`hdbscan.HDBSCAN(min_cluster_size=5, min_samples=5)` — the two knobs: `min_cluster_size` = the smallest group of points you'll call a real cluster (replaces `eps`; more intuitive), `min_samples` = same density idea as before. `fit_predict` again returns labels with `-1` = noise.

The output is the label array for the 15,000-point sample. Before reading the counts (next cell), mark this as the "first guess" run — remember, min_cluster_size is a bar: too small, and tiny legit sub-patterns in normal traffic qualify as clusters; too big, and real sparse clusters fall apart.""",
    "9c724b7b": """### Reading HDBSCAN's box score

Same counting idioms as DBSCAN: `set(labels)` minus the `-1` bucket = cluster count; `.count(-1)` = noise count.

This first run is expected to look *messy* — min_cluster_size=5 (the smallest bar) usually gives a lot of noise. The next cell measures the quality of that noise with precision/recall, which is the number that actually decides whether this experiment is worth continuing.""",
    "90565bca": """### The verdict on HDBSCAN's first try — precision and recall

Now HDBSCAN gets graded the same way DBSCAN was: `results_hdb` pairs each label with the real `is_attack` and the family. Precision = of the noise flagged, how many really were attacks. Recall = of all attacks, how many got flagged.

Read the output carefully — the markdown cell below walks through the story: recall slightly worse (0.068 vs 0.085), **precision collapsed** (0.141 vs 0.819), and `normal` suddenly has a *36% noise rate* — the "rarity → noise" pattern broke. `min_cluster_size=5` was too small: it split normal traffic's legitimate diversity into fragments, all flagged as noise. The next cells try *bigger* sizes to fix that.""",
    "bb0e45a4": """### The HDBSCAN tuning question — sweep min_cluster_size

`min_cluster_size` is a bar: too small → fragments everywhere (what we just saw). Too big → real sparse clusters destroyed. So — same disciplined approach as the DBSCAN sweep — run a **grid of sizes**: `[10, 15, 20, 30, 50, 55, 60, 65, 70, 80]`, recording clusters, noise, precision, recall for each. `hdb_sweep_results` accumulates the 10 rows; the loop cells below execute it (and extend to larger sizes 90–200 in a second pass).""",
    "424c0962": """### The sweep loop — size 10 → 80

Same metric loop as the DBSCAN sweep: for each `min_cluster_size`, run HDBSCAN, count clusters/noise, compute precision and recall on the noise bucket. Results pile into `hdb_sweep_results`, then `pd.DataFrame(...)` renders the table right in the output.

Read it column by column: watch **precision** recover as the bar rises, and watch **recall** trade against it. The table is the raw material for choosing a size — the next cell extends it to larger sizes.""",
    "119c1ae9": """### Pushing further — size 90 → 200

The first sweep may still be fragmenting large clusters (DoS's 5,445-point wall needs a high bar to hold together). This second pass extends the grid to **`[90, 100, 110, 120, 130, 150, 175, 200]`**, appending to the same `hdb_sweep_results` and re-rendering one combined table. Now the full picture is visible: where precision peaks without the normal-noise rate exploding. The markdown below settles the choice — but read the tail of the table first: at the largest sizes, `n_noise` climbs again, which is the signal that we've gone too far.""",
    "9ae72fd8": """### The "chosen" HDBSCAN — min_cluster_size=130 — and why it fails our story

From the combined sweep table, `min_cluster_size=130` was picked as the best size. This cell builds the grade sheet at that size and prints the **noise rate per family**.

But read the output with suspicion — the markdown below explains the catch: **DoS now has the highest noise rate (52.73%), higher than U2R (33.33%)**. DoS is the most common, repetitive type there is — it *shouldn't* be the most-flagged. At mcs=130, HDBSCAN can't hold the giant 5,445-point DoS blob together, so it over-fragments it into noise. Recall looks great (45.9%) but for the *wrong reason*, and normal traffic is at 25.4% false alarms. The verdict waiting below: the "rarity → noise" narrative (and precision!) stays with plain DBSCAN.""",
    "38f02533": """### One more idea — does a bigger sample change anything?

A lingering doubt: our tuned DBSCAN ran on a 15,000-row sample. Would the pattern survive on more data? This cell draws a **larger 35,000-row sample** with the **same seed 42** — deterministic, reproducible, and a superset-ish of the earlier draw. If the rarity→noise story holds on 35k rows too, the finding generalizes; if it wobbles, we've found a sample-size sensitivity worth knowing about. (The next cells would rerun the evaluation on `sample_idx_large`.)""",
    "cd3e9a0b": """### Grab the matching rows and labels for the big sample

Same lockstep as before, on the larger sample: `X_train_sample_large` = the 35,000 feature rows, `y_train_sample_large` = their matching binary labels, `attack_cat_large` = their families. Output: the shape (35,000 × 82) and the family counts — **DoS now dwarfs everything** (12,812!) vs ~1,825 in the 15k run. Keep that ratio in mind: it's about to make a headline metric misleading.""",
    "4fdecec7": """### Rerun DBSCAN on 35k rows — same parameters

Identical recipe as the 15k tuned run (`eps=3, min_samples=5`), now on the bigger sample: count clusters/noise, score precision and recall on the noise bucket, then print the **noise rate per family**.

Read the numbers twice — the markdown below explains the subtle trap: U2R's rate jumped **33% → 52.9%** (better separation!), while overall recall *fell* 0.085 → 0.016 (U2R 9 of 17 caught, but the denominator ballooned with DoS). Before concluding anything, ask: *is the model worse, or is the metric being diluted?* — the answer changes the story.""",
    "cf8f646f": """### Wrap-up — where this lands

The experiment section closes here with a blank cell — a good place to pause and let the story settle. If you want, run the family-noise-rate loop above on the large sample to double-check the ranking, or leave it as the honest record: **U2R (52.9%) >> Probe (6.5%) > R2L (3.3%) > normal (0.73%) > DoS (0.20%)** — the rarest caught most, the densest left alone. The project's defensible finding: *per-category noise rate* is the metric that tells the real story; overall recall is dominated by DoS's volume and misleads.""",
}

# ---------- Fixes: upgrade terse existing markdown cells ----------
REPLACEMENTS = {
    # Cell 0 — plan outline (+ intro on how to use this notebook)
    "decd7025": """### A beginner-friendly tour of what's coming

This notebook preprocesses the **NSL-KDD** intrusion dataset, then hunts for **anomalies** with a clustering algorithm called **DBSCAN**. Everything below is a complete self-study walkthrough:

1. Load train/test, split features vs label
2. Create a binary label (normal vs attack) — used ONLY for grading at the end
3. One-hot encode the categorical columns (protocol_type, service, flag)
4. Align train/test columns (test may have categories train doesn't, or vice versa)
5. Scale numeric features with StandardScaler
6. Save processed arrays + labels to outputs/ for reuse in later notebooks (then cluster with DBSCAN and evaluate)

**How to use this notebook:** read each `###` markdown cell before running its code cell — it tells you *what* the code does, *why* we're doing it, and *how to read* the result that appears below. If a number surprises you, pause and re-read.""",
    # ---------- Feature-group cells (37-41): upgrade to ### narrative ----------
    "ee80ea78": """### Feature group 1 — basic connection features

From the raw packet/connection info: `duration`, `protocol_type`, `service`, `flag`, `src_bytes`, `dst_bytes`, `land`, `wrong_fragment`, `urgent`

→ describes *this one connection*: how long it lasted, what protocol/service it used, how much data moved, whether it was malformed. These are the "who, what, where" of a single network event — the first description of the traffic.""",
    "3ee5d6d0": """### Feature group 2 — content features (look inside the payload)

`hot`, `num_failed_logins`, `logged_in`, `num_compromised`, `root_shell`, `su_attempted`, `num_root`, `num_file_creations`, `num_shells`, `num_access_files`, `num_outbound_cmds`, `is_host_login`, `is_guest_login`

→ describes *suspicious behavior within* the connection: did someone try `su` (switch user) or get a root shell? These need domain knowledge (they're about login attempts, privilege escalation) and are classic intrusion signals — not just unusual traffic volume.""",
    "51b80044": """### Feature group 3 — time-based traffic features (the last 2 seconds)

`count`, `srv_count`, `serror_rate`, `srv_serror_rate`, `rerror_rate`, `srv_rerror_rate`, `same_srv_rate`, `diff_srv_rate`, `srv_diff_host_rate`

→ captures *bursts*: connections to the same host/service within the last 2 seconds. A sudden flood of connections in a short window is the hallmark of DoS attacks like `neptune` — and the first glance at *context*, not just the single connection.""",
    "7b963733": """### Feature group 4 — host-based traffic features (the last 100 connections)

`dst_host_count`, `dst_host_srv_count`, `dst_host_same_srv_rate`, `dst_host_diff_srv_rate`, `dst_host_same_src_port_rate`, `dst_host_srv_diff_host_rate`, `dst_host_serror_rate`, `dst_host_srv_serror_rate`, `dst_host_rerror_rate`, `dst_host_srv_rerror_rate`

→ same idea as group 3, but over the last **100 connections** to the same destination instead of 2 seconds — catches *slower, stealthier* scans (like port scans spread over time) that a 2-second window would miss entirely.""",
    "c12af62c": """### Attack label categories — the 4 families (worth knowing for evaluation)

The ~23 specific labels roll up into **4 attack families**:

- **DoS** (Denial of Service): `neptune`, `smurf`, `back`, `teardrop`, etc. — floods, high volume → will cluster densely (our earlier prediction).
- **Probe** (surveillance/scanning): `satan`, `ipsweep`, `portsweep`, `nmap` — reconnaissance before an attack.
- **R2L** (Remote-to-Local): unauthorized access from a remote machine, e.g. `guess_passwd`, `ftp_write` — often rare and low-volume, and low-volume is exactly what DBSCAN's noise points are good at catching.
- **U2R** (User-to-Root): attacker already has local access and escalates to root, e.g. `buffer_overflow`, `rootkit` — usually the rarest category of all.

When we grade DBSCAN's noise points later, we'll classify every flagged point into one of these families (plus `normal`) — that's how we'll tell the story "rarity predicts noise".""",
    # ---------- The binary-label cell (had typos) ----------
    "dd19366d": """### The binary label convention — our grading key

A quick convention to lock in before the code that uses it: `is_attack` is a **0/1 flag**.

- `0` → Normal, not an attack
- `1` → It was an attack

It's the *answer key* we'll grade the clustering against afterwards — DBSCAN never sees it while clustering.""",
    # ---------- The large-sample experiment (new cells) ----------
    "91ad93d4": """### The robustness check — 35,000 rows instead of 15,000

Everything so far was tuned and judged on a **15,000-row sample**. A fair critic asks: *would the story survive on more data?* This section reruns the tuned DBSCAN (`eps=3, min_samples=5`) on a **35,000-row sample** drawn with the same seed 42 — deterministic, reproducible, superset-ish of the earlier draw. If the rarity→noise pattern holds on 2.3× the data, the finding generalizes; if it wobbles, we've found a sensitivity worth knowing.""",
    "c19f2fbd": """### Reading the large-sample results — a metric lesson

Compare against the 15k run — and notice the *trap* in the headline number:

- **U2R noise rate jumped: 33.3% → 52.9%** (9 of 17 caught) — a real improvement; more data let DBSCAN properly separate the rarest category.
- **Overall recall dropped: 0.085 → 0.016** — *looks* worse, but it's misleading. Recall = attacks-caught ÷ total-attacks, and total attacks ballooned (DoS alone: ~1,825 → 12,812) while DoS still correctly stays clustered (0.20% noise — even better). The denominator grew; the ratio fell. The model didn't get worse — the metric got diluted by DoS's volume.
- **The pattern is now even cleaner**: U2R (52.9%) >> Probe (6.5%) > R2L (3.3%) > normal (0.73%) > DoS (0.20%) — monotonic, rarest → most common. The sharpest, most defensible version of the finding yet.

**The real lesson, worth stating in any writeup:** aggregate recall is a **misleading headline metric** here because DoS's sheer volume dominates it. The metric that matters for the "catch novel/rare anomalies" story is **per-category noise rate**. Knowing when a metric is the wrong one to optimize — that's a mature, interview-defensible point.""",
    # ---------- The "density problem" intro (existing terse md) ----------
    "31f8e0ac": """### The motivation: one fixed eps can't serve every density

We found DBSCAN's honest weakness ourselves: one fixed `eps` has to work for the *entire* dataset. But our data has regions of wildly different density — DoS attacks are super dense (tons of nearly-identical points), while U2R is extremely sparse (only a handful of points, spread out). One global `eps` can never be "correct" for both at once — too small and you shatter the dense DoS clusters into fragments; too large and you swallow the sparse U2R points into some nearby cluster instead of flagging them.

That very real limitation is what motivates trying **HDBSCAN** next.""",
    "5b88219f": """### HDBSCAN — the tool designed for varying densities

**HDBSCAN (Hierarchical DBSCAN)** is a well-known improvement over plain DBSCAN. Instead of one fixed `eps` for the whole dataset, it handles **varying densities** — some clusters can be dense and tight, others sparse and spread out, without needing one global radius to fit all of them. Given our data has DoS (super dense) and R2L/U2R (very sparse) coexisting, this is a genuinely strong candidate — it's designed exactly for the situation we're facing. Worth trying.""",
    "2d7696f6": """### How HDBSCAN works — the mental model

**HDBSCAN's fix: it doesn't use one fixed `eps` at all.** Instead, it builds a **hierarchy of clusters at every possible density level**, then picks the most "stable" clusters across that hierarchy — meaning: for each region, it finds the density level *that region* naturally needs, rather than forcing one global number.

**Simplified mechanism (conceptually, not the full math):**
1. Imagine slowly shrinking `eps` from very large to very small, one step at a time.
2. At large `eps`, everything is one giant cluster. As `eps` shrinks, that cluster starts breaking apart into smaller, tighter sub-clusters.
3. HDBSCAN tracks how long each cluster "survives" as eps shrinks — a cluster that stays intact across a wide range of eps values is considered **stable and real**. A cluster that only exists briefly, at one narrow eps setting, is considered noise or unstable.
4. The final output picks the most stable clusters from this whole hierarchy, at whatever density level is natural for that specific region.

**Key practical difference:** instead of specifying `eps`, HDBSCAN mainly needs `min_cluster_size` (the smallest group of points you're willing to call a real cluster) — an arguably more intuitive parameter than `eps`, since you're saying "how small can a real pattern be" rather than "what's the right radius" (which we struggled to pick before).""",
    "1b02e70b": """### Reading HDBSCAN's first full verdict

Compare it against DBSCAN's numbers — the story is in the contrast:

- **Recall dropped slightly**: 0.068 vs DBSCAN's best 0.085. Not an improvement.
- **Precision collapsed**: 0.141 vs DBSCAN's 0.819. This is the critical number — HDBSCAN flagged 3,372 points as noise, but only ~14% of them were actually attacks. The vast majority (2,896 of 3,372 noise points) are **normal traffic being wrongly flagged**.
- **The category ranking broke down**: `normal` now has a **36.15% noise rate** — higher than R2L (18%), Probe (10%), and DoS (5.6%). Our clean "rarity predicts noise" pattern is gone.

**Why:** `min_cluster_size=5` was too aggressive/small for this data — it treats tons of small, legitimate sub-patterns within normal traffic (different protocols, services, etc.) as "too small to be real clusters," pushing them into noise even though they're perfectly ordinary.

**The honest conclusion**: HDBSCAN at this setting produced far more noise with substantially worse precision (14% vs 82%). This suggests HDBSCAN needs a much *larger* min_cluster_size for this dataset — next cells sweep exactly that.""",
    "7f47be93": "### The comparison table — where the story actually lands\n\n**Look at this ranking: DoS is now the highest noise rate (52.73%), higher than U2R (33.33%).**\n\nThis directly contradicts our central finding from DBSCAN — that noise rate should scale *inversely* with how common/repetitive an attack type is. DoS is the most common, most repetitive attack category, yet at `min_cluster_size=130` it has the **highest** noise rate. That's not \"catching rare anomalies well\" — that's the model becoming unable to hold DoS's naturally huge, uniform cluster together (a min_cluster_size of 130 might be splitting or excluding parts of the massive 5,445-point DoS group), while incidentally still catching a good chunk of U2R too.\n\n**So the honest conclusion, not glossing over it:** the improved recall at HDBSCAN(130) isn't coming from genuinely better rare-anomaly detection — it's coming from a different, less interesting failure mode: it's now over-fragmenting large clusters like DoS, which happens to help recall numerically but **destroys the actual narrative** we care about (rare, novel anomalies vs. common patterns). And normal traffic's noise rate (25.4%) is also uncomfortably high — 1 in 4 normal points wrongly flagged.\n\n**Comparing the two models on the story that actually matters for this project:**\n\n| | DBSCAN (eps=3) | HDBSCAN (mcs=130) |\n|---|---|---|\n| U2R noise rate | **33.3%** | 33.3% |\n| Normal noise rate | **1.1%** (low, good) | 25.4% (high, bad) |\n| DoS noise rate | **0.35%** (low, correctly not flagged) | 52.7% (high, wrong reason) |\n| Overall recall | 8.5% | 45.9% |\n| Pattern integrity | Rarity → noise, clean | Broken — DoS highest |",
    "eff7cce6": "### 👀 We have 42 columns — make sure we see them all\n\nOur table is 42 columns wide, and by default pandas hides the middle ones behind `...`. The next line flips that setting so full tables show up when we preview them.",
    "27d492fa": "### ✅ Nothing missing — verified, not assumed\n\nBoth checks returned zero: no missing values in train, none in test. Since DBSCAN genuinely can't handle gaps, this clean bill of health lets us move on without fear.",
    "68e0fa27": "### 📊 The numbers that matter, side by side\n\nHere's the `describe().T` output for the heavy hitters:\n\n- `src_bytes`: mean ~45,566, median 44, max ~**1.38 billion**\n- `dst_bytes`: mean ~19,779, median 0, max ~**1.31 billion**\n- …and the rate features (`serror_rate`, `same_srv_rate`…) all squeezed into **0 to 1**\n\nThe skew is the story: medians near 0, yet a few enormous outliers. Features on wildly different scales are the whole reason we'll standardize later.",
    "edf3895c": """### 📏 Precision & recall — what the numbers actually mean

Let's decode the two numbers this project lives or dies by.

**Precision** — of the points we flagged as noise, how many were really attacks?

$$142 \\, / \\, 199 = 71.4\\%$$

Pretty good — when DBSCAN says "this is unusual", it's right about 7 times out of 10. High precision = we trust its warnings.

**Recall** — of *all* the real attacks, how many did we actually catch?

$$142 \\, / \\, (142 + 6846) = 142 \\, / \\, 6988 = 2.03\\%$$

Ouch — we caught only 2 attacks in 100. The other 6,846 got absorbed into clusters, looking too much like normal traffic to stand out.

In one glance: DBSCAN flags *rare weirdness* precisely, but everyday floods slip past. Remember this tension — it's the whole point of the parameter sweep at the end.""",
    "2713c650": """### 🎁 What we just learned — the pattern behind the numbers

The noise-flagging rate climbs as rarity climbs:

- **U2R** — the rarest family (only 6 samples) — flagged **16.7%** of the time
- **R2L** 3.6% · **Probe** 2.3% · **DoS** 1.9%
- **normal** — densest of all — flagged just **0.71%**

The story: **the rarer and more unusual the attack, the more likely DBSCAN flags it as noise.** DoS and Probe sit in the middle — not rare enough to always stand out, not dense enough to fully hide.

That's a clean, defensible conclusion — and exactly what we'd hope from a *structure-based* anomaly detector.""",
}

INSERT_REPLACEMENTS = {
    "35497740": {"action": "fill", "source": "sweep_df = pd.DataFrame(sweep_results)\nsweep_df.sort_values(\"recall\", ascending=False)"},
}


def cell_source_str(cell) -> str:
    parts = cell.get("source", [])
    return "".join(parts) if isinstance(parts, list) else parts


def main() -> None:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert nb["nbformat"] == 4 and nb["nbformat_minor"] == 5
    orig_n = len(cells)
    print(f"original cells: {orig_n}")

    ids = [c.get("id") for c in cells]
    assert len(ids) == len(set(ids)), "duplicate ids"

    idx_of = {cid: i for i, cid in enumerate(ids)}

    # ----- preconditions (fail fast if the notebook drifted beyond what we expect) -----
    # Cell 53: the OLD typo content OR the FIXED content are both fine — replace only when typos remain.
    c53 = cells[idx_of["dd19366d"]]
    s53 = cell_source_str(c53)
    if "Tt" in s53 or "a attack" in s53:
        typo_fix_pending = True
    else:
        typo_fix_pending = False
        print("cell dd19366d already fixed — skipping its replace", file=sys.stderr)

    # Duplicate cell must already be gone, and cell 84 must already be filled,
    # on the CURRENT notebook.
    assert "43178534" not in ids, "duplicate cell 43178534 still present"
    c84 = cells[idx_of["35497740"]]
    assert cell_source_str(c84).strip() != "", "cell 84 unexpectedly empty again"
    # 71 must still exist.
    assert "af330a37" in ids, "cell 71 missing"

    # Build ops — idempotent: skip any target that already has a tutorial
    # markdown ('###') directly before it (from an earlier run).
    def already_explained(cid: str) -> bool:
        i = idx_of[cid]
        prev = cells[i - 1] if i > 0 else None
        return bool(
            prev
            and prev["cell_type"] == "markdown"
            and "".join(prev.get("source", [])).startswith("###")
        )

    ops = []
    skipped = 0
    for cid, body in BODIES.items():
        assert cid in idx_of, f"target {cid} not in notebook"
        if already_explained(cid):
            skipped += 1
            continue
        ops.append((idx_of[cid], "insert", body))
    print(f"skipping {skipped} already-explained targets")
    # fills/replaces (the delete already happened in an earlier pass — verified above)
    for cid, r in INSERT_REPLACEMENTS.items():
        ops.append((idx_of[cid], r["action"], r["source"]))
    for cid, src in REPLACEMENTS.items():
        if cid == "dd19366d" and not typo_fix_pending:
            continue  # already fixed earlier — don't touch it again
        ops.append((idx_of[cid], "replace", src))
    ops.sort(key=lambda o: o[0])

    new_cells = list(cells)
    offset = 0
    made = set(ids)
    for orig_idx, kind, payload in ops:
        target = orig_idx + offset
        if kind == "insert":
            cell = {
                "cell_type": "markdown",
                "id": uuid.uuid4().hex[:8],
                "metadata": {},
                "source": [payload],
            }
            assert cell["id"] not in made
            made.add(cell["id"])
            new_cells.insert(target, cell)
            offset += 1
        elif kind in ("replace", "fill"):
            new_cells[target]["source"] = [payload]

    nb["cells"] = new_cells
    out = json.dumps(nb, indent=1, ensure_ascii=False)
    if not out.endswith("\n"):
        out += "\n"
    NOTEBOOK.write_text(out, encoding="utf-8")

    # ---- verify ----
    nb2 = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    c2 = nb2["cells"]
    expect = orig_n + (len(BODIES) - skipped)
    assert len(c2) == expect, f"count {len(c2)} != {expect} (skipped {skipped})"
    assert nb2["metadata"] == nb["metadata"], "metadata changed"
    ids2 = [c.get("id") for c in c2]
    assert len(ids2) == len(set(ids2)), "dup ids after rewrite"
    assert "43178534" not in ids2, "dup present"
    assert "af330a37" in ids2, "cell 71 missing"
    c84 = next(c for c in c2 if c["id"] == "35497740")
    assert cell_source_str(c84).startswith("sweep_df = pd.DataFrame"), "84 not filled"
    # typo cell fixed
    s53 = cell_source_str(next(c for c in c2 if c["id"] == "dd19366d"))
    assert "Tt" not in s53 and "a attack" not in s53, "cell 53 still has typos"
    assert "not an attack" in s53 and "It was an attack" in s53, "cell 53 fix missing"
    for cid, src in REPLACEMENTS.items():
        assert cell_source_str(next(c for c in c2 if c["id"] == cid)) == src, f"{cid} replace failed"
    # check ordering: each inserted md should sit right before its target
    # (cf8f646f is the closing wrap-up markdown at the very end — no target after it)
    for cid, body in BODIES.items():
        pos = [i for i, c in enumerate(c2) if c["id"] == cid][0]
        if cid == "cf8f646f":
            continue  # closing note at end of notebook
        assert pos + 1 < len(c2), f"md {cid} at end"
        prev = c2[pos - 1] if pos > 0 else None
        assert (
            prev
            and prev["cell_type"] == "markdown"
            and "".join(prev.get("source", [])).startswith("###")
        ), f"no tutorial md immediately before {cid}"
        # the body only needs to match if we actually inserted it this run
        if not already_explained(cid):
            assert c2[pos]["source"] == [body], f"body mismatch for {cid}"

    print(f"OK: {len(c2)} cells ({orig_n} -> {expect}), {len(BODIES)} explanations inserted, "
          f"{len(REPLACEMENTS)} markdown upgrades, dup already gone, cell 84 filled, cell 53 typo fixed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)