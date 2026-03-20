# Garmin Kubernetes CronJob Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe container image definition and a Kubernetes `CronJob` manifest that runs `garmin-sync` once per day at `23:59` in `Asia/Jakarta` using a Kubernetes `Secret` for sensitive configuration.

**Architecture:** Keep the Python application unchanged and add thin deployment assets around it. The image layer is responsible only for packaging the existing CLI safely, while the Kubernetes layer is responsible only for scheduling, secret injection, and basic job retention settings.

**Tech Stack:** Python 3.11, Docker, Kubernetes `CronJob`, YAML, `README.md`

---

## File Structure

Create or modify only these files:

- `.dockerignore`
  Excludes `.env`, virtualenvs, git metadata, caches, and other local-only artifacts from the image build context.
- `Dockerfile`
  Builds a runnable image for the existing `garmin-sync` CLI.
- `k8s/garmin-sync-cronjob.yaml`
  Defines the daily Kubernetes `CronJob` and its environment contract.
- `README.md`
  Documents image build, secret creation, and manifest apply steps.

## Chunk 1: Container Packaging

### Task 1: Add a safe Docker build context

**Files:**
- Create: `.dockerignore`

- [ ] **Step 1: Write the `.dockerignore` file**

```gitignore
.env
.venv/
.pytest_cache/
__pycache__/
*.pyc
.git/
garmin_sync.egg-info/
```

- [ ] **Step 2: Verify excluded local-secret and local-dev paths are covered**

Run: `rg -n '^\\.env$|^\\.venv/$|^\\.git/$' .dockerignore`
Expected: three matching lines for `.env`, `.venv/`, and `.git/`

- [ ] **Step 3: Commit**

```bash
git add .dockerignore
git commit -m "build: add Docker ignore rules"
```

### Task 2: Add a runnable application image

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Write the Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY garmin_sync ./garmin_sync
COPY sql ./sql

RUN pip install --no-cache-dir .

CMD ["garmin-sync"]
```

- [ ] **Step 2: Build the image**

Run: `docker build -t garmin-sync:local .`
Expected: exit code `0`

- [ ] **Step 3: Verify the image exposes the CLI**

Run: `docker run --rm --entrypoint sh garmin-sync:local -c 'command -v garmin-sync'`
Expected: output contains `/usr/local/bin/garmin-sync`

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "build: add garmin sync container image"
```

## Chunk 2: Kubernetes Scheduling and Operator Docs

### Task 3: Add the daily Kubernetes CronJob manifest

**Files:**
- Create: `k8s/garmin-sync-cronjob.yaml`

- [ ] **Step 1: Write the CronJob manifest**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: garmin-sync
spec:
  schedule: "59 23 * * *"
  timeZone: Asia/Jakarta
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 1
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 1
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: garmin-sync
              image: your-registry/garmin-sync:latest
              imagePullPolicy: IfNotPresent
              command: ["garmin-sync"]
              env:
                - name: TIMEZONE
                  value: Asia/Jakarta
                - name: SYNC_DAYS
                  value: "7"
                - name: GARMIN_ACCOUNT_KEY
                  value: personal
                - name: GARMIN_EMAIL
                  valueFrom:
                    secretKeyRef:
                      name: garmin-sync-secrets
                      key: GARMIN_EMAIL
                - name: GARMIN_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: garmin-sync-secrets
                      key: GARMIN_PASSWORD
                - name: DATABASE_URL
                  valueFrom:
                    secretKeyRef:
                      name: garmin-sync-secrets
                      key: DATABASE_URL
                - name: FERNET_KEY
                  valueFrom:
                    secretKeyRef:
                      name: garmin-sync-secrets
                      key: FERNET_KEY
```

- [ ] **Step 2: Verify the required schedule and retention settings are present**

Run: `rg -n 'schedule: "59 23 \\* \\* \\*"|timeZone: Asia/Jakarta|concurrencyPolicy: Forbid|successfulJobsHistoryLimit: 1|failedJobsHistoryLimit: 3|backoffLimit: 1' k8s/garmin-sync-cronjob.yaml`
Expected: one matching line for each required setting

- [ ] **Step 3: Validate the manifest structure and command**

Run: `kubectl apply --dry-run=client -f k8s/garmin-sync-cronjob.yaml`
Expected: exit code `0`

Run: `rg -n 'command: \\[\"garmin-sync\"\\]' k8s/garmin-sync-cronjob.yaml`
Expected: one matching line for the container command

- [ ] **Step 4: Verify the secret-backed env keys are present**

Run: `rg -n 'GARMIN_EMAIL|GARMIN_PASSWORD|DATABASE_URL|FERNET_KEY|garmin-sync-secrets' k8s/garmin-sync-cronjob.yaml`
Expected: matching lines for all four secret keys and the secret name

- [ ] **Step 5: Commit**

```bash
git add k8s/garmin-sync-cronjob.yaml
git commit -m "feat: add Kubernetes CronJob manifest"
```

### Task 4: Document build and deploy usage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a Kubernetes deployment section**

````md
## Docker image

Replace `your-registry/garmin-sync:latest` with the image name you actually publish.

```bash
docker build -t your-registry/garmin-sync:latest .
```

## Kubernetes

This manifest expects a Kubernetes cluster that supports `CronJob.spec.timeZone`.

Create the secret:

```bash
kubectl create secret generic garmin-sync-secrets \
  --from-literal=GARMIN_EMAIL=... \
  --from-literal=GARMIN_PASSWORD=... \
  --from-literal=DATABASE_URL=... \
  --from-literal=FERNET_KEY=...
```

Apply the CronJob:

```bash
kubectl apply -f k8s/garmin-sync-cronjob.yaml
```
````

- [ ] **Step 2: Verify the README includes build, secret, and apply instructions**

Run: `rg -n 'Docker image|kubectl create secret generic garmin-sync-secrets|kubectl apply -f k8s/garmin-sync-cronjob.yaml|CronJob.spec.timeZone' README.md`
Expected: matching lines for all four documentation anchors

- [ ] **Step 3: Run a final packaging verification sweep**

Run: `docker build -t garmin-sync:local .`
Expected: exit code `0`

Run: `rg -n 'schedule: "59 23 \\* \\* \\*"|timeZone: Asia/Jakarta' k8s/garmin-sync-cronjob.yaml`
Expected: matching lines for the requested schedule and timezone

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add Kubernetes deployment instructions"
```
