# Government AI Multi-Agent Assistant

A locally running multi-agent AI system that simulates an internal
Government Officer Assistant. Processes Government Resolutions (GRs)
and Circulars using four coordinated AI agents powered by
Nous-Hermes-2, PraisonAI memory, and DeerFlow workflow graph.

## Architecture

| Agent | Role | Framework |
|---|---|---|
| Planner | Breaks task into steps, builds workflow | DeerFlow 2 |
| Analysis | Extracts obligations, deadlines, authorities | Hermes in-context |
| Drafting | Writes formal government response | Hermes few-shot |
| Compliance | Validates draft, runs self-critique | Hermes meta-reasoning |

## Requirements

- Windows 10/11
- Python 3.10 or higher
- LM Studio with Nous-Hermes-2-Mistral-7B-DPO loaded
- 8 GB RAM minimum
- 4 GB disk space for model

## Setup

### Step 1 - LM Studio
1. Download LM Studio from https://lmstudio.ai
2. Search for `nous-hermes-2-mistral-7b-dpo`
3. Download Q3_K_S or Q4_K_M version
4. Go to Local Server tab → Start Server

### Step 2 - Install dependencies