#!/usr/bin/env bash
# Remove everything Kubernetes created *outside* Terraform's state first
# (the Traefik NLB and the EBS volume behind the Postgres PVC). Otherwise
# `terraform destroy` hangs on the VPC because those AWS resources still use it.
#
#   ./scripts/teardown-eks.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Deleting the Argo CD application (prunes the StockPilot workloads)"
kubectl delete -f "$ROOT/k8s/argocd/application.yaml" --ignore-not-found --wait=true || true
helm uninstall stockpilot -n stockpilot 2>/dev/null || true

echo "==> Deleting PVCs (releases the EBS volumes)"
kubectl delete pvc --all -n stockpilot --ignore-not-found --wait=true || true

echo "==> Uninstalling Traefik (deletes the AWS Network Load Balancer)"
helm uninstall traefik -n traefik 2>/dev/null || true

echo "==> Uninstalling monitoring and Argo CD"
helm uninstall kube-prometheus-stack -n monitoring 2>/dev/null || true
helm uninstall argocd -n argocd 2>/dev/null || true

echo "==> Waiting 60s for AWS to release the load balancer ENIs"
sleep 60

echo "==> terraform destroy"
terraform -chdir="$ROOT/terraform" destroy
