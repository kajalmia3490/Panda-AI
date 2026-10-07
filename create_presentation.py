import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Colors
NAVY = RGBColor(24, 43, 73)
TEAL = RGBColor(0, 168, 150)
WHITE = RGBColor(255, 255, 255)
DARK = RGBColor(30, 30, 30)
LIGHT_BG = RGBColor(245, 247, 250)
GRAY = RGBColor(100, 100, 100)

def add_header(slide, title_text):
    # Header background banner
    header_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
    header_shape.fill.solid()
    header_shape.fill.fore_color.rgb = NAVY
    header_shape.line.color.rgb = NAVY
    
    # Accent line
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.1), Inches(13.333), Inches(0.1))
    accent.fill.solid()
    accent.fill.fore_color.rgb = TEAL
    accent.line.color.rgb = TEAL

    # Title text
    txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.15), Inches(11.7), Inches(0.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = 'Arial'

# Slide 1: Title Slide
blank_slide_layout = prs.slide_layouts[6]
slide1 = prs.slides.add_slide(blank_slide_layout)

bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = NAVY
bg1.line.color.rgb = NAVY

# Title Box
tb1 = slide1.shapes.add_textbox(Inches(1), Inches(1.5), Inches(11.333), Inches(4.5))
tf1 = tb1.text_frame
tf1.word_wrap = True

p = tf1.paragraphs[0]
p.text = "PROJECT PROPOSAL"
p.font.size = Pt(22)
p.font.bold = True
p.font.color.rgb = TEAL
p.font.name = 'Arial'

p2 = tf1.add_paragraph()
p2.text = "CampusConnect"
p2.font.size = Pt(54)
p2.font.bold = True
p2.font.color.rgb = WHITE
p2.font.name = 'Arial'
p2.space_before = Pt(10)

p3 = tf1.add_paragraph()
p3.text = "A Mobile Based University Student & Campus Services Platform"
p3.font.size = Pt(22)
p3.font.color.rgb = RGBColor(200, 210, 230)
p3.font.name = 'Arial'
p3.space_before = Pt(15)

p4 = tf1.add_paragraph()
p4.text = "Department of Computer Science and Engineering\nBangladesh University of Business and Technology (BUBT)"
p4.font.size = Pt(16)
p4.font.color.rgb = RGBColor(180, 190, 210)
p4.font.name = 'Arial'
p4.space_before = Pt(40)


# Slide 2: Team Members
slide2 = prs.slides.add_slide(blank_slide_layout)
add_header(slide2, "Project Team Members")

# Add table for team members
rows, cols = 6, 2
left, top, width, height = Inches(2.0), Inches(1.8), Inches(9.333), Inches(4.5)
table_shape = slide2.shapes.add_table(rows, cols, left, top, width, height)
table = table_shape.table
table.columns[0].width = Inches(5.0)
table.columns[1].width = Inches(4.333)

headers = ["Full Name", "Student ID"]
for i, h in enumerate(headers):
    cell = table.cell(0, i)
    cell.fill.solid()
    cell.fill.fore_color.rgb = NAVY
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.bold = True
    p.font.size = Pt(20)
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

members = [
    ("Nirob Sarkar", "20244203017"),
    ("Abdullah Al Adnan", "20244203038"),
    ("Khadiza Akter Lima", "20244203046"),
    ("Subir Das", "20244203048"),
    ("Kajal Mia", "20244203028")
]

for row_idx, member in enumerate(members, start=1):
    for col_idx, text in enumerate(member):
        cell = table.cell(row_idx, col_idx)
        cell.fill.solid()
        if row_idx % 2 == 0:
            cell.fill.fore_color.rgb = RGBColor(230, 235, 245)
        else:
            cell.fill.fore_color.rgb = WHITE
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.size = Pt(18)
        p.font.color.rgb = DARK
        p.alignment = PP_ALIGN.CENTER


# Slide 3: Introduction & Problem Statement
slide3 = prs.slides.add_slide(blank_slide_layout)
add_header(slide3, "Introduction & Problem Statement")

# Card 1: Introduction
shape1 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
shape1.fill.solid()
shape1.fill.fore_color.rgb = WHITE
shape1.line.color.rgb = TEAL

tf1 = shape1.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "Introduction"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_sub = tf1.add_paragraph()
p_sub.text = "• Centralized mobile platform for university academic information and campus services.\n• Replaces fragmented communication with a single mobile-first app.\n• Built as an SDP-3 project using Flutter, Node.js/Express, and MongoDB."
p_sub.font.size = Pt(16)
p_sub.font.color.rgb = DARK
p_sub.space_before = Pt(10)

# Card 2: Problem Statement
shape2 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.2))
shape2.fill.solid()
shape2.fill.fore_color.rgb = WHITE
shape2.line.color.rgb = TEAL

