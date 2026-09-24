# Privacy notice

Effective from 24 September 2026 · version 1.1 (draft) · Magyar változat: [privacy-notice.hu.md](privacy-notice.hu.md)

> This file mirrors the `legal.privacy` block of `frontend/src/locales/en/translation.json`; the website shows the same text. Update both together.

This notice explains what personal data the Mimir AI test generation service processes, why, for how long, and what your rights are. Mimir follows a "zero retention" principle: the documents you upload are used only to create your test and are deleted afterwards.

## 1. Controller

- Controller: [TO BE COMPLETED: operator's name]
- Registered / postal address: [TO BE COMPLETED]
- Email for data protection requests: [TO BE COMPLETED: e.g. privacy@mimir-ai.hu]
- Data protection officer: [TO BE COMPLETED if appointed; otherwise remove this line]
- Website: https://mimir-ai.hu

## 2. In short

- Your uploaded document, the text extracted from it and the chunks made from it are used only to generate your test and are deleted when processing ends (automatically after 60 minutes at the latest).
- A generated test is saved to your account only if you explicitly ask for it; you can delete saved tests at any time, and we keep them for at most 12 months.
- We do not use your documents to train artificial intelligence, and we do not sell them to anyone.
- We do not use tracking, advertising or analytics cookies.

## 3. What we process, why, on what legal basis and for how long

| Processing | Data | Purpose | Legal basis | Retention |
| --- | --- | --- | --- | --- |
| User account | Email address, password hash (non-reversible), verification token, registration time | Creating your account, signing in, providing the service | Performance of a contract – GDPR Art. 6(1)(b) | Until the account is deleted; unverified accounts are deleted after 30 days |
| Uploaded document and derived data | The file, extracted text, text chunks, their vector representations, the request sent to the language model | Generating the test you asked for | Performance of a contract – GDPR Art. 6(1)(b) | Only while processing; deleted when the job ends, automatically after 60 minutes at the latest |
| Generated test (draft) | The generated questions and answers | Review and editing before export | Performance of a contract – GDPR Art. 6(1)(b) | At most 60 minutes on the server; editing happens in your browser |
| Saved tests ("My tests") – only on request | Test title, PDF file, size, creation time, your account identifier (email address) | So you can download it again later | Performance of a contract – GDPR Art. 6(1)(b), at your explicit request | Until you delete it, at most 12 months |
| AI operations log | Job ID, model name, prompt version, cryptographic fingerprints (SHA-256) and lengths of the request and context, quality score, time – without the document text | Quality assurance, traceability and debugging of the AI system | Legitimate interest – GDPR Art. 6(1)(f) | 30 days |
| Server logs | Shortened (anonymised) IP address, time, requested path without parameters, status code, response time | Security, abuse detection, troubleshooting | Legitimate interest – GDPR Art. 6(1)(f) | At most 14 days |
| Contact | Name, email address, message content | Answering your enquiry | Legitimate interest – GDPR Art. 6(1)(f), or steps prior to a contract – Art. 6(1)(b) | 1 year after the enquiry is closed |
| Settings in your browser | Palette and mode (mimir-theme), language (mimir-lang), sign-in state (mimir_user), last test settings (mimir-gen-options), chosen language model (mimir-model) | Remembering your choices, keeping you signed in | Storage strictly necessary for the service you requested (exemption under Art. 5(3) of the ePrivacy Directive); no consent needed | On your own device, until you clear it or sign out |

## 4. Other people's personal data in uploaded documents

Please upload teaching materials that contain no personal data where possible. Do not upload special category data (e.g. health data), student assessments, class lists or other information about identifiable people.

If you do upload a document containing such data, you (or your institution) must have an appropriate legal basis for it. We process that data only to generate the test and only while processing, under the zero-retention rule above. For institutional use we sign a data processing agreement with the institution.

## 5. Who can access the data (recipients, processors)

- Hosting / server provider: [TO BE COMPLETED: name, address] – runs the service.
- Cloudflare, Inc. (USA) – secure network access (Cloudflare Tunnel); processes technical traffic data such as IP addresses.
- Óbuda University GenAI service (genai.uni-obuda.hu) – unless the service runs in local-only mode, selected passages of your document and your request are processed by a language model operated by the university to generate and quality-check the test. Before every upload the page shows where the document will be processed, and you can choose the local model instead; the text then does not leave the operator's server. [TO BE COMPLETED: name of the agreement with the university]
- Email delivery provider: [TO BE COMPLETED] – sends account confirmation and password reset emails.
- Local-only mode: when the operator enables LOCAL_ONLY, document text never leaves the operator's own server.

Our processors may only process data on our instructions under a written contract (GDPR Art. 28). Where required by law, we may disclose data to authorities or courts.

## 6. Transfers outside the EEA

Cloudflare, Inc. may process network data in the United States. Such transfers rely on certification under the EU–US Data Privacy Framework or, where that does not apply, on the European Commission's standard contractual clauses (GDPR Art. 46). The content of uploaded documents is not transferred outside the EEA.

## 7. Artificial intelligence and automated decision-making

- Mimir is an AI-based system: questions are generated by a large language model. The output can contain errors, so human review is mandatory before use.
- Mimir does not make automated decisions about you (or about students) that produce legal effects or similarly significantly affect you (GDPR Art. 22). The system does not assess or grade test takers.
- We do not use your documents, questions or answers to train models.

## 8. Security

- Encrypted (HTTPS/TLS) connection between your browser and the service.
- Passwords are stored only as salted, non-reversible hashes.
- Data being processed is separated per job and deleted automatically when the job ends.
- Logs contain no document content, and IP addresses are logged in shortened form.
- Access control, regular updates, and backups of account data (uploaded documents are never backed up).

## 9. Your rights

- Access (Art. 15): you can ask what data we hold about you and receive a copy.
- Rectification (Art. 16): you can ask us to correct inaccurate data.
- Erasure ("right to be forgotten", Art. 17): you can ask us to delete your data; you can delete saved tests yourself on the "My tests" page, and data stored in your browser on the "Your data" page.
- Restriction of processing (Art. 18).
- Data portability (Art. 20): you can request your account data and saved tests in a machine-readable format.
- Objection (Art. 21): you can object at any time to processing based on legitimate interest.
- Where processing is based on consent, you can withdraw it at any time; this does not affect the lawfulness of earlier processing.

Send your request to the email address in section 1. We reply within one month; where necessary this can be extended by two further months, and we will tell you if so. Before acting we may verify your identity (for example by confirmation from your account's email address). Requests are free of charge.

## 10. Complaints and remedies

If you believe we have infringed your data protection rights, please contact us first. You can lodge a complaint with the Hungarian National Authority for Data Protection and Freedom of Information (NAIH, 1055 Budapest, Falk Miksa utca 9–11; postal address: 1363 Budapest, Pf. 9; phone: +36 1 391 1400; email: ugyfelszolgalat@naih.hu; www.naih.hu) or with the supervisory authority of your EU country of residence, or you can go to court; in Hungary you may bring the case before the regional court (törvényszék) of your place of residence or stay.

## 11. Children

Mimir is intended for educators and adult users. People under 16 may not register. If we learn that we hold data of a person under 16, we delete it without delay.

## 12. Changes to this notice

We may update this notice when the service or the law changes. We announce significant changes on the website and notify registered users by email. Earlier versions are available on request.
