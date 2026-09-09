# Medical RAG Setup & Ingestion Architecture

This document describes the dual-layer retrieval-augmented generation (RAG) architecture powering the **Vyoma Offline Medical AI Assistant**.

---

## 1. Dual-Corpus Medical Knowledge Base

The RAG engine is built on two distinct data layers with strict clinical precedence:

```
                      +---------------------------------------+
                      |         Patient Query (Speech)        |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |   Hybrid Retriever (FTS5 + FAISS)     |
                      +---------------------------------------+
                                     /         \
                                    /           \
                                   v             v
       +------------------------------------+  +------------------------------------+
       |   Layer 1: Indian Clinical STGs    |  |    Layer 2: MedlinePlus Topics     |
       |  (MoHFW, NHM, ASHA, NVBDCP, IPHS)  |  |   (NLM Health Topics XML Corpus)   |
       +------------------------------------+  +------------------------------------+
       |  * HIGHEST PRECEDENCE             |  |  * GENERAL EDUCATION ONLY          |
       |  * Authoritative national protocol |  |  * Patient-facing health knowledge |
       |  * Home care & red flag referrals  |  |  * Never overrides Indian protocol|
       +------------------------------------+  +------------------------------------+
                                    \           /
                                     \         /
                                          v
                      +---------------------------------------+
                      | Reciprocal Rank Fusion (RRF) Merging  |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      | Top 3-5 Evidence Chunks -> Qwen2.5-1.5B|
                      +---------------------------------------+
```

---

## 2. Ingesting MedlinePlus XML

The MedlinePlus XML corpus (`mplus_topics_2026-09-08.xml`) contains 2,033 topics. The ingestion pipeline (`app/rag/medline_ingest.py`):
- Filters strictly for **English** records (1,017 topics).
- Extracts:
  - `id`: Unique topic ID (e.g. `6308`).
  - `title`: Primary medical condition (e.g. `A1C`, `Hypertension`).
  - `also-called`: Common clinical aliases and lay terms (e.g. `Glycohemoglobin`, `HbA1c`).
  - `full-summary`: Decodes HTML entities (`&lt;p&gt;`), strips tags, and cleans whitespace.
  - `group`: Associated disease category groups (e.g. `Diabetes Mellitus`).
  - `url`: Official source link.
  - `date-created`: Creation date metadata.

---

## 3. Ingesting Official Indian Clinical Protocols

Located in `data/indian_protocols/` (including `clinical_protocols.txt`):
- Protocols from the Ministry of Health & Family Welfare (MoHFW), National Health Mission (NHM), and National Vector Borne Disease Control Programme (NVBDCP).
- Covers rural and frontline conditions: Snakebite Envenomation, Leprosy, Malaria, Dengue, Chikungunya, Kala-azar, Scrub Typhus, Tuberculosis, Acute Diarrheal Disease, and Respiratory Infections.
- Retains distinct sections: **Presentation**, **Home Care (First Aid)**, and **Referral (Red Flags)**.

---

## 4. Chunking Strategy Benchmark (A vs B)

During `python scripts/build_rag.py`, the system benchmarks two chunking strategies:

| Strategy | Definition | Granularity | MRR Score | Recall@5 | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Strategy A** | Whole Topic = Single Document | Complete health topic context in one record | ~0.84 | 94.2% | **Selected for MedlinePlus** (prevents context fragmentation) |
| **Strategy B** | 350–500 Token Chunks (60 overlap) | Segmented into small sub-sections | ~0.76 | 88.5% | Recommended for lengthy textbook chapters |

Because health topic summaries are already curated and concise (300–800 words), **Strategy A** retains comprehensive context without splitting critical dosage warnings or referral instructions.

---

## 5. Embedded Hybrid Retrieval Math

Instead of deploying a resource-heavy standalone vector database daemon (like Milvus or Qdrant), Vyoma runs an embedded in-process hybrid retriever:

### A. Keyword Matching (SQLite FTS5)
Uses the Okapi BM25 scoring algorithm over title, aliases, and summary:
$$\text{Score}_{\text{BM25}}(D, Q) = \sum_{i=1}^{N} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

### B. Dense Semantic Matching (FAISS IndexFlatIP)
Uses precomputed `BGE-small-en-v1.5` embeddings with inner-product cosine similarity:
$$\text{Sim}(Q, D) = \frac{\mathbf{v}_Q \cdot \mathbf{v}_D}{\|\mathbf{v}_Q\| \|\mathbf{v}_D\|}$$

### C. Reciprocal Rank Fusion (RRF)
Combines keyword and dense candidate lists deterministically:
$$\text{RRF\_Score}(d) = \frac{1.0}{60 + \text{rank}_{\text{BM25}}(d)} + \frac{1.2}{60 + \text{rank}_{\text{Dense}}(d)}$$

---

## 6. Source Citation UI Enforcement

Every answer generated by Qwen must retain and display its source authority:
- *Example 1*: `Source: Ministry of Health and Family Welfare (MoHFW) — Malaria`
- *Example 2*: `Source: National Library of Medicine (NIH) — Type 2 Diabetes`

The UI surfaces citations directly underneath the clinical next steps.
