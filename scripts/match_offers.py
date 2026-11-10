import csv, json, os, time

# Scale of the "level" column in my_skills.csv (1-5 self-assessment, see Step 4).
MAX_LEVEL = 5

# Same skill, different spellings: the LLM extraction is not consistent
# (case, accents, short forms). Every name is reduced to one canonical key
# before comparing, so "REST API", "api rest" and "API REST" all match.
ALIASES = {
    "rest api": "api rest",
    "apis": "api rest",
    "api": "api rest",
    "springboot": "spring boot",
    "spring": "spring boot",
    "tests": "automated testing",
    "unit tests": "automated testing",
    "tests unitaires": "automated testing",
    "ci": "ci/cd",
    "cd": "ci/cd",
    "github actions": "ci/cd",
    "jenkins": "ci/cd",
    "anglais": "english",
    "llm": "llm integration",
    "ia générative": "llm integration",
    "genai": "llm integration",
    "dataviz": "data visualization",
}


def norm(skill):
    key = " ".join(str(skill).strip().lower().split())
    return ALIASES.get(key, key)


def load_profile(path="data/profile/my_skills.csv"):
    profile = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            profile[row["skill"]] = {"level": int(row["level"]), "evidence": row["evidence"]}
    return profile


def score_offer(profile, required_skills):
    """Match KPI (my design choice, CM2).

    - Comparison is case/space/alias-insensitive (norm()), because the AI
      extraction returns the same skill with inconsistent spellings.
    - coverage = share of the offer's required skills I have (0-1).
    - score    = coverage weighted by my self-assessed level:
                 sum(level / MAX_LEVEL for matched skills) / n_required.
      A skill I have at level 5 counts 1, at level 2 counts 0.4, missing counts 0.
    - An offer with no extracted skill gets 0: nothing to defend in a cover letter.
    - "matched" returns MY profile's skill names (so draft_cv.py finds the evidence),
      "gaps" returns the offer's names for what I don't have.
    """
    req = []
    for s in required_skills or []:
        if norm(s) not in [norm(x) for x in req]:
            req.append(s)  # de-duplicate within one offer
    if not req:
        return {"score": 0.0, "coverage": 0.0, "matched": [], "gaps": []}

    by_key = {norm(name): name for name in profile}
    matched, gaps, weight = [], [], 0.0
    for s in req:
        name = by_key.get(norm(s))
        if name:
            matched.append(name)
            weight += profile[name]["level"] / MAX_LEVEL
        else:
            gaps.append(s)

    return {
        "score": round(weight / len(req), 3),
        "coverage": round(len(matched) / len(req), 3),
        "matched": matched,
        "gaps": gaps,
    }


def build_output(results, profile):
    gap_counts = {}
    matched_counts = {}
    for r in results:
        for g in r["gaps"]:
            gap_counts[g] = gap_counts.get(g, 0) + 1
        for s in r["matched"]:
            matched_counts[s] = matched_counts.get(s, 0) + 1
    top_gaps = sorted(gap_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_matched = sorted(matched_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    n_with_comp = sum(1 for r in results if r.get("compensation_mentioned"))
    sources = {}
    for r in results:
        sources[r["source"]] = sources.get(r["source"], 0) + 1
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_offers": len(results),
        "offers_per_source": sources,
        "offers": results,
        "top_skill_gaps": [{"skill": s, "count": c} for s, c in top_gaps],
        "top_matched_skills": [{"skill": s, "count": c, "level": profile[s]["level"]} for s, c in top_matched],
        "n_offers_with_compensation": n_with_comp,
    }


# Fields that identify a scraped posting. Removed from non-publishable offers
# before anything goes to the public dashboard: only my own analysis
# (score, coverage, matched, gaps) is published, never the listing itself.
IDENTIFYING_FIELDS = ("title", "company", "location", "url", "responsibilities",
                      "experience_required", "compensation_mentioned", "date_posted")


def anonymize(r, i):
    clean = {k: v for k, v in r.items() if k not in IDENTIFYING_FIELDS}
    clean["id"] = f"offer_{i:02d}"
    clean["title"] = f"Offre {r['source']} n°{i}"
    clean["has_compensation"] = bool(r.get("compensation_mentioned"))
    return clean


def main():
    profile = load_profile()
    with open("data/offers/structured_offers.json", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for offer in data["offers"]:
        m = score_offer(profile,
