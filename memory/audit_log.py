# memory/audit_log.py
# Records every single action with timestamp
# Like CCTV footage of the entire process

import json
import os
import datetime

def save_audit_log(state, message_bus_log=None):
    """
    Automated audit trail generation
    Saves complete record of every agent decision
    """
    os.makedirs("outputs", exist_ok=True)
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    log = {
        "timestamp":        datetime.datetime.now().strftime(
                                "%d-%m-%Y %H:%M:%S"),
        "circular_no":      getattr(state, "circular_no", ""),
        "workflow_complete": getattr(state, "workflow_complete", False),
        "iterations_used":  getattr(state, "current_iteration", 0) + 1,
        "compliance_passed": getattr(state, "compliance_passed", False),
        "confidence_score": getattr(state, "confidence_score", 0),
        "fallback_triggered": getattr(state, "fallback_triggered", False),
        "agent_actions":    getattr(state, "audit_trail", []),
        "reasoning_steps":  getattr(state, "reasoning_steps", []),
        "errors":           getattr(state, "error_log", []),
        "message_bus_log":  message_bus_log or [],
        "episodic_memory":  getattr(state, "episodic_memory", [])
    }

    path = os.path.join("outputs", f"audit_log_{ts}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=2)

    print(f"  [Audit] Log saved: {path}")
    return path