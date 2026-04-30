# How to Run Benchmarks

Quick-start guide for running speaker-diarization evaluations against three different endpoints:

1. **SubQ — Production** (`https://api.aldea.ai`)
2. **SubQ — Staging** (`https://stt-api.staging.aldea.ai`)
3. **Deepgram** (managed Deepgram cloud, `nova-3`)

This file assumes you've already followed the main [`README.md`](README.md) for **installation**. If you haven't, do that first and come back here when `uv run openbench-cli summary` works without errors.

---

## Prerequisites (do these once)

Before running any benchmark you must have the following in place. Skip this block only if you've done it before on this machine.

### 1. Install the project

See the **Setting up the environment** section of [`README.md`](README.md). In short:

```bash
cd /Users/nikita/git/OpenBench
make setup            # creates .venv via uv and installs deps
```

Verify:

```bash
uv run openbench-cli summary --disable-datasets --disable-metrics --disable-compatibility
```

You should see a list of pipelines including `subq-diarization` and `deepgram-diarization`.

### 2. Log in to Weights & Biases (once)

```bash
uv run wandb login
```

Paste your API key from <https://wandb.ai/authorize>. This writes credentials to `~/.netrc` and you don't need to do it again.

> **Note:** A `WANDB_API_KEY` set in `.env` will also work, but `wandb login` is the cleanest one-time setup.

### 3. Populate `.env`

The `.env` file at the repo root must contain the right keys for the endpoint you intend to test. **You must comment/uncomment the appropriate block** before each run — there is **no default fallback** for `SUBQ_HOST_URL` anymore; the eval will fail-fast with `ValueError: SUBQ_HOST_URL is not set` if it's missing.

Recommended `.env` layout (already in the repo, just uncomment the block you want active):

```bash
# Dev environment
# SUBQ_API_KEY="org_2Uufv3-..."     # dev key
# SUBQ_HOST_URL=

# Staging environment
# SUBQ_API_KEY=org_2Uufv3-...
# SUBQ_HOST_URL="https://stt-api.staging.aldea.ai"

# Prod environment
# SUBQ_API_KEY="org_jj_A1kWT8..."
# SUBQ_HOST_URL="https://api.aldea.ai"

DEEPGRAM_API_KEY="3c2c9abe..."

WANDB_API_KEY="wandb_v1_..."
```

Only **one** SubQ block must be uncommented at a time. `DEEPGRAM_API_KEY` and `WANDB_API_KEY` can stay set permanently.

### 4. Important notes — read once before any run

- **Update `.env` *before* every SubQ run.** The `SUBQ_HOST_URL` and `SUBQ_API_KEY` lines determine whether you're hitting prod or staging. Forgetting to switch is the #1 source of "why does my run look weird" issues.
- **Verify the endpoint at the start of every run.** The very first lines after `🔧 Creating pipeline: subq-diarization` will be:
  ```
  [SubqApi] SUBQ_HOST_URL=https://api.aldea.ai           # or staging URL
  INFO:openbench.engine.subq_engine:SubqApi initialized with SUBQ_HOST_URL=...
  ```
  If that doesn't match what you intended, kill the run (`Ctrl+C`) and fix `.env`.
- **`set -a && source .env && set +a` is mandatory** before `uv run …` — that's what loads `.env` into the process environment for the eval.
- **`export WANDB_ENTITY=n-subquadratic`** ensures runs land in the team workspace `n-subquadratic/openbench-diarization`, not in your personal namespace.
- **Always use distinct `--wandb-run-name` and tags per endpoint.** Prod/staging/deepgram runs all live in the same project so they can be compared — distinguishing them by tag is what makes the comparison clean.
- **No trailing whitespace after `\`** when copy-pasting multi-line commands. zsh silently splits the command if `\` isn't the last character on a line. Copy from this file directly, not from terminal scrollbacks.
- **Staging may be unstable.** If you hit `httpx.HTTPStatusError: Server error '500'`, the whole eval aborts on the first failed sample (no per-sample retry yet). Re-run, or skip that file.
- **Pipeline output dirs** land at `outputs/YYYY-MM-DD/HH-MM-SS/<pipeline>_results/`. Each contains the per-file RTTM predictions, the W&B local cache, and the `output.log` with all metric prints. Useful for offline debugging.
- **Each run uploads ~RTTMs + embeddings** as W&B artifacts. They're a few MB total — fine, but be aware if you run many benchmarks.

---

## The three benchmark commands

All three target the same dataset (`ami-ihm`, 16 files), the same metric set, and the same W&B project so they're directly comparable.

### 1. SubQ — Production

> **Before running:** in `.env` keep only the **Prod environment** block uncommented.

```bash
cd /Users/nikita/git/OpenBench
set -a && source .env && set +a
export WANDB_ENTITY=n-subquadratic

