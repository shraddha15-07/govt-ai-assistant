# Design Note — Government AI Multi-Agent Assistant

---

## 1. Model Selection Rationale

### Primary Model: Nous-Hermes-2-Mistral-7B-DPO (Q3_K_S GGUF)

We selected **Nous-Hermes-2-Mistral-7B-DPO** as our primary model for the
following reasons:

**Instruction Following:**
Hermes-2 is specifically fine-tuned on high-quality instruction-response
pairs using Direct Preference Optimization (DPO). This makes it exceptional
at following structured prompts — critical for government document processing
where output format must be precise and consistent.

**Formal Writing Quality:**
The model produces formal, professional text that closely matches the style
required for official government correspondence. This was verified during
testing where the model consistently produced properly structured official
letters without requiring heavy prompt engineering.

**Local Deployment:**
The Q3_K_S quantized GGUF variant runs efficiently on CPU-only hardware
via LM Studio. At 3.16 GB, it fits comfortably within 8 GB RAM while
maintaining 80%+ of the full model's quality.

**Hermes Agent Alignment:**
The assignment specifically requires Hermes Agent capabilities — this model
IS the Hermes Agent. Its meta-reasoning capabilities enable the self-critique
loop in the Compliance Agent, where the model generates counter-arguments
against its own output without human feedback.

**No External APIs:**
Running via LM Studio on localhost:1234 satisfies the assignment constraint
of no external inference APIs. All processing happens on the local machine.

---

## 2. Memory Design

We implemented a two-tier memory system inspired by PraisonAI's memory
architecture:

### Long-Term Memory (Persistent across runs)

**File:** `memory/praison_memory.py`
**Storage:** `memory/memory.json`

Long-term memory stores GR interpretations permanently across sessions.
Each entry contains:
```json
{
  "timestamp": "02-06-2026 10:30",
  "source": "sample_docs/sample_gr.txt",
  "obligations": ["Implement digital record keeping..."],
  "deadlines": ["31st March 2024"],
  "authorities": ["Chief Secretary, Maharashtra"]
}
```

**Purpose:** When the same type of circular appears again, the Analysis
Agent loads past interpretations and skips redundant extraction. This
reduces processing time and improves consistency across similar documents.

**Few-shot adaptation:** The `get_few_shot_examples()` method retrieves
the last 3 processed GRs and injects them into the Drafting Agent's prompt
as examples. This is PraisonAI's cross-agent memory enabling few-shot
policy adaptation without retraining.

### Episodic Memory (Per-session)

Episodic memory logs every agent action during the current session in RAM:
```python
[
  {"time": "10:30:01", "agent": "planner", "action": "Plan created"},
  {"time": "10:30:05", "agent": "analysis", "action": "Found 3 deadlines"},
  {"time": "10:30:12", "agent": "drafting", "action": "Draft v1 written"},
  {"time": "10:30:18", "agent": "compliance", "action": "Score: 1.00 PASSED"}
]
```

**Purpose:** Episodic memory feeds directly into the audit trail generation
and provides agents with context about what happened earlier in the same run.

---

## 3. How Hermes Agent + DeerFlow 2 + PraisonAI Are Combined

### Hermes Agent

**Implementation:** Nous-Hermes-2-Mistral-7B-DPO model via LM Studio

Hermes Agent powers three distinct behaviours:

**a) In-context learning (Analysis Agent)**
The Analysis Agent passes few-shot examples from PraisonAI memory into
the Hermes prompt, allowing it to immediately adapt to new circular types
without retraining. A circular about "Digital Records" gets processed with
examples from similar past circulars injected into context.

**b) Few-shot drafting (Drafting Agent)**
The Drafting Agent uses a hardcoded few-shot example of a perfect official
letter plus dynamically retrieved examples from memory. This guides Hermes
to produce correctly formatted government correspondence every time.

**c) Meta-reasoning self-critique (Compliance Agent)**
The Compliance Agent uses Hermes in a unique "adversarial" mode — it asks
the model to argue AGAINST its own draft, finding weaknesses and compliance
gaps. This generates counter-arguments automatically without human feedback,
which is the core of Hermes-driven self-critique.

### DeerFlow 2

**Implementation:** `deerflow/replanner.py`

DeerFlow 2 is implemented as a workflow graph engine with conditional
branching and dynamic node insertion:

**a) Default workflow graph**
n1 (planner) → n2 (analysis) → n3 (drafting) → n4 (compliance)

**b) Dynamic replanning triggers**
- Ambiguities detected → inserts `clarification` node after analysis
- Errors or fallback triggered → inserts `fallback_handling` node after planner
- Contradictions found → inserts `contradiction_check` node after analysis

**c) Visual flow engine behaviour**
Each node carries metadata: `name`, `agent`, `has_condition`, `executed`,
`inserted`. This allows the system to track exactly which steps ran,
which were dynamically added, and which were conditional — matching
DeerFlow 2's visual flow engine concept.

