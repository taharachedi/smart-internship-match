import json, os, time
import requests

# Second official source, recommended by the instructor when France Travail's
# "Offres d'emploi v2" API is not available (email of 05/11/2026): Adzuna API.
# Free plan = limited number of calls -> this script is run MANUALLY only
# (workflow_dispatch, no schedule), at most once a week. One call = up to 50 offers.

APP_ID = os.environ["ADZUNA_APP_ID"]
APP_KEY = os.environ["ADZUNA_APP_KEY"]

COUNTRY = "fr"
SEARCH_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
SEARCH_PARAMS = {
    "what": "stage informatique",   # same keywords as fetch_offers.py (France Travail)
    "results_per_page": 50,
    "sort_by": "date",
    "content-type": "application/json",
}
OUT_PATH = "data/offers/adzuna_offers.json"


def search_offers(retries=3, backoff=5):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                SEARCH_URL,
                params={**SEARCH_PARAMS, "app_id": APP_ID, "app_key": APP_KEY},
                timeout=(10, 30),
            )
            print(f"  attempt {attempt}/{retries}: HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  attempt {attempt}/{retries} failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"  response body: {e.response.text[:300]}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Could not search Adzuna after {retries} attempts") from last_error


def main():
    print(f"Searching Adzuna ({COUNTRY}) for '{SEARCH_PARAMS['what']}'...")
    data = search_offers()
    results = data.get("results", [])
    print(f"Adzuna reports {data.get('count')} matching offers; received {len(results)}")

    offers = []
    for o in results:
        offers.append({
            "id": f"adzuna_{o.get('id')}",
            "source": "adzuna",
            "title": o.get("title"),
            "company": (o.get("company") or {}).get("display_name"),
            "location": (o.get("location") or {}).get("display_name"),
            "description": o.get("description", ""),   # Adzuna returns a snippet, not the full text
            "url": o.get("redirect_url"),
            "date_posted": (o.get("created") or "")[:10] or None,
            "contract_type": o.get("contract_type"),
            "salary_min": o.get("salary_min"),
            "salary_max": o.get("salary_max"),
            "salary_is_predicted": o.get("salary_is_predicted"),
            "publishable": True,  # official API, displayed with "Jobs by Adzuna" attribution
        })

    os.makedirs("data/offers", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "search_params": SEARCH_PARAMS, "offers": offers}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUT_PATH} ({len(offers)} offers)")
    if offers:
        print("First offer:", offers[0]["title"], "@", offers[0]["company"], "-", offers[0]["location"])


if __name__ == "__main__":
    main()
