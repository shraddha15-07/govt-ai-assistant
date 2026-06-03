# agents/compliance.py
# Agent 4: The Compliance Checker
# Checks if the draft follows all rules
# If not, sends feedback back to Agent 3 to fix it

import openai
from config import LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, HERMES_MODEL
from tools.compliance_engine import validate_compliance, print_compliance_report

client = openai.OpenAI(
    base_url=LM_STUDIO_BASE_URL,
    api_key=LM_STUDIO_API_KEY
)

def run_compliance(state, bus, memory):
    """
    Compliance Agent - validates draft against policy rules
    Uses Hermes self-critique (meta-reasoning)
    Uses Compliance Engine Tool for rule checking
    """
    print("\n" + "="*50)
    print("🔴 AGENT 4: COMPLIANCE checking...")
    print("="*50)

    state.log_audit("compliance", "started",
                    f"checking_draft_v{state.draft_version}")
    memory.log_episode("compliance",
                       f"Checking draft v{state.draft_version}")

    # Step 1: Run Compliance Engine Tool
    print("  [Tool] Running Compliance Engine...")
    analysis_dict = {
        "circular_no":  state.circular_no,
        "subject":      state.subject,
        "deadlines":    state.deadlines,
        "authorities":  state.authorities,
        "actions":      state.obligations
    }
    report = validate_compliance(state.draft, analysis_dict)
    print_compliance_report(report)

    # Step 2: Hermes self-critique
    # AI argues against its own output to find hidden problems
    print("\n  [Hermes] Running self-critique...")
    critique = []
    try:
        prompt = f"""You are a strict government compliance officer.
Review this draft letter and find any problems.

Draft:
{state.draft[:800]}

Original circular subject: {state.subject}
Required actions: {state.obligations}
Required deadlines: {state.deadlines}

List up to 3 specific problems with this draft.
If the draft is good write: NO ISSUES FOUND
Be very specific and brief."""

        response = client.chat.completions.create(
            model=HERMES_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a strict government compliance "
                            "officer. Find problems in official letters."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.2
        )
        critique_text = response.choices[0].message.content
        
        if "NO ISSUES FOUND" not in critique_text.upper():
            # Parse critique into list
            lines = critique_text.strip().split("\n")
            critique = [
                l.strip("•-123456789. ").strip()
                for l in lines
                if len(l.strip()) > 10
            ][:3]
            print(f"  [Hermes] Found {len(critique)} issues")
        else:
            print("  [Hermes] No issues found!")

        state.log_reasoning("compliance",
            f"Hermes critique: {critique_text[:100]}")

    except Exception as e:
        print(f"  [Compliance] AI unavailable: {e}")
        state.error_log.append(f"Compliance AI error: {e}")
        state.fallback_triggered = True

    # Step 3: Combine tool results + AI critique
    state.self_critique      = critique
    state.confidence_score   = report["confidence"]
    state.compliance_passed  = report["passed"]
    state.compliance_issues  = report["issues"] + critique

    state.log_audit("compliance", "complete",
        f"score={state.confidence_score:.2f}, "
        f"passed={state.compliance_passed}, "
        f"hermes_issues={len(critique)}")

    # Publish to message bus
    bus.publish("compliance_result", {
        "confidence_score":  state.confidence_score,
        "compliance_passed": state.compliance_passed,
        "hermes_critique":   critique
    })

    if state.compliance_passed:
        print(f"\n✅ COMPLIANCE PASSED! "
              f"Score: {state.confidence_score*100:.1f}%")
    else:
        print(f"\n❌ COMPLIANCE FAILED! "
              f"Score: {state.confidence_score*100:.1f}%")
        print(f"  Issues to fix: {len(state.compliance_issues)}")
        if state.compliance_issues:
            for issue in state.compliance_issues[:3]:
                print(f"  • {issue}")

    memory.log_episode("compliance",
        f"Score: {state.confidence_score:.2f} "
        f"({'PASSED' if state.compliance_passed else 'FAILED'})")

    return state