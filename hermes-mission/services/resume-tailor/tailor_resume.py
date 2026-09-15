#!/usr/bin/env python3
"""
Resume & Cover Letter Tailoring Service for Mr Bubba Services

Takes a client's resume and a job description, then generates:
- ATS-optimized tailored resume
- Tailored cover letter
- Keyword match analysis report
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    Document = None

# ── Keyword extraction ──────────────────────────────────────────────────────

# Common action verbs ranked by impact
ACTION_VERBS = [
    "achieved", "administered", "advanced", "analyzed", "automated",
    "built", "chaired", "coached", "conceptualized", "conducted",
    "consolidated", "constructed", "coordinated", "created", "delivered",
    "designed", "developed", "directed", "drove", "engineered",
    "established", "evaluated", "executed", "expanded", "generated",
    "guided", "implemented", "improved", "increased", "influenced",
    "initiated", "innovated", "integrated", "launched", "led",
    "managed", "mentored", "negotiated", "optimized", "orchestrated",
    "organized", "overhauled", "oversaw", "pioneered", "planned",
    "produced", "programmed", "reduced", "reorganized", "researched",
    "resolved", "restructured", "spearheaded", "streamlined", "supervised",
    "transformed", "upgraded",
]

# ATS-friendly section headers (standard, parseable)
ATS_HEADERS = {
    "summary": ["summary", "professional summary", "profile", "objective"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "education": ["education", "academic background", "qualifications"],
    "skills": ["skills", "technical skills", "core competencies", "proficiencies"],
    "certifications": ["certifications", "licenses", "certificates"],
    "projects": ["projects", "key projects", "project experience"],
}


def load_resume(path: str) -> str:
    """Load resume from .docx, .txt, or .md file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Resume not found: {path}")
    
    if p.suffix.lower() == ".docx":
        if Document is None:
            raise ImportError("python-docx is required for .docx files")
        doc = Document(path)
        return "\n".join(para.text for para in doc.paragraphs)
    else:
        return p.read_text(encoding="utf-8")


def load_jd(path_or_text: str) -> str:
    """Load JD from file or use raw text."""
    p = Path(path_or_text)
    if p.exists():
        if p.suffix.lower() == ".docx":
            if Document is None:
                raise ImportError("python-docx is required for .docx files")
            doc = Document(path_or_text)
            return "\n".join(para.text for para in doc.paragraphs)
        return p.read_text(encoding="utf-8")
    return path_or_text


def extract_keywords(text: str) -> dict:
    """Extract important keywords from job description."""
    text_lower = text.lower()
    
    # Find action verbs present in JD
    verbs_found = [v for v in ACTION_VERBS if v in text_lower]
    
    # Extract technical skills (capitalized multi-word terms, acronyms, etc.)
    tech_pattern = r'\b([A-Z][a-z]+(?:\.[a-z]+)?(?:\s+[A-Z][a-z]+)*)\b'
    tech_terms = re.findall(tech_pattern, text)
    
    # Extract acronyms (2-5 uppercase letters)
    acronyms = re.findall(r'\b([A-Z]{2,5})\b', text)
    
    # Find "required" and "preferred" section keywords
    required_keywords = []
    preferred_keywords = []
    
    # Look for years of experience patterns
    exp_patterns = re.findall(r'(\d+)\+?\s*years?', text_lower)
    
    # Extract noun phrases (simple heuristic: adj+noun patterns)
    noun_phrases = re.findall(
        r'\b([a-z]+(?:\s+[a-z]+)?)\s+(?:experience|skills?|knowledge|proficiency)',
        text_lower
    )
    
    # Deduplicate while preserving order
    seen = set()
    unique_tech = []
    for t in tech_terms + acronyms + noun_phrases:
        t_clean = t.strip().lower()
        if t_clean not in seen and len(t_clean) > 1:
            seen.add(t_clean)
            unique_tech.append(t.strip())
    
    return {
        "action_verbs": list(dict.fromkeys(verbs_found)),
        "technical_terms": unique_tech[:20],
        "acronyms": list(dict.fromkeys(acronyms)),
        "experience_years": exp_patterns,
        "raw_keywords": unique_tech,
    }


def analyze_ats_score(resume_text: str, jd_keywords: dict) -> dict:
    """Score how well resume matches JD keywords."""
    resume_lower = resume_text.lower()
    
    technical_matches = [
        kw for kw in jd_keywords.get("technical_terms", [])
        if kw.lower() in resume_lower
    ]
    
    verb_matches = [
        v for v in jd_keywords.get("action_verbs", [])
        if v in resume_lower
    ]
    
    acronym_matches = [
        a for a in jd_keywords.get("acronyms", [])
        if a in resume_text
    ]
    
    total_keywords = len(jd_keywords.get("technical_terms", []))
    match_count = len(technical_matches)
    
    score = min(100, int((match_count / max(total_keywords, 1)) * 100))
    
    missing = [
        kw for kw in jd_keywords.get("technical_terms", [])
        if kw.lower() not in resume_lower
    ]
    
    return {
        "score": score,
        "technical_matches": technical_matches,
        "action_verb_matches": verb_matches,
        "acronym_matches": acronym_matches,
        "missing_keywords": missing,
        "total_jd_keywords": total_keywords,
        "matched_count": match_count,
    }