uv run openbench-cli evaluate \
  --pipeline subq-diarization \
  --dataset ami-ihm \
  -m der \
  -m jer \
  -m sca \
  -m scer \
  -m scmae \
  -m diarization_purity \
  -m diarization_purity_coverage_fmeasure \
  -m diarization_homogeneity \
  -m detection_error_rate \
  -m detection_cost_function \
  -m detection_precision_recall_fmeasure \
  --use-wandb \
  --wandb-project openbench-diarization \
  --wandb-run-name subq-prod-ami-ihm-full-metrics \
  --wandb-tags subq-diarization \
  --wandb-tags ami-ihm \
  --wandb-tags prod \
  --wandb-tags subq-prod \
  --wandb-tags env:prod
```

Expected first lines after launch:

```
🔧 Creating pipeline: subq-diarization
[SubqApi] SUBQ_HOST_URL=https://api.aldea.ai
```

### 2. SubQ — Staging

> **Before running:** in `.env` keep only the **Staging environment** block uncommented.

```bash
cd /Users/nikita/git/OpenBench
set -a && source .env && set +a
export WANDB_ENTITY=n-subquadratic

uv run openbench-cli evaluate \
  --pipeline subq-diarization \
  --dataset ami-ihm \
  -m der \
  -m jer \
  -m sca \
  -m scer \
  -m scmae \
  -m diarization_purity \
  -m diarization_purity_coverage_fmeasure \
  -m diarization_homogeneity \
  -m detection_error_rate \
  -m detection_cost_function \
  -m detection_precision_recall_fmeasure \
  --use-wandb \
  --wandb-project openbench-diarization \
  --wandb-run-name subq-staging-ami-ihm-full-metrics \
  --wandb-tags subq-diarization \
  --wandb-tags ami-ihm \
  --wandb-tags staging \
  --wandb-tags subq-staging \
  --wandb-tags env:staging
```

Expected first lines after launch:

```
🔧 Creating pipeline: subq-diarization
[SubqApi] SUBQ_HOST_URL=https://stt-api.staging.aldea.ai
```

### 3. Deepgram

> **Before running:** ensure `DEEPGRAM_API_KEY` is set in `.env`. The SubQ env vars are not used by this command.

```bash
cd /Users/nikita/git/OpenBench
set -a && source .env && set +a
export WANDB_ENTITY=n-subquadratic

uv run openbench-cli evaluate \
  --pipeline deepgram-diarization \
  --dataset ami-ihm \
  -m der \
  -m jer \
  -m sca \
  -m scer \
  -m scmae \
  -m diarization_purity \
  -m diarization_purity_coverage_fmeasure \
  -m diarization_homogeneity \
  -m detection_error_rate \
  -m detection_cost_function \
  -m detection_precision_recall_fmeasure \
  --use-wandb \
  --wandb-project openbench-diarization \
  --wandb-run-name deepgram-ami-ihm-full-metrics \
  --wandb-tags deepgram-diarization \
  --wandb-tags ami-ihm \
  --wandb-tags deepgram \
  --wandb-tags env:deepgram
```

---

## After a run finishes

Open the project workspace:

<https://wandb.ai/n-subquadratic/openbench-diarization>

You'll see:

- **Runs list** — filter by tag (`prod`, `staging`, `deepgram`) to isolate one environment.
- **Compare** — tick 2+ runs and click *Compare* to get global-metric deltas.
- **Tables → `ami-ihm/der_breakdown_table`** — DER's `false_alarm`, `missed_detection`, `confusion` components per run.
- **Tables → `ami-ihm/task_results_table`** — per-file metric values.
- **Tables → `ami-ihm/sample_results_table`** — predicted vs reference speaker counts per file.
- **Artifacts** — `predictions` (RTTMs) and `embeddings`.

## Quick comparison cheat-sheet

| Metric | Range | Lower better? | Use for |
|---|---|---|---|
| `der` | 0 → ∞ | yes | overall time-weighted error |
| `jer` | [0, 1] | yes | per-speaker fairness (each spk = 1 vote) |
| `sca` | [0, 1] | **no** | did you nail the speaker count exactly? |
| `scer` | 0 → ∞ | yes | relative speaker-count error |
| `scmae` | 0 → ∞ | yes | "off by how many speakers on average" |
| `detection_error_rate` | 0 → ∞ | yes | VAD only (speech vs silence) |

## Troubleshooting

- **`ValueError: SUBQ_HOST_URL is not set`** → uncomment the right block in `.env` and re-`source` it.
- **`ValueError: SUBQ_API_KEY is not set`** → same fix.
- **`httpx.HTTPStatusError: 500`** → server-side error from the chosen endpoint (likely staging). Re-run.
- **Eval crashes on the first sample** → check the `[SubqApi] SUBQ_HOST_URL=…` print: it almost always means `.env` was pointed at a different env than you expected.
- **Run shows up under your personal entity** → you forgot `export WANDB_ENTITY=n-subquadratic`. Add the team-tag manually in the W&B UI to retroactively classify, or rerun.
- **Trailing-whitespace failures** → if a multiline command splits unexpectedly, copy from this file directly.
