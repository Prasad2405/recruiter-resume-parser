import streamlit as st
import re
import io
from PIL import Image
import pytesseract
import pdfplumber
import docx

st.set_page_config(page_title="Recruiter Resume Parser", layout="centered")
st.title("🧑‍💼 Recruiter Resume Auto-Fill App (Bulk Mode)")
st.write("Upload multiple resumes / biodata files. The recruiter form will be auto-filled, duplicates skipped, and data exportable to Excel.")

uploaded_files = st.file_uploader(
    "Upload Resume / Bio-data (PDF / DOCX / Image) – Multiple allowed",
    type=["pdf", "docx", "png", "jpg", "jpeg"],
    accept_multiple_files=True
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

# ---------- FIELD EXTRACTION ----------
def extract_fields(text):
    data = {}

    name_match = re.search(r"(?i)name\s*[:\-]\s*([A-Z][a-zA-Z ]+)", text)
    data["Full Name"] = name_match.group(1) if name_match else ""

    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    data["Email"] = email_match.group(0) if email_match else ""

    phone_match = re.search(r"(?:\+91[- ]?)?[6-9]\d{9}", text)
    data["Phone"] = phone_match.group(0) if phone_match else ""

    qual_match = re.search(r"(?i)(B\.Tech|M\.Tech|B\.E|MCA|MBA|BSc|MSc)", text)
    data["Qualification"] = qual_match.group(0) if qual_match else ""

    exp_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:years|yrs)", text, re.I)
    data["Experience"] = exp_match.group(1) if exp_match else "0"

    cgpa_match = re.search(r"(\d+(?:\.\d+)?)\s*CGPA", text, re.I)
    percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)

    if cgpa_match:
        data["Score"] = f"{cgpa_match.group(1)} CGPA"
    elif percent_match:
        data["Score"] = f"{percent_match.group(1)} %"
    else:
        data["Score"] = ""

    skills = re.findall(r"(?i)(Python|Java|SQL|Machine Learning|AI|Data Science|React|Node|Django)", text)
    data["Skills"] = ", ".join(sorted(set(skills)))

    return data

# ---------- MAIN APP ----------
if uploaded_files:
    unique_candidates = set()
    csv_rows = ["Name,Email,Phone,Qualification,Experience,Skills,Score"]

    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        resume_text = extract_text(uploaded_file)
        extracted = extract_fields(resume_text)

        candidate_key = f"{extracted['Email']}|{extracted['Phone']}"
        if candidate_key in unique_candidates:
            st.warning(f"Duplicate skipped: {uploaded_file.name}")
            continue
        unique_candidates.add(candidate_key)

        st.subheader(f"📋 Candidate {idx}: {uploaded_file.name}")

        name = st.text_input(f"Full Name {idx}", extracted["Full Name"], key=f"name_{idx}")
        email = st.text_input(f"Email {idx}", extracted["Email"], key=f"email_{idx}")
        phone = st.text_input(f"Phone {idx}", extracted["Phone"], key=f"phone_{idx}")
        qualification = st.text_input(f"Qualification {idx}", extracted["Qualification"], key=f"qual_{idx}")
        experience = st.text_input(f"Experience (Years) {idx}", extracted["Experience"], key=f"exp_{idx}")
        skills = st.text_area(f"Skills {idx}", extracted["Skills"], key=f"skills_{idx}")
        score = st.text_input(f"CGPA / Percentage {idx}", extracted["Score"], key=f"score_{idx}")

        csv_rows.append(
            f"{name},{email},{phone},{qualification},{experience},\"{skills}\",{score}"
        )

    st.subheader("⬇️ Bulk Export")

    st.download_button(
        "📊 Download CSV (Excel)",
        "\n".join(csv_rows),
        file_name="candidates_data.csv",
        mime="text/csv"
    )
