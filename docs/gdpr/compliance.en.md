# Mimir GDPR compliance pack

Version 1.0 (draft) · 22 September 2026 · Magyar változat: [compliance.hu.md](compliance.hu.md)

This is the internal documentation the operator of Mimir needs under the GDPR (Regulation (EU) 2016/679), the Hungarian Privacy Act (Infotv., Act CXII of 2011) and the transparency duties of the EU AI Act. The public-facing text is the [privacy notice](privacy-notice.en.md). Every item is marked **Implemented**, **Partly implemented** or **Planned**, with the GitHub issue that tracks it.

> This is an engineering compliance draft, not legal advice. Before going live with real users, have it reviewed by the university's data protection officer or a lawyer and fill in every `[TO BE COMPLETED]` field (list in section 13).

## Contents

1. Roles: who is controller and who is processor
2. Data inventory
3. Record of processing activities (Art. 30)
4. Retention schedule and deletion mechanisms
5. Processors and international transfers (Art. 28, 44–49)
6. Technical and organisational measures (Art. 32)
7. Data protection by design and by default: rules for developers (Art. 25)
8. DPIA screening (Art. 35)
9. Data subject request procedure (Art. 12–22)
10. Personal data breach procedure (Art. 33–34)
11. AI Act touchpoints
12. Implementation checklist
13. Fields still to complete

---

## 1. Roles: who is controller and who is processor

| Data | Role of the Mimir operator | Why |
| --- | --- | --- |
| User accounts, saved tests, logs, contact messages | **Controller** | The operator decides why and how this data is processed. |
| Personal data of third parties inside uploaded documents (e.g. names in a case study) | **Controller** for individual users; **processor** when an institution (school, faculty) uses Mimir for its staff | The institution decides to process its own documents; Mimir only runs the generation on its behalf. |
| Document excerpts sent to the university GenAI API | Óbuda University acts as the operator's **processor** | It runs the model on the operator's instructions only. |

Consequences:

- Institutional use needs a **data processing agreement** (Art. 28) between the institution and the operator. A template is Planned (GDPR-08, issue #80).
- If Mimir is operated *by* Óbuda University itself, the university is the controller and the GenAI service is internal. Section 5 then changes accordingly.

## 2. Data inventory

| Data item | Where it lives (target design) | Personal data? |
| --- | --- | --- |
| Email address, password hash, verification token | Postgres `users` (auth service, GW-01 #8) | Yes |
| Uploaded file bytes | Wellspring process memory only | Possibly (document content) |
| Extracted text, chunks | RuneCarver / Bifrost memory; Qdrant collection | Possibly |
| Embeddings | Qdrant (in-memory today) | Possibly (derived) |
| Prompt and raw LLM output | Worker memory only | Possibly |
| Generated exam draft | Bifrost job store (in-memory, TTL) and the browser | Possibly |
| Saved tests | Skald storage (PDF + SQLite row with owner email) | Yes |
| AI audit log | Postgres `audit_logs` (hashes and metadata only) | Pseudonymous (job ID) |
| Server logs | Nginx and container stdout | Yes (shortened IP) |
| Browser storage: `mimir-theme`, `mimir-lang`, `mimir_user` | User's own browser | `mimir_user` contains the email |

## 3. Record of processing activities (Art. 30)

**Controller:** [TO BE COMPLETED] · **Contact:** [TO BE COMPLETED] · **DPO:** [TO BE COMPLETED or "not appointed"]

| # | Activity | Purpose | Data subjects | Data categories | Legal basis | Recipients | Third-country transfer | Retention | Security measures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Account management | Provide accounts and sign-in | Registered users | Email, password hash, verification token, timestamps | Art. 6(1)(b) | Hosting, email provider | No (except Cloudflare network data) | Until deletion; unverified 30 days | TLS, hashed passwords, access control |
| 2 | Test generation | Generate a test from a user's document | Users; people mentioned in documents | Document content, derived text, embeddings, prompt | Art. 6(1)(b) | Hosting, university GenAI (unless LOCAL_ONLY) | No | Duration of the job, max 60 min | In-memory processing, purge after job, TTL |
| 3 | Saved tests (opt-in) | Let users re-download tests | Users | Title, PDF, owner email, timestamps | Art. 6(1)(b) at user request | Hosting | No | Until deleted, max 12 months | Owner check on delete, automatic purge |
| 4 | AI operations log | Quality, traceability, debugging | Users (pseudonymous) | Job ID, model, prompt version, SHA-256 hashes, lengths, score | Art. 6(1)(f) | Hosting | No | 30 days | No content stored, automatic purge |
| 5 | Security logging | Security, abuse detection | Visitors | Shortened IP, time, path without query, status | Art. 6(1)(f) | Hosting, Cloudflare | Cloudflare (DPF / SCC) | Max 14 days | IP truncation, no query strings |
| 6 | Contact | Answer enquiries | Enquirers | Name, email, message | Art. 6(1)(f) / (b) | Email provider | No | 1 year after closure | Access control |

A legitimate interest assessment (balancing test) is required for activities 4, 5 and 6. Short version: the interests (security, service quality) are necessary, the data is minimised (no content, shortened IP), retention is short and users can object. Write it up in full before launch (Planned, GDPR-08 #80).

## 4. Retention schedule and deletion mechanisms

| Data | Retention | Deletion mechanism | Status |
| --- | --- | --- | --- |
| Uploaded file bytes | Duration of the request | Never written to disk; freed after extraction | **Implemented** (Wellspring already processes in memory) |
| Chunks and embeddings | Until the job ends, max 60 min | Bifrost clears the vector store when a job finishes or fails; the next ingest also clears it | **Implemented** in this change; per-topic isolation is Planned (TOP-03 #107) |
| Job results (exam draft) | 60 min (`JOB_TTL_SECONDS`) | Bifrost drops expired jobs on every request | **Implemented** in this change |
| Saved tests | Until deleted, max 12 months (`HISTORY_RETENTION_DAYS=365`) | Skald purge at start-up and every 24 h; user delete endpoint; saving is opt-in | **Implemented** in this change |
| AI audit log | 30 days (`AUDIT_RETENTION_DAYS`) | The Forge purges hourly; stores hashes only; legacy text columns are erased at start-up | **Implemented** in this change |
| Server logs | Max 14 days | Nginx access log without query strings and with truncated IP; error log only at `crit` level; Docker logs rotate at 10 MB × 3 files per container | **Partly implemented** (anonymisation and size-based rotation done; a strict 14-day time limit is an ops task) |
| Accounts | Until deletion; unverified 30 days | Auth service | **Planned** (GW-01 #8, GDPR-07 #79) |
| Contact messages | 1 year | Mailbox rule | **Planned** (contact form not connected yet) |
| Browser storage | Until the user clears it or signs out | "Your data" page deletes all Mimir keys | **Implemented** in this change |
| Data already in git history (`services/skald/storage`) | Must be removed | Files are untracked in this change; history rewrite with `git filter-repo` | **Partly implemented** (history rewrite: PLT-01 #1) |

**Planned change – Topic workspace ([epic #103](https://github.com/Deatron01/Project-Mimir/issues/103)):** when topics ship, chunks, embeddings, the concept graph and chat history are kept per topic until the user deletes the file or topic, or the topic is inactive for the period decided in [#104](https://github.com/Deatron01/Project-Mimir/issues/104) (proposal: 90 days). Raw files are still never stored. Deleting a topic cascades to all of its data ([#108](https://github.com/Deatron01/Project-Mimir/issues/108)). The privacy notice and this pack must be updated before release ([#121](https://github.com/Deatron01/Project-Mimir/issues/121)); until then the rules above apply.

Backups: account data may be backed up; uploaded documents, chunks and job results must never be included in backups. Backups older than the retention above must be rotated out.

## 5. Processors and international transfers

| Processor | Data | Location | Contract (Art. 28) | Transfer tool | Status |
| --- | --- | --- | --- | --- | --- |
| Hosting provider [TO BE COMPLETED] | All service data | [TO BE COMPLETED] | Required | — | Open |
| Cloudflare, Inc. | Network traffic metadata (IP) | USA / global | Cloudflare DPA (accepted in the dashboard) | EU–US Data Privacy Framework or SCCs | Check that the DPA is accepted |
| Óbuda University GenAI (genai.uni-obuda.hu) | Document excerpts, prompts | Hungary | Required: written agreement stating no retention and no training | — | Open (research spike R6 #98) |
| Email provider [TO BE COMPLETED] | Email address, email content | [TO BE COMPLETED] | Required | Depends on provider | Open |

Checklist for every processor: written contract; processing only on instructions; confidentiality; security measures; sub-processor approval; help with data subject requests; deletion or return at the end; audit rights.

**Local-only mode:** set `LOCAL_ONLY=true` in `.env` and Bifrost, Heimdall and Wellspring stop calling the university API. Document text then never leaves the operator's server. **Implemented** in this change (default `false` so the current deployment keeps working; switch it on once a local model is available on the server).

## 6. Technical and organisational measures (Art. 32)

| Measure | Status |
| --- | --- |
| TLS for all traffic (Cloudflare Tunnel, HTTPS) | Implemented |
| Passwords hashed with bcrypt/Argon2 | Planned with the auth service (GW-01 #8) |
| Real authentication and per-user authorisation on every endpoint | Planned (GW-01 #8, GW-02 #9, SKA-02 #45) — **highest priority**: today `/tests` and downloads trust a `user_id` parameter |
| Topic-isolated processing (mandatory `topic_id` filter, no shared search) | Planned (TOP-03 #107) |
| Automatic purge of processing data, job results, saved tests, audit log | Implemented in this change |
| No document content in logs or the audit log | Implemented in this change |
| IP truncation and no query strings in access logs | Implemented in this change |
| Secrets only in `.env`, never in git; `.env.example` committed | Partly (credentials still in `docker-compose.yml`, PLT-04 #4) |
| Rate limiting and upload size limits | Partly (50 MB in Nginx; rate limiting GW-04 #11) |
| File validation (type, size, malicious PDFs) | Planned (WEL-05 #18) |
| Only the gateway exposed to the internet | Planned (GW-06 #13) |
| Dependency and image vulnerability scanning in CI | Planned (section 4 of the roadmap) |
| Access to production limited to named team members; MFA on GitHub and Cloudflare | Organisational — to do |
| Team confidentiality commitment and short GDPR training | Organisational — to do |
| Annual review of this pack | Organisational — to do |

## 7. Data protection by design and by default: rules for developers (Art. 25)

1. Never write uploaded content, extracted text, prompts or model output to disk, a database, a log line or an error message. Log IDs, sizes and hashes instead.
2. Every piece of processing data carries a job or session ID and a TTL. If you add a store, add its purge in the same PR.
3. Optional storage is **off by default** (saving tests is opt-in).
4. New third-party services or data flows need an update of this pack (sections 3 and 5) in the same PR.
5. Never commit user data, generated exams or databases. Use synthetic or public-domain documents for tests.
6. User-facing texts about privacy must be true for the current deployment (no "never leaves your machine" when an external API is used).
7. The PR template includes a zero-retention checkbox; reviewers must check it.

## 8. DPIA screening (Art. 35)

| NAIH / EDPB criterion | Applies? |
| --- | --- |
| Innovative technology (generative AI) | Yes |
| Data about vulnerable people (students, possibly minors, may appear in documents) | Possibly |
| Large-scale processing | Not at pilot scale; yes if rolled out university-wide |
| Evaluation or scoring of people | No (Mimir does not grade students) — keep it that way |
| Automated decisions with legal effect | No |
| Special category data | Not intended; possible if users upload such documents |

**Conclusion:** at least two criteria may apply, so a **full DPIA is recommended before institutional rollout**. For the pilot, the risks below are mitigated by zero retention.

| Risk | Likelihood / impact | Mitigation | Status |
| --- | --- | --- | --- |
| Another user sees my document or test (shared vector store) | High / high | Topic isolation (TOP-03 #107, tested by TOP-08 #112); purge after each job | Partly |
| Unauthorised access to saved tests | High / medium | Real auth and ownership checks (GW-01 #8, SKA-02 #45) | Planned |
| Document content retained in logs or the audit log | Medium / high | Metadata-only audit log, log redaction | Implemented |
| Excessive retention | Medium / medium | TTLs and purge jobs | Implemented |
| Content sent to a third party without a legal basis or contract | Medium / high | `LOCAL_ONLY` mode; processor agreement with the university | Partly |
| Users upload special category or students' data | Medium / high | Upload warning and confirmation; DPA for institutions | Implemented (UI warning) / Planned (DPA) |
| Inaccurate AI output harms students | Medium / medium | Mandatory human review, editor, disclaimer | Implemented |

## 9. Data subject request procedure

1. **Receive:** requests arrive at the privacy email address (or via the "Your data" page, which links to it). Log each request in the request register (date, type, requester, deadline, outcome) — no document content.
2. **Verify identity:** ask the requester to confirm from the email address of the account. Do not ask for more data than needed.
3. **Deadline:** answer within 1 month of receipt; extend by up to 2 more months for complex cases, informing the requester within the first month.
4. **Act:**
   - Access / portability: export account data and saved tests (JSON + PDFs).
   - Erasure: delete the account row, saved tests (Skald rows and files), and any audit rows for the user's job IDs if linkable. Processing data is already gone because of zero retention; say so in the answer.
   - Rectification: update the email address.
   - Objection / restriction: stop the relevant processing for that user and record it.
5. **Answer** in the language of the request (Hungarian or English), free of charge.
6. **Tooling status:** self-service deletion of saved tests and local data is **Implemented** in this change; account export and deletion endpoints are **Planned** (GDPR-07 #79, depends on GW-01 #8).

## 10. Personal data breach procedure

1. **Detect and contain** (0–4 h): whoever notices it tells the incident lead [TO BE COMPLETED] immediately. Stop the leak (rotate secrets, take the endpoint offline, revoke tokens).
2. **Assess** (within 24 h): what data, how many people, likely consequences. Record everything in the breach register (Art. 33(5)) even if it is not reported.
3. **Notify NAIH within 72 hours** of becoming aware, unless the breach is unlikely to result in a risk. Use NAIH's online breach notification form. If some information is missing, notify in phases.
4. **Inform affected people without undue delay** if the risk is high (Art. 34), in plain language: what happened, likely consequences, what we did, what they can do, contact point.
5. **Processors** must notify the operator without undue delay; put this in every processor contract.
6. **Post-mortem** within 2 weeks: root cause, fixes, update of this pack.

Example: the unauthenticated `/api/v1/tests` endpoint (see the roadmap audit) would count as a breach if anyone other than the owner downloaded a saved test. Check the access logs before deciding whether to notify.

## 11. AI Act touchpoints

- **Transparency (Art. 50):** users must know they are interacting with an AI system and that questions are AI-generated. **Implemented:** chat disclaimer, privacy notice section 7, and the PDF metadata page stating the content was made with an AI assistant.
- **Human oversight:** the editor forces a review step before export. **Implemented.**
- **Risk class:** annex III lists AI used to *evaluate learning outcomes* or *steer the learning process* in education as **high-risk**. Test *generation* for teachers who review everything is outside that, but **automatic grading of student answers would move Mimir into the high-risk category**. Do not add grading without a new assessment.
- **Logging:** the metadata-only audit log supports traceability without storing content.

## 12. Implementation checklist

| Requirement | Where | Status | Issue |
| --- | --- | --- | --- |
| Privacy notice in HU and EN, shown on the site | `docs/gdpr/privacy-notice.*.md`, `/privacy` page | Implemented (placeholders to fill) | GDPR-08 #80 |
| Upload warning and confirmation | Chat page | Implemented | GDPR-10 #82 |
| Saving tests is opt-in, with retention notice | Question editor, Skald `save` flag | Implemented | SKA-01 #44 |
| Delete a saved test | "My tests" page, Skald `DELETE /api/v1/tests/{id}` | Implemented (owner checked by user_id until real auth) | GDPR-07 #79 |
| "Your data" page: view, export and delete browser data | `/data` page | Implemented | GDPR-07 #79 |
| Purge processing data after each job; job TTL | Bifrost | Implemented | GDPR-02 #74, GDPR-03 #75 |
| Metadata-only audit log, 30-day retention, legacy scrub | Bifrost, The Forge | Implemented | FRG-05 #42, GDPR-01 #73 |
| Saved tests retention (12 months) | Skald | Implemented | GDPR-03 #75 |
| Access logs: no query strings, truncated IP | Nginx | Implemented | GDPR-05 #77 |
| Local-only mode (no external AI) | Bifrost, Heimdall, Wellspring, compose | Implemented (default off) | GDPR-06 #78 |
| Stop tracking stored user data in git | `.gitignore`, `git rm --cached` | Implemented | PLT-01 #1 |
| Rewrite git history to remove old user data | Repository | Planned (needs team coordination and force push) | PLT-01 #1 |
| Real authentication and ownership checks | Auth service, gateway, Skald | Planned | GW-01 #8, GW-02 #9, SKA-02 #45 |
| Isolation of vector data | Bifrost | Planned (now per topic) | TOP-03 #107 (supersedes BIF-01 #25) |
| Account export and deletion | Auth service | Planned | GDPR-07 #79 |
| Automated zero-retention test in CI | Tests | Planned | GDPR-04 #76 |
| Topic isolation: hard `topic_id` filtering in Qdrant | Bifrost | Planned | TOP-03 #107 |
| Topic cascade delete and janitor | Skald, Bifrost, The Forge | Planned | TOP-04 #108 |
| Topic isolation and zero-residue test suite | Tests | Planned | TOP-08 #112 |
| Auto-delete inactive topics | The Forge | Planned | TOP-09 #113 |
| Retention decision and encryption at rest for topic data | Architecture | Planned | TOP-18 #104 |
| Privacy notice and pack updated for topics | Docs | Planned (before topics ship) | TOP-17 #121 |
| Processor agreements (hosting, university, email) and institutional DPA template | Legal | Planned | R6 #98, GDPR-08 #80 |
| Legitimate interest assessment, full DPIA before rollout | Legal | Planned | GDPR-08 #80 |
| Log rotation | `docker-compose.yml` (10 MB × 3 per container); 14-day time limit on the host | Partly implemented | GDPR-05 #77 |

## 13. Fields still to complete

- Controller name, address, privacy email and DPO (privacy notice section 1; this pack section 3).
- Hosting provider and email provider (privacy notice section 5; this pack section 5).
- Name of the agreement with Óbuda University for the GenAI API.
- Incident lead and deputy (section 10).
- Date of legal review and reviewer.