tf2 = shape2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "Problem Statement"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_sub2 = tf2.add_paragraph()
p_sub2.text = "• Information scattered across notice boards, department groups, messaging apps & print.\n• Difficult to find department- or semester-specific notices quickly.\n• Lack of unified workflow for maintenance complaints, event registration, and course materials."
p_sub2.font.size = Pt(16)
p_sub2.font.color.rgb = DARK
p_sub2.space_before = Pt(10)


# Slide 4: Proposed Solution & Target Users
slide4 = prs.slides.add_slide(blank_slide_layout)
add_header(slide4, "Proposed Solution & Target Users")

# Card 1: Solution
shape1 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
shape1.fill.solid()
shape1.fill.fore_color.rgb = WHITE
shape1.line.color.rgb = TEAL

tf1 = shape1.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "Proposed Solution"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_sub = tf1.add_paragraph()
p_sub.text = "• Secure & user-friendly mobile application with role-based access control.\n• Students: Access academic info and campus services.\n• Teachers: Manage courses, materials, and assignments.\n• Staff: Handle complaints & service requests.\n• Administrators: Manage users, notices, events, and system settings."
p_sub.font.size = Pt(15)
p_sub.font.color.rgb = DARK
p_sub.space_before = Pt(10)

# Card 2: Target Users
shape2 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.2))
shape2.fill.solid()
shape2.fill.fore_color.rgb = WHITE
shape2.line.color.rgb = TEAL

tf2 = shape2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "Target Users & Roles"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_sub2 = tf2.add_paragraph()
p_sub2.text = "1. Students\n   • Access notices, routines, courses, materials, assignments, events, complaints, and Lost & Found.\n2. Teachers\n   • Upload materials, manage assignments, and support attendance/event workflows.\n3. Administrators\n   • Manage users, departments, courses, notices, routines and system settings."
p_sub2.font.size = Pt(15)
p_sub2.font.color.rgb = DARK
p_sub2.space_before = Pt(10)


# Slide 5: Key Objectives
slide5 = prs.slides.add_slide(blank_slide_layout)
add_header(slide5, "Project Objectives")

shape = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
shape.fill.solid()
shape.fill.fore_color.rgb = WHITE
shape.line.color.rgb = TEAL

tf = shape.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Key Goals & Objectives of CampusConnect:"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

objectives = [
    "Develop a centralized mobile platform for university students and campus services.",
    "Provide personalized academic information based on department, semester, and role.",
    "Enable authorized users to publish and manage university and department notices.",
    "Provide seamless access to class routines, courses, learning materials, and assignments.",
    "Support event discovery, registration, transparent complaint tracking, and Lost & Found.",
    "Implement secure authentication (JWT), role-based authorization, and scalable backend architecture."
]

for obj in objectives:
    p_obj = tf.add_paragraph()
    p_obj.text = "• " + obj
    p_obj.font.size = Pt(16)
    p_obj.font.color.rgb = DARK
    p_obj.space_before = Pt(8)


# Slide 6: Major Features (Part 1)
slide6 = prs.slides.add_slide(blank_slide_layout)
add_header(slide6, "Major Features (1/2)")

features_part1 = [
    ("Authentication & Authorization", "Secure login, token-based security, and row-level role-based access control."),
    ("Home Dashboard", "Personalized view showing today's classes, latest notices, upcoming assignments, and events."),
    ("Notice Management", "University/department notices with filtering, search, priority tags, attachments, and expiration."),
    ("Class Routine", "Daily and weekly schedules including course titles, teachers, room numbers, and timings.")
]

for i, (title, desc) in enumerate(features_part1):
    col = i % 2
    row = i // 2
    left = Inches(0.8 + col * 5.9)
    top = Inches(1.6 + row * 2.7)
    
    card = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.6), Inches(2.5))
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = TEAL
    
    tf = card.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = NAVY
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.size = Pt(15)
    p2.font.color.rgb = DARK
    p2.space_before = Pt(6)


# Slide 7: Major Features (Part 2)
slide7 = prs.slides.add_slide(blank_slide_layout)
add_header(slide7, "Major Features (2/2)")

features_part2 = [
    ("Course & Learning Materials", "Access course info, credits, schedules, and view/download learning materials uploaded by teachers."),
    ("Assignment Management", "Teachers can create assignments; students can submit work online and view marks/feedback."),
    ("Notifications & Profile", "In-app notification history, Firebase push notifications, and editable academic/personal profile."),
    ("Admin Management", "Centralized control for users, departments, courses, notices, and other system entities.")
]

