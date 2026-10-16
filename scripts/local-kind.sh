#!/usr/bin/env bash
# Run the full Kubernetes stack locally on kind (no AWS bill), the same
# charts and values as EKS, with Traefik exposed on http://stockpilot.local:8088
#
#   ./scripts/local-kind.sh          # create + deploy
#   kind delete cluster --name stockpilot
#
# Requires: docker, kind, kubectl, helm. Add "127.0.0.1 stockpilot.local" to /etc/hosts.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLUSTER=stockpilot

if ! kind get clusters | grep -qx "$CLUSTER"; then
  cat <<EOF | kind create cluster --name "$CLUSTER" --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080
        hostPort: 8088
EOF
fi

echo "==> Building and loading local images"
docker compose -f "$ROOT/docker-compose.yml" build backend frontend
kind load docker-image stockpilot-backend:local stockpilot-frontend:local --name "$CLUSTER"

helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo update >/dev/null

helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system --version 3.14.0 \
  -f "$ROOT/monitoring/metrics-server-values.yaml" --set 'args={--kubelet-insecure-tls}' --wait
helm upgrade --install traefik traefik/traefik -n traefik --create-namespace --version 42.0.0 \
  -f "$ROOT/k8s/ingress/traefik-values.yaml" --set service.spec.type=NodePort --set ports.web.nodePort=30080 --wait
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring \
  --create-namespace --version 92.9.0 -f "$ROOT/monitoring/kube-prometheus-stack-values.yaml" --wait --timeout 10m

kubectl apply -f "$ROOT/k8s/namespace.yaml"
helm upgrade --install stockpilot "$ROOT/helm/stockpilot" -n stockpilot \
  -f "$ROOT/helm/stockpilot/values-dev.yaml" --wait --timeout 6m

kubectl get pods,svc,ingress,hpa -n stockpilot
echo "Open http://stockpilot.local:8088"
