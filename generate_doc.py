import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

doc = Document()

# Page setup: 1 inch margins
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# Helper for cell background shading
def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)

# Helper for cell padding
def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

# Helper for adding styled headings
def add_custom_heading(text, level, color_rgb=(15, 23, 42)):
    h = doc.add_heading(level=level)
    run = h.add_run(text)
    run.font.name = 'Calibri'
    run.font.color.rgb = RGBColor(*color_rgb)
    run.font.bold = True
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(6)
    return h

# Helper for callout box
def add_callout(text, title='KEY HIGHLIGHT'):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, 'F1F5F9')
    set_cell_margins(cell, 140, 140, 180, 180)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run(f'[{title}] ')
    r1.bold = True
    r1.font.name = 'Calibri'
    r1.font.color.rgb = RGBColor(2, 132, 199)
    r2 = p.add_run(text)
    r2.font.name = 'Calibri'
    r2.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ----------------- TITLE SECTION -----------------
p_title = doc.add_paragraph()
p_title.paragraph_format.space_before = Pt(16)
p_title.paragraph_format.space_after = Pt(4)
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_title = p_title.add_run('Trust- and Compliance-Aware Decentralised Emergency Vehicle Corridor Coordination Using Local Digital Twins and Swarm Intelligence')
r_title.bold = True
r_title.font.size = Pt(20)
r_title.font.name = 'Calibri'
r_title.font.color.rgb = RGBColor(15, 23, 42)

p_sub = doc.add_paragraph()
p_sub.paragraph_format.space_after = Pt(14)
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sub = p_sub.add_run('Comprehensive System Architecture & UML Design Specification Document\n(Derived & Enhanced from Traffic_review2.pptx)')
r_sub.font.size = Pt(12)
r_sub.font.name = 'Calibri'
r_sub.font.italic = True
r_sub.font.color.rgb = RGBColor(71, 85, 105)

# Authors Table
author_table = doc.add_table(rows=2, cols=2)
author_table.alignment = WD_TABLE_ALIGNMENT.CENTER

row0 = author_table.rows[0].cells
row0[0].paragraphs[0].text = 'Project Team Members:'
row0[1].paragraphs[0].text = 'Internal Guide:'
for c in row0:
    set_cell_shading(c, 'E2E8F0')
    set_cell_margins(c, 100, 100, 140, 140)
    for p in c.paragraphs:
        for r in p.runs:
            r.font.name = 'Calibri'
            r.font.bold = True
            r.font.size = Pt(10)

row1 = author_table.rows[1].cells
row1[0].paragraphs[0].text = '• V Krishna Teja (23P61A66H6)\n• V Manasa (23P61A66H9)\n• S Sri Ram (23P61A66F4)'
row1[1].paragraphs[0].text = 'Mrs. T. Adarana\nAssistant Professor\nDept. of Computer Science & Engineering'
for c in row1:
    set_cell_shading(c, 'F8FAFC')
    set_cell_margins(c, 100, 100, 140, 140)
    for p in c.paragraphs:
        for r in p.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(9.5)

doc.add_paragraph().paragraph_format.space_after = Pt(8)

# ----------------- EXECUTIVE SUMMARY -----------------
add_custom_heading('Executive Summary', level=1, color_rgb=(2, 132, 199))
p_exec = doc.add_paragraph(
    'This document formalizes the software design and architectural modeling for the Trust- and Compliance-Aware '
    'Decentralised Emergency Vehicle Corridor Coordination system, derived from and enhancing the research concepts '
    'presented in Traffic_review2.pptx (SwarmTwin). '
    'The platform resolves urban emergency vehicle bottlenecks through a fully decentralised multi-agent paradigm incorporating '
    'independent Local Digital Twins (LDT) on every vehicle, ECDSA NIST P-256 cryptographic message verification, behavioural trust scoring, '
    'Isolation Forest anomaly detection, PyTorch LSTM trajectory prediction, XGBoost driver yielding compliance prediction, '
    'Distributed Particle Swarm Optimization (DPSO), and A* dynamic route replanning.'
)
p_exec.paragraph_format.space_after = Pt(8)

