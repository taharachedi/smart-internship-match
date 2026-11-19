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


# Inputs:
# - data/offers/adzuna_structured.json : official Adzuna API offers, structured (LLM step),
#   publishable -> committed, so this script can run in GitHub Actions.
# - data/offers/structured_offers.json : OPTIONAL, local only (gitignored), Indeed offers
#   (scraped, publishable: false). Absent in GitHub Actions -> public output = Adzuna only.
ADZUNA_PATH = "data/offers/adzuna_structured.json"
LOCAL_PATH = "data/offers/structured_offers.json"


def main():
    profile = load_profile()
    with open(ADZUNA_PATH, encoding="utf-8") as f:
        adzuna = json.load(f)
    offers = list(adzuna["offers"])
    if os.path.exists(LOCAL_PATH):
        with open(LOCAL_PATH, encoding="utf-8") as f:
            offers += json.load(f)["offers"]
        print(f"Local file {LOCAL_PATH} found: added non-publishable offers (personal use only)")

    results = []
    for offer in offers:
        m = score_offer(profile, offer["required_skills"])
        results.append({**offer, **m})

    results.sort(key=lambda r: r["score"], reverse=True)
    for r in results:
        print(f"  {r['score']:.3f}  {r['title']} @ {r['company']}  ({r['source']}, "
              f"coverage {r['coverage']:.0%}, gaps: {r['gaps']})")

    os.makedirs("data/offers", exist_ok=True)
    with open("data/offers/matches_all_local.json", "w", encoding="utf-8") as f:
        json.dump(build_output(results, profile), f, indent=2, ensure_ascii=False)
    print(f"Wrote data/offers/matches_all_local.json ({len(results)} offers) -- gitignored, local only")

    # Public dashboard = publishable sources ONLY (manual's rule): scraped offers never
    # leave this machine, not even anonymized.
    public_results = [r for r in results if r.get("publishable", False)]
    n_pub = len(public_results)
    out = build_output(public_results, profile)
    out["n_offers_with_compensation"] = sum(1 for r in public_results if r.get("compensation_mentioned") or r.get("has_compensation"))
    out["n_offers_with_skills"] = sum(1 for r in public_results if r.get("required_skills"))
    out["pipeline"] = adzuna.get("pipeline", {})
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/matches.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote docs/data/matches.json ({n_pub} of {len(results)} offers -- publishable sources only)")


if __name__ == "__main__":
    main()
