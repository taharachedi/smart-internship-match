# Reflections — TP1 Smart Internship Match

**1. What was the hardest part of the project?**
Getting real data. The France Travail application was created correctly (OAuth2 client_credentials, secrets in GitHub Actions), but every token request returned `invalid_client`. I checked the secrets from inside the workflow (length and format only, never the values): ID 89 characters starting with `PAR_`, secret 64 characters, no hidden spaces. The real cause: the application had no authorized API, because "Offres d'emploi v2" is no longer in the list of APIs offered to new applications.

**2. How did you adapt?**
I kept the France Travail step in the weekly workflow with `continue-on-error`, and used a second source: 15 real Indeed internship offers, structured by an LLM (Claude, playing the role of Ollama in `extract_offers.py`). Because scraped content cannot be republished, these offers are `publishable: false`: they stay local, and the public dashboard only shows my own anonymized scores.

**3. How did you design the match KPI?**
`coverage` = share of required skills I have; `score` = the same share weighted by my level (level / 5). Matching is case-, space- and synonym-insensitive, because the LLM does not always spell a skill the same way. Weighting matters: Angular at level 2 must not count like Java at level 4.

**4. Which KPIs matter most?**
Pipeline health (offers per source, extraction errors found, offers with compensation 5/15) tells me whether I can trust the rest. Search effectiveness (average score 0.40, 4/15 good matches, top gap JavaScript) tells me whether my keywords target the right offers and what to learn. Outcome (applications sent, response rate) is the only one that measures real progress — and it is 0 today.

**5. Which AI errors did you catch?**
The extraction invented "Pandas" in 2 offers that only said "data analysis tools"; I removed it (one score dropped from 0.47 to 0.44). A posting stated "0,10 € par mois": faithfully copied, but absurd, so I rejected it. In the cover-letter drafts I checked that no tool missing from my profile is claimed as a skill.

**6. What did the monitoring show?**
Two manual runs plus a daily schedule, three rules (good offer not applied after 7 days, no response after 10 days, no good offer at all). Both runs were OK, but they made one fact visible: 0 applications sent. If nothing changes, R1 turns to ALERT on 18/11.

**7. What decisions will you take?**
Apply first to the 3 offers scoring ≥ 0.55 (GenAI Python 0.70, FullStack 0.60, Java 0.57) using the reviewed drafts; learn JavaScript then SQL (6 and 4 offers); ignore Big Data and PHP/WordPress offers.

**8. What would you improve?**
Merge France Travail and Indeed with de-duplication once the API is available again, weight "required" vs "nice to have" skills, and track the response rate over several weeks.
