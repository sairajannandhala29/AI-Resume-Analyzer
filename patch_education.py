from pathlib import Path
import re

path = Path("app.py")
text = path.read_text(encoding="utf-8")

# ---------------------------------------------------------
# 1. Add education eligibility helper
# ---------------------------------------------------------
helper = r'''

def _calculate_education_eligibility(jd_text, resume_text):
    """Calculate education eligibility from JD and resume."""

    jd = str(jd_text or "").lower()
    resume = str(resume_text or "").lower()

    # Detect whether JD actually specifies education
    education_required = any(x in jd for x in [
        "degree",
        "bachelor",
        "bachelor's",
        "bachelors",
        "b.sc",
        "bsc",
        "bca",
        "computer science",
        "information technology",
        "information systems",
        "engineering",
        "related field",
        "master",
        "master's",
        "mca",
    ])

    if not education_required:
        return "Not applicable", "—", "No specific education requirement detected."

    # Candidate degree evidence
    candidate_has_degree = any(x in resume for x in [
        "mca",
        "master of computer applications",
        "b.sc",
        "bsc",
        "bachelor of science",
        "bca",
        "bachelor",
        "computer science",
        "information technology",
        "information systems",
    ])

    if not candidate_has_degree:
        return "Not Eligible", "✗", "No degree matching the requirement was found."

    # Explicit CS / IT requirement
    cs_it_required = any(x in jd for x in [
        "computer science",
        "information technology",
        "information systems",
        "software engineering",
    ])

    cs_it_candidate = any(x in resume for x in [
        "computer science",
        "information technology",
        "information systems",
        "computer applications",
        "mca",
    ])

    if cs_it_required and cs_it_candidate:
        return "Eligible", "✓", "Your Computer Science / related qualification matches."

    # Bachelor requirement
    bachelor_required = any(x in jd for x in [
        "bachelor",
        "bachelor's",
        "bachelors",
        "b.sc",
        "bsc",
        "bca",
    ])

    bachelor_candidate = any(x in resume for x in [
        "b.sc",
        "bsc",
        "bachelor of science",
        "bca",
        "bachelor",
    ])

    if bachelor_required and bachelor_candidate:
        return "Eligible", "✓", "Your bachelor's degree satisfies the requirement."

    # Master's requirement
    master_required = any(x in jd for x in [
        "master",
        "master's",
        "masters",
        "mca",
        "postgraduate",
        "post-graduate",
    ])

    master_candidate = any(x in resume for x in [
        "mca",
        "master of computer applications",
    ])

    if master_required and master_candidate:
        return "Eligible", "✓", "Your master's qualification satisfies the requirement."

    # Generic degree requirement
    if candidate_has_degree:
        return "Eligible", "✓", "A relevant degree is present in the resume."

    return "Not Eligible", "✗", "The education requirement could not be matched."


'''

# Insert helper only once
if "_calculate_education_eligibility" not in text:
    marker = "\ndef "
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + helper + text[pos:]
    else:
        text += helper

# ---------------------------------------------------------
# 2. Replace the old education eligibility display logic
# ---------------------------------------------------------
pattern = re.compile(
    r'(?s)(education_status\s*=.*?)(?=\n\s*(?:with\s+card|st\.markdown|st\.columns|#|if\s+__name__))'
)

# Instead of depending on the old block, inject calculation
# immediately before the Job Requirements section.
calculation = r'''
# Calculate final education eligibility directly from the actual JD and resume
try:
    _education_status, _education_icon, _education_reason = (
        _calculate_education_eligibility(
            job_description,
            resume_text
        )
    )
except Exception:
    _education_status = "Not applicable"
    _education_icon = "—"
    _education_reason = "Education eligibility could not be calculated."

# Final overall eligibility = Experience AND Education
try:
    _experience_is_eligible = (
        str(eligibility_status).strip().lower() == "eligible"
    )
except Exception:
    _experience_is_eligible = False

_education_is_eligible = (
    str(_education_status).strip().lower() == "eligible"
)

if _education_status == "Not applicable":
    overall_eligibility = (
        "Eligible" if _experience_is_eligible else "Not Eligible"
    )
else:
    overall_eligibility = (
        "Eligible"
        if (_experience_is_eligible and _education_is_eligible)
        else "Not Eligible"
    )
'''

# Find Job Requirements heading and inject calculation before it
job_req_pos = text.find("Job Requirements")

if job_req_pos != -1:
    # Find beginning of line containing Job Requirements
    line_start = text.rfind("\n", 0, job_req_pos) + 1

    # Avoid duplicate injection
    if "overall_eligibility = (" not in text[:line_start]:
        text = text[:line_start] + calculation + "\n" + text[line_start:]

# ---------------------------------------------------------
# 3. Replace displayed education status
# ---------------------------------------------------------
text = re.sub(
    r'education_status\s*=\s*[^,\n]+',
    '_education_status',
    text
)

# Replace common UI references
text = text.replace(
    "{education_status}",
    "{_education_status}"
)

text = text.replace(
    "{education_icon}",
    "{_education_icon}"
)

# ---------------------------------------------------------
# 4. Replace overall eligibility references
# ---------------------------------------------------------
text = text.replace(
    "{eligibility_status}",
    "{overall_eligibility}"
)

path.write_text(text, encoding="utf-8")

print("PATCH COMPLETE")
print("Education eligibility helper added.")
print("Overall eligibility now requires Experience + Education.")