# ----------------- 1. SYSTEM ARCHITECTURE -----------------
add_custom_heading('1. System Architecture Diagram', level=1, color_rgb=(2, 132, 199))
p_arch = doc.add_paragraph(
    'The system architecture follows a hierarchical, multi-tier edge-cloud paradigm connecting vehicle onboard units (OBU), '
    'cryptographic communication channels, local digital twin state managers, machine learning predictors, swarm optimization engines, '
    'and the user dashboard. Below is the system architecture diagram referenced from Slide 8 of Traffic_review2.pptx.'
)
p_arch.paragraph_format.space_after = Pt(6)

if os.path.exists('extracted_ppt_images/image3.jpeg'):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture('extracted_ppt_images/image3.jpeg', width=Inches(6.2))
    p_cap = doc.add_paragraph('Figure 1: SwarmTwin - Traffic Detection and Route Recommendation System Architecture (Slide 8 Reference)')
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.runs[0].font.size = Pt(9)
    p_cap.runs[0].font.italic = True
    p_cap.runs[0].font.color.rgb = RGBColor(100, 116, 139)

add_callout(
    'In this implementation, the architecture is upgraded to run as an autonomous software application (FastAPI + React.js) '
    'using synthetic JSON datasets. Key enhancements include ECDSA NIST P-256 digital signatures, individual Local Digital Twins per node, '
    'and real-time closed-loop dynamic replanning whenever a vehicle fails to yield.',
    title='ARCHITECTURE ENHANCEMENT'
)

# ----------------- 2. USE CASE DIAGRAM -----------------
add_custom_heading('2. Use Case Diagram', level=1, color_rgb=(2, 132, 199))
p_uc = doc.add_paragraph(
    'The Use Case Diagram defines the interactions between the system boundary and its key actors: Normal Vehicles, '
    'Emergency Ambulances, Drivers, and Traffic Authorities. Below is the Use Case Diagram referenced from Slide 11 of Traffic_review2.pptx.'
)
p_uc.paragraph_format.space_after = Pt(6)

if os.path.exists('extracted_ppt_images/image5.png'):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture('extracted_ppt_images/image5.png', width=Inches(6.2))
    p_cap = doc.add_paragraph('Figure 2: SwarmTwin - Traffic Detection and Route Recommendation Use Case Diagram (Slide 11 Reference)')
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.runs[0].font.size = Pt(9)
    p_cap.runs[0].font.italic = True
    p_cap.runs[0].font.color.rgb = RGBColor(100, 116, 139)

doc.add_paragraph(
    'Key Actors and Primary Use Cases:\n'
    '1. Vehicle Agent: Collects sensor telemetry (speed, lane, heading), signs V2V beacons, verifies incoming beacons, discovers spatial neighbors.\n'
    '2. Ambulance (Priority Vehicle): Initiates emergency dispatch broadcast, targets center lane corridor (Lane 2), executes priority navigation.\n'
    '3. Driver / In-Vehicle UI: Receives recommended lateral lane yielding directives (MOVE_LEFT, MOVE_RIGHT, REDUCE_SPEED), inspects local digital twin, views live traffic map.\n'
    '4. Traffic Authority: Injects road network topology, road capacity parameters, and static congestion thresholds into the digital twin substrate.'
)

# ----------------- 3. SEQUENCE DIAGRAM -----------------
add_custom_heading('3. Sequence Diagram', level=1, color_rgb=(2, 132, 199))
p_seq = doc.add_paragraph(
    'The Sequence Diagram captures the chronological message and control flow between the Driver, Vehicle, On-board Sensors, '
    'Nearby Vehicles, V2V Cryptography, Swarm Agent, Local Digital Twin, Navigation Engine, and Dashboard. '
    'Below is the sequence diagram referenced from Slide 12 of Traffic_review2.pptx.'
)
p_seq.paragraph_format.space_after = Pt(6)

if os.path.exists('extracted_ppt_images/image6.png'):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture('extracted_ppt_images/image6.png', width=Inches(6.2))
    p_cap = doc.add_paragraph('Figure 3: SwarmTwin - Traffic Detection and Route Recommendation Sequence Diagram (Slide 12 Reference)')
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.runs[0].font.size = Pt(9)
    p_cap.runs[0].font.italic = True
    p_cap.runs[0].font.color.rgb = RGBColor(100, 116, 139)

