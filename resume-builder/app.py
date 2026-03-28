import os
from flask import Flask, render_template, request, send_file, jsonify
from fpdf import FPDF
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')


def _clean_items(items):
    return [item.strip() for item in items if item and item.strip()]


def _analyze_resume_payload(payload):
    name = (payload.get('name') or '').strip()
    description = (payload.get('description') or '').strip()
    education = _clean_items(payload.get('education', []))
    skills = _clean_items(payload.get('skills', []))
    projects = _clean_items(payload.get('projects', []))
    experience = _clean_items(payload.get('experience', []))

    summary_score = 20 if len(description) >= 120 else 12 if len(description) >= 60 else 5 if description else 0
    skills_score = min(len(skills) * 4, 20)
    projects_score = min(len(projects) * 6, 20)
    experience_score = min(len(experience) * 6, 20)
    education_score = 20 if education else 0

    overall = summary_score + skills_score + projects_score + experience_score + education_score
    if name:
        overall = min(100, overall + 2)

    suggestions = []
    if len(description) < 80:
        suggestions.append("Write a 2-3 line summary highlighting your role, strengths, and target job profile.")
    if len(skills) < 5:
        suggestions.append("Add more relevant skills (at least 5) including tools/technologies from your target role.")
    if not projects:
        suggestions.append("Add at least one project with outcome and technologies used.")
    if not experience:
        suggestions.append("Include internship, freelance, or academic experience with measurable impact.")
    if education and all(len(item.split()) < 4 for item in education):
        suggestions.append("Make education entries more specific (degree, institute, year, achievements).")

    if not suggestions:
        suggestions = [
            "Great structure. Tailor summary and skills to each job description before applying.",
            "Add metrics (percentages, users, performance gains) in projects/experience for stronger impact.",
            "Keep formatting ATS-friendly and avoid long paragraphs in section bullets."
        ]

    return {
        "overall_score": overall,
        "section_scores": {
            "summary": summary_score,
            "skills": skills_score,
            "projects": projects_score,
            "experience": experience_score,
            "education": education_score,
        },
        "suggestions": suggestions[:3],
    }


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        payload = request.get_json(silent=True) or {}
        result = _analyze_resume_payload(payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        # 1. HANDLE IMAGE UPLOAD
        image_file = request.files.get('profile_pic')
        image_path = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        # 2. CAPTURE SINGLE FIELDS
        name = request.form.get('name', 'YOUR NAME')
        email = request.form.get('email', 'email@example.com')
        phone = request.form.get('phone', '0000 000 000')
        description = request.form.get('description', '')

        # 3. CAPTURE DYNAMIC LISTS (using getlist for multiple inputs)
        skills = request.form.getlist('skills[]')
        languages = request.form.getlist('languages[]')
        education = request.form.getlist('education[]')
        projects = request.form.getlist('projects[]')
        experience = request.form.getlist('experience[]')

        # 4. STYLED PDF GENERATION
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # --- THEME: SIDEBAR (Dark Slate) ---
        pdf.set_fill_color(15, 23, 42) # Matches --dark CSS
        pdf.rect(0, 0, 70, 297, 'F')

        # Profile Image in Sidebar
        if image_path:
            # Positioned at top of sidebar
            pdf.image(image_path, x=15, y=15, w=40)
        
        # Sidebar Content (White Text)
        pdf.set_text_color(255, 255, 255)
        current_y = 70 if image_path else 20
        pdf.set_xy(5, current_y)
        
        # Contact Section
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 10, "CONTACT", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(60, 7, f"Email:\n{email}\n\nPhone:\n{phone}")
        pdf.ln(10)

        # Sidebar Lists: Skills
        pdf.set_x(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 10, "SKILLS", ln=True)
        pdf.set_font("Arial", '', 10)
        for s in skills:
            if s.strip():
                pdf.set_x(5)
                pdf.cell(60, 6, f"- {s}", ln=True)
        
        pdf.ln(10)
        # Sidebar Lists: Languages
        pdf.set_x(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 10, "LANGUAGES", ln=True)
        pdf.set_font("Arial", '', 10)
        for l in languages:
            if l.strip():
                pdf.set_x(5)
                pdf.cell(60, 6, f"- {l}", ln=True)

        # --- THEME: MAIN CONTENT (Right Side) ---
        pdf.set_text_color(30, 41, 59) # Dark grey text
        pdf.set_xy(75, 20)
        
        # Name Header
        pdf.set_font("Arial", 'B', 28)
        pdf.cell(0, 15, name.upper(), ln=True)
        
        # Profile Description
        pdf.set_x(75)
        pdf.set_font("Arial", 'I', 11)
        pdf.set_text_color(100, 116, 139)
        pdf.multi_cell(0, 6, description)
        pdf.ln(10)

        # Section Helper Function
        def add_pdf_sec(title, items):
            if not any(item.strip() for item in items): return
            
            pdf.set_x(75)
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(37, 99, 235) # Professional Blue
            pdf.cell(0, 10, title, ln=True)
            
            # Draw Underline
            pdf.set_draw_color(37, 99, 235)
            pdf.line(75, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
            
            pdf.set_text_color(51, 65, 85)
            pdf.set_font("Arial", '', 11)
            for item in items:
                if item.strip():
                    pdf.set_x(75)
                    pdf.multi_cell(0, 7, f"o {item}")
                    pdf.ln(2)
            pdf.ln(5)

        add_pdf_sec("EDUCATION", education)
        add_pdf_sec("PROJECTS", projects)
        add_pdf_sec("EXPERIENCE", experience)

        # 5. FINAL OUTPUT
        output_file = "professional_resume.pdf"
        pdf.output(output_file)
        
        return send_file(output_file, as_attachment=True)

    except Exception as e:
        return f"Error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
