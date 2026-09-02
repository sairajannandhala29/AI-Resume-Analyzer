# 🤖 AI Resume Analyzer

AI Resume Analyzer is an ATS-focused resume analysis and optimization application built with Python and Streamlit.

It analyzes a candidate's resume against a target job description, identifies relevant and missing skills, calculates an ATS score, and can generate an optimized version of the resume while preserving the original DOCX structure.

---

## 🚀 Features

### Resume Analysis
- Upload a resume in PDF or DOCX format
- Extract resume text automatically
- Detect resume skills
- Analyze job-description requirements
- Identify matched and missing skills

### ATS Scoring
The application evaluates the resume using multiple signals:

- Skills Match — 40%
- Semantic Match — 25%
- Experience Match — 20%
- Keyword Match — 10%
- Resume Structure — 5%

The final score is displayed as a percentage from 0–100.

### AI Resume Optimization
Supports:

- Google Gemini
- OpenAI

The AI optimizer improves existing resume wording for the selected job description.

The optimization process is designed to:

- Preserve factual information
- Avoid inventing skills or experience
- Preserve company names
- Preserve job titles
- Preserve employment dates
- Preserve project names
- Preserve education details
- Preserve certifications
- Improve ATS keyword alignment
- Improve professional wording

### Same-Structure DOCX Editing

DOCX resumes are edited from the original document instead of generating a completely unrelated resume.

The editor attempts to preserve:

- Existing section headings
- Existing document order
- Existing formatting
- Existing job titles
- Existing company information
- Existing dates
- Existing project names

The original uploaded resume is never intentionally overwritten.

### Application Fit Estimate

After optimization, the application calculates an estimated application-fit score based on resume/JD alignment.

This percentage is an estimate and is **not a guaranteed probability of getting selected**.

---

## 🏗️ Project Structure

```text
AI-Resume-Analyzer/
│
├── app.py
├── analyzer.py
├── config.py
├── pdf_parser.py
├── skill_extractor.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── modules/
│   ├── __init__.py
│   ├── ai_rewriter.py
│   ├── ai_rewriter_backup.py
│   ├── application_advisor.py
│   ├── application_advisor_backup.py
│   ├── ats_scorer.py
│   ├── ats_scorer_backup.py
│   ├── fact_validator.py
│   ├── jd_analyzer.py
│   ├── pdf_parser.py
│   ├── recommendations.py
│   ├── resume_editor.py
│   ├── resume_editor_backup.py
│   ├── resume_generator.py
│   ├── resume_optimizer.py
│   ├── resume_optimizer_backup.py
│   ├── semantic_matcher.py
│   ├── skill_extractor.py
│   ├── text_cleaner.py
│   └── text_processor.py
│
├── tests/
│   ├── __init__.py
│   ├── test_analyzer.py
│   ├── test_ats_scorer.py
│   ├── test_matcher.py
│   └── test_pdf_parser.py
│
├── templates/
│   └── resume_template.docx
│
└── data/