doc.add_paragraph(
    'Step-by-Step Execution Sequence:\n'
    '• Steps 1-4: Telemetry acquisition from onboard sensors (speed, lane occupancy, heading).\n'
    '• Steps 5-8: Cryptographic V2V beacon broadcast, neighbor discovery (<450m), and signature verification.\n'
    '• Steps 9-11: Movement consistency analysis, Isolation Forest anomaly scoring, and local risk assessment.\n'
    '• Steps 12-14: State integration into independent Local Digital Twins and road graph cost updates.\n'
    '• Steps 15-18: Distributed Particle Swarm Optimization (DPSO) convergence to identify optimal vehicle yielding actions.\n'
    '• Steps 19-22: A* route generation, dynamic replan trigger if a driver fails to yield, and real-time dashboard visualization.'
)

# ----------------- 4. ACTIVITY DIAGRAM -----------------
add_custom_heading('4. Activity Diagram', level=1, color_rgb=(2, 132, 199))
p_act = doc.add_paragraph(
    'The Activity Diagram illustrates the operational lifecycle, parallel processing pipelines, decision logic gates, '
    'and the closed-loop Dynamic Replanning mechanism developed specifically for this project.'
)
p_act.paragraph_format.space_after = Pt(6)

if os.path.exists('extracted_ppt_images/activity_diagram.png'):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture('extracted_ppt_images/activity_diagram.png', width=Inches(5.6))
    p_cap = doc.add_paragraph('Figure 4: Decentralised Emergency Vehicle Corridor Coordination - Operational Activity Diagram')
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.runs[0].font.size = Pt(9)
    p_cap.runs[0].font.italic = True
    p_cap.runs[0].font.color.rgb = RGBColor(100, 116, 139)

doc.add_paragraph(
    'Detailed Activity Workflow Phases:\n'
    '1. Initialization & Broadcast: Ambulance EV01 enters active dispatch and issues an ECDSA-signed emergency corridor request.\n'
    '2. Cryptographic & Freshness Check: Receiving nodes verify the NIST P-256 signature, check monotonic sequence numbers for replay attacks, and discard stale beacons (>15s).\n'
    '3. Multi-Agent Perception: Each vehicle updates its independent Local Digital Twin (LDT) with discovered neighbors within 450m.\n'
    '4. Parallel Intelligence Engine: Concurrently computes behavioural trust T(i) = w1*P + w2*C + w3*F + w4*S, executes Isolation Forest anomaly detection, forecasts 5-step trajectories with PyTorch LSTM, and infers driver compliance with XGBoost.\n'
    '5. Swarm Optimization: DPSO minimizes multi-objective fitness (emergency delay, safety margin, traffic delay, conflict penalty, compliance penalty).\n'
    '6. Verification & Dynamic Replanning: If a non-compliant driver blocks the primary corridor, the bottleneck is detected, the edge cost is penalized, and A* replans the route via the Mission Bypass in real time.'
)

# ----------------- 5. CLASS DIAGRAM REFERENCE -----------------
add_custom_heading('5. Class Diagram Reference', level=1, color_rgb=(2, 132, 199))
p_cls = doc.add_paragraph(
    'Below is the Class Diagram from Slide 10 of Traffic_review2.pptx, detailing the object-oriented structure '
    'of Vehicles, Sensors, SwarmAgents, Local Digital Twins, Navigation, and Drivers.'
)
p_cls.paragraph_format.space_after = Pt(6)

if os.path.exists('extracted_ppt_images/image4.png'):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture('extracted_ppt_images/image4.png', width=Inches(6.2))
    p_cap = doc.add_paragraph('Figure 5: SwarmTwin - Class Diagram (Slide 10 Reference)')
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.runs[0].font.size = Pt(9)
    p_cap.runs[0].font.italic = True
    p_cap.runs[0].font.color.rgb = RGBColor(100, 116, 139)

# Save Document
out_doc_path = 'Emergency_Vehicle_Corridor_Coordination_Design_Document.docx'
doc.save(out_doc_path)
print(f'Document successfully created and saved to {out_doc_path}!')