for i, (title, desc) in enumerate(features_part2):
    col = i % 2
    row = i // 2
    left = Inches(0.8 + col * 5.9)
    top = Inches(1.6 + row * 2.7)
    
    card = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.6), Inches(2.5))
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = TEAL
    
    tf = card.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = NAVY
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.size = Pt(15)
    p2.font.color.rgb = DARK
    p2.space_before = Pt(6)


# Slide 8: UI/UX Concept & Security
slide8 = prs.slides.add_slide(blank_slide_layout)
add_header(slide8, "UI/UX Concept & Security Architecture")

# Card 1: UI/UX
shape1 = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
shape1.fill.solid()
shape1.fill.fore_color.rgb = WHITE
shape1.line.color.rgb = TEAL

tf1 = shape1.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "UI/UX Design Concept"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_sub = tf1.add_paragraph()
p_sub.text = "• Clean, modern, mobile-first design approach.\n• Consistent reusable components & card-based layout.\n• Primary Nav: Home, Services, Notifications, Profile.\n• Visual status timeline for complaint tracking.\n• Simplified forms for rapid user actions."
p_sub.font.size = Pt(16)
p_sub.font.color.rgb = DARK
p_sub.space_before = Pt(10)

# Card 2: Security
shape2 = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.2))
shape2.fill.solid()
shape2.fill.fore_color.rgb = WHITE
shape2.line.color.rgb = TEAL

tf2 = shape2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "Security Standards"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_sub2 = tf2.add_paragraph()
p_sub2.text = "• Secure Password Hashing (Never stored in plain text).\n• Protected REST APIs requiring valid authentication tokens.\n• Strict Input Validation on all API requests.\n• File upload validation (Type & Size constraints).\n• RLS (Row Level Security) for data access control."
p_sub2.font.size = Pt(16)
p_sub2.font.color.rgb = DARK
p_sub2.space_before = Pt(10)


# Slide 9: Technology Stack & Database Overview
slide9 = prs.slides.add_slide(blank_slide_layout)
add_header(slide9, "Technology Stack & Database Overview")

# Card 1: Tech Stack
shape1 = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
shape1.fill.solid()
shape1.fill.fore_color.rgb = WHITE
shape1.line.color.rgb = TEAL

tf1 = shape1.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "Technology Stack"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_sub = tf1.add_paragraph()
p_sub.text = "• Mobile Frontend: Flutter / Dart\n• Backend: Node.js + Express.js (REST API)\n• Database: MongoDB + Mongoose\n• Version Control: Git + GitHub\n• API Testing: Postman / Thunder Client"
p_sub.font.size = Pt(16)
p_sub.font.color.rgb = DARK
p_sub.space_before = Pt(10)

# Card 2: Database
shape2 = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.2))
shape2.fill.solid()
shape2.fill.fore_color.rgb = WHITE
shape2.line.color.rgb = TEAL

tf2 = shape2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "Database Collections"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_sub2 = tf2.add_paragraph()
p_sub2.text = "• Primary DB: MongoDB\n• Planned Collections:\n  1. Users, Departments, Courses\n  2. Enrollments, Notices, Routines\n  3. Materials, Assignments, Submissions\n• Relationship mapping for future scalability."
p_sub2.font.size = Pt(15)
p_sub2.font.color.rgb = DARK
p_sub2.space_before = Pt(10)


# Slide 10: Conclusion
slide10 = prs.slides.add_slide(blank_slide_layout)
add_header(slide10, "Conclusion & Project Scope")

shape = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
shape.fill.solid()
shape.fill.fore_color.rgb = WHITE
shape.line.color.rgb = TEAL

tf = shape.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Conclusion & Suitability for SDP-3"
p.font.bold = True
p.font.size = Pt(22)
p.font.color.rgb = NAVY

p_body = tf.add_paragraph()
p_body.text = "CampusConnect is a practical university-focused mobile application combining academic information and campus services into one unified platform.\n\nWhy it is ideal for SDP-3:\n• Demonstrates full cross-platform mobile application development (Flutter).\n• Implements robust backend API design and business logic (Node.js/Express).\n• Features comprehensive database management and data modeling (MongoDB).\n• Integrates security, role-based access control, push notifications, and file handling.\n• Solves real-world academic workflows and campus communication bottlenecks."
p_body.font.size = Pt(16)
p_body.font.color.rgb = DARK
p_body.space_before = Pt(15)

# Save presentation
prs.save("CampusConnect_Presentation.pptx")
print("Presentation created successfully!")
