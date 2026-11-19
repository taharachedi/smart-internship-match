# 🎯 Smart Internship Match

Système personnel d'aide à la décision pour ma recherche de stage : collecter de vraies offres, les structurer, les comparer à mes compétences, m'aider à agir (prioriser, adapter ma lettre) puis suivre les résultats.

**Dashboard :** https://taharachedi.github.io/smart-internship-match/

## 1. Pipeline

| Étape | Fichier | Où | Rôle |
|---|---|---|---|
| Profil | `data/profile/my_skills.csv` | repo | 14 compétences (niveau 1-5) + preuve concrète pour chacune |
| Acquisition officielle 1 | `scripts/fetch_offers.py` + `fetch_offers.yml` | GitHub Actions, chaque lundi | API France Travail « Offres d'emploi v2 » (OAuth2), indisponible, voir §8 |
| Acquisition officielle 2 | `scripts/fetch_offers_adzuna.py` + `fetch_adzuna.yml` | GitHub Actions, **manuel uniquement** | API Adzuna, source recommandée par l'enseignant → `data/offers/adzuna_offers.json` |
| Structuration (IA) | prompt de `scripts/extract_offers.py` | Claude (rôle d'Ollama) | `required_skills`, `responsibilities`, `experience_required`, `compensation_mentioned` → `data/offers/adzuna_structured.json` |
| KPI de matching | `scripts/match_offers.py` → `score_offer()` + `match.yml` | GitHub Actions, manuel | score, coverage, matched, gaps → `docs/data/matches.json` |
| Action (IA) | `scripts/draft_cv.py` | local | paragraphe d'accroche pour le top 3, fondé uniquement sur mes preuves |
| Suivi | `data/tracking/applications.csv` | repo | tableau que je tiens moi-même (pas l'IA) |
| Monitoring | `scripts/monitor_applications.py` + `monitor.yml` | GitHub Actions, chaque jour | 3 règles d'alerte, historique dans `docs/data/monitoring.json` |
| Restitution | `docs/index.html` | GitHub Pages | dashboard Chart.js |

**Respect des limites Adzuna (consigne de l'enseignant) :** pas de lancement automatique, au maximum une collecte par semaine. Une collecte = 1 seul appel (50 offres).

**Sources et publication :** le dashboard public ne contient **que des sources publiables** (API officielle Adzuna, avec l'attribution « Jobs by Adzuna »). Les 15 offres Indeed collectées au début du projet (contenu scrapé, `publishable: false`) restent **uniquement en local**, dans les fichiers gitignorés.

## 2. Le KPI de matching (`score_offer`)

- `coverage` = compétences demandées que j'ai / compétences demandées
- `score` = Σ (mon niveau / 5) pour les compétences trouvées / compétences demandées
- **Comparaison normalisée** : minuscules, espaces et synonymes (`REST API` = `API REST`, `Jenkins` → `CI/CD`…). Une simple égalité de chaînes sous-compterait les vraies correspondances.
- **Pondération par le niveau** : Angular au niveau 2 ne vaut pas Java au niveau 4.
- `matched` contient le nom de **ma** compétence (pour que `draft_cv.py` retrouve la preuve) ; `gaps` contient le nom utilisé par l'offre.
- **Offre sans compétence extraite** : score 0 dans le classement, mais le dashboard l'affiche « ? » et l'**exclut des moyennes**. Une information inconnue n'est pas une mauvaise correspondance.

## 3. KPI (3 catégories) — collecte Adzuna du 19/11/2026

| Catégorie | KPI | Valeur |
|---|---|---|
| Santé du pipeline | Offres collectées | 50 (Adzuna, sur 369 disponibles) |
| Santé du pipeline | Après nettoyage | 31 (10 doublons + 9 hors sujet retirés) |
| Santé du pipeline | Offres avec compétences extraites | 19 / 31 (61 %) |
| Santé du pipeline | Rémunération indiquée | 1 / 31 |
| Santé du pipeline | France Travail | 0 (API non disponible) |
| Efficacité de la recherche | Score moyen / couverture moyenne (19 offres connues) | 0,11 / 17 % |
| Efficacité de la recherche | Bonnes correspondances (score ≥ 0,5) | 2 / 19 |
| Efficacité de la recherche | Lacune n°1 | Intelligence artificielle (6 offres) |
| Résultat | Candidatures envoyées / taux de réponse | 0 / — |
| Résultat | Exécutions du monitoring | 12 (dont 2 en ALERT) |

KPI qui ne mesure pas « plus de candidatures, plus vite » : **la lacune n°1**. Elle me dit quoi apprendre, pas combien postuler.

**Top 3 actuel :** Safran – ingénieur informatique Python (0,80) · Thales – automatisation du déploiement logiciel (0,60) · Thales – DevOps Docker / CI-CD (0,40).

## 4. Choix des graphiques (pour qui, quelle décision, pourquoi ce type)

| Visuel | Pour qui | Décision | Pourquoi ce type |
|---|---|---|---|
| Cartes KPI par catégorie | moi, en 5 secondes | « mon pipeline marche-t-il ? ma recherche cible-t-elle bien ? » | un chiffre + un contexte, groupés selon les 3 catégories demandées |
| Histogramme des scores | moi | élargir ou resserrer mes mots-clés | je veux la **forme** de la distribution (15 offres sur 19 sous 0,2 → mots-clés trop larges), pas comparer les offres une à une |
| Barres horizontales des compétences (vert / rouge) | moi | quoi apprendre en premier | libellés longs → barres horizontales triées par fréquence ; la couleur sépare ce que j'ai de ce qui me manque |
| Tableau des offres classées (avec lien) | moi | à quelles offres postuler en premier | j'ai besoin de détails exacts (compétences, lien pour postuler), pas d'une tendance |
| Historique du monitoring | moi / l'enseignant | « dois-je agir ? » | une liste chronologique avec un statut OK / ALERT : c'est le journal d'un contrôle, pas une mesure |

Pas de graphique des salaires : 1 seule offre sur 31 indique un chiffre.

## 5. Erreurs et pièges d'IA repérés (relecture critique, CM5)

1. **Compétence inventée** (première extraction, offres Indeed) : « Pandas » ajouté à 2 offres qui disaient seulement « outils d'analyse de données ». Retiré.
2. **Chiffre absurde recopié** (Indeed) : « 0,10 € par mois » de rémunération, bien présent dans le texte mais impossible. Rejeté.
3. **Contexte pris pour une exigence** (Adzuna, SFR) : l'extrait cite « IA, data, cloud, cybersécurité », mais ces mots décrivent l'**entreprise**, pas le stage. Non extraits.
4. **Faux ami** (Adzuna, Michelin) : « outil de conception générative » est du design paramétrique, **pas** de l'IA générative. Non converti en « LLM integration », ce qui aurait gonflé mon score.
5. **Faute de frappe** (Adzuna, Safran) : le titre dit « PHYTON ». Normalisé en « Python » à la relecture : une égalité exacte l'aurait raté.
6. **Brouillons de lettre** : vérification qu'aucun outil absent de mon profil (LangGraph, JavaScript, Docker…) n'est présenté comme une compétence.

## 6. Monitoring

Règles, c'est-à-dire ma définition de « ma recherche va mal » :
- **R1** : une offre avec un score ≥ 0,5 est encore `to_apply` après 7 jours → je n'agis pas.
- **R2** : une candidature est `sent` sans réponse depuis 10 jours → il faut relancer.
- **R3** : aucune offre n'a un score ≥ 0,5 → mes mots-clés ne ciblent plus les bonnes offres.

**Exécutions :** 2 manuelles le 10/11/2026, puis une par jour (12 au total le 19/11).
**Ce que ça a détecté :** les runs n°10 (18/11) et n°11 (19/11) sont passés en **ALERT (R1)**. Les 3 meilleures offres du suivi étaient toujours « à postuler » après 8 à 9 jours. Le contrôle a donc joué son rôle : il a transformé un dashboard « joli » en signal d'action. Le suivi a été mis à jour le 19/11 avec les nouvelles offres Adzuna (statut OK), et l'alerte reviendra si je ne postule pas sous 7 jours.

## 7. Confidentialité et données

- Identifiants France Travail et Adzuna uniquement dans GitHub Secrets ; aucun fichier d'identifiants commité.
- Dashboard public = sources publiables uniquement (Adzuna). Les offres Indeed, les brouillons de lettre et le classement complet restent sur mon PC (`.gitignore`).
- Le profil ne contient que des compétences et des preuves professionnelles.

## 8. Problèmes rencontrés et limites

- **France Travail :** l'application a été créée, mais l'API « Offres d'emploi v2 » ne figure pas dans la liste des API ajoutables → `invalid_client`. Les secrets ont été vérifiés depuis le workflow (format et longueur uniquement). L'étape est conservée avec `continue-on-error`.
- **Adzuna, plan gratuit :** 25 appels de test, et surtout **un extrait de 500 caractères seulement** par offre, souvent la présentation de l'entreprise. Résultat : 12 offres sur 31 sans compétence lisible. C'est la principale limite de la donnée, pas un défaut du pipeline. Le score de ces offres est « inconnu ».
- **Mots-clés trop larges :** « stage informatique » ramène beaucoup d'offres industrielles (informatique industrielle, électronique), d'où un score moyen faible (0,11). Piste : chercher « stage développeur Java » ou « stage Python ».
- Petit échantillon et profil auto-évalué : le score sert à classer les offres, ce n'est pas une probabilité d'embauche.

## 9. Décisions

1. Postuler d'abord à **Safran – Python (0,80)** et **Thales – automatisation du déploiement (0,60)**, puis Thales DevOps après une remise à niveau Docker.
2. Apprendre les bases de l'**IA appliquée** (demandée dans 6 offres sur 19) et **Docker**.
3. Affiner les mots-clés de la prochaine collecte hebdomadaire (« stage développeur Java / Python ») pour réduire les offres hors profil.
