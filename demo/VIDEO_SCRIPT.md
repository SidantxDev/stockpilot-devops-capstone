# Presentation video: recording script

Target length: **12–15 minutes**. Record your screen with your voice (OBS Studio, or Windows `Win + Alt + R` / Xbox Game Bar, or Clipchamp). Save it as **`demo/presentation.mp4`**. GitHub rejects files over 100 MB, so export at 1080p / 30 fps (≈ 60–90 MB for 15 min). If it's still too big, upload it as a **GitHub Release asset** and link it in the README.

The order below follows the grading rubric exactly.

---

## Part 1: Slides (≈ 4–5 min)

Open `demo/presentation.pptx` in slideshow mode. The speaker notes under each slide are your script; read them naturally.

| Slide | Say in one line |
|---|---|
| 1 Title | What StockPilot is and that the focus is the delivery pipeline |
| 2 What I built | The inventory problem and the app (screenshot) |
| 3 Tech stack | One sentence per layer |
| 4 Architecture | Walk the diagram: left = delivery, right = AWS/EKS runtime |
| 5 Application layer | Endpoints, health vs ready, Alembic, tests use SQLite |
| 6 CI/CD | The 5 stages, SHA tags, PRs never push |
| 7 DevSecOps | The 4 CVEs Trivy caught and how pip removal fixed them |
| 8 Terraform | 2 AZs, public/private subnets, EKS, cost, destroy |
| 9 K8s + Helm | Chart objects + the real HPA load-test chart |
| 10 GitOps | The 5-step Argo CD flow |
| 11 Observability | ServiceMonitor → Prometheus → Grafana, alerts |
| 12 Learnings | Six takeaways, then "now the live demo" |

---

## Part 2: Live walkthrough (≈ 8–10 min)

Have these ready **before** recording: VS Code with the repo open, a terminal with `kubectl` pointed at EKS, browser tabs for GitHub Actions, GHCR packages, AWS Console (EKS + VPC), Argo CD, Prometheus, Grafana and the app.

Start the port-forwards in separate terminals first:

```bash
kubectl port-forward -n argocd svc/argocd-server 8443:80
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
```

### 2.1 Codebase (≈ 1.5 min)
- Show the folder tree in VS Code: `backend/`, `frontend/`, `terraform/`, `helm/stockpilot/`, `k8s/`, `monitoring/`, `.github/workflows/`.
- Open `backend/app/main.py`: `/health`, `/ready`, `/metrics`.
- Open `backend/app/routes/products.py`: the CRUD + `adjust` endpoint and the custom Prometheus counters.
- Open `backend/tests/conftest.py`: "tests use in-memory SQLite, never the real DB".
- Open `backend/Dockerfile` and `frontend/Dockerfile`: multi-stage, `USER 10001` / nginx-unprivileged.

### 2.2 CI/CD: trigger a push (≈ 2 min)
Make a small visible change, for example the warehouse name in `frontend/src/App.jsx`:

```bash
# edit "Main warehouse · Bengaluru" -> "Main warehouse · Mumbai"
git add frontend/src/App.jsx
git commit -m "feat(frontend): rename main warehouse location to Mumbai"
git push
```

- Open **GitHub → Actions** and click the new run. Show the jobs: *Backend · lint + pytest* → *Frontend · npm build* → *Image · backend/frontend* (expand the **Trivy scan · gate** step) → *Deploy · bump Helm image tag*.
- While it runs, continue with Terraform (2.3) and come back to show it **green**.
- Show the **job summary** (Trivy tables) and the new `deploy: roll out images …` commit on `main`.
- Open **GHCR packages** (github.com/SidantxDev?tab=packages) and show the tag = the commit SHA.

### 2.3 Terraform + AWS Console (≈ 1.5 min)
```bash
cd terraform
terraform plan          # "No changes. Your infrastructure matches the configuration."
terraform output
```
- **AWS Console → VPC** (region *Asia Pacific (Mumbai) ap-south-1*): `stockpilot-capstone-vpc`, its 2 public + 2 private subnets, NAT gateway.
- **AWS Console → EKS → stockpilot-capstone-eks**: status Active, version 1.34, **Compute** tab shows the node group with 2 nodes.

### 2.4 Argo CD (≈ 1 min)
- Open http://localhost:8443 → the `stockpilot` app: **Synced / Healthy**, the resource tree (Deployments, StatefulSet, Ingress, HPA…).
- Click **History and rollback**: the newest revision is the `deploy:` commit from the pipeline. "CI changed Git, Argo CD deployed it."
- Optional: refresh the app in the browser and show the new warehouse name + new build SHA in the sidebar.

### 2.5 Kubernetes (≈ 1.5 min)
```bash
kubectl get nodes
kubectl get pods -n stockpilot -o wide
kubectl get svc -n stockpilot
kubectl get ingress -n stockpilot
kubectl get hpa -n stockpilot
helm list -n stockpilot
```
- Open the app via the Ingress (NLB hostname from `kubectl get svc -n traefik traefik`). Add a product and adjust stock, live.
- Optional HPA demo: `./scripts/load-test.sh start 6` then `kubectl get hpa -n stockpilot -w` until replicas climb, then `./scripts/load-test.sh stop`.

### 2.6 Prometheus (≈ 45 s)
- http://localhost:9090/targets → filter `stockpilot` → **serviceMonitor/stockpilot/stockpilot-backend: 2/2 UP**.
- Run a query, e.g. `sum by (handler) (rate(http_requests_total[1m]))`.

### 2.7 Grafana (≈ 1 min)
- http://localhost:3001 (user `admin`, password from the README) → **Dashboards → StockPilot · API Overview**.
- Point at: targets UP, requests/sec, p95 latency, stock movements by reason, HPA replicas (if you ran the load test).

### 2.8 Close (≈ 15 s)
"That's the full path: commit → tests → scan → registry → GitOps → EKS → monitoring. After recording I ran `scripts/teardown-eks.sh` so no AWS resources are left running."
