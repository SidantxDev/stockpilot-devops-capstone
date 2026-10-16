#!/usr/bin/env bash
# Generate controlled CPU load on the backend so the HPA scales out, and so
# the Grafana panels have traffic to show. Runs inside the cluster, so it
# works with or without the Ingress.
#
#   ./scripts/load-test.sh start [workers]     # default 6 workers
#   kubectl get hpa -n stockpilot -w            # watch REPLICAS climb
#   ./scripts/load-test.sh stop
set -euo pipefail

NS="${NAMESPACE:-stockpilot}"
TARGET="${TARGET:-http://stockpilot-backend:8000}"
ACTION="${1:-start}"
WORKERS="${2:-6}"

case "$ACTION" in
  start)
    kubectl apply -n "$NS" -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: load-generator
  labels:
    app: load-generator
spec:
  replicas: ${WORKERS}
  selector:
    matchLabels:
      app: load-generator
  template:
    metadata:
      labels:
        app: load-generator
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: curl
          image: curlimages/curl:8.16.0
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests: { cpu: 20m, memory: 16Mi }
            limits: { cpu: 200m, memory: 64Mi }
          command: ["sh", "-c"]
          args:
            - |
              while true; do
                curl -s -o /dev/null ${TARGET}/api/products
                curl -s -o /dev/null ${TARGET}/api/products/stats
                curl -s -o /dev/null "${TARGET}/api/products?q=box"
                curl -s -o /dev/null ${TARGET}/api/products/999999
              done
EOF
    echo "Load generator running with ${WORKERS} workers. Watch: kubectl get hpa -n ${NS} -w"
    ;;
  stop)
    kubectl delete deployment load-generator -n "$NS" --ignore-not-found
    echo "Load generator stopped. The HPA scales back down after its 2 min stabilization window."
    ;;
  *)
    echo "usage: $0 start [workers] | stop" >&2
    exit 1
    ;;
esac
