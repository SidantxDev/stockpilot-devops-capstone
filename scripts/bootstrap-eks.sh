#!/usr/bin/env bash
# Install the cluster add-ons and hand the app over to Argo CD.
# Run after `terraform apply` in terraform/.
#
#   ./scripts/bootstrap-eks.sh                # uses terraform outputs for region/cluster
#
# Requires: aws CLI v2, kubectl, helm (3.x or 4.x), terraform.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REGION="${AWS_REGION:-$(terraform -chdir="$ROOT/terraform" output -raw region)}"
CLUSTER="${CLUSTER_NAME:-$(terraform -chdir="$ROOT/terraform" output -raw cluster_name)}"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

step "Configuring kubectl for $CLUSTER ($REGION)"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER"
kubectl get nodes -o wide

step "Bootstrap manifests: default gp3 StorageClass + stockpilot namespace"
kubectl apply -f "$ROOT/k8s/storageclass-gp3.yaml"
kubectl apply -f "$ROOT/k8s/namespace.yaml"

step "Helm repositories"
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add argo https://argoproj.github.io/argo-helm >/dev/null
helm repo update >/dev/null

step "metrics-server (HPA + kubectl top)"
helm upgrade --install metrics-server metrics-server/metrics-server \
  -n kube-system --version 3.14.0 -f "$ROOT/monitoring/metrics-server-values.yaml" --wait

step "Traefik ingress controller (AWS NLB)"
helm upgrade --install traefik traefik/traefik \
  -n traefik --create-namespace --version 42.0.0 -f "$ROOT/k8s/ingress/traefik-values.yaml"

step "Prometheus + Grafana (kube-prometheus-stack)"
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace --version 92.9.0 \
  -f "$ROOT/monitoring/kube-prometheus-stack-values.yaml" --wait --timeout 10m

step "Argo CD"
helm upgrade --install argocd argo/argo-cd \
  -n argocd --create-namespace --version 10.10.5 -f "$ROOT/k8s/argocd/values.yaml" --wait --timeout 10m

step "Argo CD Application -> helm/stockpilot (GitOps)"
kubectl apply -f "$ROOT/k8s/argocd/application.yaml"

step "Waiting for the Traefik load balancer hostname"
for _ in $(seq 1 60); do
  LB="$(kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)"
  [ -n "$LB" ] && break
  sleep 5
done

cat <<EOF

Done.
  App (allow ~2 min for NLB DNS) : http://${LB:-<pending: kubectl get svc -n traefik traefik>}
  Argo CD UI : kubectl port-forward -n argocd svc/argocd-server 8443:80   -> http://localhost:8443
               password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
  Grafana    : kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80 -> http://localhost:3001
               password: kubectl -n monitoring get secret kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d
  Prometheus : kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090 -> http://localhost:9090/targets

  kubectl get pods,svc,ingress,hpa -n stockpilot
EOF
