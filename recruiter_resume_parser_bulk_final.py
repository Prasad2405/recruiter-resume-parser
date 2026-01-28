import streamlit as st
import re
import io
from PIL import Image
import pytesseract
import pdfplumber
import docx

st.set_page_config(page_title="Recruiter Resume Parser", layout="centered")
st.title("🧑‍💼 Recruiter Resume Auto-Fill App (Bulk – FINAL)")
st.write("Upload multiple resumes or biodata files. Names, experience, and CGPA/percentage are extracted correctly.")

uploaded_files = st.file_uploader(
    "Upload Resume / Bio-data (PDF / DOCX / Image) – Multiple allowed",
    type=["pdf", "docx", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

# ---------------- TEXT EXTRACTION ----------------
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

# ---------------- NAME EXTRACTION ----------------
def extract_name(text):
    match = re.search(r"(?i)name\s*[:\-]\s*([A-Z][a-zA-Z ]+)", text)
    if match:
        return match.group(1).strip()

    for line in text.split("\n"):
        line = line.strip()
        if (
            1 < len(line.split()) <= 3
            and line.replace(" ", "").isalpha()
            and not re.search(r"email|phone|resume|skills", line, re.I)
        ):
            return line
    return ""

# ---------------- SCORE EXTRACTION (FINAL FIX) ----------------
def extract_score(text):
    clean_text = re.sub(r"\n+", " ", text)

    cgpa = re.search(
        r"(?:CGPA|GPA)\s*[:\-]?\s*(\d+(?:\.\d+)?)",
        clean_text,
        re.I,
    )

    percent = re.search(r"(\d+(?:\.\d+)?)\s*%", clean_text)

    if cgpa:
        return f"{cgpa.group(1)} CGPA"
    elif percent:
        return f"{percent.group(1)} %"
    return ""

# ---------------- FIELD EXTRACTION ----------------
def extract_fields(text):
    data = {}

    data["Full Name"] = extract_name(text)

    email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    data["Email"] = email.group(0) if email else ""

    phone = re.search(r"(?:\+91[- ]?)?[6-9]\d{9}", text)
    data["Phone"] = phone.group(0) if phone else ""

    qual = re.search(r"(?i)(B\.Tech|M\.Tech|B\.E|MCA|MBA|BSc|MSc)", text)
    data["Qualification"] = qual.group(0) if qual else ""

    exp = re.search(r"(\d+(?:\.\d+)?)\s*(?:years|yrs)", text, re.I)
    data["Experience"] = exp.group(1) if exp else "0"

    data["Score"] = extract_score(text)

    skills = re.findall(
        r"(?i)(Python|Java|SQL|Machine Learning|AI|Data Science|React|Node|Django)",
        text,
    )
    data["Skills"] = ", ".join(sorted(set(skills)))

    return data

# ---------------- MAIN APP ----------------
if uploaded_files:
    unique_candidates = set()
    csv_rows = ["Name,Email,Phone,Qualification,Experience,Skills,Score"]

    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        text = extract_text(uploaded_file)
        extracted = extract_fields(text)

        key = f"{extracted['Email']}|{extracted['Phone']}"
        if key in unique_candidates:
            st.warning(f"Duplicate skipped: {uploaded_file.name}")
            continue
        unique_candidates.add(key)

        st.subheader(f"📋 Candidate {idx}: {uploaded_file.name}")

        name = st.text_input(f"Full Name {idx}", extracted["Full Name"], key=f"n{idx}")
        email = st.text_input(f"Email {idx}", extracted["Email"], key=f"e{idx}")
        phone = st.text_input(f"Phone {idx}", extracted["Phone"], key=f"p{idx}")
        qualification = st.text_input(f"Qualification {idx}", extracted["Qualification"], key=f"q{idx}")
        experience = st.text_input(f"Experience (Years) {idx}", extracted["Experience"], key=f"x{idx}")
        skills = st.text_area(f"Skills {idx}", extracted["Skills"], key=f"s{idx}")
        score = st.text_input(f"CGPA / Percentage {idx}", extracted["Score"], key=f"c{idx}")

        csv_rows.append(
            f"{name},{email},{phone},{qualification},{experience},\"{skills}\",{score}"
        )

    st.subheader("⬇️ Bulk Export")
    st.download_button(
        "📊 Download CSV (Excel)",
        "\n".join(csv_rows),
        file_name="candidates_data.csv",
        mime="text/csv",
    )