# Reflections — TP1 Smart Internship Match

**1. What was the hardest part of the project?**
Getting real data. The France Travail application was created correctly (OAuth2 client_credentials, secrets in GitHub Actions), but every token request returned `invalid_client`. I checked the secrets from inside the workflow (length and format only, never the values): ID 89 characters starting with `PAR_`, secret 64 characters, no hidden spaces. So the credentials were correct; the real cause was that the application had **no authorized API**, because "Offres d'emploi v2" is no longer in the list of APIs offered to new applications.

**2. How did you adapt?**
I kept the France Travail step in the workflow with `continue-on-error` (so it can be switched back on later) and used a replacement source: 15 real internship offers from Indeed, with skills extracted by an LLM from the full descriptions, as in TD3. The rest of the pipeline (matching, KPIs, dashboard, weekly automation) did not change, which shows the value of separating collection from analysis.

**3. Why this scoring method?**
`score = 100 × Σ(level / 4) / number of required skills`. It is simple, explainable and penalises both missing skills and weakly mastered ones. Its limit: all skills weigh the same, whether the offer says "required" or "nice to have".

**4. Which KPIs matter most, and why?**
- Pipeline health (offers collected, % with extracted skills, median age): if the data is stale or incomplete, every other number is meaningless.
- Search effectiveness (average score, good-match rate 10/15): tells me whether my search keywords target the right offers.
- Outcome (best offer, top missing skill): directly actionable — where to apply first and what to learn next.

**5. What did the data teach you about your profile?**
My back-end core (Java, Spring Boot, tests, CI/CD, Python, Git, English) is exactly what most offers ask for: 7 of the top 10 demanded skills are already in my profile. The main gap is front-end: JavaScript appears in 6 offers out of 15 and is missing from my profile, followed by SQL, HTML/CSS and Agile.

**6. What decisions will you take?**
Apply first to Capgemini GenAI Python (85 %), Natixis FullStack (75 %) and Capgemini Java (70.8 %); build a small JavaScript + SQL project to close the most frequent gap; ignore Big Data (Scala/Spark) and PHP/WordPress offers, which are far from my profile.

**7. What about data protection and ethics?**
API credentials live only in GitHub Secrets and the credentials file never touched the repository. Only structured fields are published (title, company, city, date, link, extracted skills), never full job descriptions. Personal administrative information from my preparation notes was deliberately left out of the skills profile.

**8. What would you improve with more time?**
Merge several sources with de-duplication (title + company), weight skills by importance in the offer, track applications sent and answers received as a true outcome KPI, and add a trend over time thanks to the weekly runs.
