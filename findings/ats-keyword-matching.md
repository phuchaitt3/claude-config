# How ATS keyword matching finds a resume

- **Question:** Does an applicant tracking system (ATS) match only the keywords in the job description, or also "assumed" skills that recruiters expect but the posting does not name (e.g. Git, Jupyter)?
- **Finding:**
  - An ATS is mostly a searchable database, not an automatic rejecter. Several sources call blanket auto-rejection a myth. The exceptions are knockout questions and hard filters a recruiter sets on the requisition (e.g. a required years-of-experience answer, location, work authorisation).
  - Recruiter searches and match scores are built from the posting. Sources describe the query as derived from the job description, typically 3–5 terms: a job title, 2–3 required skills, optionally a certification or location. Boolean search matches literal text (with OR for variants), so a term absent from the resume makes it invisible to a search for that term.
  - Some systems (Workday is cited) also match semantically or on related terms, and Workday's recruiter search reads structured profile fields (titles, skills, education) taken from the application. Sources disagree on how literal Workday's matching is.
  - No source says recruiters routinely search for tools a posting does not name. *Checker's inference:* keywords to keep are the posting's own terms (exact spelling, plus the abbreviation where one exists) and the core skills of the role's title. Universal tools the posting omits (Git, Jupyter, package managers) are unlikely search terms. Dropping them from a page-limited resume costs little, especially when a related term (GitHub) already appears elsewhere on the page. This matches [resume-skills-section-tailoring](resume-skills-section-tailoring.md): universal tools add little to a skills row.
- **Sources:**
  - ResumeGeni, how recruiters search inside an ATS; Workday ATS guide (vendor blogs): https://resumegeni.com/blog/how-recruiters-search-inside-ats , https://resumegeni.com/blog/workday-ats-resume-guide
  - atsverification.com, how ATS scoring works; how recruiters sort candidates (vendor blogs, 2026): https://atsverification.com/blog/how-ats-scoring-works/ , https://atsverification.com/blog/how-recruiters-sort-candidates-ats-2026/
  - Blake Crosley, how ATS systems actually work (practitioner write-up): https://blakecrosley.com/ko/work/ats-insider
  - Simplify, debunking ATS myths (job platform blog): https://simplify.jobs/blog/debunking-applicant-tracking-system-ats-myths
  - Hiration, does an ATS automatically reject your resume? (vendor blog): https://www.hiration.com/blog/ats-auto-reject-resume-myth/
  - University of Kentucky career centre, "Yes, Virginia, ATS do reject candidates based on the keywords" (university career centre): https://pigmancareers.uky.edu/blog/2024/08/04/yes-virginia-ats-do-reject-candidates-based-on-the-keywords-in-their-resumes/
  - Leonstaff, ATS blocklists and knockout questions (staffing blog): https://leonstaff.com/blogs/ats-blocklist-guide/
- **Limits:** Almost all sources are resume-optimisation vendors or career blogs with a commercial interest; no ATS vendor documentation (Workday, Greenhouse) or controlled study was read. Statistics such as "75% of resumes rejected" have no traceable source and are not used here. How a specific employer configures its ATS is unknown. Read through search summaries, not every page in full.
- **Checked:** 2026-11-11
