# Garmin Kubernetes CronJob Design

## Goal

Package the existing `garmin-sync` CLI into a container image and provide a Kubernetes manifest that runs it once per day at 23:59 in `Asia/Jakarta`.

The deployment should be simple to apply, keep secrets out of the manifest, and require as little Kubernetes-specific logic as possible inside the Python application.

## Scope

This design covers:

- Containerizing the existing Python application with a minimal `Dockerfile`
- Defining a Kubernetes `CronJob` that runs once per day
- Reading sensitive runtime configuration from a Kubernetes `Secret`
- Keeping non-sensitive defaults such as timezone and sync window in the manifest
- Documenting the basic build and deploy flow in the repository README

This design does not cover:

- Helm charts, Kustomize overlays, or multi-environment deployment templates
- Image publishing automation or CI/CD pipelines
- Kubernetes-managed database provisioning
- Alerting, log shipping, or observability beyond default pod logs

## Recommended Approach

Use a native Kubernetes `CronJob` plus a minimal application image.

This is preferred over an external scheduler because Kubernetes already provides the exact execution model needed here: create one short-lived pod per schedule and let the container exit when the sync is finished. It is preferred over embedding scheduling logic in Python because the application already models a single sync run cleanly through `garmin-sync`.

## Architecture

The design keeps responsibilities separated into three units:

- `Dockerfile`: builds a runnable image for the existing `garmin-sync` CLI
- Kubernetes manifest: schedules and configures the workload
- `README.md`: explains how operators build the image, create the secret, and apply the manifest

The Python code remains unchanged unless implementation reveals a packaging issue. Kubernetes is responsible only for scheduling and environment injection, while the container remains responsible only for running one sync and exiting.

## Container Design

The image should be intentionally small and straightforward:

- Use Python 3.11 to match the project requirement in `pyproject.toml`
- Copy the application source into the image
- Install the package with `pip`
- Start the process by running `garmin-sync`

The container should not embed secrets or a `.env` file. All runtime configuration must come from Kubernetes environment variables so the same image can be reused across environments.

## Scheduling Design

The Kubernetes workload should use a `CronJob` with:

- schedule: `59 23 * * *`
- timezone: `Asia/Jakarta`
- one pod per run
- no overlapping runs

Using `spec.timeZone` ensures the job fires at 23:59 Jakarta time even if the Kubernetes control plane uses UTC or another timezone.

### Run overlap behavior

Use `concurrencyPolicy: Forbid` so a new run is skipped if the previous run is still active. This is safer than allowing overlap because the sync writes to the same tables and reuses the same Garmin account credentials.

### Retry behavior

Use a conservative retry policy:

- `restartPolicy: Never` at the pod level
- small `backoffLimit` at the job level

This keeps failed executions visible without creating noisy retry storms or multiple overlapping sync attempts.

### Retention behavior

Keep only a small amount of history:

- a small successful jobs history
- a small failed jobs history

This is enough for troubleshooting while keeping the namespace tidy.

## Configuration Design

Runtime configuration should be split by sensitivity.

### Sensitive values from `Secret`

The `CronJob` should read these values from a Kubernetes `Secret`:

- `GARMIN_EMAIL`
- `GARMIN_PASSWORD`
- `DATABASE_URL`
- `FERNET_KEY`

This keeps credentials and database access out of the checked-in manifest.

### Non-sensitive values in the manifest

The manifest can define these values inline:

- `TIMEZONE=Asia/Jakarta`
- `SYNC_DAYS=7`
- optional `GARMIN_ACCOUNT_KEY=personal`

These defaults match the current application behavior and keep the first deployment simple.

### Secret contract

The README should document the exact secret key names so operators can create a matching secret without reading the manifest internals.

## Execution Flow

Each day at 23:59 Jakarta time:

1. Kubernetes creates a `Job` from the `CronJob`.
2. The job starts one pod using the built Garmin sync image.
3. The pod receives environment variables from the `Secret` and inline manifest settings.
4. The container runs `garmin-sync`.
5. The Python application performs one sync and exits.
6. Kubernetes marks the job as succeeded or failed and retains a small history.

This design intentionally avoids long-running containers, sidecars, or internal loops.

## Failure Handling

The manifest should remain explicit about normal operational failure modes:

- If the `Secret` is missing or incomplete, the pod should fail fast on startup.
- If Garmin authentication fails, the container should exit non-zero and the job should be marked failed.
- If the database is unavailable, the container should exit non-zero and Kubernetes should retain failed job history for inspection.
- If a previous day’s run is still active at the next schedule boundary, Kubernetes should skip the new run because overlap is forbidden.

These behaviors are acceptable for the initial version because they are predictable and easy to debug from pod logs and job status.

## Files And Boundaries

The implementation should be limited to a small set of files with clear ownership:

- `Dockerfile`: build and runtime packaging for the application image
- `k8s/garmin-sync-cronjob.yaml`: Kubernetes `CronJob` manifest and secret contract reference
- `README.md`: operator documentation for image build, secret creation, and deploy steps

No application module should take on Kubernetes-specific concerns unless packaging reveals a concrete need.

## Testing Strategy

This change is mostly packaging and deployment configuration, so validation should focus on deterministic checks:

- build the Docker image successfully
- inspect the manifest for valid Kubernetes structure
- verify the cron schedule and timezone are set to the requested values
- confirm the manifest references the expected secret keys and uses the `garmin-sync` command

If local Kubernetes validation tools are not available in the environment, implementation can still verify file content and document any unverified assumptions.

## Open Questions Resolved

- Schedule time: `23:59 Asia/Jakarta`
- Secret usage: yes, for sensitive values
- Packaging scope: include both `Dockerfile` and Kubernetes manifest

## Implementation Notes

Keep the initial deployment intentionally simple:

- one checked-in manifest
- one image definition
- one README section

Avoid adding templating systems, multiple environments, or cluster-specific customizations until a concrete deployment need appears.
