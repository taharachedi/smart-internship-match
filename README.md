# 🎯 Smart Internship Match

Pipeline BI qui collecte des offres de stage en informatique, en extrait les compétences demandées, les compare à mon profil et publie un dashboard.

**Dashboard :** https://taharachedi.github.io/smart-internship-match/

## Architecture

| Étape | Fichier | Rôle |
|---|---|---|
| 1. Profil | `data/profile/my_skills.csv` | 14 compétences notées 1-4, chacune justifiée par une expérience (ALTEN, Capgemini, projets, TD BI) |
| 2. Collecte | `scripts/fetch_offers.py` | Appel OAuth2 à l'API France Travail « Offres d'emploi v2 » (workflow hebdomadaire) |
| 3. Structuration | `data/offers/indeed_offers.json` | 15 offres Indeed, compétences extraites par LLM (Claude) depuis la description complète |
| 4. Matching | `scripts/match_offers.py` | Score pondéré + KPI → `docs/data/matches.json` |
| 5. Automatisation | `.github/workflows/fetch_offers.yml` | Exécution manuelle + chaque lundi 7h UTC, commit automatique des résultats |
| 6. Restitution | `docs/index.html` | Dashboard Chart.js publié sur GitHub Pages |

## Méthode de score

`score = 100 × Σ (niveau_compétence / 4) / nombre_de_compétences_demandées`

- Comparaison insensible à la casse entre les compétences de l'offre et celles du profil.
- Une compétence absente du profil compte 0 ; une compétence maîtrisée au niveau 4 compte 1.
- Seuil « bonne correspondance » : **50 %**.

## KPI (3 catégories)

| Catégorie | KPI | Valeur |
|---|---|---|
| Santé du pipeline | Offres collectées | 15 |
| Santé du pipeline | Offres avec compétences extraites | 100 % (âge médian 32 jours) |
| Efficacité de la recherche | Score moyen | 50,4 % |
| Efficacité de la recherche | Bonnes correspondances | 10 / 15 (66,7 %) |
| Résultat | Meilleure offre | Capgemini – Développeur GenAI Python (85 %) |
| Résultat | Compétence à acquérir n°1 | JavaScript (6 offres) |

## Résultats et décisions

- **Top 3 où postuler :** Capgemini GenAI Python (85 %), Natixis FullStack (75 %), Capgemini Java (70,8 %).
- **Points forts confirmés :** Java, Spring Boot, tests automatisés, Python, CI/CD, Git, anglais (chacun demandé dans 6-7 offres sur 15).
- **Lacunes prioritaires :** JavaScript (6 offres), SQL (4), HTML/CSS (4), Agile (4) → un petit projet front JS + SQL permettrait de gagner 10-15 points sur plusieurs offres.
- Les offres Big Data (Scala, Spark, Hadoop) et front PHP/WordPress sont hors de mon profil : je ne les priorise pas.

## Limites et problèmes rencontrés

- **API France Travail indisponible :** l'application a bien été créée (OAuth2 client_credentials), mais l'API « Offres d'emploi v2 » n'apparaît pas dans la liste des API ajoutables. Sans API autorisée, le serveur renvoie `invalid_client`. Diagnostic fait en vérifiant la longueur et le format des secrets dans GitHub Actions (identifiant 89 caractères, clé 64, sans espace). L'étape est conservée dans le workflow avec `continue-on-error`.
- **Source de remplacement :** offres Indeed (connecteur de Claude), dont les compétences ont été extraites par LLM, comme dans le TD3. Seuls les champs structurés (titre, entreprise, lieu, date, lien, compétences) sont publiés, jamais les descriptions complètes.
- **Échantillon réduit :** 15 offres, concentrées en Île-de-France ; les scores dépendent de l'extraction des compétences et de l'auto-évaluation du profil.
- **Sécurité :** identifiants stockés uniquement dans GitHub Secrets ; aucun fichier d'identifiants ni de donnée personnelle sensible dans le repo.

## Pistes d'amélioration

- Rebrancher France Travail dès que l'API est de nouveau proposée, et fusionner les sources (dédoublonnage par titre + entreprise).
- Pondérer les compétences selon leur importance dans l'offre (obligatoire / souhaitée).
- Ajouter un suivi des candidatures envoyées (taux de réponse) comme KPI de résultat.
