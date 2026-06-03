# agents/analysis.py
# Agent 2: The Analysis Agent
# Reads document carefully and extracts all important information
# Like a careful reader with a highlighter

import openai
from config import LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, HERMES_MODEL
from tools.gr_analyzer import analyze_gr, format_analysis

client = openai.OpenAI(
    base_url=LM_STUDIO_BASE_URL,
    api_key=LM_STUDIO_API_KEY
)

def run_analysis(state, bus, memory):
    """
    Analysis Agent - extracts policy content
    Uses GR Analyzer Tool for pattern matching
    Uses Hermes AI for deeper understanding
    """
    print("\n" + "="*50)
    print("🟢 AGENT 2: ANALYSIS starting...")
    print("="*50)

    state.log_audit("analysis", "started")
    memory.log_episode("analysis", "Analysis started")

    # Handle empty document
    if not state.pdf_text or len(state.pdf_text.strip()) < 50:
        print("  [Analysis] ⚠️ Document is empty or too short!")
        print("  [Analysis] Triggering fallback behavior...")
        state.fallback_triggered = True
        state.ambiguities.append("Document is empty or incomplete")
        state.error_log.append("Empty document received")
        state.log_reasoning("analysis",
            "Fallback triggered: document too short")
        _set_fallback_values(state)
        return state

    # Step 1: Use GR Analyzer Tool
    print("  [Tool] Running GR Analyzer Tool...")
    tool_results = analyze_gr(state.pdf_text)
    format_analysis(tool_results)

    # Step 2: Use AI for deeper analysis
    print("\n  [AI] Running Hermes deep analysis...")
    try:
        few_shot = memory.get_few_shot_examples()
        few_shot_text = f"\nPast examples:\n{few_shot}" \
                        if few_shot else ""

        prompt = f"""Analyze this government document and extract:
1. Main subject in one line
2. All deadlines (format: date - action)
3. Who issued it (authority)
4. What actions are required (numbered list)
5. Who must comply (applicability)
{few_shot_text}

Document:
{state.pdf_text[:1000]}

Be precise and brief."""

        response = client.chat.completions.create(
            model=HERMES_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a government document analyst. "
                            "Extract information precisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.2
        )
        ai_analysis = response.choices[0].message.content
        print(f"  [AI] Analysis complete")
        state.log_reasoning("analysis", f"AI extracted: {ai_analysis[:100]}")

    except Exception as e:
        print(f"  [Analysis] AI unavailable: {e}")
        state.error_log.append(f"Analysis AI error: {e}")
        state.fallback_triggered = True

    # Step 3: Save results to state
    state.circular_no  = tool_results["circular_no"]
    state.date         = tool_results["date"]
    state.subject      = tool_results["subject"]
    state.deadlines    = tool_results["deadlines"]
    state.authorities  = tool_results["authorities"]
    state.obligations  = tool_results["actions"]
    state.applicability = tool_results["applicability"]
    state.ambiguities  = tool_results["ambiguities"]
    state.penalty      = tool_results["penalty"]

    state.log_audit("analysis", "complete",
        f"deadlines={len(state.deadlines)}, "
        f"actions={len(state.obligations)}, "
        f"ambiguities={len(state.ambiguities)}")

    # Publish to message bus
    bus.publish("analysis_complete", {
        "obligations_count": len(state.obligations),
        "deadlines_count":   len(state.deadlines),
        "ambiguities_count": len(state.ambiguities)
    })

    print("✅ Analysis done!")
    memory.log_episode("analysis",
        f"Found {len(state.deadlines)} deadlines, "
        f"{len(state.obligations)} actions")
    return state


def _set_fallback_values(state):
    """Set default values when document is missing or unclear"""
    state.circular_no   = "UNKNOWN"
    state.subject       = "Unknown subject - document unclear"
    state.deadlines     = ["No deadlines found"]
    state.authorities   = ["Unknown authority"]
    state.obligations   = ["Review document manually"]
    state.applicability = ["All departments"]