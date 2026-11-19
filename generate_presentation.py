# generate_presentation.py
import sys
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    
    # Set slide dimensions to widescreen (16:9)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # Colors
    BG_COLOR = RGBColor(15, 23, 42)       # Slate 900
    TEXT_COLOR = RGBColor(241, 245, 249)  # Slate 100
    MUTED_COLOR = RGBColor(148, 163, 184) # Slate 400
    ACCENT_COLOR = RGBColor(99, 102, 241) # Indigo 500
    ACCENT_ALT = RGBColor(34, 211, 238)   # Cyan 400
    
    def set_slide_background(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = BG_COLOR
        
    def add_title(slide, text):
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0)
        tf.margin_top = Inches(0)
        
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = 'Segoe UI'
        p.font.size = Pt(36)
        p.font.bold = True
        p.font.color.rgb = ACCENT_ALT
        return title_box

    # --- SLIDE 1: Title Slide ---
    slide_layout = prs.slide_layouts[6] # Blank slide
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide)
    
    # Large Title + Subtitle in one text box for perfect flow
    title_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(4.0))
    tf = title_box.text_frame
    tf.word_wrap = True
    
    # Project Title
    p_title = tf.paragraphs[0]
    p_title.text = "HYBRID REAL-TIME FRAUD DETECTION"
    p_title.font.name = 'Segoe UI'
    p_title.font.size = Pt(44)
    p_title.font.bold = True
    p_title.font.color.rgb = ACCENT_COLOR
    p_title.alignment = PP_ALIGN.LEFT
    
    # Subtitle
    p_sub = tf.add_paragraph()
    p_sub.text = "Integrating Rule Engines, Machine Learning, and Human-in-the-Loop RAG Agents"
    p_sub.font.name = 'Segoe UI'
    p_sub.font.size = Pt(22)
    p_sub.font.color.rgb = TEXT_COLOR
    p_sub.space_before = Pt(14)
    p_sub.alignment = PP_ALIGN.LEFT
    
    # Presenter / Info
    p_info = tf.add_paragraph()
    p_info.text = "Academic Project Presentation  |  Evaluation Criteria: 10 Marks"
    p_info.font.name = 'Segoe UI'
    p_info.font.size = Pt(14)
    p_info.font.color.rgb = MUTED_COLOR
    p_info.space_before = Pt(40)
    p_info.alignment = PP_ALIGN.LEFT

    # --- SLIDE 2: Problem Statement ---
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide)
    add_title(slide, "Problem Statement")
    
    content_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    tf = content_box.text_frame
    tf.word_wrap = True
    
    problems = [
        ("Rigidity of Traditional Rules", "Legacy fraud check rule engines are binary (pass/fail) and easily bypassed by changing transaction headers or structures. They fail to identify complex, multi-vector attack correlations."),
        ("Explainability Gap in ML", "Modern supervised classifiers (e.g. Random Forest, XGBoost) output probability scores (like 0.89) but cannot supply a natural language rationale. This hinders manual investigation and compliance auditing."),
        ("Operator Alert Fatigue", "High rates of false-positives overwhelm security teams, leading to delayed decisions and potential oversight of high-severity compromises."),
        ("Slow Adaptability Loop", "Feedback from manual resolutions is typically stored as flat archives in databases rather than dynamically informing active models or classifiers.")
    ]
    
    for i, (title, desc) in enumerate(problems):
        p_title = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p_title.text = f"\u25AA  {title}"
        p_title.font.name = 'Segoe UI'
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = ACCENT_COLOR
        p_title.space_after = Pt(2)
        if i > 0:
            p_title.space_before = Pt(14)
            
        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = 'Segoe UI'
        p_desc.font.size = Pt(14)
        p_desc.font.color.rgb = TEXT_COLOR
        p_desc.space_after = Pt(4)
        p_desc.level = 0
        p_desc.margin_left = Inches(0.4)

    # --- SLIDE 3: Objectives ---
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide)
    add_title(slide, "Objectives")
    
    content_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    tf = content_box.text_frame
    tf.word_wrap = True
    
    objectives = [
        ("Layered Hybrid Decision Pipeline", "Combine YAML-based deterministic rules with a probabilistic Machine Learning model (Random Forest Classifier) to produce a balanced combined score."),
        ("Generative AI Advisory Layer", "Introduce a Retrieval-Augmented Generation (RAG) agent that investigates transactions and automatically produces a summary, confidence score, and specific evidence list."),
        ("Dynamic In-Context Indexing", "Construct a dynamic index of playbooks and past human actions using TF-IDF vector retrieval to anchor LLM responses and eliminate hallucinations."),
        ("Closed Human-in-the-Loop (HITL) Feedback", "Immediately parse manual analyst decisions and review notes into retrieval documents so the system updates its reasoning patterns in real-time without retraining."),
        ("Operational Dashboard Console", "Build a dark-themed monitoring interface containing real-time queues, custom RAG chat follow-ups, and review analytics.")
    ]
    
    for i, (title, desc) in enumerate(objectives):
        p_title = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p_title.text = f"\u25AA  {title}"
        p_title.font.name = 'Segoe UI'
        p_title.font.size = Pt(18)
        p_title.font.bold = True
        p_title.font.color.rgb = ACCENT_COLOR
        p_title.space_after = Pt(2)
        if i > 0:
            p_title.space_before = Pt(12)
            
        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = 'Segoe UI'
        p_desc.font.size = Pt(14)
        p_desc.font.color.rgb = TEXT_COLOR
        p_desc.space_after = Pt(4)
        p_desc.level = 0
        p_desc.margin_left = Inches(0.4)

    # --- SLIDE 4: Literature Survey & Gap Identification ---
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide)
    add_title(slide, "Literature Survey & Gaps")
    
    # Table creation
    rows, cols = 4, 4
    left = Inches(0.8)
    top = Inches(1.8)
    width = Inches(11.7)
    height = Inches(4.5)
    
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    
    # Column widths
    table.columns[0].width = Inches(2.2)  # Approach
    table.columns[1].width = Inches(3.2)  # Technologies
    table.columns[2].width = Inches(3.2)  # Limitations
    table.columns[3].width = Inches(3.1)  # Our Solution
    
    headers = ["Approach", "Key Technologies", "Limitations", "Our Solution"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT_COLOR
        p = cell.text_frame.paragraphs[0]
        p.font.name = 'Segoe UI'
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = TEXT_COLOR
        p.alignment = PP_ALIGN.CENTER
        
    data = [
        ["Rule-Based", "Expert System rules, SQL triggers", "High maintenance cost, easily bypassed by smart attackers.", "YAML configuration, dynamic score weight matching."],
        ["Supervised ML", "Random Forest, XGBoost, Neural Nets", "No textual explainability, lack of compliance transparency.", "ML inference output combined with rules scoring."],
        ["GenAI & RAG", "LLM APIs, Vector Stores (Chroma, etc.)", "High token latency, hallucinations, lack of business bounds.", "LLM as an advisory agent; grounded locally in SQLite/Playbooks."]
    ]
    
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = table.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(30, 41, 59) # Slate 800
            p = cell.text_frame.paragraphs[0]
            p.font.name = 'Segoe UI'
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_COLOR
            p.alignment = PP_ALIGN.LEFT if j > 0 else PP_ALIGN.CENTER
            
    # Highlight Gap at the bottom
    gap_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.6))
    tf_gap = gap_box.text_frame
    tf_gap.word_wrap = True
    p_gap = tf_gap.paragraphs[0]
    p_gap.text = "Key Research Gap: Absence of systems that dynamically index analyst feedback comments to train GenAI triages without model retraining."
    p_gap.font.name = 'Segoe UI'
    p_gap.font.size = Pt(13)
    p_gap.font.italic = True
    p_gap.font.bold = True
    p_gap.font.color.rgb = ACCENT_ALT

    # --- SLIDE 5: Proposed Methodology (System Architecture) ---
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide)
    add_title(slide, "Proposed Methodology")
    
    # Textual Flow Description on left
    left_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(6.0), Inches(5.0))
    tf_l = left_box.text_frame
    tf_l.word_wrap = True
    
    steps = [
        ("1. Ingestion & Preprocessing", "FastAPI receives transaction details. Payload formatted to align with the Random Forest feature matrix."),
        ("2. Rule Evaluation", "A lightweight rules runner scans transaction parameters against rules stored in default_rules.yaml."),
        ("3. Probabilistic ML Inference", "Random Forest estimates is_fraud probability. Missing categories are dynamically padded at inference."),
        ("4. Combined Scoring (Fusion)", "Risk and ML scores are merged via a weighted average: Combined Score = 0.7 * Risk + 0.3 * ML."),
        ("5. GenAI RAG Investigation", "If combined score >= 0.5, TF-IDF retrieves matches from playbook & resolved alerts, prompting the LLM for structured analysis.")
    ]
    
    for i, (num, desc) in enumerate(steps):
        p = tf_l.add_paragraph() if i > 0 else tf_l.paragraphs[0]
        p.text = f"{num}"
        p.font.name = 'Segoe UI'
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = ACCENT_ALT
        p.space_after = Pt(2)
        if i > 0:
            p.space_before = Pt(8)
            
        p_desc = tf_l.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = 'Segoe UI'
        p_desc.font.size = Pt(12)
        p_desc.font.color.rgb = TEXT_COLOR
        p_desc.margin_left = Inches(0.2)
        
    # Visual Block diagram on the right using simple shapes
    # Shape coords
    shapes_info = [
        ("FastAPI Ingestion", Inches(7.5), Inches(1.8), Inches(4.5), Inches(0.7)),
        ("Rules Engine (YAML)", Inches(7.5), Inches(2.7), Inches(2.1), Inches(0.7)),
        ("ML Classifier (RF)", Inches(9.9), Inches(2.7), Inches(2.1), Inches(0.7)),
        ("Risk Fusion & Alert Trigger", Inches(7.5), Inches(3.6), Inches(4.5), Inches(0.7)),
        ("NeMo RAG Agent Advisor", Inches(7.5), Inches(4.5), Inches(4.5), Inches(0.7)),
        ("Human Operator Console", Inches(7.5), Inches(5.4), Inches(4.5), Inches(0.7)),
        ("RAG Index Update (HITL)", Inches(7.5), Inches(6.3), Inches(4.5), Inches(0.6)),
    ]
    
    for label, left, top, w, h in shapes_info:
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, w, h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(30, 41, 59)
        shape.line.color.rgb = ACCENT_COLOR
        shape.line.width = Pt(1.5)
        
        p = shape.text_frame.paragraphs[0]
        p.text = label
        p.font.name = 'Segoe UI'
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = TEXT_COLOR
        p.alignment = PP_ALIGN.CENTER

    # --- SLIDE 6: Expected Outcomes ---
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide)
    add_title(slide, "Expected Outcomes")
    
    content_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    tf = content_box.text_frame
    tf.word_wrap = True
    
    outcomes = [
        ("Improved Triage Speed", "Instead of checking databases or rules manually, analysts receive a formatted checklist of evidence, risk scoring breakdown, and initial playbook recommendations within 2 seconds of ingestion."),
        ("Dynamically Evolving System (Zero Code Retrain)", "Analyst override notes are instantly indexed by the TF-IDF search engine. When a similar fraud scenario repeats, the agent explains the historical human decision, allowing operations to scale immediately."),
        ("Drastic False-Positive Reduction", "By weighting the rules layer with the machine learning model, low-probability transactions are fast-tracked, allowing the operations team to focus on high-risk alerts."),
        ("Compliance Transparency", "Every alert is stored with its rules score, risk scores, and the generated RAG advice. This creates a concrete audit trail showing compliance with risk boundaries.")
    ]
    
    for i, (title, desc) in enumerate(outcomes):
        p_title = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p_title.text = f"\u25AA  {title}"
        p_title.font.name = 'Segoe UI'
        p_title.font.size = Pt(18)
        p_title.font.bold = True
        p_title.font.color.rgb = ACCENT_COLOR
        p_title.space_after = Pt(2)
        if i > 0:
            p_title.space_before = Pt(12)
            
        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = 'Segoe UI'
        p_desc.font.size = Pt(14)
        p_desc.font.color.rgb = TEXT_COLOR
        p_desc.space_after = Pt(4)
        p_desc.level = 0
        p_desc.margin_left = Inches(0.4)

    # --- SLIDE 7: Demonstration Overview ---
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide)
    add_title(slide, "Demonstration Overview")
    
    content_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    tf = content_box.text_frame
    tf.word_wrap = True
    
    demo_steps = [
        ("Step 1: Real-time Ingestion", "Simulate a live transaction using API request. If scores cross thresholds, a new alert appears in the Operations Console Queue."),
        ("Step 2: Alert Queue Review", "Examine metrics (Total Alerts, Pending, Approved, Blocked) on the main Operations dashboard."),
        ("Step 3: Interactive RAG Investigation", "Open an alert to review Rule hits, Random Forest probabilities, and generated Agent Recommendations (Summary, Confidence, Evidence, suggested actions)."),
        ("Step 4: Interactive Chat Dialog", "Ask the agent follow-up queries (e.g. 'Why is this flagged card-not-present?') and watch it retrieve playbooks and return instant answers."),
        ("Step 5: Feedback Overrides", "Decide to block or approve with notes. Submit the review, and show that this immediately updates dashboard analytics and is indexed for future lookups.")
    ]
    
    for i, (step, desc) in enumerate(demo_steps):
        p_title = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p_title.text = f"{step}"
        p_title.font.name = 'Segoe UI'
        p_title.font.size = Pt(18)
        p_title.font.bold = True
        p_title.font.color.rgb = ACCENT_ALT
        p_title.space_after = Pt(2)
        if i > 0:
            p_title.space_before = Pt(10)
            
        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = 'Segoe UI'
        p_desc.font.size = Pt(14)
        p_desc.font.color.rgb = TEXT_COLOR
        p_desc.space_after = Pt(2)
        p_desc.level = 0
        p_desc.margin_left = Inches(0.4)

    # Save presentation
    output_path = os.path.join(os.path.dirname(__file__), "presentation.pptx")
    prs.save(output_path)
    print(f"Presentation saved successfully to {output_path}")

if __name__ == '__main__':
    create_presentation()
