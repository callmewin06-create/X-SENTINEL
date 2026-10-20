#!/usr/bin/env bash
# Run the four frozen bundles on the same file manifest.
set -euo pipefail
[[ $# -eq 5 ]] || {
  echo 'Usage: bash scripts/bodmas_run_matrix.sh COHORT PREFIX LIMIT LABEL LABEL_SOURCE' >&2
  exit 2
}
kit_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cohort="$1"
prefix="$2"
limit="$3"
label="$4"
label_source="$5"
[[ "$prefix" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,59}$ && "$limit" =~ ^[1-9][0-9]*$ ]] || exit 2
case "$label" in unknown|benign|malware) ;; *) exit 2 ;; esac
first_run="${prefix}_2018_reduced"
overall=0
for alias in 2018-reduced 2018-full 2024-reduced 2024-full; do
  run="${prefix}_${alias//-/_}"
  options=(--limit "$limit" --seed 17 --declared-label "$label" --label-source "$label_source")
  if [[ "$run" != "$first_run" ]]; then
    options+=(--manifest "/results/$first_run/manifest.json")
  fi
  status=0
  bash "$kit_root/scripts/bodmas_run_static.sh" scan "$cohort" "$alias" "$run" "${options[@]}" || status=$?
  if [[ "$status" -gt 1 ]]; then
    echo "Configuration/container error in $run (exit $status); stopped." >&2
    exit "$status"
  fi
  [[ "$status" -eq 0 ]] || overall=1
done
echo "Four bundle runs completed. File errors are retained. Exit: $overall"
exit "$overall"