### PraisonAI

**Implementation:** `memory/praison_memory.py`

PraisonAI enables four key behaviours:

**a) Cross-agent memory**
All four agents share the same PraisonMemory instance. When Analysis Agent
stores a GR interpretation, Drafting Agent can immediately retrieve it as
a few-shot example in the same run.

**b) Multi-round negotiation**
The main orchestration loop in `main.py` runs up to 3 iterations of
Drafting ↔ Compliance negotiation. Each iteration, the Compliance Agent
passes specific issues back to the Drafting Agent, which rewrites the
draft addressing those issues. This converges on a policy-compliant draft.

**c) Long-term consistency**
By remembering past GR interpretations, the system avoids conflicting
interpretations of similar circulars across different sessions.

**d) Episodic session logging**
Every agent action is logged to episodic memory and later saved to the
automated audit trail — the complete trace of every decision.

### Combined Behaviour

The three frameworks interact to produce emergent capabilities:
PraisonAI memory feeds few-shot examples
↓
Hermes uses them for better drafting
↓
DeerFlow detects if output is ambiguous
↓
DeerFlow inserts clarification step
↓
Hermes re-analyzes with extra context
↓
PraisonAI logs the whole session to audit trail

This combination produces behaviour none of the three could achieve alone:
adaptive processing of new document types without retraining, dynamic
workflow adjustment based on content, and self-improving drafts through
multi-round negotiation.

---

## 4. Failure Case Handling

### Case 1: Empty or very short document
**Detection:** `len(state.pdf_text.strip()) < 50`
**Handling:** Fallback values set automatically, ambiguity logged,
DeerFlow inserts fallback_handling step, processing continues with
default values rather than crashing.

### Case 2: AI model unavailable (LM Studio not running)
**Detection:** `except Exception as e` around every API call
**Handling:** Each agent has hardcoded fallback responses. The system
completes the full pipeline using rule-based outputs instead of AI outputs.
Error logged to `state.error_log` and `audit_log.json`.

### Case 3: Compliance fails after 3 iterations
**Detection:** `iteration == max_iterations - 1` and `not compliance_passed`
**Handling:** System saves the best draft achieved, marks status as FAILED
in outputs, records all compliance issues in compliance_report. Officer
is informed of specific issues to fix manually.

### Case 4: Missing circular number or date
**Detection:** GR Analyzer Tool returns empty string for circular_no or date
**Handling:** Ambiguity added to `state.ambiguities`, DeerFlow inserts
clarification step, draft uses "N/A" placeholder, compliance report flags
the missing field.

### Case 5: PDF reading failure
**Detection:** `except Exception` in `load_document()`
**Handling:** Error logged, `state.fallback_triggered = True`, system
attempts to process with empty text, produces error report in outputs.

### Case 6: Contradictory documents
**Detection:** Two documents provided via `--pdf2` argument
**Handling:** Comparator tool detects contradicting clauses, stores in
`state.contradictions`, DeerFlow inserts contradiction_check step,
compliance report highlights contradictions.

---

## 5. Future Scalability Considerations

### Short-term (1-3 months)

**Batch processing:**
Add support for processing multiple GR documents in a queue. The current
PraisonAI memory system already supports this — each document's interpretation
is stored and can inform the next.

**Better PDF support:**
Integrate table extraction from PDFs using pdfplumber. Government circulars
often contain tabular data with deadlines that the current text extraction
misses.

**Multi-language support:**
Add Marathi and Hindi language support using a multilingual model variant.
Maharashtra government circulars are often issued in Marathi.

### Medium-term (3-6 months)

**Vector memory database:**
Replace the current JSON-based memory with ChromaDB or FAISS for semantic
search across thousands of past GRs. This enables "find similar circulars"
functionality.

**Department-specific compliance rules:**
Different government departments have different rule sets. Add a
department-specific compliance engine that loads the correct rulebook
based on the issuing authority detected by the Analysis Agent.

**Email integration:**
Connect the Drafting Agent output directly to an email client so approved
drafts can be sent automatically after officer review.

### Long-term (6-12 months)

**Multi-department deployment:**
Package as a Docker container for deployment across multiple government
offices. Each office maintains its own memory store while sharing the
base model.

**Fine-tuned government model:**
Fine-tune Hermes-2 on a corpus of Maharashtra government circulars and
official responses to improve domain-specific performance without
increasing model size.

**Real-time circular monitoring:**
Connect to the Maharashtra government portal to automatically detect new
circulars, process them overnight, and have draft responses ready for
officer review the next morning.

**Audit compliance dashboard:**
Build a Streamlit dashboard that visualizes audit logs across all
processed documents, showing compliance trends, common failure points,
and officer workload reduction metrics.