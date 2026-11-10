import csv, json, os, time
import requests

# Drafts the opening paragraph of a cover letter for my best matches.
# Run locally only. In this project the LLM step was done with Claude instead of
# Ollama (allowed by the instructor): same prompt, same grounding rule -- only the
# evidence column of my_skills.csv may be used, nothing invented.
# Output goes to output/cv_drafts/, which is gitignored: drafts never reach the repo.

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:8b"
TOP_N = 3
MIN_COVERAGE = 0.3

PROMPT_TEMPLATE = """Tu es un(e) assistant(e) de redaction. Redige UNIQUEMENT le paragraphe
d'accroche (3-4 phrases) d'une lettre de motivation en francais, pour l'offre suivante, en
mettant en avant UNIQUEMENT les competences du candidat qui correspondent reellement a l'offre
(n'invente aucune competence ou experience non listee ci-dessous).

Offre: {title} chez {company}
Missions: {responsibilities}
Competences requises correspondantes chez le candidat: {matched_skills}
Preuves concretes du candidat: {evidence}

Ne pas halluciner d'experience professionnelle non mentionnee. Style: direct, concret, pas de
formules creuses.
"""


def load_profile(path="data/profile/my_skills.csv"):
    profile = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            profile[row["skill"]] = row["evidence"]
    return profile


def call_ollama(prompt, retries=3, backoff=5):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                OLLAMA_URL,
                proxies={"http": None, "https": None},
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=(10, 180),
            )
            resp.raise_for_status()
            return resp.json()["response"].strip()
        except Exception as e:
            last_error = e
            print(f"  Ollama call attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(backoff)
    raise RuntimeError(f"Ollama unreachable after {retries} attempts") from last_error


def main():
    profile = load_profile()
    # matches_all_local.json (all sources, gitignored): writing a private letter from a
    # scraped offer is personal use; only publishing the listing is restricted.
    with open("data/offers/matches_all_local.json", encoding="utf-8") as f:
        data = json.load(f)

    candidates = [o for o in data["offers"] if o["coverage"] >= MIN_COVERAGE][:TOP_N]
    print(f"Drafting opening paragraphs for {len(candidates)} of {data['n_offers']} offers "
          f"(coverage >= {MIN_COVERAGE:.0%}, top {TOP_N})")

    os.makedirs("output/cv_drafts", exist_ok=True)
    for offer in candidates:
        evidence = {s: profile[s] for s in offer["matched"] if s in profile}
        prompt = PROMPT_TEMPLATE.format(
            title=offer["title"], company=offer["company"] or "cette entreprise",
            responsibilities=", ".join(offer["responsibilities"]),
            matched_skills=", ".join(offer["matched"]),
            evidence=json.dumps(evidence, ensure_ascii=False),
        )
        print(f"  Drafting for: {offer['title']} @ {offer['company']}...")
        paragraph = call_ollama(prompt)
        out_path = f"output/cv_drafts/offer_{offer['id']}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"Offer: {offer['title']} @ {offer['company']}\n\n{paragraph}\n")
        print(f"    -> {out_path}")

    print("\nReminder: output/cv_drafts/ is gitignored -- review and edit every draft yourself, "
          "never commit them to the (public) repo.")


if __name__ == "__main__":
    main()
