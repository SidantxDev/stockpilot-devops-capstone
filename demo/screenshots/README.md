# Evidence screenshots

Graders ask for these. Save each one in this folder with the file name shown, then commit them.

| # | File name | Module | What to capture |
|---|---|---|---|
| 1 | `app-ui-desktop.png` ✅ | M1 | App running in the browser (included) |
| 2 | `app-ui-mobile.png` ✅ | M1 | Responsive layout (included) |
| 3 | `pytest-passing.png` | M2 | Terminal: `cd backend && pytest -v` with **19 passed** |
| 4 | `git-log.png` | M3 | GitHub → Commits page (or `git log --oneline`) showing 10+ commits |
| 5 | `docker-compose-up.png` | M4 | Terminal: `docker compose up --build` with all 3 services started |
| 6 | `app-localhost-3000.png` | M4 | Browser at `http://localhost:3000` |
| 7 | `github-actions-green.png` | M5 | Successful pipeline run (all jobs green) |
| 8 | `ghcr-packages.png` | M5 | GHCR package page showing the SHA tag |
| 9 | `trivy-scan.png` | M6 | The *Trivy scan · gate* step output (or the job summary table) |
| 10 | `terraform-plan.png` | M7 | `terraform plan` output (before apply: "Plan: N to add") |
| 11 | `aws-vpc.png` | M7 | AWS Console → VPC → `stockpilot-capstone-vpc` with subnets |
| 12 | `aws-eks.png` | M7 | AWS Console → EKS → cluster Active + node group |
| 13 | `terraform-destroy.png` | M7 | `terraform destroy` ending in "Destroy complete!" |
| 14 | `kubectl-get-pods.png` | M8 | `kubectl get pods -n stockpilot`, all Running |
| 15 | `kubectl-get-svc.png` | M8 | `kubectl get svc -n stockpilot` |
| 16 | `helm-list.png` | M8 | `helm list -n stockpilot` |
| 17 | `app-via-ingress.png` | M8 | App opened at the Traefik NLB hostname |
| 18 | `metrics-endpoint.png` | M9 | `curl http://localhost:8000/metrics` (port-forward) |
| 19 | `prometheus-targets.png` | M9 | Prometheus Targets page, stockpilot-backend **UP** |
| 20 | `grafana-dashboard.png` | M9 | Grafana "StockPilot · API Overview" with data |
| 21 | `argocd-synced.png` | GitOps | Argo CD app Synced + Healthy |
