# Google Cloud and local deployment

## Local containers

`docker compose up --build` starts Next.js on 127.0.0.1:3000, the private FastAPI service and private synthetic telecom fixtures. Only web is exposed. API runtime configuration injects Gemini credentials; no key is baked into an image. API state is persisted in the cx-data volume. `docker compose down` retains it.

## Google Cloud reference deployment

The durable single-process deployment target for this implementation is **Compute Engine with an ext4 persistent disk**, running these same three containers with Docker Compose. No Google resources have been created. This is a prepared deployment approach, not a claim of a running cloud service.

1. Create an Artifact Registry Docker repository and use `gcloud builds submit --config deployment/cloudbuild.yaml --substitutions=_REGION=REGION,_REPOSITORY=REPO` to build images. Substitute your project and region; review the build before running. No build needs a model secret.
2. Provision a Linux Compute Engine VM with Docker/Compose installed, a dedicated service account, private enterprise networking and a separately attached persistent disk formatted ext4. Mount it at /srv/relay/data. Use Google's current disk mounting instructions. Do not place SQLite WAL databases on NFS or Cloud Storage mounts.
3. Transfer this source release without .env. Replace Compose build entries with immutable Artifact Registry image digests. Bind /srv/relay/data to /app/data in the API container instead of the development named volume. Give UID 10001 ownership. Run **one API container/process**.
4. Retrieve the Gemini key from Secret Manager using the VM's service account, with secretAccessor granted on that secret alone. Put runtime configuration in a root-readable file outside the checkout; use `docker compose --env-file /secure/path/relay.env up -d`. Protect Docker access; never log resolved Compose configuration containing secrets.
5. Terminate TLS at a managed HTTPS load balancer or authenticated reverse proxy. Bind the local web port to loopback and route only the public frontend through it. Set PUBLIC_ORIGIN to the exact HTTPS hostname and COOKIE_SECURE=true. Keep the API and synthetic mock unexposed; restrict ingress and allow only required outbound Gemini/enterprise access. Configure health checks, resource limits and log retention.
6. Configure consistent SQLite backups using SQLite's backup API, disk snapshots, restore drills and session retention. Ship redacted JSON events to Cloud Logging, alert on uncertain actions, fallback, authorization denials and tool failures. Use traceId for investigations.
7. Validate all scenarios after deployment. Drain requests before replacing containers; retain completed and uncertain action markers during rollback. Reconcile any uncertain case with the enterprise system instead of replaying it. Track image digests and schema versions.

Cloud Run is an alternative **after** migrating SQLite to Cloud SQL and implementing transactional cross-instance action claims. A single-instance cap does not make an ephemeral filesystem durable. An authenticated private API gateway/identity-token integration is also required before splitting web/API across private Cloud Run services. These changes are not represented as complete.

Synthetic authentication/mock telecom are for challenge qualification, not real customer use. Production federation, mTLS/IAM enterprise adapters, queue delivery, distributed rate limits and external penetration/load evaluation remain engineering work. The custom Gemini architecture and managed-service mapping are documented in docs/GEMINI_CX_MAPPING.md. No Dialogflow CX, Agent Studio or Vertex deployment is claimed.

Official references: https://cloud.google.com/compute/docs/disks/add-persistent-disk and https://cloud.google.com/compute/docs/containers/deploying-containers .

## Runtime configuration and operational limits

`PUBLIC_ORIGIN` is the exact browser origin; configure forwarded scheme/host consistently at the TLS ingress. `COOKIE_SECURE=true` is required for HTTPS deployment. `/api/health` through Next.js is API liveness; the protected `/api/ops/health` additionally probes enterprise readiness. Provider readiness comes from actual AI events, not a health badge.

`REQUEST_TIMEOUT=2` seconds bounds each enterprise socket operation; `MAX_RETRIES=1` (clamped 0–2) applies only to safe reads/read-only diagnostic calls. Case creation and login are not retried. `AI_TIMEOUT=40` seconds bounds one model call, with one SDK attempt. Next.js allows up to 120 seconds for upstream workflows. These are transport timeouts, not a full slow-drip-safe workflow deadline. UI account verification is an independent read and does not change a pending chat/action.

Cost drivers are two model stages per informational request, VM uptime, persistent disk capacity/backups, network egress and structured-log retention. Reviewer has no model cost. Set Google Cloud budgets, provider quotas, bounded retention and alerts before operating; no cloud pricing estimate, token-cost report or paid deployment is claimed. Metrics scan persisted events and state mutations serialize in one API process, so throughput/load requirements must be measured before production sizing. Keep a consistent SQLite backup and completed action markers for rollback; never replay uncertain writes after restoring state.
