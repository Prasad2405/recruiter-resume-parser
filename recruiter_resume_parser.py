import streamlit as st
import re
import io
from PIL import Image
import pytesseract
import pdfplumber
import docx

st.set_page_config(page_title="Recruiter Resume Parser", layout="centered")
st.title("🧑‍💼 Recruiter Resume Auto‑Fill App")
st.write("Upload a resume and the recruiter form will be auto‑filled.")

uploaded_file = st.file_uploader(
    "Upload Resume (PDF / DOCX / Image)",
    type=["pdf", "docx", "png", "jpg", "jpeg"]
)

# ---------- TEXT EXTRACTION ----------
def extract_text(file):
    text = ""
    ext = file.name.split('.')[-1].lower()

    if ext in ["png", "jpg", "jpeg"]:
        text = pytesseract.image_to_string(Image.open(file))

    elif ext == "pdf":
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    elif ext == "docx":
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"

    return text

# ---------- FIELD EXTRACTION (LIKE GITHUB RESUME PARSERS) ----------
def extract_fields(text):
    data = {}

    patterns = {
        "Full Name": r"(?i)name[:\- ]+([A-Z][a-zA-Z ]+)",
        "Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "Phone": r"(?:\+91[- ]?)?[6-9]\d{9}",
        "Qualification": r"(?i)(B\.Tech|M\.Tech|B\.E|MCA|MBA|BSc|MSc)",
        "Experience": r"(\d+(?:\.\d+)?)\s*(?:years|yrs)",
        "CGPA / Percentage": r"(\d+(?:\.\d+)?\s*(?:%|CGPA))",
        "Skills": r"(?i)(Python|Java|SQL|Machine Learning|AI|Data Science|React|Node|Django)"
    }

    for field, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if field == "Skills":
            data[field] = ", ".join(set(matches))
        else:
            data[field] = matches[0] if matches else ""

    return data

# ---------- MAIN APP ----------
if uploaded_file:
    resume_text = extract_text(uploaded_file)
    extracted = extract_fields(resume_text)

    st.subheader("📋 Recruiter Candidate Form (Auto‑Filled)")

    name = st.text_input("Full Name", extracted.get("Full Name", ""))
    email = st.text_input("Email", extracted.get("Email", ""))
    phone = st.text_input("Phone", extracted.get("Phone", ""))
    qualification = st.text_input("Qualification", extracted.get("Qualification", ""))
    experience = st.text_input("Experience (Years)", extracted.get("Experience", ""))
    skills = st.text_area("Skills", extracted.get("Skills", ""))
    cgpa = st.text_input("CGPA / Percentage", extracted.get("CGPA / Percentage", ""))

    if st.button("📥 Download Candidate Details"):
        output = f"""
Full Name: {name}
Email: {email}
Phone: {phone}
Qualification: {qualification}
Experience: {experience}
Skills: {skills}
CGPA / Percentage: {cgpa}
"""
        st.download_button(
            "Download",
            output,
            file_name="candidate_details.txt",
            mime="text/plain"
        )
