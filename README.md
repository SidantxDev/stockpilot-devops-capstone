# StockPilot: Inventory Management on a DevSecOps Pipeline

StockPilot is a small but realistic **inventory management** SaaS app (products, stock levels, reorder alerts, stock-movement audit trail). This README follows it from a developer laptop to a **monitored, autoscaling Kubernetes deployment on AWS EKS**:

> React + FastAPI + PostgreSQL → pytest → Docker → GitHub Actions → Trivy → GHCR → Terraform (VPC + EKS) → Helm → Argo CD (GitOps) → Traefik Ingress → HPA → Prometheus + Grafana

| | |
|---|---|
| **Domain** | Warehouse inventory: products, SKUs, stock in/out, low-stock alerts |
| **Region** | AWS `ap-south-1` (Mumbai) |
| **Images** | `ghcr.io/sidantxdev/stockpilot-backend:<git-sha>`, `ghcr.io/sidantxdev/stockpilot-frontend:<git-sha>` |
| **Demo** | [`demo/`](demo/): presentation video + slide deck |

---

## Contents

1. [Architecture](#1-architecture)
2. [Tech stack](#2-tech-stack)
3. [Repository structure](#3-repository-structure)
4. [The application](#4-the-application)
5. [Run locally with Docker Compose](#5-run-locally-with-docker-compose)
6. [Run the backend directly](#6-run-the-backend-directly)
7. [Testing](#7-testing)
8. [Docker images](#8-docker-images)
9. [CI/CD pipeline](#9-cicd-pipeline)
10. [Security scanning (Trivy)](#10-security-scanning-trivy)
11. [Terraform: AWS infrastructure](#11-terraform-aws-infrastructure)
12. [Kubernetes + Helm deployment](#12-kubernetes--helm-deployment)
13. [GitOps with Argo CD](#13-gitops-with-argo-cd)
14. [Ingress and autoscaling (HPA)](#14-ingress-and-autoscaling-hpa)
15. [Observability: Prometheus + Grafana](#15-observability-prometheus--grafana)
16. [Troubleshooting lab](#16-troubleshooting-lab)
17. [Tear down (avoid AWS charges)](#17-tear-down-avoid-aws-charges)
18. [Known issues and limitations](#18-known-issues-and-limitations)
19. [Key learnings](#19-key-learnings)

---

## 1. Architecture

```mermaid
flowchart LR
    dev[Developer] -->|git push| gh[GitHub repo]
    gh --> ci

    subgraph ci[GitHub Actions]
      t1[pytest + flake8] --> b[docker build]
      t2[npm build] --> b
      b --> tv[Trivy scan<br/>fail on HIGH/CRITICAL]
      tv --> push[push to GHCR<br/>tag = commit SHA]
      push --> bump[commit new tag to<br/>helm/stockpilot/values.yaml]
    end

    push --> ghcr[(GHCR)]
    bump --> gh

    subgraph aws[AWS ap-south-1 · provisioned by Terraform]
      subgraph vpc[VPC 10.20.0.0/16 · 2 public + 2 private subnets]
        nlb[Network Load Balancer]
        subgraph eks[EKS cluster]
          argo[Argo CD] -->|helm sync| app
          tr[Traefik Ingress] -->|/| fe[frontend x2<br/>React + Nginx]
          tr -->|/api| be[backend x2-6<br/>FastAPI, HPA]
          be --> pg[(PostgreSQL<br/>StatefulSet + EBS gp3)]
          prom[Prometheus] -->|scrape /metrics| be
          graf[Grafana] --> prom
          app((StockPilot release))
        end
      end
    end

    gh -.->|Argo CD polls Git| argo
    ghcr -.->|image pull| eks
    user[Browser] --> nlb --> tr
```

**Request path:** browser → AWS NLB → Traefik (Ingress controller) → `/` frontend Service or `/api` backend Service → Pods → PostgreSQL Service → Postgres Pod (EBS volume).

**Delivery path:** `git push` → GitHub Actions tests, builds, scans and pushes images tagged with the commit SHA → the pipeline commits that SHA into the Helm values → Argo CD sees the Git change and rolls it out. CI never needs cluster credentials.

---

## 2. Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, plain responsive CSS, served by **Nginx** (unprivileged) |
| Backend | Python 3.12, **FastAPI**, Pydantic v2, Uvicorn |
| Database | **PostgreSQL 17**, SQLAlchemy 2 ORM, **Alembic** migrations |
| Testing | **pytest**, FastAPI TestClient, in-memory SQLite, flake8 |
| Containers | Docker multi-stage builds, Docker Compose |
| CI/CD | **GitHub Actions** |
| Registry | **GitHub Container Registry (GHCR)** |
| Security | **Trivy** image scanning, non-root containers, read-only root FS, Pod Security "restricted" |
| Infrastructure as Code | **Terraform** (`terraform-aws-modules` VPC, EKS, IAM) |
| Cloud | **AWS**: VPC, subnets, NAT Gateway, EKS, managed node group, EBS CSI, NLB |
| Orchestration | **Kubernetes** 1.34, **Helm** chart |
| GitOps | **Argo CD** |
| Ingress | **Traefik** ingress controller |
| Autoscaling | HorizontalPodAutoscaler + metrics-server |
| Observability | **Prometheus** (kube-prometheus-stack, ServiceMonitor, PrometheusRule), **Grafana** |

---

## 3. Repository structure

```
.
├── backend/                     FastAPI service
│   ├── app/
│   │   ├── main.py              app, /health, /ready, /metrics
│   │   ├── config.py            env-based settings (DATABASE_URL, CORS)
│   │   ├── database.py          engine, session, get_db dependency
│   │   ├── models.py            Product, StockMovement tables
│   │   ├── schemas.py           Pydantic request/response models
│   │   └── routes/products.py   REST API + custom Prometheus counters
│   ├── alembic/versions/        0001 create tables, 0002 seed demo data
│   ├── tests/                   19 pytest cases (conftest.py = isolated test DB)
│   ├── Dockerfile               multi-stage, non-root uid 10001
│   ├── docker-entrypoint.sh     runs `alembic upgrade head`, then uvicorn
│   ├── pytest.ini  .flake8
│   └── requirements.txt / requirements-dev.txt
├── frontend/                    React + Vite dashboard
│   ├── src/                     App.jsx, components/, api.js, styles.css
│   ├── nginx/default.conf.template   SPA + /api reverse proxy
│   └── Dockerfile               Node build stage -> nginx-unprivileged runtime
├── docker-compose.yml           postgres + backend + frontend
├── .github/workflows/ci-cd.yml  test -> build -> Trivy -> GHCR -> GitOps deploy
├── terraform/                   VPC + EKS (+ EBS CSI IAM role)
├── helm/stockpilot/             Helm chart (Deployments, Services, StatefulSet,
│                                Ingress, HPA, PDB, ServiceMonitor, alerts, dashboard)
├── k8s/                         namespace, gp3 StorageClass, Traefik values, Argo CD app
├── monitoring/                  kube-prometheus-stack + metrics-server values
├── troubleshooting/             deliberately broken manifests (labs)
├── scripts/                     bootstrap/teardown EKS, kind, load test, smoke test
└── demo/                        presentation video + slides + screenshots
```

---

## 4. The application

### Features

- KPI cards: product count, units on hand, inventory value (₹), items needing reorder
- Product table with search, status filter (in stock / low stock / out of stock) and status badges
- Add / edit / delete products (modal forms with validation)
- **Stock adjustments** (restock, sale, return, damaged, correction), each recorded in an audit trail
- Recent stock-movement feed and category breakdown
- Responsive layout (sidebar collapses into a drawer; the table turns into cards on phones), plus loading, empty and backend-error states
- Sidebar shows the deployed build (git SHA baked into the image by CI)

### REST API

Swagger UI: `http://localhost:8000/docs`

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service info |
| GET | `/health` | **Liveness**: process is up (no DB call) |
| GET | `/ready` | **Readiness**: runs `SELECT 1`; returns 503 if the DB is unreachable |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/products` | List products (`?q=`, `?category=`, `?status=low_stock`) |
| GET | `/api/products/stats` | Inventory KPIs |
| GET | `/api/products/{id}` | Get one product |
| POST | `/api/products` | Create product (409 on duplicate SKU) |
| PUT | `/api/products/{id}` | Update product (partial updates allowed) |
| DELETE | `/api/products/{id}` | Delete product (and its movements) |
| POST | `/api/products/{id}/adjust` | Record a stock movement (400 if stock would go negative) |
| GET | `/api/movements` | Recent stock movements |

### Database

Two tables, both created by **Alembic** (`backend/alembic/versions/`):

- `products`: sku (unique), name, category, quantity (≥ 0 check constraint), reorder_level, unit_price, supplier, location, timestamps
- `stock_movements`: product_id (FK, cascade delete), change (+/−), reason, note, created_at

Migration `0002` seeds 10 demo products so a fresh environment isn't empty. Every backend replica runs `alembic upgrade head` on start; a **Postgres advisory lock** in `alembic/env.py` makes concurrent replicas migrate one at a time.

---

## 5. Run locally with Docker Compose

Requirements: Docker Desktop / Docker Engine with Compose v2.

```bash
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:3000 | StockPilot UI |
| http://localhost:8000/docs | Swagger API docs |
| http://localhost:8000/health | Liveness |
| http://localhost:8000/ready | Readiness |
| http://localhost:8000/metrics | Prometheus metrics |

Start-up order is enforced with health checks: `postgres (pg_isready)` → `backend (/health)` → `frontend`.

```bash
docker compose exec postgres psql -U stockpilot -c "select sku, name, quantity from products;"   # look at the DB
./scripts/smoke-test.sh http://localhost:3000                                                    # CRUD end-to-end
docker compose down        # stop
docker compose down -v     # stop and delete the database volume
```

> If port 3000 is busy: `FRONTEND_PORT=3001 docker compose up --build`. Credentials can be overridden with a `.env` file (see `.env.example`).

---

## 6. Run the backend directly

Requirements: Python 3.12+, a running PostgreSQL.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://stockpilot:stockpilot@localhost:5432/stockpilot'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend dev server (proxies `/api` to `:8000`):

```bash
cd frontend && npm install && npm run dev     # http://localhost:5173
```

---

## 7. Testing

```bash
cd backend
pytest -v
```

- **19 test cases** across `tests/test_health.py`, `tests/test_products.py` and `tests/test_stock_movements.py`, covering every endpoint: health/ready/metrics, list/filter/search, create (incl. duplicate SKU and validation errors), get/404, update, delete, stats, stock adjustments (incl. negative-stock guard and invalid reason) and the custom Prometheus counter.
- **Never touches the real database**: `tests/conftest.py` sets `DATABASE_URL` to SQLite *before* the app is imported and overrides the `get_db` dependency with a fresh **in-memory SQLite** DB per test (`StaticPool`, foreign keys on).
- `pytest.ini` configures test paths, `pythonpath` and warning filters. `flake8` runs as a lint gate in CI.

Tests are the first quality gate: if `pytest` fails, the pipeline stops and no image is built or pushed.

---

## 8. Docker images

| | Backend | Frontend |
|---|---|---|
| Build | 2 stages: build a venv → copy into a clean `python:3.12-slim` | 2 stages: `node:22-alpine` runs `npm ci && npm run build` → `nginxinc/nginx-unprivileged:1.29-alpine` |
| User | **non-root uid 10001** (`app`) | **non-root uid 101** (`nginx`) |
| Port | 8000 | 8080 |
| Hardening | OS packages upgraded, pip/setuptools removed from runtime | OS packages upgraded, no Node or build tooling in the final image |
| Health check | `GET /health` | `GET /healthz` |

```bash
docker build -t stockpilot-backend:local ./backend
docker build -t stockpilot-frontend:local --build-arg APP_VERSION=$(git rev-parse HEAD) ./frontend
docker run --rm stockpilot-backend:local id     # uid=10001(app)
```

The frontend's Nginx serves the SPA and reverse-proxies `/api/` to `${BACKEND_URL}` (rendered from `nginx/default.conf.template` at start-up), so the browser only ever calls its own origin.

---

## 9. CI/CD pipeline

File: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml). Triggers on **push to `main`**, on pull requests, and manually (`workflow_dispatch`).

```
 backend-tests ─┐
  (flake8,      │
   pytest)      ├─► build-scan-push (matrix: backend, frontend) ─► gitops-deploy
 frontend-build ┘     docker build → Trivy report → Trivy gate     (main only)
  (npm ci,             → login GHCR → push :<git-sha>               sed image tag → commit [skip ci]
   npm run build)                                                    → Argo CD syncs
```

| Job | What it proves |
|---|---|
| **Backend · lint + pytest** | `flake8` + `pytest -v`; any failure fails the build. JUnit report uploaded as an artifact. |
| **Frontend · npm build** | `npm ci` + `vite build`; `dist/` uploaded as an artifact. |
| **Image · backend / frontend** | Docker Buildx build (GHA layer cache) → Trivy → push to GHCR. Pull requests build and scan but **never push**. |
| **Deploy · GitOps** | Rewrites `tag:` lines marked `# ci:image-tag` in `helm/stockpilot/values.yaml` to the commit SHA and pushes a `deploy:` commit (with `[skip ci]` so it doesn't loop). Argo CD deploys it. |

**Image tags are the full Git commit SHA, never `latest`**, so every running Pod traces back to the exact commit that built it (also visible in the UI sidebar and the `org.opencontainers.image.revision` label).

Permissions are least-privilege: `contents: read` by default, `packages: write` only for the image job, `contents: write` only for the GitOps job. The Trivy action is pinned to a **commit SHA** (not a mutable tag) because of the 2026 tag-hijacking incident on that action.

---

## 10. Security scanning (Trivy)

Each image is scanned **twice** in the pipeline:

1. **Report**: all severities, written to the job summary and uploaded as an artifact (never fails).
2. **Gate**: `severity: HIGH,CRITICAL`, `ignore-unfixed: true`, `exit-code: 1`. **Any fixable HIGH or CRITICAL CVE fails the pipeline, so the image is not pushed.**

**What Trivy scanned and what the result means.** Trivy scanned both container images: the OS packages (Debian 13 in the backend, Alpine 3.23 in the frontend) and every Python package in the backend's virtualenv. The frontend is completely clean (0 vulnerabilities). The backend has **0 fixable HIGH/CRITICAL** findings, so the gate passes. Trivy still reports HIGH CVEs in Debian base packages such as `libacl1` (**CVE-2026-54369**, a symlink-traversal bug in ACL helpers) that Debian has **not shipped a fix for yet** (status `affected`). We accept these because nothing in the app calls those utilities, the container runs as non-root with a read-only filesystem and all capabilities dropped, and the `apt-get upgrade` in the Dockerfile picks up the fix automatically as soon as Debian publishes it.

**A real finding the gate caught.** The first scan failed with 4 HIGH CVEs: `urllib3` **CVE-2026-97687** (TLS settings ignored through an HTTPS proxy, enabling traffic interception), `urllib3` CVE-2026-97689, `msgpack` GHSA-6v7p-g79w-8964 and `setuptools` CVE-2025-47273. None were our dependencies: they were **vendored inside `pip`**, which the virtualenv carried into the runtime image. The fix (commit *"strip pip from runtime venv"*) uninstalls pip/setuptools/wheel after installing requirements. The app doesn't need them at runtime, and the rescan was clean.

Scanning is one control among several (SAST, dependency scanning, secret scanning, runtime security); it doesn't guarantee the system is secure.

---

## 11. Terraform: AWS infrastructure

Directory: [`terraform/`](terraform/). It uses the community `terraform-aws-modules` (VPC 5.21, EKS 20.37, IAM 5.60) on AWS provider 5.x.

```
AWS ap-south-1
└── VPC 10.20.0.0/16
    ├── public subnets   10.20.0.0/24, 10.20.1.0/24   (2 AZs; NLB + NAT; tag kubernetes.io/role/elb)
    ├── private subnets  10.20.10.0/24, 10.20.11.0/24 (2 AZs; worker nodes)
    ├── Internet Gateway + 1 NAT Gateway
    └── EKS cluster "stockpilot-capstone-eks" (Kubernetes 1.34, public API endpoint)
        ├── managed node group: 2 × t3.medium (min 2, max 4), AL2023 AMI
        ├── add-ons: vpc-cni, coredns, kube-proxy, eks-pod-identity-agent, aws-ebs-csi-driver
        └── IAM role (IRSA) for the EBS CSI driver
```

| File | Purpose |
|---|---|
| `versions.tf` | Terraform ≥ 1.6, AWS provider pin, optional S3 backend |
| `providers.tf` | AWS provider with default tags (Project / Environment / ManagedBy) |
| `variables.tf` | region, CIDR, AZ count (validated ≥ 2), k8s version, node sizing |
| `main.tf` | VPC, EKS, node group, add-ons, EBS CSI IRSA role |
| `outputs.tf` | VPC/subnet IDs, cluster name/endpoint, `configure_kubectl` command |
| `terraform.tfvars.example` | Example inputs. **No credentials**: AWS auth comes from `aws configure` / SSO |

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars    # optional, defaults work
terraform init
terraform plan                                  # dozens of resources to add, 0 to change/destroy
terraform apply                                 # ~15 minutes
$(terraform output -raw configure_kubectl)      # aws eks update-kubeconfig ...
kubectl get nodes
```

**Estimated cost while running:** about **US$0.30/hour** (EKS control plane $0.10, 2 × t3.medium, NAT Gateway, NLB). Destroy it the same day (see [§17](#17-tear-down-avoid-aws-charges)).

---

## 12. Kubernetes + Helm deployment

### One-command bootstrap on EKS

```bash
./scripts/bootstrap-eks.sh
```

This installs, in order: gp3 default StorageClass, the `stockpilot` namespace, metrics-server, Traefik, kube-prometheus-stack, Argo CD, and the Argo CD Application that deploys the Helm chart. The steps are spelled out below.

### Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

The namespace enforces the **Pod Security Standard `restricted`**: every Pod must run as non-root, drop all capabilities, disallow privilege escalation and use a seccomp profile. The chart complies.

### Helm chart: `helm/stockpilot`

| Template | Kubernetes objects |
|---|---|
| `backend.yaml` | Deployment (≥ 2 replicas, rolling update, init container waiting for Postgres, startup/liveness/readiness probes), ClusterIP Service, PodDisruptionBudget |
| `frontend.yaml` | Deployment (2 replicas), ClusterIP Service |
| `postgres.yaml` | StatefulSet with a PersistentVolumeClaim (EBS gp3), ClusterIP Service |
| `secret.yaml` / `configmap.yaml` | DB password / DB host, name, user, app env |
| `ingress.yaml` | `/api` → backend, `/` → frontend (Traefik) |
| `hpa.yaml` | autoscaling/v2 on CPU (2 → 6 replicas at 60%) |
| `monitoring.yaml` | ServiceMonitor, PrometheusRule (3 alerts), Grafana dashboard ConfigMap |
| `tests/test-api.yaml` | `helm test` Pod that curls the API and frontend |

Values files: `values.yaml` (defaults; CI updates the image tags), `values-eks.yaml` (gp3 storage, Traefik on the NLB), `values-dev.yaml` (local images, `stockpilot.local`).

```bash
helm upgrade --install stockpilot ./helm/stockpilot \
  --namespace stockpilot \
  -f helm/stockpilot/values-eks.yaml

helm list -n stockpilot
helm test stockpilot -n stockpilot
kubectl get pods,svc,ingress,hpa -n stockpilot
helm rollback stockpilot 1 -n stockpilot     # roll back to a previous revision
```

Every container runs **non-root with a read-only root filesystem**; writable paths (`/tmp`, Nginx `conf.d`) are `emptyDir` volumes.

### Run the same stack locally (no AWS)

```bash
./scripts/local-kind.sh        # kind cluster + Traefik + Prometheus/Grafana + app
# http://stockpilot.local:8088  (add "127.0.0.1 stockpilot.local" to your hosts file)
```

---

## 13. GitOps with Argo CD

```bash
helm upgrade --install argocd argo/argo-cd -n argocd --create-namespace \
  --version 10.10.5 -f k8s/argocd/values.yaml
kubectl apply -f k8s/argocd/application.yaml
kubectl port-forward -n argocd svc/argocd-server 8443:80          # http://localhost:8443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

The `stockpilot` Application tracks `helm/stockpilot` on `main` with `values.yaml` + `values-eks.yaml`, with **automated sync, prune and self-heal**:

1. A developer pushes code to `main`.
2. GitHub Actions tests, builds, scans and pushes `:<sha>` images.
3. The pipeline commits `deploy: roll out images <sha>` to `values.yaml`.
4. Argo CD polls Git every 60 s, sees the new commit and runs a rolling update.
5. If someone `kubectl edit`s the cluster by hand, self-heal reverts it to what Git says.

---

## 14. Ingress and autoscaling (HPA)

**Ingress.** An Ingress object is just configuration; **Traefik** (`k8s/ingress/traefik-values.yaml`) is the controller that implements it. On EKS, Traefik's `LoadBalancer` Service provisions an **AWS Network Load Balancer** in the public subnets.

```bash
kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
# open http://<that-hostname>/   and   http://<that-hostname>/api/products
```

**HPA.** The backend scales on CPU between 2 and 6 replicas (target 60% of the 100m request). It needs **metrics-server** (installed by the bootstrap script).

```bash
./scripts/load-test.sh start 6          # 6 in-cluster curl workers
kubectl get hpa -n stockpilot -w        # verified locally: 2 -> 4 replicas within ~40s
./scripts/load-test.sh stop             # scales back after a 2-min stabilization window
```

---

## 15. Observability: Prometheus + Grafana

```bash
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace --version 92.9.0 \
  -f monitoring/kube-prometheus-stack-values.yaml
```

| Piece | How it works |
|---|---|
| **`/metrics`** | `prometheus-fastapi-instrumentator` exposes `http_requests_total{handler,method,status}` and `http_request_duration_seconds`. The app adds business counters `stockpilot_stock_movements_total{reason}` and `stockpilot_stock_units_moved_total{direction}`. |
| **Scraping** | The chart's **ServiceMonitor** selects the backend Service; Prometheus scrapes every backend Pod every 15 s. |
| **Alerts** | **PrometheusRule**: `StockPilotBackendDown`, `StockPilotHighErrorRate` (> 5% 5xx), `StockPilotSlowRequests` (p95 > 500 ms). |
| **Dashboard** | ConfigMap labelled `grafana_dashboard=1`, auto-loaded by Grafana's sidecar: **"StockPilot · API Overview"** with targets UP, req/s, error rate, p95 latency, request rate by endpoint, status codes, latency by endpoint, stock movements by reason, units in/out, CPU/memory per pod, and HPA replicas. |

```bash
# Prometheus -> Status -> Targets: "serviceMonitor/stockpilot/stockpilot-backend" (2/2 UP)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
# Grafana -> Dashboards -> "StockPilot · API Overview"  (user: admin)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
kubectl -n monitoring get secret kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d
# raw metrics
kubectl port-forward -n stockpilot svc/stockpilot-backend 8000:8000 && curl localhost:8000/metrics
```

The control-plane scrape jobs (etcd, scheduler, controller-manager, kube-proxy) are disabled because EKS doesn't expose them, so the Targets page has no false DOWN targets.

---

## 16. Troubleshooting lab

Deliberately broken manifests in [`troubleshooting/`](troubleshooting/) (namespace `stockpilot-lab`):

| Lab | Symptom | Investigate | Root cause / fix |
|---|---|---|---|
| `broken-image.yaml` | `ImagePullBackOff` | `kubectl describe pod`, `kubectl get events --sort-by=.lastTimestamp` | Tag doesn't exist → `kubectl set image` to a real SHA tag |
| `broken-service.yaml` | Service times out | `kubectl get endpointslices`, `kubectl get pods --show-labels` | Selector typo `backnd` → no endpoints → patch the selector |
| `broken-readiness.yaml` | Pod `Running` but `0/1 READY` | `kubectl describe pod` (readiness 503), logs | DB unreachable → `/ready` fails → Pod kept out of the Service |

Clean up: `kubectl delete namespace stockpilot-lab`.

---

## 17. Tear down (avoid AWS charges)

```bash
./scripts/teardown-eks.sh
```

The order matters. The Traefik **NLB** and the Postgres **EBS volume** are created by Kubernetes, not Terraform, so they must be deleted first or `terraform destroy` gets stuck on the VPC. The script removes the Argo CD app, PVCs, Traefik and the monitoring stack, waits for AWS to release the ENIs, and then runs `terraform destroy`. Afterwards, check that EC2 → Load Balancers and EC2 → Volumes are empty in `ap-south-1`.

---

## 18. Known issues and limitations

- **PostgreSQL runs inside the cluster** (single-replica StatefulSet), which is fine for a classroom demo. In production I'd use **Amazon RDS** (Multi-AZ, automated backups, point-in-time restore) and drop the StatefulSet.
- **The DB password is a chart default** in `values.yaml` (`stockpilot-k8s-demo`). For real use, create the Secret out-of-band (or with External Secrets / Sealed Secrets) and set `postgres.existingSecret`. Grafana and Argo CD admin passwords are generated at install time, not committed.
- **Brand-new AWS account cannot create load balancers yet** (`OperationNotPermitted: This AWS account currently does not support creating load balancers`). The Traefik `LoadBalancer` Service therefore stays `<pending>` in the demo, and the app is reached through the in-cluster ingress with `kubectl port-forward -n traefik svc/traefik 8080:80`. Once AWS Support lifts the restriction, the NLB is created automatically with no code change.
- **No TLS.** The app is served over plain HTTP on the NLB hostname. Production would add a domain, cert-manager / ACM and HTTPS redirects.
- **GHCR images are public** because they are linked to this public repo (`org.opencontainers.image.source` label), so EKS pulls them without credentials. In a private repo you would set `imagePullSecrets` in `values.yaml`.
- **Base-image CVEs without a fix** (Debian status `affected`) are reported but not blocking (`ignore-unfixed`); see §10.
- **Single NAT Gateway** to save cost, which means one AZ is a single point of failure for egress. Production would use one per AZ.
- **Terraform state is local.** For a team, enable the commented S3 backend in `versions.tf` with locking.
- **Migrations run at container start** behind a Postgres advisory lock. At larger scale I'd move them to a dedicated Job / Argo CD PreSync hook.
- **No authentication** on the app itself (out of scope for the capstone).
- Locally, port 3000 may already be in use. Override with `FRONTEND_PORT=3001`.

---

## 19. Key learnings

- **Quality gates belong before artifacts.** Tests and Trivy run before the push, so a broken or vulnerable image never reaches the registry.
- **Immutable SHA tags + GitOps** make every deployment traceable and reversible (`git revert` = rollback), and CI never needs cluster credentials.
- **Liveness and readiness are different questions.** `/health` keeps a busy process from being killed, and `/ready` keeps a process without a database out of the load balancer.
- **Least privilege everywhere:** non-root containers, read-only filesystems, Pod Security `restricted`, scoped `GITHUB_TOKEN` permissions, IRSA instead of node-wide IAM, no keys in Git.
- **Kubernetes creates cloud resources that Terraform doesn't know about** (load balancers, volumes). Tear-down order matters.
- **Observability needs both technical and business metrics.** Request rate and latency show the service is healthy; stock movements show it's being used.

---

*Built by **SidantxDev** for the DevOps Final Capstone (Session 21). The application domain and implementation are original; the DevOps architecture follows the course reference design.*
