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

## Transcription benchmarks (WER)

Same OpenBench engine, different pipeline (`subq-transcription` instead of `subq-diarization`), different metric (`wer`), and a different set of datasets that have a transcription ground truth.

The W&B project for transcription is `openbench-transcription` (so it doesn't pollute the diarization workspace). The `subq-transcription` pipeline routes through the same `SUBQ_HOST_URL` / `SUBQ_API_KEY` as `subq-diarization` — switch endpoints by editing `.env` exactly as for diarization (Cohere / Staging / Prod block).

### 4. SubQ Transcription — single dataset (alias mode)

Use this for quick iteration, sanity-checking a new endpoint, or one-off WER measurements. Same alias-mode CLI shape as the diarization recipes above:

```bash
cd /Users/nikita/git/OpenBench
set -a && source .env && set +a
export WANDB_ENTITY=n-subquadratic

uv run openbench-cli evaluate \
  --pipeline subq-transcription \
  --dataset earnings22-3hours \
  -m wer \
  --use-wandb \
  --wandb-project openbench-transcription \
  --wandb-run-name subq-cohere-earnings22-3hours \
  --wandb-tags subq-transcription \
  --wandb-tags earnings22-3hours \
  --wandb-tags cohere \
  --wandb-tags env:cohere
```

Useful single datasets to know about (all transcription-compatible, all publicly accessible from the standard HF account):

| Alias | HF repo | Audio | What it tests |
|---|---|---:|---|
| `earnings22-keywords-debug` | `argmaxinc/earnings22-kws-golden` | ~5 min, 5 samples | Smoke test (~30s wall) |
| `librispeech-200` | `argmaxinc/librispeech-openbench` | ~27 min, 200 clips | Clean read speech baseline |
| `earnings22-3hours` | `argmaxinc/earnings22-openbench` | ~3 h, 3 calls | Quick long-form check |
| `earnings22-12hours` | `argmaxinc/earnings22-openbench` | ~12 h, 13 calls | Long-form business, 22-country accents |
| `chime-6` | `argmaxinc/chime-6` | ~5 h, 2 sessions | Far-field conversational (hardest) |
| `common-voice-en` | `argmaxinc/common_voice_17_0-argmax_subset-400-openbench` | ~39 min, 400 clips | Diverse speaker / mic short clips |

Datasets that are **not** accessible (HF gated): `argmaxinc/ami-openbench` (both `ihm-mix` and `sdm` subsets), `argmaxinc/callhome-english`, `argmaxinc/msdwild`, `argmaxinc/icsi`. Don't include them in transcription configs unless you have access — the eval will abort on the first attempt to load.

### 5. SubQ Transcription — comprehensive multi-dataset suite (config-file mode)

For real cross-endpoint comparisons (Cohere vs Prod, model A vs model B), run a full suite of complementary datasets in **one** `evaluate` invocation. This produces a single W&B run with one `wer` value per dataset, all directly comparable in the workspace.

The repo includes a ready-made config covering 4 audio-condition axes:

```bash
cd /Users/nikita/git/OpenBench
set -a && source .env && set +a
export WANDB_ENTITY=n-subquadratic
export SUBQ_REQUEST_TIMEOUT=1200          # 20 min per-request, see "Operational env vars" below
export SUBQ_MAX_RETRIES=8                 # retry on 429/5xx, see "Operational env vars" below

uv run openbench-cli evaluate \
  --evaluation-config config/eval_subq_cohere_comprehensive.yaml \
  --verbose
```

The shipped config (`config/eval_subq_cohere_comprehensive.yaml`) defaults to model `CohereLabs/cohere-transcribe-03-2026` and 4 datasets: `librispeech-200`, `earnings22-12hours`, `chime-6`, `common-voice-en`. Wall clock is ~30–60 min depending on endpoint speed. Edit the file (or use Hydra overrides, below) to change the model, datasets, or W&B run name.

#### Hydra overrides — same config, different endpoint/model

To run the same suite against a different endpoint or model **without editing the YAML**, use `--evaluation-config-overrides` (one `-eov` flag per override). This is how the comparison runs were done:

```bash
# Step 1: edit .env to swap endpoint blocks (Cohere ↔ Prod ↔ Staging) — exactly as for diarization
# Step 2:

cd /Users/nikita/git/OpenBench
set -a && source .env && set +a
export WANDB_ENTITY=n-subquadratic
export SUBQ_REQUEST_TIMEOUT=1200
export SUBQ_MAX_RETRIES=8

uv run openbench-cli evaluate \
  --evaluation-config config/eval_subq_cohere_comprehensive.yaml \
  --evaluation-config-overrides 'pipeline_config.SubqTranscriptionPipeline.model_version=nvidia/parakeet-tdt-0.6b-v2' \
  --evaluation-config-overrides 'benchmark_config.wandb_config.run_name=subq-prod-parakeet-tdt-0.6b-v2-comprehensive' \
  --evaluation-config-overrides 'benchmark_config.wandb_config.tags=[subq-transcription,comprehensive,prod,model:nvidia-parakeet-tdt-0.6b-v2,env:prod]' \
  --verbose
```

> **Note on `model_version` against the Prod endpoint.** Probing four different model names against `https://api.aldea.ai` (`nvidia/parakeet-tdt-0.6b-v2`, `parakeet-tdt-0.6b-v2`, `parakeet`, `nova-3`) all return the **same** SHA-256 model hash in the response metadata. Prod ignores `model=` and runs whatever it runs (currently Parakeet). The `model_version` field is therefore **informational only on prod** — set it to whatever value you want recorded in the W&B config snapshot, but don't expect the server to honor it. Cohere and dev endpoints **do** honor `model=`.

---

## Long-running evals: detached / nohup pattern

The default Cursor / IDE shell invocation handoff between foreground and background can SIGKILL a long-running `uv run` python process at the moment it transitions to background, even though the docs say it shouldn't. Symptoms: process dies at exactly the `block_until_ms` mark with `exit_code: unknown`, no Python traceback, W&B run never closes cleanly (`resource_tracker: leaked semaphore objects`).

For any eval that takes more than ~2 min, **always launch fully detached** instead of relying on the foreground/background handoff:

```bash
nohup uv run openbench-cli evaluate ...args... \
  > /tmp/openbench_<run>.log 2>&1 & disown
echo "started PID=$!"
```

Then, **always do a 3-line sanity check 10–60 s after launch** to confirm (a) the process is alive and (b) it's pointed at the endpoint you intended:

```bash
ps -p <PID> > /dev/null && echo "ALIVE" || echo "DEAD"
grep -E "SUBQ_HOST_URL|✅|Iteration:" /tmp/openbench_<run>.log | head -10
```

You're looking for `[SubqApi] SUBQ_HOST_URL=<the URL you expected>` and at least one `Iteration: N of M` line. If `SUBQ_HOST_URL` is wrong, kill the process (`kill <PID>`) and fix `.env` before wasting the run.

To monitor mid-run progress:

```bash
grep -E "Evaluating |Iteration:|✅ Evaluation completed|❌|Traceback" /tmp/openbench_<run>.log | tail -20
grep "retrying in" /tmp/openbench_<run>.log | wc -l   # count retry events (rate-limit pressure)
```

---

## Operational env vars (transcription pipeline)

Three env vars on the SubQ engine are useful for keeping long evals alive against unstable or rate-limited endpoints. All are **opt-in** — defaults preserve the original behavior.

| Env var | Default | Recommended for long evals | What it does |
|---|---:|---:|---|
| `SUBQ_REQUEST_TIMEOUT` | `600` (s) | `1200` | Per-request HTTP timeout. Bump if any endpoint occasionally hangs on a single file (Cohere has been observed hanging >10 min on individual earnings22 files). |
| `SUBQ_MAX_RETRIES` | `0` | `8` | Number of retries on **retryable** upstream errors (`429`, `500`, `502`, `503`, `504`). Without this, the eval aborts on the **first** rate-limit / transient server error. |
| `SUBQ_RETRY_BACKOFF_BASE_S` | `2.0` | leave default | Base for exponential backoff between retries. Wait sequence: 2 s, 4 s, 8 s, 16 s, 32 s, 60 s (capped). |
| `SUBQ_RETRY_BACKOFF_CAP_S` | `60.0` | leave default | Maximum single backoff wait. |

> **When to set `SUBQ_MAX_RETRIES`.** Always set it for any prod run (`https://api.aldea.ai`) because prod has tight rate limits. The Common Voice dataset (400 short clips at ~1 req/s sustained) reliably hits HTTP 429 within seconds; without retries the eval dies on sample ~60 of 200 with `DeepgramApiError: None (Status: 429)`. With `SUBQ_MAX_RETRIES=8`, the eval rides through the rate-limit windows and completes (typically with 20–40 retry events that you can count via the `grep ... retrying in` snippet above). Tracking ticket: see Linear `INFRA-3`.

> **Caveat: retries inflate timing metrics.** When a retry fires, the wait time gets included in `prediction_time` and degrades the reported `speed_factor` for that sample. For pure-WER measurement this is fine. For latency benchmarking, set `SUBQ_MAX_RETRIES=0` and re-run only after the rate limit issue is resolved server-side.

---

## Endpoint quirks (production `https://api.aldea.ai`)

These three behaviors of the prod endpoint affect how to interpret results. They came up repeatedly during cross-endpoint benchmarking.

1. **`model=` query parameter is ignored** — see the note in section 5 above. All four model names probed return the same SHA-256 model hash. Prod always runs whatever model is currently deployed.
2. **Empty `words[]` array, transcript-only response.** Prod returns the transcription as a single `transcript` string with `words: []`, while Cohere/Deepgram return per-word objects with timestamps. The pipeline's engine (`src/openbench/engine/subq_engine.py`) falls back to splitting `transcript` on whitespace when `words[]` is empty, so **WER works**. But **per-word timestamps are zeroed** in the W&B `task_results_table` for prod responses — fine for WER, broken for any timing-based downstream metric (segment alignment, captions, WDER). Tracking ticket: see Linear `STT-940`.
3. **Tight rate limits** — see the `SUBQ_MAX_RETRIES` guidance above.

The Cohere endpoint (`https://cohere.sparsecompute.com:4433`) doesn't exhibit any of (1)–(3), but does occasionally hang on individual long-form files; that's what `SUBQ_REQUEST_TIMEOUT=1200` is for.

---

## Publishing a comparison report to W&B

Once you have two (or more) finished runs in `openbench-transcription` (or `openbench-diarization`), you can publish a W&B Report comparing them programmatically using `wandb_workspaces.reports.v2`. This is much richer than the W&B UI's built-in run-comparison view because you can pull per-sample tables down via the Public API and compute things like substitution/insertion/deletion breakdowns or per-file win/loss counts.

One-time install of the optional dependency:

```bash
uv pip install "wandb[workspaces]"
```

Skeleton (full example used during the Cohere-vs-Parakeet comparison lives in `/tmp/build_wandb_report.py` from that session):

```python
import wandb
import wandb_workspaces.reports.v2 as wr

# Pull the runs and (optionally) per-sample task_results_table artifacts
api = wandb.Api()
cohere = api.run("n-subquadratic/openbench-transcription/twk01lmy")
prod   = api.run("n-subquadratic/openbench-transcription/qqkgz3lv")

# Per-sample table example (one per dataset per run)
art = api.artifact("n-subquadratic/openbench-transcription/run-twk01lmy-librispeech-200task_results_table-sohX3w:v0")
# columns: dataset_name, sample_id, pipeline_name, metric_name, result,
#          detailed_num_substitutions, detailed_num_words,
#          detailed_num_insertions, detailed_num_deletions

report = wr.Report(
    project="openbench-transcription",
    entity="n-subquadratic",
    title="Cohere vs Prod — Comprehensive Transcription Comparison",
    description="...",
    blocks=[
        wr.MarkdownBlock(text="## TL;DR\n..."),
        wr.HorizontalRule(),
        # ...one MarkdownBlock per section with markdown tables + bullets
    ],
)
url = report.save()
print(url)
```

Tip: build all the markdown content as Python f-strings using values fetched from `run.summary` and the per-sample tables, so the report is regenerable verbatim if you re-run the underlying evals.

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
