#!/usr/bin/env bash
# Static analysis only. Samples are never invoked as programs.
set -euo pipefail
KIT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${BODMAS_WORK_ROOT:-$HOME/xsentinel-bodmas-work}"
IMAGE='xsentinel-bodmas:20261019'
usage() {
  echo 'Usage: bash scripts/bodmas_run_static.sh catalog'
  echo '       bash scripts/bodmas_run_static.sh scan COHORT BUNDLE RUN [checker options]'
  echo 'COHORT: smoke | malware | benign; BUNDLE: 2018-reduced | 2018-full | 2024-reduced | 2024-full'
  exit 2
}
[[ $# -ge 1 ]] || usage
command_name="$1"
shift
if [[ "$command_name" == 'catalog' ]]; then
  [[ $# -eq 0 ]] || usage
  exec python3 -m json.tool "$KIT_ROOT/bundle_catalog.json"
fi
[[ "$command_name" == 'scan' && $# -ge 3 ]] || usage
cohort="$1"
bundle_alias="$2"
run_name="$3"
shift 3
case "$cohort" in smoke|malware|benign) ;; *) usage ;; esac
case "$bundle_alias" in 2018-reduced|2018-full|2024-reduced|2024-full) ;; *) usage ;; esac
[[ "$run_name" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$ ]] || usage
[[ -d "$WORK_ROOT/samples/$cohort" && ! -L "$WORK_ROOT/samples" && ! -L "$WORK_ROOT/samples/$cohort" ]] || {
  echo "Missing input directory or symbolic link rejected: $WORK_ROOT/samples/$cohort" >&2
  exit 2
}
for argument in "$@"; do
  case "$argument" in
    --input-dir|--input-dir=*|--bundle-root|--bundle-root=*|--bundle-id|--bundle-id=*|--out|--out=*)
      echo 'Input, model and output paths are managed by this wrapper.' >&2
      exit 2 ;;
  esac
done
bundle_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]]["id"])' "$KIT_ROOT/bundle_catalog.json" "$bundle_alias")"
mkdir -p -- "$WORK_ROOT/results"
[[ ! -e "$WORK_ROOT/results/$run_name" ]] || {
  echo 'Output exists. Choose a new RUN name; previous evidence is preserved.' >&2
  exit 2
}
exec sudo docker run --rm --pull=never --no-healthcheck \
  --network none --read-only --user "$(id -u):$(id -g)" \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --cpus 2 --memory 4g \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m,mode=1777 \
  -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
  --mount "type=bind,src=$KIT_ROOT/outputs/primary,dst=/app/outputs/primary,readonly" \
  --mount "type=bind,src=$WORK_ROOT/samples,dst=/samples,readonly" \
  --mount "type=bind,src=$WORK_ROOT/results,dst=/results" \
  "$IMAGE" python scripts/check_bodmas_static.py scan \
  --input-dir "/samples/$cohort" --bundle-root /app/outputs/primary \
  --bundle-id "$bundle_id" --out "/results/$run_name" "$@"
