# tools/compliance_engine.py
# Tool 2: Checks if the draft letter follows all government rules

def validate_compliance(draft_text, analysis_results):
    """
    Compliance Validation Engine
    Checks draft against policy rules like a strict proofreader
    Returns a detailed report with score
    """
    
    checks = []
    score = 0
    total_rules = 10

    # Rule 1 - Circular number present
    if analysis_results.get("circular_no") and \
       analysis_results["circular_no"] in draft_text:
        checks.append({"rule": "Circular number present", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Circular number present", "passed": False,
                       "fix": "Add circular number to draft"})

    # Rule 2 - Subject mentioned
    subject = analysis_results.get("subject", "")
    subject_words = subject.split()[:3]
    if any(word.lower() in draft_text.lower() for word in subject_words):
        checks.append({"rule": "Subject mentioned", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Subject mentioned", "passed": False,
                       "fix": "Mention the subject clearly"})

    # Rule 3 - Date present
    if "2024" in draft_text or "2025" in draft_text or "2026" in draft_text:
        checks.append({"rule": "Date present", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Date present", "passed": False,
                       "fix": "Add current date to draft"})

    # Rule 4 - All actions listed
    actions = analysis_results.get("actions", [])
    actions_found = 0
    for action in actions:
        first_words = " ".join(action.split()[:2]).lower()
        if first_words in draft_text.lower():
            actions_found += 1
    if actions and actions_found >= len(actions) // 2:
        checks.append({"rule": "Actions listed", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Actions listed", "passed": False,
                       "fix": "List all required actions in draft"})

    # Rule 5 - Deadlines mentioned
    deadlines = analysis_results.get("deadlines", [])
    if deadlines and any(
        d.split()[0] in draft_text for d in deadlines
    ):
        checks.append({"rule": "Deadlines mentioned", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Deadlines mentioned", "passed": False,
                       "fix": "Add all deadlines to draft"})

    # Rule 6 - Proper greeting
    greetings = ["sir/madam", "sir", "madam", "respected"]
    if any(g in draft_text.lower() for g in greetings):
        checks.append({"rule": "Proper greeting present", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Proper greeting present", "passed": False,
                       "fix": "Add proper greeting (Sir/Madam)"})

    # Rule 7 - Proper sign off
    signoffs = ["yours faithfully", "yours sincerely", "yours truly"]
    if any(s in draft_text.lower() for s in signoffs):
        checks.append({"rule": "Proper sign-off present", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Proper sign-off present", "passed": False,
                       "fix": "Add 'Yours faithfully' at the end"})

    # Rule 8 - Authority acknowledged
    authorities = analysis_results.get("authorities", [])
    if authorities and any(
        a.lower() in draft_text.lower() for a in authorities
    ):
        checks.append({"rule": "Authority acknowledged", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Authority acknowledged", "passed": False,
                       "fix": "Mention the issuing authority"})

    # Rule 9 - Government header present
    gov_headers = ["government", "office of", "department"]
    if any(h in draft_text.lower() for h in gov_headers):
        checks.append({"rule": "Government header present", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Government header present", "passed": False,
                       "fix": "Add government office header"})

    # Rule 10 - Minimum length check
    if len(draft_text.strip()) >= 200:
        checks.append({"rule": "Draft has sufficient content", "passed": True})
        score += 1
    else:
        checks.append({"rule": "Draft has sufficient content", "passed": False,
                       "fix": "Draft is too short, add more detail"})

    # Calculate final score
    confidence = score / total_rules
    passed = confidence >= 0.80

    # Get list of issues to fix
    issues = [
        c["fix"] for c in checks
        if not c["passed"] and "fix" in c
    ]

    # Build full report
    report = {
        "checks":     checks,
        "score":      score,
        "total":      total_rules,
        "confidence": confidence,
        "passed":     passed,
        "issues":     issues,
        "status":     "APPROVED" if passed else "NEEDS REVISION"
    }

    return report


def print_compliance_report(report):
    """Print compliance report nicely in terminal"""
    print("\n" + "="*50)
    print("🔴 COMPLIANCE ENGINE REPORT")
    print("="*50)
    
    for check in report["checks"]:
        icon = "✅" if check["passed"] else "❌"
        print(f"{icon} {check['rule']}")
        if not check["passed"] and "fix" in check:
            print(f"   → Fix: {check['fix']}")
    
    print("-"*50)
    print(f"SCORE     : {report['score']}/{report['total']}")
    print(f"CONFIDENCE: {report['confidence']*100:.1f}%")
    print(f"STATUS    : {report['status']}")
    
    if report["issues"]:
        print("\nIssues to fix:")
        for issue in report["issues"]:
            print(f"  • {issue}")
    
    return report