# X-SENTINEL primary comparison

Primary M3 is view mass. M5 and Metadata-only stress are outside this primary matrix.

| Dataset | Complete | Unsupported | Failed | Not run |
|---|---:|---:|---:|---:|
| EMBER2018 | 27 | 0 | 0 | 0 |
| EMBER2024 | 27 | 0 | 0 | 0 |

Per-run metrics are in [results.csv](results.csv). Counts and uncertainty are retained in the underlying final cell artifacts.

The same held-out source IDs are reused across seeds within each dataset. These are paired within-run comparisons; do not treat repeated IDs as independent observations or pool datasets into one confidence interval.

Weak, failed and unsupported cells remain explicit. Low ASR or unconfirmed attack viability does not establish detector efficacy.

Full uses three additional clean view models. Calibration times, model bytes and alternating-order warmed-up latency are recorded per completed cell. Shared-process peak memory does not establish an isolated full-versus-reduced RAM difference.
