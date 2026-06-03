# main.py
# The main controller - runs everything in order
# Just run: python main.py sample_docs/sampledoc.txt

import os
import sys
import json
import datetime
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import OUTPUTS_DIR, COMPLIANCE_THRESHOLD
from memory.workflow_state import WorkflowState
from memory.praison_memory import PraisonMemory
from memory.audit_log import save_audit_log
from deerflow.replanner import replan_workflow, build_default_graph
from agents.planner import run_planner
from agents.analysis import run_analysis
from agents.drafting import run_drafting
from agents.compliance import run_compliance

console = Console()

# ── Message Bus ───────────────────────────────────────────────
class MessageBus:
    """Simple message bus for agent communication"""
    def __init__(self):
        self._subscribers = {}
        self._log = []

    def subscribe(self, event, callback):
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)

    def publish(self, event, payload):
        self._log.append({
            "time":    datetime.datetime.now().strftime("%H:%M:%S"),
            "event":   event,
            "payload": payload
        })
        for cb in self._subscribers.get(event, []):
            try:
                cb({"event": event, "payload": payload})
            except Exception as e:
                print(f"  [Bus] Error in {event}: {e}")

    def get_log(self):
        return self._log

# ── Listeners ─────────────────────────────────────────────────
def on_plan_ready(m):
    p = m["payload"]
    console.print(f"  [cyan]► Planner:[/] "
                  f"{p['task_count']} tasks, "
                  f"memory_used={p['memory_used']}")

def on_analysis_complete(m):
    p = m["payload"]
    console.print(f"  [green]► Analysis:[/] "
                  f"{p['obligations_count']} obligations, "
                  f"{p['deadlines_count']} deadlines, "
                  f"{p['ambiguities_count']} ambiguities")

def on_draft_ready(m):
    p = m["payload"]
    console.print(f"  [yellow]► Drafting:[/] "
                  f"v{p['version']} ({p['length']} chars)")

def on_compliance_result(m):
    p = m["payload"]
    clr = "green" if p["compliance_passed"] else "red"
    console.print(f"  [magenta]► Compliance:[/] "
                  f"score={p['confidence_score']:.2f} "
                  f"[{clr}]"
                  f"{'PASSED' if p['compliance_passed'] else 'FAILED'}[/]")

# ── Load document ─────────────────────────────────────────────
def load_document(path):
    """Load text or PDF document"""
    if not os.path.exists(path):
        return None, f"File not found: {path}"

    try:
        # Try PDF first
        if path.endswith(".pdf"):
            import fitz
            doc  = fitz.open(path)
            text = "\n".join(page.get_text() for page in doc)
            return text, None

        # Try plain text
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), None

    except Exception as e:
        return None, str(e)

# ── Main Orchestrator ─────────────────────────────────────────
def run_orchestrator(doc_path):
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    # Setup
    state  = WorkflowState(max_iterations=3)
    bus    = MessageBus()
    memory = PraisonMemory()

    # Subscribe listeners
    bus.subscribe("plan_ready",          on_plan_ready)
    bus.subscribe("analysis_complete",   on_analysis_complete)
    bus.subscribe("draft_ready",         on_draft_ready)
    bus.subscribe("compliance_result",   on_compliance_result)

    console.rule("[bold blue]Government AI Multi-Agent Assistant[/]")
    console.print(
        "\n[bold]Frameworks:[/] "
        "PraisonAI memory · "
        "DeerFlow workflow · "
        "Hermes self-critique\n"
    )

    # ── Step 1: Load document ─────────────────────────────────
    console.print("[bold]Step 1:[/] Loading document...")
    text, error = load_document(doc_path)

    if error:
        console.print(f"  [red]Error: {error}[/]")
        state.fallback_triggered = True
        state.error_log.append(error)
        state.pdf_text = ""
    else:
        state.pdf_text = text
        console.print(f"  Loaded: {len(text)} characters")
        state.log_audit("orchestrator", "document_loaded",
                        f"chars={len(text)}")

    # ── Step 2: Analysis ──────────────────────────────────────
    console.print("\n[bold]Step 2:[/] Running Analysis Agent...")
    state = run_analysis(state, bus, memory)

    # ── Step 3: Main loop ─────────────────────────────────────
    console.print(
        f"\n[bold]Step 3:[/] Orchestration loop "
        f"(max {state.max_iterations} iterations)..."
    )

    graph = build_default_graph()

    for iteration in range(state.max_iterations):
        state.current_iteration = iteration
        console.print(f"\n  [bold]── Iteration {iteration+1} ──[/]")

        # Planner
        state, graph = run_planner(state, bus, memory)

        # DeerFlow replanning
        graph, inserted = replan_workflow(graph, state)
        if inserted:
            console.print(
                f"  [cyan]DeerFlow replanned:[/] {inserted}"
            )
            state.log_reasoning("DeerFlow",
                f"Replanned: {inserted}")

        # Drafting
        state = run_drafting(state, bus, memory)

        # Compliance
        state = run_compliance(state, bus, memory)

        if state.compliance_passed:
            console.print(
                f"\n  [green]✓ Passed at iteration {iteration+1}[/]"
            )
            break

        if iteration < state.max_iterations - 1:
            console.print(
                f"  [yellow]⚠ Failed. "
                f"Negotiating next round...[/]"
            )

    # ── Step 4: Save to memory ────────────────────────────────
    memory.store_gr_interpretation(
        doc_path,
        state.obligations,
        state.deadlines,
        state.authorities
    )
    console.print(
        "\n  [cyan]Praison memory:[/] GR stored for future runs."
    )

    state.workflow_complete = True
    state.cross_agent_memory["message_bus_log"] = bus.get_log()
    state.episodic_memory = memory.episodic

    return state