def tailor_resume(resume_text: str, jd_text: str, output_path: str) -> str:
    """Generate an ATS-optimized tailored resume."""
    keywords = extract_keywords(jd_text)
    analysis = analyze_ats_score(resume_text, keywords)
    
    lines = resume_text.strip().split("\n")
    
    # Build tailored content
    output_lines = []
    output_lines.append("# TAILORED RESUME")
    output_lines.append(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output_lines.append("")
    output_lines.append("---")
    output_lines.append("")
    
    # Insert optimized summary with top keywords
    top_keywords = keywords["technical_terms"][:8]
    if top_keywords:
        output_lines.append("## PROFESSIONAL SUMMARY")
        output_lines.append(
            f"Results-driven professional with expertise in "
            f"{', '.join(top_keywords[:5])}. "
            f"Proven track record of delivering high-impact results "
            f"using {', '.join(top_keywords[5:8] if len(top_keywords) > 5 else top_keywords[:3])}."
        )
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
    
    # Process existing sections
    current_section = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            output_lines.append("")
            continue
        
        # Detect section headers
        section_match = None
        for section, headers in ATS_HEADERS.items():
            if stripped.lower().rstrip(":").strip() in headers:
                section_match = section
                break
        
        if section_match:
            current_section = section_match
            output_lines.append(f"## {stripped.upper()}")
            continue
        
        # Enhance experience bullets with JD action verbs
        if current_section == "experience" and stripped.startswith(("-", "•", "*")):
            enhanced = enhance_bullet(stripped, keywords["action_verbs"])
            output_lines.append(enhanced)
        else:
            output_lines.append(line)
    
    # Add missing keywords section
    if analysis["missing_keywords"]:
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
        output_lines.append("## ADDITIONAL SKILLS & KEYWORDS")
        output_lines.append(
            f"*Relevant competencies: {', '.join(analysis['missing_keywords'][:15])}*"
        )
    
    # Write output
    output_text = "\n".join(output_lines)
    
    if output_path.endswith(".docx") and Document:
        write_docx(output_text, output_path)
    else:
        Path(output_path).write_text(output_text, encoding="utf-8")
    
    return output_text


def enhance_bullet(bullet: str, verbs: list) -> str:
    """Enhance a bullet point with stronger action verb if appropriate."""
    # Remove bullet marker
    content = bullet.lstrip("-•* ").strip()
    if not content:
        return bullet
    
    # Check if starts with a weak verb
    first_word = content.split()[0].lower().rstrip(".,;:") if content else ""
    weak_verbs = ["worked", "helped", "responsible", "assisted", "handled", "did", "made"]
    
    if first_word in weak_verbs and verbs:
        # Replace with stronger JD-aligned verb
        content = verbs[0].capitalize() + " " + " ".join(content.split()[1:])
        return f"- {content}"
    
    return bullet


def generate_cover_letter(resume_text: str, jd_text: str, output_path: str,
                          company_name: str = "[Company Name]",
                          position_title: str = "[Position Title]") -> str:
    """Generate a tailored cover letter."""
    keywords = extract_keywords(jd_text)
    
    # Extract key requirements from JD
    jd_lines = jd_text.strip().split("\n")
    responsibilities = []
    for line in jd_lines[:20]:
        stripped = line.strip()
        if stripped.startswith(("-", "•", "*")):
            responsibilities.append(stripped.lstrip("-•* ").strip())
    
    # Build cover letter
    letter = f"""[Your Name]
[Your Address]
[City, State ZIP]
[Your Email]
[Your Phone Number]

{datetime.now().strftime('%B %d, %Y')}

Hiring Manager
{company_name}
[Company Address]

Dear Hiring Manager,

I am writing to express my strong interest in the {position_title} position at {company_name}. With my background in {', '.join(keywords['technical_terms'][:3])}, I am confident I would make a valuable addition to your team.

In my previous experience, I have successfully leveraged {', '.join(keywords['technical_terms'][3:6] if len(keywords['technical_terms']) > 3 else keywords['technical_terms'][:2])} to drive meaningful results. My expertise aligns closely with your requirements, particularly in areas such as {', '.join(keywords['technical_terms'][:5])}.

Key qualifications I bring to this role include:
"""
    
    # Add bullet points using JD keywords
    for i, verb in enumerate(keywords["action_verbs"][:5]):
        term = keywords["technical_terms"][i % len(keywords["technical_terms"])]
        letter += f"\n- {verb.capitalize()} initiatives involving {term}"
    
    letter += f"""

I am particularly drawn to {company_name} because of the opportunity to contribute to impactful projects while continuing to grow professionally. My experience with {keywords['technical_terms'][0] if keywords['technical_terms'] else 'relevant technologies'} positions me to deliver immediate value.

I would welcome the opportunity to discuss how my skills and experience align with the needs for the {position_title} role. Thank you for considering my application.

Sincerely,
[Your Name]
"""
    
    if output_path.endswith(".docx") and Document:
        write_docx(letter, output_path)
    else:
        Path(output_path).write_text(letter, encoding="utf-8")
    
    return letter


def write_docx(content: str, path: str):
    """Write content to a .docx file."""
    doc = Document()
    
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("# "):
            p = doc.add_heading(line[2:], level=0)
        elif line.startswith("## "):
            p = doc.add_heading(line[3:], level=1)
        elif line.startswith("---"):
            p = doc.add_paragraph("_" * 50)
        elif line.startswith("- "):
            p = doc.add_paragraph(line[2:], style="List Bullet")
        else:
            p = doc.add_paragraph(line)
    
    doc.save(path)


def generate_report(jd_keywords: dict, ats_analysis: dict, output_path: str):
    """Generate keyword match analysis report."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "ats_compatibility_score": ats_analysis["score"],
        "keywords_from_jd": {
            "action_verbs": jd_keywords["action_verbs"],
            "technical_terms": jd_keywords["technical_terms"],
            "acronyms": jd_keywords["acronyms"],
        },
        "matches": {
            "technical": ats_analysis["technical_matches"],
            "verbs": ats_analysis["action_verb_matches"],
            "acronyms": ats_analysis["acronym_matches"],
        },
        "missing_keywords": ats_analysis["missing_keywords"],
        "recommendations": generate_recommendations(ats_analysis),
    }
    
    Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def generate_recommendations(analysis: dict) -> list:
    """Generate actionable recommendations."""
    recs = []
    
    if analysis["score"] < 60:
        recs.append("LOW MATCH: Add more JD keywords to your resume for better ATS scoring")
    
    if len(analysis.get("action_verb_matches", [])) < 3:
        recs.append("Strengthen action verbs - use more JD-specific verbs like 'developed', 'implemented', 'led'")
    
    if analysis.get("missing_keywords"):
        recs.append(f"Consider adding these missing keywords: {', '.join(analysis['missing_keywords'][:5])}")
    
    if analysis["score"] >= 80:
        recs.append("STRONG MATCH: Your resume aligns well with this job description")
    
    return recs


def main():
    parser = argparse.ArgumentParser(
        description="Tailor resume and generate cover letter for a job description"
    )
    parser.add_argument("resume", help="Path to resume file (.docx, .txt, .md)")
    parser.add_argument("jd", help="Job description (file path or raw text)")
    parser.add_argument("-o", "--output-dir", default="output",
                       help="Output directory (default: ./output)")
    parser.add_argument("-c", "--company", default="[Company Name]",
                       help="Target company name")
    parser.add_argument("-p", "--position", default="[Position Title]",
                       help="Target position title")
    parser.add_argument("--format", choices=["txt", "docx", "both"], default="both",
                       help="Output format")
    
    args = parser.parse_args()
    
    # Load inputs
    print(f"[*] Loading resume: {args.resume}")
    resume_text = load_resume(args.resume)
    
    print(f"[*] Loading job description")
    jd_text = load_jd(args.jd)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract keywords and analyze
    print("[*] Analyzing job description keywords...")
    jd_keywords = extract_keywords(jd_text)
    
    print(f"    Found {len(jd_keywords['action_verbs'])} action verbs")
    print(f"    Found {len(jd_keywords['technical_terms'])} technical terms")
    print(f"    Found {len(jd_keywords['acronyms'])} acronyms")
    
    ats_analysis = analyze_ats_score(resume_text, jd_keywords)
    print(f"[*] ATS Compatibility Score: {ats_analysis['score']}%")
    
    # Generate tailored documents
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.format in ("txt", "both"):
        resume_out = output_dir / f"tailored_resume_{timestamp}.txt"
        print(f"[*] Generating tailored resume: {resume_out}")
        tailor_resume(resume_text, jd_text, str(resume_out))
    
    if args.format in ("docx", "both"):
        resume_out = output_dir / f"tailored_resume_{timestamp}.docx"
        print(f"[*] Generating tailored resume (DOCX): {resume_out}")
        tailor_resume(resume_text, jd_text, str(resume_out))
    
    if args.format in ("txt", "both"):
        cover_out = output_dir / f"cover_letter_{timestamp}.txt"
        print(f"[*] Generating cover letter: {cover_out}")
        generate_cover_letter(resume_text, jd_text, str(cover_out),
                             args.company, args.position)
    
    if args.format in ("docx", "both"):
        cover_out = output_dir / f"cover_letter_{timestamp}.docx"
        print(f"[*] Generating cover letter (DOCX): {cover_out}")
        generate_cover_letter(resume_text, jd_text, str(cover_out),
                             args.company, args.position)
    
    # Generate analysis report
    report_out = output_dir / f"ats_report_{timestamp}.json"
    print(f"[*] Generating ATS analysis report: {report_out}")
    report = generate_report(jd_keywords, ats_analysis, str(report_out))
    
    print("\n" + "=" * 50)
    print("TAILORING COMPLETE")
    print(f"ATS Score: {ats_analysis['score']}%")
    print(f"Output directory: {output_dir.absolute()}")
    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
