import os
import sys
import subprocess


def _ensure_dependencies():
    try:
        import flask  # noqa: F401
        import fpdf  # noqa: F401
        import werkzeug  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    cmd = [sys.executable, "-m", "pip", "install"]
    if os.path.exists(requirements_path):
        cmd.extend(["-r", requirements_path])
    else:
        cmd.extend(["Flask>=3.0.0", "fpdf2>=2.7.0", "Werkzeug>=3.0.0"])

    print("Installing missing dependencies...")
    subprocess.check_call(cmd)


_ensure_dependencies()

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


def _add_pdf_section(pdf, title, items, x=75, title_color=(37, 99, 235), bullet="o"):
    if not any(item.strip() for item in items):
        return

    pdf.set_x(x)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(*title_color)
    pdf.cell(0, 10, title, ln=True)

    pdf.set_draw_color(*title_color)
    pdf.line(x, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_text_color(51, 65, 85)
    pdf.set_font("Arial", '', 11)
    for item in items:
        if item.strip():
            pdf.set_x(x)
            pdf.multi_cell(0, 7, f"{bullet} {item}")
            pdf.ln(2)
    pdf.ln(4)


def _render_modern_template(pdf, image_path, name, email, phone, description, skills, languages, education, projects, experience):
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 70, 297, 'F')

    if image_path:
        pdf.image(image_path, x=15, y=15, w=40)

    pdf.set_text_color(255, 255, 255)
    current_y = 70 if image_path else 20
    pdf.set_xy(5, current_y)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "CONTACT", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(60, 7, f"Email:\n{email}\n\nPhone:\n{phone}")
    pdf.ln(10)

    pdf.set_x(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "SKILLS", ln=True)
    pdf.set_font("Arial", '', 10)
    for item in skills:
        if item.strip():
            pdf.set_x(5)
            pdf.cell(60, 6, f"- {item}", ln=True)

    pdf.ln(8)
    pdf.set_x(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "LANGUAGES", ln=True)
    pdf.set_font("Arial", '', 10)
    for item in languages:
        if item.strip():
            pdf.set_x(5)
            pdf.cell(60, 6, f"- {item}", ln=True)

    pdf.set_text_color(30, 41, 59)
    pdf.set_xy(75, 20)
    pdf.set_font("Arial", 'B', 28)
    pdf.cell(0, 15, name.upper(), ln=True)

    pdf.set_x(75)
    pdf.set_font("Arial", 'I', 11)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(0, 6, description)
    pdf.ln(8)

    _add_pdf_section(pdf, "EDUCATION", education, x=75, title_color=(37, 99, 235), bullet="o")
    _add_pdf_section(pdf, "EXPERIENCE", experience, x=75, title_color=(37, 99, 235), bullet="o")
    _add_pdf_section(pdf, "PROJECTS", projects, x=75, title_color=(37, 99, 235), bullet="o")


def _render_classic_template(pdf, image_path, name, email, phone, description, skills, languages, education, projects, experience):
    pdf.set_text_color(17, 24, 39)
    pdf.set_font("Arial", 'B', 24)
    pdf.set_xy(15, 16)
    pdf.cell(130, 12, name.upper())

    if image_path:
        pdf.image(image_path, x=165, y=14, w=28)

    pdf.set_xy(15, 30)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f"{email} | {phone}", ln=True)

    pdf.set_draw_color(148, 163, 184)
    pdf.line(15, 40, 195, 40)

    pdf.set_xy(15, 46)
    pdf.set_font("Arial", 'I', 11)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(180, 6, description)
    pdf.ln(4)

    _add_pdf_section(pdf, "EDUCATION", education, x=15, title_color=(30, 64, 175), bullet="-")
    _add_pdf_section(pdf, "EXPERIENCE", experience, x=15, title_color=(30, 64, 175), bullet="-")
    _add_pdf_section(pdf, "PROJECTS", projects, x=15, title_color=(30, 64, 175), bullet="-")
    _add_pdf_section(pdf, "SKILLS", skills, x=15, title_color=(30, 64, 175), bullet="-")
    _add_pdf_section(pdf, "LANGUAGES", languages, x=15, title_color=(30, 64, 175), bullet="-")


def _render_compact_template(pdf, image_path, name, email, phone, description, skills, languages, education, projects, experience):
    pdf.set_fill_color(17, 24, 39)
    pdf.rect(0, 0, 60, 297, 'F')

    if image_path:
        pdf.image(image_path, x=14, y=14, w=32)

    pdf.set_text_color(226, 232, 240)
    pdf.set_xy(6, 52)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(48, 8, "CONTACT", ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(48, 6, f"{email}\n{phone}")

    pdf.ln(4)
    pdf.set_x(6)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(48, 8, "SKILLS", ln=True)
    pdf.set_font("Arial", '', 9)
    for item in skills:
        if item.strip():
            pdf.set_x(6)
            pdf.cell(48, 5, f"- {item}", ln=True)

    pdf.ln(4)
    pdf.set_x(6)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(48, 8, "LANGUAGES", ln=True)
    pdf.set_font("Arial", '', 9)
    for item in languages:
        if item.strip():
            pdf.set_x(6)
            pdf.cell(48, 5, f"- {item}", ln=True)

    pdf.set_text_color(30, 41, 59)
    pdf.set_xy(66, 16)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 12, name.upper(), ln=True)

    pdf.set_x(66)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(130, 6, description)
    pdf.ln(4)

    _add_pdf_section(pdf, "EDUCATION", education, x=66, title_color=(30, 64, 175), bullet="-")
    _add_pdf_section(pdf, "EXPERIENCE", experience, x=66, title_color=(30, 64, 175), bullet="-")
    _add_pdf_section(pdf, "PROJECTS", projects, x=66, title_color=(30, 64, 175), bullet="-")


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
        template_choice = request.form.get('template', 'modern')

        # 3. CAPTURE DYNAMIC LISTS (using getlist for multiple inputs)
        skills = request.form.getlist('skills[]')
        languages = request.form.getlist('languages[]')
        education = request.form.getlist('education[]')
        projects = request.form.getlist('projects[]')
        experience = request.form.getlist('experience[]')

        # 4. STYLED PDF GENERATION (by selected template)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        if template_choice == 'classic':
            _render_classic_template(pdf, image_path, name, email, phone, description, skills, languages, education, projects, experience)
        elif template_choice == 'compact':
            _render_compact_template(pdf, image_path, name, email, phone, description, skills, languages, education, projects, experience)
        else:
            _render_modern_template(pdf, image_path, name, email, phone, description, skills, languages, education, projects, experience)

        # 5. FINAL OUTPUT
        output_file = "professional_resume.pdf"
        pdf.output(output_file)
        
        return send_file(output_file, as_attachment=True)

    except Exception as e:
        return f"Error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
