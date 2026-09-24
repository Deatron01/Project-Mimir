# Data processing agreement (template)

Version 0.1 (draft, 24 September 2026) · Magyar változat: [dpa-template.hu.md](dpa-template.hu.md)

> **Draft for legal review.** This template follows GDPR Art. 28(3) and the European Commission's standard contractual clauses between controllers and processors (Implementing Decision (EU) 2021/915). It is for **institutional use** of Mimir (a school or faculty using it for its staff), where the institution is the controller and the Mimir operator is the processor (see [compliance pack, section 1](compliance.en.md#1-roles-who-is-controller-and-who-is-processor)). Have it reviewed by a lawyer before signing, and fill in every `[TO BE COMPLETED]` field. Individual users do not sign this; the [privacy notice](privacy-notice.en.md) applies to them.

---

**between**

**Controller:** [TO BE COMPLETED: institution name, registered address, registration number, represented by] ("Controller")

**and**

**Processor:** [TO BE COMPLETED: Mimir operator name, address, registration number, represented by] ("Processor")

## 1. Subject and duration

1.1 The Processor provides the Mimir AI test generation service ("Service") to the Controller's authorised staff under [TO BE COMPLETED: main agreement / order, date]. In doing so it processes personal data on the Controller's behalf.

1.2 This agreement applies for as long as the Processor processes personal data for the Controller, and ends automatically when the main agreement ends, subject to clause 10.

## 2. Nature, purpose and scope of the processing

The details are in **Annex 1**. The Processor processes personal data only to provide the Service: to generate test questions from documents uploaded by the Controller's staff, and to store tests only where a user explicitly saves them.

## 3. Instructions

3.1 The Processor processes personal data only on the Controller's documented instructions, including with regard to transfers to third countries, unless EU or Member State law requires otherwise; in that case the Processor informs the Controller of that legal requirement before processing, unless the law prohibits this.

3.2 This agreement, the configuration chosen under Annex 1 (in particular whether `LOCAL_ONLY` is enabled) and the users' actions in the Service (uploading a document, saving or deleting a test) are the Controller's instructions. Further instructions must be given in writing (email is sufficient).

3.3 The Processor informs the Controller without delay if, in its opinion, an instruction infringes the GDPR or other data protection law.

## 4. Confidentiality

The Processor ensures that everyone authorised to process the personal data is bound by confidentiality (by contract or by law) and processes it only as needed to provide the Service.

## 5. Security of processing

5.1 The Processor implements the technical and organisational measures in **Annex 2** (GDPR Art. 32). It may replace a measure only with one that provides at least the same level of protection.

5.2 Zero retention: uploaded documents, the text extracted from them, text chunks, embeddings and prompts are processed only for the duration of the generation job and deleted when it ends, at the latest after 60 minutes. They are not used to train models and are never included in backups.

## 6. Sub-processors

6.1 The Controller gives general authorisation for the sub-processors in **Annex 3**.

6.2 The Processor informs the Controller in writing at least [TO BE COMPLETED: 30] days before adding or replacing a sub-processor. The Controller may object on reasonable data protection grounds within that period; if the parties cannot agree, the Controller may terminate the affected part of the Service.

6.3 The Processor imposes the same data protection obligations on each sub-processor by written contract and remains fully liable to the Controller for the sub-processor's performance.

## 7. Transfers outside the EEA

Personal data from uploaded documents is not transferred outside the EEA. Network traffic metadata (e.g. IP addresses) may be processed by Cloudflare, Inc. in the United States under the EU–US Data Privacy Framework or, where that does not apply, the Commission's standard contractual clauses (GDPR Art. 46). Any other transfer requires the Controller's prior written instruction.

## 8. Assistance to the Controller

