# memory/workflow_state.py
# Shared memory that all agents read and write to
# Like a shared whiteboard in the office

import datetime

class WorkflowState:
    """
    Central shared state passed between all agents
    Every agent reads from this and writes results to it
    """

    def __init__(self, text="", max_iterations=3):
        # Document info
        self.pdf_text         = text
        self.pdf_text2        = ""
        self.circular_no      = ""
        self.date             = ""
        self.subject          = ""

        # Extracted information
        self.obligations      = []
        self.deadlines        = []
        self.authorities      = []
        self.applicability    = []
        self.ambiguities      = []
        self.contradictions   = []
        self.penalty          = ""

        # Draft info
        self.draft            = ""
        self.draft_version    = 0

        # Compliance info
        self.compliance_passed  = False
        self.compliance_issues  = []
        self.confidence_score   = 0.0
        self.self_critique      = []

        # Workflow control
        self.current_iteration  = 0
        self.max_iterations     = max_iterations
        self.workflow_complete  = False
        self.fallback_triggered = False
        self.workflow_graph     = []

        # Logging
        self.audit_trail        = []
        self.reasoning_steps    = []
        self.error_log          = []
        self.episodic_memory    = []
        self.cross_agent_memory = {}

    def log_audit(self, agent, action, detail=""):
        """Log an action to the audit trail"""
        self.audit_trail.append({
            "time":   datetime.datetime.now().strftime("%H:%M:%S"),
            "agent":  agent,
            "action": action,
            "detail": detail
        })

    def log_reasoning(self, agent, step):
        """Log a reasoning step"""
        self.reasoning_steps.append(
            f"[{agent}] {step}"
        )

    def to_summary_dict(self):
        """Convert state to JSON-friendly dictionary"""
        return {
            "circular_no":       self.circular_no,
            "date":              self.date,
            "subject":           self.subject,
            "obligations":       self.obligations,
            "deadlines":         self.deadlines,
            "authorities":       self.authorities,
            "applicability":     self.applicability,
            "ambiguities":       self.ambiguities,
            "contradictions":    self.contradictions,
            "penalty":           self.penalty,
            "compliance_passed": self.compliance_passed,
            "confidence_score":  self.confidence_score,
            "draft_version":     self.draft_version,
            "iterations_used":   self.current_iteration + 1,
            "fallback_triggered":self.fallback_triggered,
            "self_critique":     self.self_critique,
            "reasoning_steps":   self.reasoning_steps,
            "workflow_graph":    self.workflow_graph
        }