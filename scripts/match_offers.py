"""Match internship offers against my skills profile.

Input : data/profile/my_skills.csv      (skill, level 1-4)
        data/offers/indeed_offers.json  (structured offers, skills extracted)
Output: docs/data/matches.json          (scores + KPIs for the dashboard)
"""
import csv
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_CSV = ROOT / "data" / "profile" / "my_skills.csv"
OFFERS_JSON = ROOT / "data" / "offers" / "indeed_offers.json"
OUTPUT_JSON = ROOT / "docs" / "data" / "matches.json"

MAX_LEVEL = 4
GOOD_MATCH = 50  # score (%) from which an offer is worth applying to


def load_profile(path):
    """Return {skill_lowercase: level} from the skills CSV."""
    profile = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        skill_col = next((c for c in cols if c.strip().lower() in ("skill", "competence", "compétence")), cols[0])
        level_col = next((c for c in cols if c.strip().lower() in ("level", "niveau")), cols[1])
        for row in reader:
            name = (row.get(skill_col) or "").strip()
            if not name:
                continue
            try:
                level = int(float(row.get(level_col) or 0))
            except ValueError:
                level = 0
            profile[name.lower()] = max(0, min(level, MAX_LEVEL))
    return profile


def score_offer(offer_skills, profile):
    """Score = weighted share of required skills I have (case-insensitive)."""
    if not offer_skills:
        return 0.0, [], []
    matched = [s for s in offer_skills if s.lower() in profile]
    missing = [s for s in offer_skills if s.lower() not in profile]
    weight = sum(profile[s.lower()] / MAX_LEVEL for s in matched)
    return round(100 * weight / len(offer_skills), 1), matched, missing


def days_old(published):
    try:
        return (date.today() - datetime.strptime(published, "%Y-%m-%d").date()).days
    except (TypeError, ValueError):
        return None


def main():
    profile = load_profile(SKILLS_CSV)
    offers = json.loads(OFFERS_JSON.read_text(encoding="utf-8"))

    results = []
    for o in offers:
        score, matched, missing = score_offer(o.get("skills", []), profile)
        results.append({
            "title": o.get("title"),
            "company": o.get("company"),
            "location": o.get("location"),
            "published": o.get("published"),
            "age_days": days_old(o.get("published")),
            "url": o.get("url"),
            "source": o.get("source"),
            "score": score,
            "matched": matched,
            "missing": missing,
        })
    results.sort(key=lambda r: r["score"], reverse=True)

    n = len(results)
    with_skills = sum(1 for o in offers if o.get("skills"))
    ages = [r["age_days"] for r in results if r["age_days"] is not None]
    good = [r for r in results if r["score"] >= GOOD_MATCH]
    demand = Counter(s for o in offers for s in o.get("skills", []))
    gaps = Counter(s for r in results for s in r["missing"])

    kpis = {
        "pipeline_health": {
            "offers_collected": n,
            "offers_with_skills_pct": round(100 * with_skills / n, 1) if n else 0,
            "median_offer_age_days": sorted(ages)[len(ages) // 2] if ages else None,
            "sources": sorted({r["source"] for r in results if r["source"]}),
        },
        "search_effectiveness": {
            "average_score": round(sum(r["score"] for r in results) / n, 1) if n else 0,
            "good_matches": len(good),
            "good_match_rate_pct": round(100 * len(good) / n, 1) if n else 0,
            "threshold": GOOD_MATCH,
        },
        "outcome": {
            "best_offer": f'{results[0]["company"]} - {results[0]["title"]}' if results else None,
            "best_score": results[0]["score"] if results else None,
            "top_demanded_skills": demand.most_common(10),
            "top_missing_skills": gaps.most_common(8),
        },
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profile_skills": len(profile),
        "kpis": kpis,
        "matches": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Profile: {len(profile)} skills | Offers: {n} | Good matches (>= {GOOD_MATCH}%): {len(good)}")
    for r in results[:5]:
        print(f'  {r["score"]:5.1f}%  {r["company"]} - {r["title"]}')


if __name__ == "__main__":
    main()
