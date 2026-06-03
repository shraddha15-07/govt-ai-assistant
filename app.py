# app.py - Streamlit Web Interface
# Run with: streamlit run app.py

import streamlit as st
import os
import json
import datetime
from main import run_orchestrator, generate_outputs

# Page config
st.set_page_config(
    page_title="Government AI Assistant",
    page_icon="🏛️",
    layout="wide"
)

# Header
st.title("🏛️ Government AI Multi-Agent Assistant")
st.markdown("""
> Powered by **Nous-Hermes-2** · **DeerFlow** workflow · **PraisonAI** memory
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.success("✅ LM Studio Connected")
    st.info("Model: Nous-Hermes-2-Mistral-7B")
    
    st.markdown("---")
    st.header("📋 Agents")
    st.markdown("🟣 Planner Agent")
    st.markdown("🟢 Analysis Agent")
    st.markdown("🔵 Drafting Agent")
    st.markdown("🔴 Compliance Agent")
    
    st.markdown("---")
    st.header("🔧 Tools")
    st.markdown("📄 GR Analyzer Tool")
    st.markdown("✅ Compliance Engine")

# Main area
st.markdown("---")

# Input section
st.header("📄 Input Document")

input_method = st.radio(
    "Choose input method:",
    ["Paste Text", "Upload File"],
    horizontal=True
)

document_text = ""

if input_method == "Paste Text":
    document_text = st.text_area(
        "Paste your Government Resolution or Circular here:",
        height=200,
        placeholder="""GOVERNMENT OF MAHARASHTRA
General Administration Department
Circular No. GAD/2024/CR-45/M-1
Date: 15th January 2024

Subject: Implementation of Digital Record Keeping...
"""
    )

else:
    uploaded_file = st.file_uploader(
        "Upload document (TXT or PDF)",
        type=["txt", "pdf"]
    )
    if uploaded_file:
        if uploaded_file.name.endswith(".txt"):
            document_text = uploaded_file.read().decode("utf-8")
            st.success(f"✅ File loaded: {uploaded_file.name}")
        else:
            import fitz
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            document_text = "\n".join(
                page.get_text() for page in doc
            )
            st.success(f"✅ PDF loaded: {uploaded_file.name}")

# Show document preview
if document_text:
    with st.expander("📖 Document Preview"):
        st.text(document_text[:500] + "..." if len(document_text) > 500 else document_text)

# Process button
st.markdown("---")
col1, col2, col3 = st.columns([1,2,1])
with col2:
    process_btn = st.button(
        "🚀 Process Document",
        type="primary",
        use_container_width=True,
        disabled=not document_text
    )

# Processing
if process_btn and document_text:
    
    # Save document temporarily
    temp_path = "sample_docs/temp_input.txt"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(document_text)

    # Progress tracking
    progress = st.progress(0)
    status = st.status("🤖 Processing document...", expanded=True)

    with status:
        st.write("🟣 Agent 1: Planner creating workflow...")
        progress.progress(10)

        try:
            st.write("🟢 Agent 2: Analysis extracting information...")
            progress.progress(30)

            # Run the full system
            state = run_orchestrator(temp_path)
            progress.progress(70)

            st.write("🔵 Agent 3: Drafting official letter...")
            progress.progress(80)

            st.write("🔴 Agent 4: Compliance checking...")
            progress.progress(90)

            # Generate output files
            paths = generate_outputs(state)
            progress.progress(100)

            status.update(
                label="✅ Processing complete!",
                state="complete"
            )

        except Exception as e:
            status.update(
                label=f"❌ Error: {e}",
                state="error"
            )
            st.error(f"Error: {e}")
            st.stop()

    st.markdown("---")

    # Results section
    st.header("📊 Results")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Confidence Score",
            f"{state.confidence_score*100:.1f}%"
        )
    with col2:
        st.metric(
            "Status",
            "✅ PASSED" if state.compliance_passed else "❌ FAILED"
        )
    with col3:
        st.metric(
            "Iterations",
            state.current_iteration + 1
        )
    with col4:
        st.metric(
            "Draft Version",
            f"v{state.draft_version}"
        )

    st.markdown("---")

    # Tabs for different outputs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Official Draft",
        "📋 Analysis",
        "✅ Compliance",
        "🔍 Reasoning",
        "📁 Audit Trail"
    ])

    with tab1:
        st.subheader("Official Government Letter")
        st.text_area(
            "Draft Letter:",
            value=state.draft,
            height=400
        )
        st.download_button(
            "⬇️ Download Draft",
            data=state.draft,
            file_name="official_draft.txt",
            mime="text/plain"
        )

    with tab2:
        st.subheader("Extracted Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📌 Circular Details**")
            st.write(f"**Circular No:** {state.circular_no}")
            st.write(f"**Date:** {state.date}")
            st.write(f"**Subject:** {state.subject}")
            
            st.markdown("**⏰ Deadlines**")
            for d in state.deadlines:
                st.write(f"• {d}")

        with col2:
            st.markdown("**👤 Authorities**")
            for a in state.authorities:
                st.write(f"• {a}")
            
            st.markdown("**✔️ Actions Required**")
            for i, action in enumerate(state.obligations, 1):
                st.write(f"{i}. {action}")

        if state.ambiguities:
            st.warning("⚠️ Ambiguities Detected:")
            for amb in state.ambiguities:
                st.write(f"• {amb}")

        # JSON download
        summary = state.to_summary_dict()
        st.download_button(
            "⬇️ Download JSON Summary",
            data=json.dumps(summary, indent=2),
            file_name="summary.json",
            mime="application/json"
        )

    with tab3:
        st.subheader("Compliance Report")

        # Score gauge
        score_pct = state.confidence_score * 100
        color = "green" if state.compliance_passed else "red"
        
        st.markdown(f"""
        <div style='text-align:center; padding:20px;
                    background:#f0f0f0; border-radius:10px;'>
            <h1 style='color:{color}'>{score_pct:.1f}%</h1>
            <h3>{'✅ APPROVED' if state.compliance_passed else '❌ NEEDS REVISION'}</h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        if state.self_critique:
            st.markdown("**🤖 Hermes Self-Critique:**")
            for critique in state.self_critique:
                st.warning(f"• {critique}")

        if state.compliance_issues:
            st.markdown("**❌ Issues Found:**")
            for issue in state.compliance_issues:
                st.error(f"• {issue}")
        else:
            st.success("✅ No compliance issues found!")

    with tab4:
        st.subheader("Agent Reasoning Steps")
        for i, step in enumerate(state.reasoning_steps, 1):
            st.markdown(f"**Step {i}:** {step}")

    with tab5:
        st.subheader("Audit Trail")
        st.markdown("*Every agent action recorded with timestamp*")
        
        for entry in state.audit_trail:
            col1, col2, col3 = st.columns([1, 2, 4])
            with col1:
                st.code(entry.get("time", ""))
            with col2:
                st.write(f"**{entry.get('agent', '')}**")
            with col3:
                st.write(entry.get("action", ""))

        # Download audit log
        audit_data = json.dumps(state.audit_trail, indent=2)
        st.download_button(
            "⬇️ Download Audit Log",
            data=audit_data,
            file_name="audit_log.json",
            mime="application/json"
        )

    # Output files
    st.markdown("---")
    st.header("📁 Output Files")
    for name, path in paths.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            st.download_button(
                f"⬇️ Download {name}",
                data=content,
                file_name=os.path.basename(path),
                key=name
            )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:gray;'>
Government AI Multi-Agent Assistant · 
Powered by Nous-Hermes-2 · DeerFlow · PraisonAI
</div>
""", unsafe_allow_html=True)