"""Monitoring check (CM4): trigger -> run -> check, applied to my own outcome data.

Rules (my definition of "something is wrong with my search"):
  R1  a good offer (score >= 0.5) is still "to_apply" after 7 days  -> I am not acting
  R2  an application is "sent" with no update after 10 days         -> follow up
  R3  zero offers with score >= 0.5 in the latest matches           -> search keywords are off
Every run is appended to docs/data/monitoring.json, so the history proves how often it ran.
"""
import csv, json, os, time
from datetime import date, datetime

TRACKER = "data/tracking/applications.csv"
MATCHES = "docs/data/matches.json"
HISTORY = "docs/data/monitoring.json"
GOOD_SCORE = 0.5
STALE_TO_APPLY_DAYS = 7
NO_RESPONSE_DAYS = 10


def days_since(value):
    try:
        return (date.today() - datetime.strptime(value, "%Y-%m-%d").date()).days
    except (TypeError, ValueError):
        return None


def main():
    with open(TRACKER, encoding="utf-8") as f:
        apps = list(csv.DictReader(f))
    with open(MATCHES, encoding="utf-8") as f:
        matches = json.load(f)

    alerts = []
    for a in apps:
        status = a["status"].strip()
        score = float(a["score"] or 0)
        if status == "to_apply" and score >= GOOD_SCORE:
            age = days_since(a["last_update"])
            if age is not None and age > STALE_TO_APPLY_DAYS:
                alerts.append(f"R1 {a['offer_id']}: good match ({score}) still not applied after {age} days")
        if status == "sent":
            age = days_since(a["date_sent"] or a["last_update"])
            if age is not None and age > NO_RESPONSE_DAYS:
                alerts.append(f"R2 {a['offer_id']}: no response {age} days after sending -> follow up")

    n_good = sum(1 for o in matches["offers"] if o["score"] >= GOOD_SCORE)
    if n_good == 0:
        alerts.append("R3 no offer with score >= 0.5 -> review search keywords")

    counts = {}
    for a in apps:
        counts[a["status"]] = counts.get(a["status"], 0) + 1
    n_sent = sum(v for k, v in counts.items() if k in ("sent", "interview", "rejected", "offer"))
    n_answered = sum(v for k, v in counts.items() if k in ("interview", "rejected", "offer"))

    run = {
        "run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trigger": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "tracked": len(apps),
        "status_counts": counts,
        "applications_sent": n_sent,
        "response_rate_pct": round(100 * n_answered / n_sent, 1) if n_sent else None,
        "good_matches_available": n_good,
        "alerts": alerts,
        "status": "ALERT" if alerts else "OK",
    }

    history = {"runs": []}
    if os.path.exists(HISTORY):
        with open(HISTORY, encoding="utf-8") as f:
            history = json.load(f)
    history["runs"].append(run)
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(f"Monitoring run #{len(history['runs'])}: {run['status']} "
          f"({n_sent} sent, {n_good} good matches available)")
    for a in alerts:
        print("  ALERT", a)


if __name__ == "__main__":
    main()
