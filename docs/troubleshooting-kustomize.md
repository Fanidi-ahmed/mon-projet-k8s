**$$
# Fiche de Documentation : Migration vers Kustomize & Troubleshooting

Cette fiche documente le passage d'une gestion manuelle des manifestes (avec `kubectl apply -f`) vers une gestion structurée et multi-environnements avec **Kustomize**, ainsi que les erreurs rencontrées lors de cette transition.

---

## 1. Pourquoi Kustomize ?

Avant Kustomize, nous avions un dossier `k8s/` avec des fichiers YAML statiques. Pour déployer en dev ou en prod, il fallait soit :
- Dupliquer les fichiers et modifier les valeurs (source d'erreurs).
- Utiliser des outils de templating complexes (Helm) pour un besoin simple.

Kustomize (natif à `kubectl`) permet de séparer le **socle commun** (`base`) des **spécificités par environnement** (`overlays`).

---

## 2. La nouvelle structure

```text
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── fastapi.yaml
│   ├── redis.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   └── redis-pvc.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml (1 réplica, namespace mon-app)
    └── prod/
        └── kustomization.yaml (3 réplicas, namespace mon-app-prod)

--------------------

## 3. La migration : De kubectl apply à kubectl apply -k
Avant (manuel) :

bash
kubectl apply -f k8s/apps/fastapi.yaml
kubectl apply -f k8s/apps/redis.yaml
kubectl apply -f k8s/config/configmap.yaml
# ... (risque d'oublier un fichier)
Après (Kustomize) :

bash
# Déployer l'environnement dev complet en une commande
kubectl apply -k k8s/overlays/dev/

# Voir le YAML final généré (sans l'appliquer)
kubectl kustomize k8s/overlays/dev/

-------------------

4. Les erreurs rencontrées et leurs solutions
Erreur 1 : Le pod FastAPI ne se crée pas (0/1, UP-TO-DATE 0)
Symptôme : Après le
kubectl apply -k
, le Deployment FastAPI affiche 0/1 mais aucun pod n'apparaît dans kubectl get pods.

Cause : Le ReplicaSet n'arrive pas à créer le pod. Dans notre cas, le problème était un état incohérent du ReplicaSet après plusieurs manipulations, ou un webhook d'admission bloquant la création.

Solution :

bash
# 1. Diagnostiquer le ReplicaSet
kubectl describe rs -n mon-app -l app=fastapi

# 2. Forcer la recréation (supprimer le Deployment et redéployer)
kubectl delete deployment fastapi -n mon-app
kubectl apply -k k8s/overlays/dev/
Erreur 2 : Readiness probe failed: HTTP probe failed with statuscode: 404
Symptôme : Le pod est en Running, mais 0/1 (non prêt). Les événements montrent une erreur 404 sur /ready.

Cause : L'image Docker déployée ne contenait pas la route /ready. Le code source avait été mis à jour en local, mais l'image sur Docker Hub (ou dans Kind) était l'ancienne version.

Solution :

bash
# 1. Reconstruire l'image localement
cd app
docker build -t ahmedfanidi/fastapi-demo:latest .

# 2. Charger l'image dans Kind (sans passer par Docker Hub)
kind load docker-image ahmedfanidi/fastapi-demo:latest

# 3. Forcer le redémarrage
cd ..
kubectl rollout restart deployment fastapi -n mon-app
Erreur 3 : push access denied (Docker Hub)
Symptôme : Impossible de pousser l'image sur Docker Hub (insufficient_scope).

Cause : Le token ou le compte Docker Hub n'a pas les droits d'écriture, ou le dépôt n'existe pas.

Solution : Utiliser un Personal Access Token (PAT) avec les droits "Read & Write" pour docker login, ou contourner le problème avec kind load docker-image (méthode utilisée en développement local).

----------

5. Bonnes pratiques retenues
Ne jamais dupliquer les YAML : Le base contient le socle, les overlays ne contiennent que les différences (réplicas, namespace, tags d'images).

Utiliser kubectl kustomize avant kubectl apply -k : Cela permet de voir exactement ce qui va être envoyé au cluster, et de détecter les erreurs de fusion.

Comprendre les Field Managers : kubectl apply -f et kubectl apply -k modifient les mêmes ressources. Si on change de méthode, il faut parfois forcer la prise de contrôle (--force-conflicts ou suppression/recréation).

Sur Kind, privilégier kind load pour les tests : Cela évite les allers-retours avec Docker Hub et accélère le cycle de développement.