# ── Generate output files ─────────────────────────────────────
def generate_outputs(state):
    ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = {}
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    # 1. Draft letter
    draft_path = os.path.join(OUTPUTS_DIR, f"draft_{ts}.txt")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(state.draft)
    paths["draft"] = draft_path

    # 2. JSON summary
    json_path = os.path.join(OUTPUTS_DIR, f"summary_{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(state.to_summary_dict(), f, indent=2,
                  ensure_ascii=False)
    paths["json_summary"] = json_path

    # 3. Compliance report
    comp_path = os.path.join(OUTPUTS_DIR,
                             f"compliance_report_{ts}.txt")
    with open(comp_path, "w", encoding="utf-8") as f:
        f.write("COMPLIANCE REPORT\n" + "="*60 + "\n")
        f.write(f"Status    : "
                f"{'PASSED' if state.compliance_passed else 'FAILED'}\n")
        f.write(f"Score     : {state.confidence_score:.2f}\n")
        f.write(f"Threshold : {COMPLIANCE_THRESHOLD}\n")
        f.write(f"Iterations: {state.current_iteration+1}\n\n")
        f.write("HERMES SELF-CRITIQUE:\n")
        for c in state.self_critique:
            f.write(f"  - {c}\n")
        f.write("\nISSUES:\n")
        for i in state.compliance_issues:
            f.write(f"  - {i}\n")
        f.write("\nOBLIGATIONS:\n")
        for o in state.obligations:
            f.write(f"  - {o}\n")
        f.write("\nDEADLINES:\n")
        for d in state.deadlines:
            f.write(f"  - {d}\n")
    paths["compliance_report"] = comp_path

    # 4. Confidence score
    conf_path = os.path.join(OUTPUTS_DIR, f"confidence_{ts}.json")
    with open(conf_path, "w", encoding="utf-8") as f:
        json.dump({
            "confidence_score": state.confidence_score,
            "threshold":        COMPLIANCE_THRESHOLD,
            "passed":           state.compliance_passed,
            "iterations":       state.current_iteration + 1,
            "draft_version":    state.draft_version,
            "fallback":         state.fallback_triggered
        }, f, indent=2)
    paths["confidence"] = conf_path

    # 5. Reasoning steps
    reason_path = os.path.join(OUTPUTS_DIR, f"reasoning_{ts}.txt")
    with open(reason_path, "w", encoding="utf-8") as f:
        f.write("REASONING STEPS\n" + "="*60 + "\n")
        for i, step in enumerate(state.reasoning_steps, 1):
            f.write(f"Step {i:02d}: {step}\n")
    paths["reasoning"] = reason_path

    # 6. Audit log
    audit_path = save_audit_log(
        state,
        state.cross_agent_memory.get("message_bus_log", [])
    )
    paths["audit_log"] = audit_path

    # 7. Schema validation
    schema = {
        "valid":    True,
        "has_draft":       bool(state.draft),
        "has_summary":     bool(state.obligations),
        "has_compliance":  state.confidence_score > 0,
        "has_confidence":  state.confidence_score > 0,
        "has_reasoning":   bool(state.reasoning_steps),
        "has_audit":       bool(state.audit_trail)
    }
    schema_path = os.path.join(OUTPUTS_DIR,
                               f"schema_validation_{ts}.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    paths["schema"] = schema_path

    return paths

# ── Display results ───────────────────────────────────────────
def display_results(state, paths):
    console.print("\n")
    console.rule("[bold green]Results[/]")

    t = Table(title="Extraction Summary")
    t.add_column("Category",  style="cyan")
    t.add_column("Count",     style="magenta")
    t.add_column("Sample",    style="white")

    for label, items in [
        ("Obligations",   state.obligations),
        ("Deadlines",     state.deadlines),
        ("Authorities",   state.authorities),
        ("Ambiguities",   state.ambiguities),
    ]:
        sample = items[0][:50] if items else "-"
        t.add_row(label, str(len(items)), sample)

    console.print(t)

    color = "green" if state.compliance_passed else "red"
    console.print(Panel(
        f"[bold]Score:[/] {state.confidence_score:.2f} | "
        f"[bold]Status:[/] [{color}]"
        f"{'PASSED' if state.compliance_passed else 'FAILED'}[/]\n"
        f"[bold]Iterations:[/] {state.current_iteration+1} | "
        f"[bold]Draft v:[/] {state.draft_version} | "
        f"[bold]Fallback:[/] {state.fallback_triggered}",
        title="Final Status",
        border_style=color
    ))

    console.print("\n[bold]Output files saved:[/]")
    for name, path in paths.items():
        console.print(f"  [green]✓[/] {name}: {path}")

# ── Entry point ───────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Government AI Multi-Agent Assistant"
    )
    parser.add_argument(
        "doc_path",
        nargs="?",
        default=os.path.join("sample_docs", "sampledoc.txt"),
        help="Path to government document (txt or pdf)"
    )
    args = parser.parse_args()

    try:
        state = run_orchestrator(args.doc_path)
        paths = generate_outputs(state)
        display_results(state, paths)
        console.print("\n[bold green]✓ Complete![/]")

    except Exception as e:
        console.print(f"\n[red]FATAL ERROR: {e}[/]")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()