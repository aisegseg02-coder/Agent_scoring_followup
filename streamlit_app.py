import os
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie

from db import init_db, save_meeting_result, load_all_meetings
from wave import run_pipeline


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Sales Meeting Analyzer",
    page_icon="📈",
    layout="wide",
)

init_db()
executor = ThreadPoolExecutor(max_workers=4)


# ============================================================
# LOTTIE SAFE LOADER
# ============================================================

def load_lottie(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def safe_lottie(anim, height=180):
    if anim:
        st_lottie(anim, height=height)
    else:
        st.markdown(
            f"""
            <div style='height:{height}px; background:#EEE; border-radius:10px;
                        display:flex; justify-content:center; align-items:center;
                        color:#888; font-size:13px;'>
                Animation unavailable
            </div>
            """,
            unsafe_allow_html=True,
        )


profile_anim = load_lottie("https://assets8.lottiefiles.com/packages/lf20_puciaact.json")
success_anim = load_lottie("https://assets2.lottiefiles.com/packages/lf20_jbrw3hcz.json")
loading_anim = load_lottie("https://assets4.lottiefiles.com/packages/lf20_usmfx6bp.json")


# ============================================================
# WEIGHTED SCORE CALCULATOR
# ============================================================

def compute_weighted_scores(meetings: list[dict]) -> dict:
    if not meetings:
        return {}

    sorted_ms = sorted(meetings, key=lambda x: x["meeting_date"], reverse=True)

    weights = [1.0, 0.8, 0.6, 0.4, 0.2]
    agg = {}
    total_w = 0.0

    for i, m in enumerate(sorted_ms):
        w = weights[i] if i < len(weights) else 0.1
        total_w += w
        scoring = m.get("scoring", {}) or {}
        for k, v in scoring.items():
            agg[k] = agg.get(k, 0.0) + float(v) * w

    if total_w == 0:
        return {}

    return {k: round(v / total_w, 2) for k, v in agg.items()}


# ============================================================
# SIDEBAR — DYNAMIC SALES PROFILE
# ============================================================

with st.sidebar:
    safe_lottie(profile_anim, height=140)
    st.markdown("## Sales Intelligent Profile")

    sales_id = st.text_input("Sales Agent ID", "SLS-442")
    sales_name = st.text_input("Sales Agent Name", "Ahmed Hassan")
    role = st.selectbox("Role", ["Junior", "Senior", "Team Leader", "Head of Sales"])

    st.markdown("---")

    all_meetings = load_all_meetings()
    my_meetings = [m for m in all_meetings if m["sales_id"] == sales_id]

    if not my_meetings:
        st.info("No meetings yet for this sales agent.")
    else:
        st.metric("Total Meetings", len(my_meetings))
        st.metric("Last Meeting", my_meetings[-1]["meeting_date"][:19])

        weighted_scores = compute_weighted_scores(my_meetings)

        st.markdown("### Weighted Performance (Last 5 Meetings)")
        cols_w = st.columns(3)
        i = 0
        for metric, value in weighted_scores.items():
            color = "#2E7D32" if value >= 7.5 else ("#FB8C00" if value >= 5 else "#C62828")

            with cols_w[i % 3]:
                st.markdown(
                    f"""
                    <div style='padding:12px; border-radius:10px;
                                background:{color}; color:white; text-align:center;
                                margin-bottom:10px; box-shadow:0 2px 5px rgba(0,0,0,0.18);'>
                        <div style='font-size:22px; font-weight:bold;'>{value}</div>
                        <div style='font-size:11px;'>{metric.replace("_"," ").title()}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            i += 1

        st.markdown("---")
        st.markdown("### Diagnostic Insights")

        if weighted_scores:
            best = max(weighted_scores, key=weighted_scores.get)
            worst = min(weighted_scores, key=weighted_scores.get)

            st.success(f"Strength: {best.replace('_',' ').title()} ({weighted_scores[best]}/10)")
            st.error(f"Weakness: {worst.replace('_',' ').title()} ({weighted_scores[worst]}/10)")

        st.markdown("---")
        st.markdown("### Mini Heatmap (Latest 5 Meetings)")

        last_5 = sorted(my_meetings, key=lambda x: x["meeting_date"], reverse=True)[:5]

        heat_rows = []
        for m in last_5:
            scoring = m.get("scoring", {}) or {}
            for k, v in scoring.items():
                heat_rows.append({"meeting": m["id"], "metric": k, "value": v})

        if heat_rows:
            dfh = pd.DataFrame(heat_rows)
            pivot = dfh.pivot(index="meeting", columns="metric", values="value")

            fig_heat_sidebar = px.imshow(
                pivot,
                aspect="auto",
                color_continuous_scale="Blues"
            )
            fig_heat_sidebar.update_layout(height=220, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_heat_sidebar, use_container_width=True)
        else:
            st.info("No scoring data available.")
# ============================================================
# RENDER SINGLE MEETING PROFILE (FULL CASE VIEW)
# ============================================================




























# ------------------------------------------------------------
#  PROFESSIONAL MEETING RENDERER
# ------------------------------------------------------------
def render_meeting_profile(meeting):
    
    import plotly.graph_objects as go
    import streamlit as st
    import hashlib

    analysis = meeting.get("analysis", {})
    followup = meeting.get("followup", {})
    pdfs = meeting.get("pdfs", [])
    scoring = meeting.get("scoring", {})

    # ------------------------------------------------------------
    # GLOBAL STYLE
    # ------------------------------------------------------------
    st.markdown("""
        <style>
            .card {
                padding: 22px;
                margin-bottom: 22px;
                border-radius: 16px;
                background: #ffffff;
                border: 1px solid #e3e3e3;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            }
            .title {
                font-size: 22px;
                margin-bottom: 12px;
                font-weight: 700;
                color: #333;
            }
            .sub {
                font-size: 16px;
                color: #444;
                line-height: 1.6;
            }
            .badge {
                padding: 6px 12px;
                background: #eef5ff;
                color: #333;
                border-radius: 8px;
                font-size: 13px;
            }
        </style>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------
    # HEADER SECTION
    # ------------------------------------------------------------
    st.markdown(f"""
        <h2 style="margin-bottom:4px;">📂 Meeting Report</h2>

        <div class="badge">Sales Agent: {meeting.get('sales_id','N/A')}</div>
        <div class="badge">Date: {meeting.get('meeting_date','')[:19]}</div>

        <br><hr><br>
    """, unsafe_allow_html=True)

    # ============================================================
    # SECTION 1 — SUMMARY
    # ============================================================
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='title'> Summary</div>", unsafe_allow_html=True)
    st.markdown(analysis.get("summary", "No summary available."))
    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # SECTION 2 — TOPICS
    # ============================================================
    topics = analysis.get("topics", [])
    if topics:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='title'> Topics Discussed</div>", unsafe_allow_html=True)
        for t in topics:
            st.markdown(f"- {t}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # SECTION 3 — MAIN OBJECTION
    # ============================================================
    objection = analysis.get("objection")
    if objection:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='title'> Main Objection</div>", unsafe_allow_html=True)
        st.error(objection)
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # SECTION 4 — MISTAKES
    # ============================================================
    wrong = followup.get("wrong_chat_or_action", [])
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='title'>❗ Mistakes & Wrong Answers</div>", unsafe_allow_html=True)

    if wrong:
        for w in wrong:
            st.markdown(f" **{w}**")
    else:
        st.success("No mistakes detected.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # SECTION 5 — MISSED OPPORTUNITIES
    # ============================================================
    missed = followup.get("missed_important_service", [])
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='title'> Missed Opportunities</div>", unsafe_allow_html=True)

    if missed:
        for m in missed:
            st.warning(f" {m}")
    else:
        st.info("No missed opportunities.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # SECTION 6 — FOLLOW-UP PLAN
    # ============================================================
    followups = {k: v for k, v in followup.items() if k.startswith("followup_")}

    if followups:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='title'> Follow-Up Plan</div>", unsafe_allow_html=True)

        for key, item in sorted(followups.items()):
            st.markdown(f"###  {item.get('subject', 'Follow-up Email')}")
            st.markdown(item.get("body", ""))

            attachments = item.get("attachments", [])

            # Normalize attachments to always be list of dicts
            normalized_attachments = []

            if isinstance(attachments, list):
                for att in attachments:
                    if isinstance(att, dict):
                        normalized_attachments.append({
                            "name": att.get("name", "file.pdf"),
                            "description": att.get("description", "")
                        })
                    else:
                        # If model returned a simple string
                        normalized_attachments.append({
                            "name": str(att),
                            "description": ""
                        })

            elif isinstance(attachments, dict):
                # Single dict only
                normalized_attachments.append({
                    "name": attachments.get("name", "file.pdf"),
                    "description": attachments.get("description", "")
                })

            elif isinstance(attachments, str):
                # Pure string
                normalized_attachments.append({
                    "name": attachments,
                    "description": ""
                })

            # Display normalized attachments
            if normalized_attachments:
                st.markdown("#### 📎 Attachments")

                for att in normalized_attachments:
                    st.markdown(f"""
                        <div style='padding:10px;border:1px solid #ddd;border-radius:10px;margin-bottom:10px;background:#f9faff'>
                            <b>📄 {att["name"]}</b><br>
                            <small>{att["description"]}</small>
                        </div>
                    """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # SECTION 7 — SCORE RADAR CHART
    # ============================================================
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='title'> Performance & Scores</div>", unsafe_allow_html=True)

    if scoring:

        labels = list(scoring.keys())
        values = list(scoring.values())

        # Unique chart key → prevents Streamlit collisions
        unique_key = "radar_" + hashlib.md5(
            str(meeting.get("id", meeting.get("meeting_date",""))).encode()
        ).hexdigest()

        fig = go.Figure(
            data=[go.Scatterpolar(
                r=values + [values[0]],
                theta=labels + [labels[0]],
                fill='toself',
                line=dict(width=2)
            )]
        )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=False,
            height=420,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        st.plotly_chart(fig, use_container_width=True, key=unique_key)
    else:
        st.info("No scoring available.")
        
    st.markdown("</div>", unsafe_allow_html=True)




























# ============================================================
# MAIN TABS
# ============================================================

tab_home, tab_analysis, tab_archive = st.tabs(
    [" Home Dashboard", " Analyze New Meeting", "📚 Meetings Archive & Cases"]
)


# TAB 1 — HOME DASHBOARD
###########################################################################################home edit
with tab_home:
    st.markdown("""
        <h2 style='text-align:center; margin-bottom:20px;'>📊 Global Sales Intelligence Dashboard</h2>
        <p style='text-align:center; color:gray;'>A unified view of performance, quality, and improvement opportunities across all telesales meetings</p>
    """, unsafe_allow_html=True)

    all_meetings = load_all_meetings()

    if not all_meetings:
        st.info("No meetings exist yet.")
        st.stop()

    # ==========================================================
    # BUILD DATAFRAME
    # ==========================================================
    rows = []
    for m in all_meetings:
        scoring = m.get("scoring", {}) or {}
        for metric, val in scoring.items():
            rows.append({
                "meeting": m["id"],
                "metric": metric,
                "value": val
            })

    df_all = pd.DataFrame(rows)

    # ==========================================================
    # TOP SUMMARY KPI CARDS
    # ==========================================================
    st.markdown("### 🚀 Key Performance Indicators")

    avg_scores = df_all.groupby("metric")["value"].mean().round(2)

    best_metric = avg_scores.idxmax()
    best_score = avg_scores.max()

    worst_metric = avg_scores.idxmin()
    worst_score = avg_scores.min()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Meetings", len(all_meetings))
    col2.metric("Top Strength", best_metric.replace("_"," ").title(), f"{best_score}/10")
    col3.metric("Weakest Area", worst_metric.replace("_"," ").title(), f"{worst_score}/10")

    st.divider()

    # ==========================================================
    # INTERACTIVE TABS (Charts)
    # ==========================================================
    chart_tab1, chart_tab2, chart_tab3 = st.tabs([
        "🔥 Heatmap Overview",
        "📈 Performance Trends",
        "🛡 Average Radar"
    ])

    # =======================
    # TAB 1 - HEATMAP
    # =======================
    with chart_tab1:
        st.markdown("### 🔥 Heatmap of All Scores")
        pivot_all = df_all.pivot(index="meeting", columns="metric", values="value")
        fig_heat_all = px.imshow(
            pivot_all,
            aspect="auto",
            color_continuous_scale="Blues"
        )
        fig_heat_all.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_heat_all, use_container_width=True)

    # =======================
    # TAB 2 - METRIC TIMELINE
    # =======================
    with chart_tab2:
        st.markdown("### 📈 Metric Timeline Across Meetings")
        fig_line = px.line(
            df_all,
            x="meeting",
            y="value",
            color="metric",
            markers=True
        )
        fig_line.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_line, use_container_width=True)

    # =======================
    # TAB 3 - RADAR
    # =======================
    with chart_tab3:
        st.markdown("### 🛡 Average Radar Chart")

        metrics = list(avg_scores.index)
        values = list(avg_scores.values)

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=metrics + [metrics[0]],
            fill="toself",
            name="Average"
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0,10])
            ),
            showlegend=False
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()

    # ==========================================================
    # EXECUTIVE SUMMARY (Stakeholder Friendly)
    # ==========================================================
    st.markdown("### 🧠 Executive Summary")
    
    st.write(f"""
    **Overall Performance Snapshot**
    - The strongest capability across all meetings is **{best_metric.replace('_',' ').title()}** scoring **{best_score}/10**.
    - The area needing the most improvement is **{worst_metric.replace('_',' ').title()}** with an average score of **{worst_score}/10**.
    
    **Recommendation**
    - Focus training and coaching on improving the lowest metric.
    - Use high-performing metrics as best-practice templates to duplicate across the team.
    """)

            
######################################################################################################################home edit 

# ============================================================
# TAB 2 — ANALYZE NEW MEETING
# ============================================================












#analyzing new mee####################################################################################
with tab_analysis:
 # ==========================================================
# 📝 ANALYZE NEW MEETING — Full Page
# ==========================================================
    st.markdown("""
        <h2 style='text-align:center; margin-bottom:12px;'> Analyze New Meeting</h2>
        <p style='text-align:center; color:gray;'>
            Run the AI pipeline to understand customer needs, objections, and opportunities in seconds
        </p>
    """, unsafe_allow_html=True)

    st.divider()

    # ==========================================================
    # INPUT
    # ==========================================================
    st.markdown("###  Provide Meeting Transcript")

    col_in1, col_in2 = st.columns([2.5, 1.5])

    with col_in1:
        transcript_input = st.text_area(
            "Paste transcript",
            height=240,
            placeholder="ضع نص الاجتماع هنا (أي لغة)…"
        )

    with col_in2:
        transcript_file = st.file_uploader(
            "Or upload a .txt file",
            type=["txt"],
            help="Uploading a file overrides the text input"
        )

        st.markdown("""
            <div style='background:#eef5ff; padding:10px 14px; border-radius:10px; margin-top:12px;'>
                💡 <b>Tip:</b> Use recording → speech-to-text → paste transcript here.
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    run_btn = st.button(" Run AI Pipeline", use_container_width=True)

    # ==========================================================
    # RUN PIPELINE
    # ==========================================================
    if run_btn:
        if transcript_file:
            transcript = transcript_file.read().decode("utf-8", errors="ignore")
        else:
            transcript = transcript_input

        if not transcript.strip():
            st.error(" You must provide transcript text before running the pipeline.")
            st.stop()

        with st.spinner("⏳ Running AI pipeline…"):
            future = executor.submit(run_pipeline, transcript)

            try:
                analysis, pdfs, followup = future.result()
            except Exception as e:
                st.error(f"Pipeline Error: {e}")
                st.stop()

        safe_lottie(success_anim, height=120)
        st.success("✔ AI Analysis Completed — Meeting Saved Successfully")

        save_meeting_result(sales_id, analysis, pdfs, followup)

        st.divider()

        # ==========================================================
        # RESULTS TABS
        # ==========================================================
        st.markdown("## 🔍 Results Overview")

        summary_tab, topics_tab, objection_tab, follow_tab = st.tabs([
            " Summary",
            " Topics",
            " Main Objection",
            " Follow-Up Plan"
        ])

        # ==========================================================
        # SUMMARY TAB
        # ==========================================================
        with summary_tab:
            st.markdown("###  Executive Summary")
            st.info(analysis.get("summary", "No summary extracted."))

        # ==========================================================
        # TOPICS TAB
        # ==========================================================
        with topics_tab:
            st.markdown("###  Detected Topics")
            topics = analysis.get("topics", [])
            if topics:
                for t in topics:
                    st.markdown(f"- {t}")
            else:
                st.warning("No topics identified.")

        # ==========================================================
        # OBJECTION TAB
        # ==========================================================
        with objection_tab:
            st.markdown("###  Main Customer Objection")
            st.error(analysis.get("objection", "No objection found."))

        # ==========================================================
        # FOLLOW-UP TAB
        # ==========================================================
        
        
                
                
        with follow_tab:
            st.markdown("##  Recommended Follow-Up Plan")
            st.write("")

            follow_data = followup or {}
            if not follow_data:
                st.info("No follow-up plan available.")
                st.stop()

            # ► Extract followup_x items
            followups = {k: v for k, v in follow_data.items() if k.startswith("followup_")}

            scoring = follow_data.get("sales_scoring", {})
            wrong = follow_data.get("wrong_chat_or_action", [])
            missed = follow_data.get("missed_important_service", [])

            # ==========================================================
            # FOLLOW-UP EMAIL BLOCKS — NEW BEAUTIFUL CLEAN VIEW
            # ==========================================================
            st.markdown("""
                <style>
                    .follow-card {
                        padding: 20px; 
                        border-radius: 14px;
                        border: 1px solid #ddd; 
                        background: #ffffff; 
                        margin-bottom: 24px;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
                    }
                    .attach-box {
                        padding: 12px; 
                        border-radius: 10px; 
                        border: 1px solid #cbd5e1; 
                        background: #f0f6ff; 
                        margin-bottom: 12px;
                    }
                </style>
            """, unsafe_allow_html=True)

            for key, item in sorted(followups.items()):
                st.markdown(f"""
                    <div class="follow-card">
                        <h3 style='margin-bottom:6px;'> {item.get('subject','No subject')}</h3>
                        <p style='color:#333; line-height:1.7; font-size:15px;'>{item.get('body','')}</p>
                """, unsafe_allow_html=True)

                # ATTACHMENTS
                attachments = item.get("attachments", [])
                if attachments:
                    st.markdown("<h4>📎 Attached Materials</h4>", unsafe_allow_html=True)

                    for att in attachments:
                        name = att.get("name","file.pdf")
                        desc = att.get("description","")

                        st.markdown(f"""
                            <div class="attach-box">
                                <b>📄 {name}</b><br>
                                <small style='color:#555;'>{desc}</small><br><br>

                                <i style='color:#666;'>💡 Why this PDF helps</i>
                                <p style='margin-top:5px; color:#444; line-height:1.6;'>
                                    This PDF reinforces the topic <b>{item.get("subject","")}</b> 
                                    and helps the client fully understand the solution.
                                </p>
                            </div>
                        """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")

            # ==========================================================
            # SALES SCORING — MODERN GRID VIEW
            # ==========================================================
            st.markdown("###  Sales Scoring")

            if scoring:
                import plotly.express as px
                import pandas as pd

                # Convert scoring dict → DataFrame
                df_scoring = pd.DataFrame({
                    "Skill": [k.replace("_", " ").title() for k in scoring.keys()],
                    "Score": list(scoring.values())
                })

                # Create bar chart
                fig = px.bar(
                    df_scoring,
                    x="Score",
                    y="Skill",
                    orientation="h",
                    text="Score",
                    range_x=[0, 10],
                    title="Sales Skill Scores",
                )

                # Styling
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    height=420,
                    yaxis=dict(title=""),
                    xaxis=dict(title="Score (0–10)"),
                    margin=dict(l=10, r=10, t=50, b=10)
                )

                # Render
                st.plotly_chart(fig, use_container_width=True, key="sales_scoring_bar")

            else:
                st.info("No scoring data available.")

            st.markdown("---")


            # ==========================================================
            # MISTAKES
            # ==========================================================
            st.markdown("###  Mistakes / Wrong Actions")
            if wrong:
                for w in wrong:
                    st.markdown(f" **{w}**")
            else:
                st.success("No mistakes detected.")

            st.markdown("---")

            # ==========================================================
            # MISSED OPPORTUNITIES
            # ==========================================================
            st.markdown("###  Missed Opportunities")
            if missed:
                for m in missed:
                    st.markdown(f" {m}")
            else:
                st.info("No missed opportunities.")









####
#ending of analysig meet #####################################################################################













# TAB 3 — ARCHIVE & CASES
#####################################################################################
with tab_archive:
    st.markdown("## 📁 Meetings Archive & Case Profiles")

    all_meetings = load_all_meetings()

    if not all_meetings:
        st.info("No meetings stored yet.")
        st.stop()

    # Sort newest → oldest
    sorted_meetings = sorted(
        all_meetings,
        key=lambda x: x["meeting_date"],
        reverse=True,
    )

    st.markdown("###  Select a Meeting to Inspect")

    for meeting in sorted_meetings:

        summary_snip = meeting["analysis"].get("summary", "")
        if len(summary_snip) > 60:
            summary_snip = summary_snip[:60] + "..."

        label = (
            f" {meeting['meeting_date'][:19]} | "
            f" {meeting['sales_id']} | "
            f" {summary_snip}"
        )

        with st.expander(label):
            render_meeting_profile(meeting)

















#
##
####
#######
#################
#####################
# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <hr>
    <p style='text-align:center; font-size:12px; color:#999;'>
        © 2025 — AI Sales Meeting Analyzer • LLaMA + RAG Engine
    </p>
    """,
    unsafe_allow_html=True
)
