#!/usr/bin/env sh
# =============================================================================
# SomaOS Brain Next — container entrypoint
#   --mode demo     run the self-contained demo loop (default, no weights)
#   --mode service  start the closed-source motor runtime (compiled core)
# =============================================================================
set -eu

MODE="demo"
for arg in "$@"; do
  case "$arg" in
    --mode) : ;;
    demo|service) MODE="$arg" ;;
  esac
done

echo "[somaos-motor] entrypoint: mode=${MODE}"

if [ "${MODE}" = "service" ]; then
  # Model weights are fetched at startup from a maintainer-controlled source.
  # If not configured, the runtime refuses to start the closed core and falls
  # back to the demo loop instead of failing.
  if [ -n "${SOMAOS_WEIGHT_URL:-}" ]; then
    echo "[somaos-motor] fetching model weights..."
    python /opt/somaos/weight_client.py \
      --url "${SOMAOS_WEIGHT_URL}" \
      --sha256 "${SOMAOS_WEIGHT_SHA256:-}" \
      --dest "${SOMAOS_WEIGHTS_DIR:-/var/lib/somaos/weights}" || {
        echo "[somaos-motor] weight fetch failed; falling back to demo mode"
        MODE="demo"
      }
  else
    echo "[somaos-motor] SOMAOS_WEIGHT_URL not configured; falling back to demo mode"
    MODE="demo"
  fi
fi

if [ "${MODE}" = "service" ]; then
  exec python /opt/somaos/service/motor_service.py --host 0.0.0.0 --port "${SOMAOS_PORT:-8766}"
fi

# ---- demo loop -------------------------------------------------------------
echo "============================================================"
echo " SomaOS Brain Next — demo loop (virtual servos)"
echo "============================================================"
python /opt/somaos/demos/safety_gate/demo_safety_gate.py
echo
python /opt/somaos/demos/traj_follow/demo_traj_follow.py --seed 3 --hz 20
echo
echo "[somaos-motor] demo loop finished — exit OK"
