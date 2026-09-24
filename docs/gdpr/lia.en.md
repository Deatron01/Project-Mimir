# Legitimate interest assessment

Version 0.1 (draft, 24 September 2026) · Magyar változat: [lia.hu.md](lia.hu.md)

> **Draft for legal review.** GDPR Art. 6(1)(f) allows processing that is necessary for the controller's legitimate interests unless the data subjects' interests or rights override them. This document runs the three-part test (purpose, necessity, balancing) for the three activities in the [record of processing activities](compliance.en.md#3-record-of-processing-activities-art-30) that rely on legitimate interest: **4. AI operations log**, **5. security logging** and **6. contact**. It also documents the right to object (Art. 21). Review it when the processing changes, and at least once a year.

Controller: [TO BE COMPLETED] · Prepared by: [TO BE COMPLETED] · Reviewed by (DPO / legal): [TO BE COMPLETED]

## Summary

| # | Activity | Legitimate interest | Necessary? | Balance | Outcome |
| --- | --- | --- | --- | --- | --- |
| 4 | AI operations log | Quality, traceability and debugging of an AI system; demonstrating human oversight and record-keeping expected under the EU AI Act | Yes: without a per-job record, wrong or unsafe output cannot be traced or fixed | Pseudonymous job ID, no content (only SHA-256 hashes and lengths), 30 days | **Passes** |
| 5 | Security logging | Keeping the service secure and available; detecting abuse and attacks | Yes: attacks and faults are found through access logs | Shortened IP, no query strings, 14 days; expected by users of any website | **Passes** |
| 6 | Contact | Answering enquiries that people send us | Yes: we cannot reply without the address and the message | Data given by the person for this purpose; 1 year after closure | **Passes** |

## 4. AI operations log

**Purpose test.** The operator runs a system that generates exam questions with a large language model. It needs to know which model and prompt version produced a result, how the quality check scored it, and when, so that faulty output can be investigated and fixed and so that it can show how the system is supervised (EU AI Act transparency and record-keeping duties, [compliance pack section 11](compliance.en.md#11-ai-act-touchpoints)). This is a real, present and lawful interest.

**Necessity test.** The log is the least intrusive way to reach the purpose: it does not store the document, the prompt or the output, only their SHA-256 fingerprints and lengths, plus the job ID, model name, prompt version, quality score and time. With fingerprints the operator can tell whether two jobs used the same input without keeping the input. A log without any link to a job could not support debugging.

**Balancing test.**

- *Nature of the data:* pseudonymous (job ID); no document content; no special category data.
- *Reasonable expectations:* users of an AI service expect the operator to monitor quality; the [privacy notice](privacy-notice.en.md) (section 3) describes the log.
- *Impact:* very low. Hashes cannot be reversed into the text; the log is not used for decisions about individuals or for profiling.
- *Safeguards:* 30-day retention with automatic purge (`AUDIT_RETENTION_DAYS`), access limited to the operator's team, legacy rows with content were scrubbed (GDPR-01).

**Outcome:** the operator's interest is not overridden. Processing may continue with the safeguards above.

## 5. Security logging

**Purpose test.** Keeping the service and its users' data secure (GDPR Art. 32) requires detecting attacks, abuse and faults. Recital 49 recognises network and information security as a legitimate interest.

**Necessity test.** Access logs are the standard way to find attacks and errors. They are minimised: the IP address is shortened, request parameters (query strings) are not logged, and request bodies are never logged.

**Balancing test.**

- *Nature of the data:* shortened IP address, time, path without parameters, status code, response time.
- *Reasonable expectations:* visitors expect a website to keep basic security logs; the privacy notice lists them.
- *Impact:* low; shortened IPs make identification unlikely; logs are not combined with other data or used for profiling.
- *Safeguards:* at most 14 days' retention, access limited to the operator's team, Cloudflare processes network data under its DPA and a valid transfer tool.

**Outcome:** the operator's interest is not overridden.

## 6. Contact

**Purpose test.** Replying to people who contact the operator is a legitimate interest (and, where the enquiry concerns using the service, a step prior to a contract under Art. 6(1)(b)).

**Necessity test.** A reply needs the sender's name, email address and message; nothing else is requested.

**Balancing test.**

- *Nature of the data:* what the person chose to send; they are asked not to include sensitive data.
- *Reasonable expectations:* people who write to us expect us to read and answer the message and keep it while the matter is open.
- *Impact:* low.
- *Safeguards:* deletion 1 year after the enquiry is closed, access limited to the team answering enquiries.

**Outcome:** the operator's interest is not overridden. Note: the contact form is not connected yet ([compliance pack, retention schedule](compliance.en.md#4-retention-schedule-and-deletion-mechanisms)); re-check this assessment when it is.

## Right to object (Art. 21)

Data subjects can object at any time to processing based on legitimate interest, using the address in the privacy notice (section 1). On an objection the operator stops processing that person's data for the activity concerned, unless it demonstrates compelling legitimate grounds that override the person's interests, or the data is needed for legal claims. For activity 5 an objection is usually answered by explaining the security need, because the logs are short-lived and minimised; the decision is recorded in the data subject request log ([compliance pack, section 9](compliance.en.md#9-data-subject-request-procedure)).

## Review log

| Date | Change | By |
| --- | --- | --- |
| 2026-09-24 | First draft | [TO BE COMPLETED] |
