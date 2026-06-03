# agents/planner.py
# Agent 1: The Planner
# Reads the document and decides what steps are needed
# Like a team manager making a to-do list

import openai
import datetime
from config import LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, HERMES_MODEL
from deerflow.replanner import build_default_graph, graph_to_dict

client = openai.OpenAI(
    base_url=LM_STUDIO_BASE_URL,
    api_key=LM_STUDIO_API_KEY
)

def run_planner(state, bus, memory):
    """
    Planner Agent - breaks task into subtasks
    Uses DeerFlow graph for workflow management
    """
    print("\n" + "="*50)
    print("🟣 AGENT 1: PLANNER starting...")
    print("="*50)

    state.log_audit("planner", "started")
    memory.log_episode("planner", "Planning started")

    # Check memory for similar past GRs
    similar = memory.get_similar_gr(state.subject or "government")
    memory_hint = ""
    if similar:
        memory_hint = (
            f"\nNote: Similar GR was processed before. "
            f"Deadlines were: {similar.get('deadlines', [])}"
        )
        print(f"  [Memory] Found similar past GR!")
        state.log_reasoning("planner",
            "Found similar GR in memory - using past context")

    # Build default workflow graph
    graph = build_default_graph()

    # Create plan using AI
    try:
        doc_preview = state.pdf_text[:500] if state.pdf_text else \
                      "No document provided"

        prompt = f"""You are a government office planner.
A document has been received. Create a brief processing plan.
{memory_hint}

Document preview:
{doc_preview}

List exactly 4 steps to process this document.
Be very brief - one line per step."""

        response = client.chat.completions.create(
            model=HERMES_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a government office planner. "
                            "Be brief and precise."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        ai_plan = response.choices[0].message.content

    except Exception as e:
        print(f"  [Planner] AI unavailable: {e}")
        print(f"  [Planner] Using default plan")
        state.fallback_triggered = True
        state.error_log.append(f"Planner AI error: {e}")
        ai_plan = """Step 1: Extract key information from document
Step 2: Identify deadlines and authorities
Step 3: Draft official response
Step 4: Validate compliance"""

    # Always use clean structured plan
    clean_plan = [
        "Step 1: Extract key information from document",
        "Step 2: Identify all deadlines and responsible authorities",
        "Step 3: Draft official response in proper format",
        "Step 4: Validate draft against compliance rules"
    ]

    state.log_reasoning("planner", f"Plan created: {len(clean_plan)} steps")
    state.log_audit("planner", "plan_created",
                    f"steps={len(clean_plan)}")

    # Save graph to state
    state.workflow_graph = graph_to_dict(graph)

    # Publish to message bus
    bus.publish("plan_ready", {
        "task_count":  len(clean_plan),
        "graph_nodes": len(graph),
        "memory_used": similar is not None
    })

    print("✅ Planner done!")
    for step in clean_plan:
        print(f"  {step}")

    memory.log_episode("planner", "Plan ready")
    return state, graph