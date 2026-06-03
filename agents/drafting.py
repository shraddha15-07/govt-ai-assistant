# agents/drafting.py
# Agent 3: The Drafting Agent
# Writes the official government letter
# Like a professional letter writer

import openai
import datetime
from config import LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, HERMES_MODEL

client = openai.OpenAI(
    base_url=LM_STUDIO_BASE_URL,
    api_key=LM_STUDIO_API_KEY
)

# Few-shot example - shows AI what a good letter looks like
FEW_SHOT_EXAMPLE = """
EXAMPLE OF GOOD OFFICIAL LETTER:

GOVERNMENT OF MAHARASHTRA
Office of the District Collector, Pune
Date: 15 March 2024

SUBJECT: Acknowledgement of Circular No. XYZ/2024/CR-10

Sir/Madam,

With reference to circular No. XYZ/2024/CR-10 dated 1st January 2024
regarding "Implementation of New Policy", this office hereby acknowledges
receipt of the same and confirms compliance with all directives.

The following actions will be taken as directed:
1. Action one will be completed
2. Action two will be completed

All deadlines will be strictly adhered to.

Yours faithfully,

District Collector
Government of Maharashtra
"""

def run_drafting(state, bus, memory):
    """
    Drafting Agent - generates official format output
    Uses Hermes few-shot learning for better quality
    Uses template for consistent government format
    """
    print("\n" + "="*50)
    print("🔵 AGENT 3: DRAFTING starting...")
    print("="*50)

    state.draft_version += 1
    state.log_audit("drafting", "started",
                    f"version={state.draft_version}")
    memory.log_episode("drafting",
                       f"Drafting v{state.draft_version} started")

    # Get feedback from previous compliance check if any
    feedback = ""
    if state.compliance_issues:
        feedback = (
            "\nPrevious draft had these issues - fix them:\n" +
            "\n".join(f"- {i}" for i in state.compliance_issues)
        )
        print(f"  [Drafting] Fixing {len(state.compliance_issues)} "
              f"issues from compliance agent...")
        state.log_reasoning("drafting",
            f"Received feedback: {state.compliance_issues}")

    # Get few-shot examples from memory
    few_shot = memory.get_few_shot_examples()

    # Step 1: Generate content using Hermes AI
    try:
        prompt = f"""Write a short official government acknowledgement.

{FEW_SHOT_EXAMPLE}

Now write a NEW letter using this information:
- Circular No: {state.circular_no or 'N/A'}
- Date: {state.date or 'N/A'}
- Subject: {state.subject or 'N/A'}
- Authority: {', '.join(state.authorities) if state.authorities else 'N/A'}
{feedback}

Write ONLY the middle paragraph (2-3 sentences).
Do not repeat the template. Just write the body content."""

        response = client.chat.completions.create(
            model=HERMES_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a senior government officer "
                            "writing formal letters. Be precise "
                            "and professional."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        ai_content = response.choices[0].message.content.strip()
        state.log_reasoning("drafting",
            f"AI generated content: {ai_content[:80]}")

    except Exception as e:
        print(f"  [Drafting] AI unavailable: {e}")
        state.error_log.append(f"Drafting AI error: {e}")
        state.fallback_triggered = True
        ai_content = (
            "This office acknowledges receipt of the circular and "
            "confirms that all directives will be implemented as "
            "specified within the given timelines."
        )

    # Step 2: Build complete official letter using template
    today = datetime.datetime.now().strftime("%d %B %Y")

    actions_text = ""
    for i, action in enumerate(state.obligations, 1):
        actions_text += f"\n  {i}. {action}"

    deadlines_text = ""
    for deadline in state.deadlines:
        deadlines_text += f"\n  • {deadline}"

    # Official template format
    draft = f"""
GOVERNMENT OF MAHARASHTRA
Office of the District Collector
Date: {today}

SUBJECT: Acknowledgement and Compliance - Circular No. {state.circular_no or 'N/A'}

Sir/Madam,

With reference to the circular No. {state.circular_no or 'N/A'} \
dated {state.date or 'N/A'} regarding "{state.subject or 'N/A'}", \
this office hereby acknowledges receipt of the same.

{ai_content}

The following actions will be undertaken as directed:
{actions_text}

The deadlines as specified will be strictly adhered to:
{deadlines_text}

This office assures full compliance with the directives issued by \
{', '.join(state.authorities) if state.authorities else 'the competent authority'}.

Yours faithfully,

District Collector
General Administration Department
Government of Maharashtra
Date: {today}
"""

    state.draft = draft
    state.log_audit("drafting", "draft_ready",
        f"version={state.draft_version}, "
        f"length={len(draft)}")

    # Publish to message bus
    bus.publish("draft_ready", {
        "action":  "draft_created",
        "version": state.draft_version,
        "length":  len(draft)
    })

    print(f"✅ Draft v{state.draft_version} ready!")
    print(draft)

    memory.log_episode("drafting",
        f"Draft v{state.draft_version} complete "
        f"({len(draft)} chars)")
    return state