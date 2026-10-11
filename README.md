<h1 align="center">Project Mimir</h1>

<p align="center">
  Documents in, exam questions out.<br />
  <samp>FASTAPI · NODE · REACT · POSTGRESQL · REDIS · MINIO · OLLAMA · DOCKER</samp><br />
  <samp><a href="https://mimir-ai.hu/">MIMIR-AI.HU ↗</a></samp>
</p>

### <samp>01 — WHAT IT IS</samp>

> *"From Mímir's well springs knowledge and understanding. Whoever drinks from it sees the order in the chaos."*

Project Mimir is an AI-driven, microservice-based system that turns raw documents into
structured tests and exam questions. Upload a PDF or a DOCX; get back multiple-choice,
true/false and essay questions you can edit and export.

What sets it apart is how much of it is written by hand. Document parsing, chunking, the
RAG pipeline, the worker pool and the PDF / XML export are all its own code rather than a
stack of high-level frameworks, and the language model runs locally so documents never
leave the machine.

### <samp>02 — FEATURES</samp>

- **Document processing.** PDF, DOCX and TXT, up to 20 MB per file.
- **Question generation.** Multiple-choice, true/false and essay questions.
- **Adjustable difficulty.** Beginner, intermediate or advanced.
- **RAG-grounded answers.** Retrieval-augmented generation keeps questions tied to the
  source text and hallucinations down.
- **Interactive editor.** Change, delete and add questions before you finalise a test.
- **Export.** JSON for data exchange, Moodle XML for LMS import, and a printable PDF.

### <samp>03 — ARCHITECTURE</samp>

Loosely coupled services, named after the parts of Norse myth that deal with knowledge and
making things.

| Service | Role |
|---|---|
| **Wellspring** (the archivist) | Parses files at the binary level and extracts clean text and tables from PDF / DOCX with its own logic |
| **RuneCarver** (the sculptor) | Semantic chunking: splits text into sentences and cuts where cosine similarity says the topic changes |
| **Bifrost** (the navigator) | The RAG conductor. Talks to the vector store and the LLM and assembles the context prompt |
| **Heimdall** (the censor) | Filters model output through strict JSON schemas and confidence rules, guarding against hallucination and prompt injection |
| **The Forge** (the engine room) | A worker pool on PostgreSQL and `FOR UPDATE SKIP LOCKED` that schedules CPU- and GPU-heavy jobs |
| **Skald** (the scribe) | The export engine. Assembles Moodle XML by hand (CDATA and MathJax included) and draws PDFs with its own layout code |

In front of them sit an nginx API gateway and a React + TypeScript frontend.

### <samp>04 — STACK</samp>

- **Backend:** Python (FastAPI) and Node.js services
- **Data:** PostgreSQL for structured metadata, MinIO (S3-compatible) for binary files
- **Cache:** Redis for frequent queries and sessions
- **Security:** JWT authentication and TLS
- **Frontend:** React, TypeScript, Vite, Tailwind, TanStack Query, i18next; tested with Vitest, Playwright and Storybook
- **Infrastructure:** Docker Compose locally, Kubernetes (HPA) for scaling in the cloud

### <samp>05 — GETTING STARTED</samp>

The services run in Docker containers. The model runs locally through Ollama.

##### Prerequisites

- **Docker Desktop**
- **Python 3.10+** for the test harness
- **[Ollama](https://ollama.com/)** for the local LLM
- A dedicated GPU with at least 8 GB of VRAM (an RTX 3070 Ti, for example)

##### 1. Start the local model

Mimir currently generates questions with `hf.co/mradermacher/PULI-LlumiX-Llama-3.1-GGUF:Q4_K_M`.

```bash
ollama run hf.co/mradermacher/PULI-LlumiX-Llama-3.1-GGUF:Q4_K_M
```

Once the `>>>` prompt appears you can leave the session, but **Ollama has to keep running
in the background**. The containers reach it at `host.docker.internal:11434`.

##### 2. Start the services

From the repository root:

```bash
docker-compose up -d --build
```

The first build takes a few minutes while Docker pulls the Python images, the FastAPI
dependencies and Bifrost's embedding model.

##### 3. Run the end-to-end test

With every container up (`docker ps`):

```bash
pip install requests pandas matplotlib tabulate
python tests/tester.py
```

The script pushes a complex document through the whole system and writes a
`tests/Test_Result_[timestamp]/` folder containing:

- a colour-coded latency chart,
- a detailed Markdown audit log,
- the raw JSON the model generated,
- the final, print-ready PDF exam sheet.

### <samp>06 — ALSO IN THIS REPOSITORY</samp>

| Path | What it is |
|---|---|
| `frontend/` | The web app, with its own [`README`](./frontend/README.md) |
| `services/` | One folder per service listed above |
| `api-gateway/` | nginx configuration |
| `docs/` | Roadmap, architecture decision records, GDPR documentation (EN / HU), usability test plan |
| `tests/` | The end-to-end tester, evaluation sets and saved test results |
| `tdk/`, `paper/` | The research write-up and its figures and tables |

<br />

<p align="center">
  <a href="https://github.com/Deatron01"><img src="https://raw.githubusercontent.com/Deatron01/Deatron01/main/assets/icon.png" width="56" alt="Dea" /></a><br />
  <sub><i>Little chaos in a quiet mind.</i></sub><br />
  <sub><samp>MORE WORK AT <a href="https://github.com/Deatron01">GITHUB.COM/DEATRON01</a></samp></sub>
</p>
