# Gemini CX architecture mapping

The challenge explicitly permits a custom controlled AI-assisted workflow. Relay uses the Google GenAI SDK and genuine Gemini interpretation plus verified fact selection. One deterministic orchestrator coordinates authentication, account/profile, billing, outage, diagnostics, XML subscriber status and case management. There is no arbitrary model tool execution.

Customer and support experiences run in Next.js/TypeScript on Bun. FastAPI provides the session, workflow and operational API. Synthetic enterprise adapters implement the supplied contracts. Structured events, trace correlation, event-derived metrics and handoff records persist in SQLite for reproducible evaluation.

Google mapping: Gemini Developer API is implemented and live-tested (see current evidence). Artifact Registry/Cloud Build and a single-process Compute Engine deployment with ext4 persistent disk are prepared. Secret Manager, least-privilege service accounts, Cloud Logging/Monitoring exports and private enterprise IAM are deployment integration steps. Managed Cloud SQL is required before horizontal scaling or durable Cloud Run use. No cloud resources were provisioned. This is not a claim of Dialogflow CX, CX Agent Studio, Vertex AI or certified CSP deployment.
