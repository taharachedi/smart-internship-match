# 🎯 Smart Internship Match

Système personnel d'aide à la décision pour ma recherche de stage : collecter de vraies offres, les structurer, les comparer à mes compétences, m'aider à agir (prioriser, adapter ma lettre) puis suivre les résultats.

**Dashboard :** https://taharachedi.github.io/smart-internship-match/

## 1. Pipeline

| Étape | Fichier | Où | Rôle |
|---|---|---|---|
| Profil | `data/profile/my_skills.csv` | repo | 14 compétences (niveau 1-5) + preuve concrète pour chacune |
| Acquisition officielle | `scripts/fetch_offers.py` + `fetch_offers.yml` | GitHub Actions, chaque lundi | API France Travail « Offres d'emploi v2 » (OAuth2) |
| Acquisition 2e source | Indeed (connecteur Claude) | local | 15 offres de stage réelles (10/11/2026) |
| Structuration (IA) | Claude, prompt de `extract_offers.py` | local | `required_skills`, `responsibilities`, `experience_required`, `compensation_mentioned` |
| KPI de matching | `scripts/match_offers.py` → `score_offer()` | local | score, coverage, matched, gaps |
| Action (IA) | `scripts/draft_cv.py` | local | paragraphe d'accroche pour le top 3, fondé uniquement sur mes preuves |
| Suivi | `data/tracking/applications.csv` | repo | tableau que je tiens moi-même (pas l'IA) |
| Monitoring | `scripts/monitor_applications.py` + `monitor.yml` | GitHub Actions, chaque jour | 3 règles d'alerte, historique dans `docs/data/monitoring.json` |
| Restitution | `docs/index.html` | GitHub Pages | dashboard Chart.js |

Fichiers **locaux uniquement** (gitignorés) : `structured_offers.json`, `matches_all_local.json`, `output/cv_drafts/`.

## 2. Le KPI de matching (`score_offer`)

- `coverage` = compétences demandées que j'ai / compétences demandées
- `score` = Σ (mon niveau / 5) pour les compétences trouvées / compétences demandées
- **Comparaison normalisée** : minuscules, espaces et synonymes (`REST API` = `API REST`, `anglais` = `English`, `Jenkins` → `CI/CD`...). Une simple égalité de chaînes sous-compterait les vraies correspondances, puisque l'IA ne renvoie pas toujours la même orthographe.
- **Pourquoi pondérer par le niveau ?** Avoir Angular au niveau 2 ne vaut pas Java au niveau 4. La couverture seule surestimerait les offres front.
- `matched` contient le nom de **ma** compétence, ce qui permet à `draft_cv.py` de retrouver la preuve correspondante. `gaps` contient le nom utilisé par l'offre.
- Une offre sans compétence extraite obtient 0, puisqu'il n'y a rien à défendre dans une lettre.

## 3. KPI (3 catégories)

| Catégorie | KPI | Valeur |
|---|---|---|
| Santé du pipeline | Offres collectées / par source | 15 (Indeed 15, France Travail 0) |
| Santé du pipeline | Offres avec compétences extraites | 100 % |
| Santé du pipeline | Erreurs d'extraction trouvées à la relecture | 3 sur 15 offres (voir §5) |
| Santé du pipeline | Offres indiquant une rémunération | 5 / 15 |
| Efficacité de la recherche | Score moyen / couverture moyenne | 0,40 / 58 % |
| Efficacité de la recherche | Bonnes correspondances (score ≥ 0,5) | 4 / 15 |
| Efficacité de la recherche | Lacune n°1 | JavaScript (6 offres) |
| Résultat | Candidatures envoyées / taux de réponse | 0 / — |
| Résultat | Exécutions du monitoring | 2 (manuelles) + 1 par jour |

KPI qui ne mesure pas « plus de candidatures, plus vite » : **la lacune n°1**. Elle me dit quoi apprendre, pas combien postuler.

## 4. Choix des graphiques (pour qui, quelle décision, pourquoi ce type)

| Visuel | Pour qui | Décision | Pourquoi ce type |
|---|---|---|---|
| Cartes KPI par catégorie | moi, en 5 secondes | « mon pipeline marche-t-il ? ma recherche cible-t-elle bien ? » | un chiffre + un contexte, groupés selon les 3 catégories demandées |
| Histogramme des scores | moi | élargir ou resserrer mes mots-clés | je veux la **forme** de la distribution (9 offres entre 0,4 et 0,6), pas comparer les offres une à une |
| Barres horizontales des compétences (vert / rouge) | moi | quoi apprendre en premier | les libellés sont longs, donc les barres sont horizontales et triées par fréquence. La couleur sépare ce que j'ai de ce qui me manque, sans légende à lire |
| Tableau des offres classées | moi | à quelles offres postuler en premier | j'ai besoin de détails exacts (compétences trouvées et manquantes), pas d'une tendance : un tableau convient mieux qu'un graphique |
| Historique du monitoring | moi / l'enseignant | « dois-je agir ? » | une liste chronologique avec un statut OK/ALERT : c'est le journal d'un contrôle, pas une mesure |

Pas de graphique des salaires : seules 5 offres sur 15 indiquent un chiffre, ce graphique serait surtout vide.

## 5. Erreurs d'IA repérées (relecture critique, CM5)

1. **Compétence inventée** : l'extraction a ajouté « Pandas » à 2 offres (GenAI Python et Python Finance) alors que les annonces disent seulement « outils d'analyse de données » ou « traitement de données ». Je l'ai retiré, et le score de l'offre Python Finance passe de 0,47 à 0,44. C'est exactement le risque d'une IA qui « complète » à partir du contexte.
2. **Chiffre absurde recopié** : une annonce indique « 0,10 € par mois » de rémunération. Le chiffre est bien dans le texte, donc une extraction fidèle le recopie, mais il est impossible (la gratification légale tourne autour de 4,35 €/h). Je l'ai rejeté : on passe de 6 à 5 offres avec rémunération.
3. **Brouillons de lettre** : je vérifie qu'aucun outil absent de mon profil (LangGraph, JavaScript, React...) n'est présenté comme une compétence. « Agile » n'apparaît que comme contexte (la squad chez ALTEN), pas comme maîtrise de Scrum.

## 6. Monitoring

Règles, c'est-à-dire ma définition de « ma recherche va mal » :
- **R1** : une offre avec un score ≥ 0,5 est encore `to_apply` après 7 jours. Je n'agis pas.
- **R2** : une candidature est `sent` sans réponse depuis 10 jours. Il faut relancer.
- **R3** : aucune offre n'a un score ≥ 0,5. Mes mots-clés ne ciblent plus les bonnes offres.

**Exécutions :** run n°1 et run n°2 le 10/11/2026 (manuels), puis un run chaque jour à 8h17 UTC. Résultat : `OK (0 sent, 4 good matches available)`.
**Ce que ça a montré :** aucune alerte pour l'instant, mais **0 candidature envoyée**. Si rien ne change, R1 passera en ALERT le 18/11 pour les 3 offres du top. C'est le contrôle qui transforme le dashboard en action.

## 7. Confidentialité et données

- Les identifiants France Travail sont uniquement dans GitHub Secrets. Le fichier d'identifiants n'a jamais été commité.
- Les offres Indeed sont du contenu scrapé, non republiable (`publishable: false`). Le dashboard public ne montre que **mes** scores, anonymisés (« Offre indeed n°1 »), jamais le titre, l'entreprise, le lien ou la description. Un premier fichier d'offres a été retiré du repo après coup ; il reste dans l'historique git.
- Les brouillons de lettre et le classement complet restent sur mon PC.
- Le profil ne contient que des compétences et des preuves professionnelles, aucune information administrative personnelle.

## 8. Problèmes rencontrés et limites

- **France Travail :** l'application a bien été créée, mais l'API « Offres d'emploi v2 » ne figure plus dans la liste des API ajoutables. Sans API autorisée, le token renvoie `invalid_client`. J'ai vérifié les secrets depuis le workflow (longueur et format uniquement : identifiant de 89 caractères commençant par `PAR_`, clé de 64 caractères) pour écarter une erreur de copie. L'étape reste dans le workflow avec `continue-on-error`, pour fonctionner dès que l'API sera de nouveau proposée.
- **Petit échantillon** (15 offres, majoritairement en Île-de-France) et **profil auto-évalué** : les scores servent à classer les offres, ce ne sont pas des probabilités d'embauche.
- Le score donne le même poids à une compétence « obligatoire » et à une compétence « appréciée ».

## 9. Décisions

1. Postuler d'abord aux 3 offres avec un score ≥ 0,55 (GenAI Python 0,70, FullStack 0,60, Java 0,57), avec les brouillons relus.
2. Combler JavaScript puis SQL : un petit projet front JS + SQL ferait gagner des points sur 6 offres.
3. Ignorer les offres Big Data (Scala/Spark) et PHP/WordPress, trop éloignées de mon profil.