8.1 **Data subject requests:** the Processor forwards any request it receives directly from a data subject to the Controller without delay and does not answer it itself unless instructed. Taking into account the nature of the processing, it helps the Controller respond to requests under GDPR Articles 15–22 (for example by exporting or deleting a user's saved tests).

8.2 **Other obligations:** the Processor helps the Controller meet its obligations under GDPR Articles 32–36 (security, breach notification, data protection impact assessment, prior consultation), taking into account the information available to it.

## 9. Personal data breaches

9.1 The Processor notifies the Controller without undue delay, and in any case within **[TO BE COMPLETED: 48] hours**, after becoming aware of a personal data breach affecting the Controller's data.

9.2 The notification contains, as far as available: the nature of the breach, the categories and approximate number of data subjects and records, the likely consequences, the measures taken or proposed, and a contact point. Information not yet available is provided in phases.

9.3 The Processor documents every breach and follows the procedure in the [compliance pack, section 10](compliance.en.md#10-personal-data-breach-procedure).

## 10. Deletion or return at the end

When the Service ends, the Processor, at the Controller's choice, returns (as a machine-readable export) or deletes all personal data processed for the Controller within [TO BE COMPLETED: 30] days, and deletes existing copies unless EU or Member State law requires storage. Data held only in job memory is already deleted under clause 5.2. The Processor confirms deletion in writing on request.

## 11. Audits and information

11.1 The Processor makes available all information necessary to demonstrate compliance with this agreement and GDPR Art. 28, including this agreement's annexes, the record of processing activities and the relevant parts of the compliance pack.

11.2 The Controller (or an auditor it appoints who is bound by confidentiality) may carry out audits, including inspections, with at least [TO BE COMPLETED: 30] days' written notice, during business hours and without disproportionately disrupting the Processor's operations. Each party bears its own costs unless the audit reveals a material breach by the Processor.

## 12. Liability and final provisions

12.1 Liability is governed by GDPR Art. 82 and [TO BE COMPLETED: the liability clause of the main agreement].

12.2 If this agreement and the main agreement conflict on data protection, this agreement prevails.

12.3 This agreement is governed by Hungarian law. [TO BE COMPLETED: competent court or dispute resolution.]

12.4 Amendments must be made in writing.

Place, date: [TO BE COMPLETED]

| Controller | Processor |
| --- | --- |
| Name, position: | Name, position: |
| Signature: | Signature: |

---

## Annex 1 – Description of the processing

| Item | Details |
| --- | --- |
| Categories of data subjects | (a) The Controller's staff who use the Service (users); (b) people mentioned in documents the users upload (e.g. authors, people in case studies) |
| Categories of personal data | (a) Users: email address, password hash, saved tests (title, PDF, creation time), pseudonymous job metadata. (b) People in documents: whatever personal data the uploaded teaching material contains |
| Special categories of data | None intended. Users are instructed not to upload special category data (Art. 9) or data about students; the upload screen requires them to confirm this |
| Nature of the processing | Text extraction, splitting into passages, vector search, question generation with a large language model, human review in the browser, PDF export; optional saving of tests |
| Purpose | Generating test questions from the Controller's teaching materials |
| Processing location | The Processor's server in [TO BE COMPLETED: country]. Unless `LOCAL_ONLY` is enabled, selected passages are processed by the Óbuda University GenAI service (Hungary). Before each upload the user sees where the document will be processed and can choose the local model instead |
| Configuration chosen by the Controller | `LOCAL_ONLY` = [TO BE COMPLETED: true / false] |
| Retention | Documents and derived data: duration of the job, max 60 minutes. Draft tests: max 60 minutes on the server. Saved tests: until the user deletes them, max 12 months. AI operations log (no content): 30 days. Server logs: max 14 days |

## Annex 2 – Technical and organisational measures

- Encryption in transit: HTTPS/TLS for all traffic (Cloudflare Tunnel).
- Zero retention: documents and derived data are processed in memory and deleted after each job; job results expire after 60 minutes; nothing from uploads is backed up.
- Data minimisation in logs: the AI operations log stores only hashes and lengths, never document text; access logs store shortened IP addresses and no query strings.
- Local-only mode (`LOCAL_ONLY=true`): no document text is sent to any external service.
- Access control: production access limited to named staff with MFA on the code host and the network provider. [TO BE COMPLETED: status]
- Passwords stored only as salted, non-reversible hashes (with the authentication service). [TO BE COMPLETED: status]
- Human review of every generated test before use (EU AI Act art. 14); generated PDFs state that the content was made with an AI assistant and which model was used.
- Data subject request and breach procedures as in the compliance pack, sections 9–10.
- Annual review of these measures.

## Annex 3 – Authorised sub-processors

| Sub-processor | Service | Data | Location | Transfer tool |
| --- | --- | --- | --- | --- |
| [TO BE COMPLETED: hosting provider] | Server hosting | All Service data | [TO BE COMPLETED] | — |
| Cloudflare, Inc. | Secure network access (tunnel) | Network traffic metadata (IP) | USA / global | EU–US Data Privacy Framework or SCCs |
| Óbuda University (genai.uni-obuda.hu) – only if `LOCAL_ONLY` is off | Language model inference | Document passages, prompts | Hungary | — |
| [TO BE COMPLETED: email provider] | Account emails | Email address, email content | [TO BE COMPLETED] | [TO BE COMPLETED] |
