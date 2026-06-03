# tools/gr_analyzer.py
# This tool scans the document and finds important information automatically

import re

def analyze_gr(text):
    """
    Tool 1: GR Analyzer
    Scans government document and extracts key information
    like a highlighter finding important parts automatically
    """
    
    results = {
        "circular_no": "",
        "date": "",
        "subject": "",
        "deadlines": [],
        "authorities": [],
        "actions": [],
        "applicability": [],
        "ambiguities": [],
        "penalty": ""
    }

    # Find circular number
    circular_match = re.search(
        r'circular\s*no\.?\s*([A-Z0-9/\-]+)', 
        text, re.IGNORECASE
    )
    if circular_match:
        results["circular_no"] = circular_match.group(1).strip()

    # Find date
    date_match = re.search(
        r'date[:\s]+(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})',
        text, re.IGNORECASE
    )
    if date_match:
        results["date"] = date_match.group(1).strip()

    # Find subject
    subject_match = re.search(
        r'subject[:\s]+(.+?)(?:\n|$)',
        text, re.IGNORECASE
    )
    if subject_match:
        results["subject"] = subject_match.group(1).strip()

    # Find deadlines - looks for dates with "by" before them
    deadline_matches = re.findall(
        r'by\s+(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})',
        text, re.IGNORECASE
    )
    results["deadlines"] = list(set(deadline_matches))

    # Find authorities
    authority_keywords = [
        "chief secretary", "collector", "director",
        "secretary", "commissioner", "head of department"
    ]
    for keyword in authority_keywords:
        if keyword.lower() in text.lower():
            results["authorities"].append(keyword.title())

    # Find actions - numbered points
    action_matches = re.findall(
        r'\d+\.\s+(.+?)(?:\n|$)',
        text
    )
    results["actions"] = [a.strip() for a in action_matches if len(a.strip()) > 10]

    # Find applicability
    applicability_match = re.search(
        r'(all\s+[\w\s]+(?:collectors|departments|offices|officers))',
        text, re.IGNORECASE
    )
    if applicability_match:
        results["applicability"].append(applicability_match.group(1).strip())

    # Find penalty
    penalty_match = re.search(
        r'penalty[:\s]+(.+?)(?:\n|$)',
        text, re.IGNORECASE
    )
    if penalty_match:
        results["penalty"] = penalty_match.group(1).strip()

    # Check for ambiguities
    if not results["circular_no"]:
        results["ambiguities"].append("Circular number not found")
    if not results["deadlines"]:
        results["ambiguities"].append("No deadlines found")
    if not results["subject"]:
        results["ambiguities"].append("Subject not clearly stated")
    if len(text.strip()) < 100:
        results["ambiguities"].append("Document seems incomplete")

    return results


def format_analysis(results):
    """Print the analysis results nicely"""
    print("\n" + "="*50)
    print("📋 GR ANALYZER TOOL RESULTS")
    print("="*50)
    print(f"Circular No : {results['circular_no'] or 'Not found'}")
    print(f"Date        : {results['date'] or 'Not found'}")
    print(f"Subject     : {results['subject'] or 'Not found'}")
    print(f"Penalty     : {results['penalty'] or 'Not found'}")
    
    print("\nDeadlines found:")
    for d in results["deadlines"]:
        print(f"  - {d}")
    
    print("\nAuthorities:")
    for a in results["authorities"]:
        print(f"  - {a}")
    
    print("\nActions required:")
    for i, action in enumerate(results["actions"], 1):
        print(f"  {i}. {action}")
    
    print("\nApplicability:")
    for a in results["applicability"]:
        print(f"  - {a}")
    
    if results["ambiguities"]:
        print("\n⚠️  Ambiguities detected:")
        for amb in results["ambiguities"]:
            print(f"  - {amb}")
    
    return results