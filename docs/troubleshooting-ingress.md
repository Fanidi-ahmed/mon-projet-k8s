# Fiche de Troubleshooting : Ingress Nginx sur Kind

Cette fiche répertorie les erreurs rencontrées lors du déploiement de l'Ingress Controller et de la ressource Ingress sur un cluster Kind, avec les solutions appliquées.

---

## Erreur 1 : Conflit Helm "release name check failed"

**Message :**
`Error: INSTALLATION FAILED: release name check failed: cannot reuse a name that is still in use`

**Cause :** Helm a trouvé une trace résiduelle d'une installation précédente (un Secret Helm orphelin) dans le namespace.

**Solution :**
Supprimer le secret de release orphelin, ou supprimer le namespace entier.
```bash
kubectl get secrets -n ingress-nginx | grep sh.helm.release
kubectl delete secret sh.helm.release.v1.ingress-nginx.v1 -n ingress-nginx
# OU
kubectl delete namespace ingress-nginx

-----------------

Erreur 2 : Conflit de "Field Manager" (kubectl vs Helm)

Message :
Error: UPGRADE FAILED: conflict occurred while applying object ... conflict with "kubectl-client-side-apply"

Cause : Les ressources (ClusterRole, Webhook, Service) existaient déjà et avaient été créées par kubectl apply. Helm refuse de prendre le contrôle sans autorisation explicite.

Solution :
Forcer Helm à utiliser l'ancienne méthode (Client-Side) pour écraser les résidus :

bash
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --set controller.hostPort.enabled=true \
  --force \
  --server-side=false
Si le conflit persiste, nettoyer manuellement les ressources cluster-wide :

bash
kubectl delete validatingwebhookconfiguration ingress-nginx-admission --ignore-not-found
kubectl delete clusterrole ingress-nginx --ignore-not-found
kubectl delete clusterrolebinding ingress-nginx --ignore-not-found
kubectl delete ingressclass nginx --ignore-not-found

----------------

Erreur 3 : Namespace bloqué en "Terminating"
Message :
La commande kubectl delete namespace ingress-
nginx
 ne se termine jamais.

Cause : Un composant (webhook d'admission ou APIService) empêche la suppression définitive du namespace.

Solution :
Forcer la suppression en vidant les finalizers du namespace :

bash
kubectl patch namespace ingress-nginx -p '{"spec":{"finalizers":null}}' --type=merge
Si cela échoue, utiliser la méthode manuelle (API) :

bash
kubectl get namespace ingress-nginx -o json | \
python3 -c "import sys,json; data=json.load(sys.stdin); data['spec']['finalizers']=[]; print(json.dumps(data))" > /tmp/ns.json

kubectl replace --raw /api/v1/namespaces/ingress-nginx/finalize -f /tmp/ns.json

-------------------

Erreur 4 : curl: (7) Failed to connect to localhost port 80
Message :
Impossible de joindre l'Ingress depuis le Mac alors que le pod contrôleur est Running.

Cause : Le cluster Kind a été créé par défaut, sans mapper les ports 80/443 de la machine hôte vers le nœud du cluster.

Solution :
Recréer le cluster Kind avec un fichier de configuration incluant extraPortMappings.

Créer kind-config.yaml :

yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
Recréer le cluster :

bash
kind delete cluster
kind create cluster --config kind-config.yaml
Réinstaller l'Ingress Controller avec le manifeste officiel Kind :

bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
Bonnes pratiques retenues
Toujours nettoyer les ressources cluster-wide (ClusterRole, Webhook, IngressClass) lors de la suppression d'un composant. Supprimer un namespace ne les supprime pas.

Comprendre la différence entre kubectl apply et helm install : ils gèrent tous deux les ressources, mais avec des "Field Managers" différents, ce qui peut créer des conflits.

Sur Kind, l'Ingress nécessite un mapping de ports (extraPortMappings). Sans cela, le contrôleur tourne mais n'est pas accessible depuis l'extérieur.

Utiliser
kubectl wait
 pour s'assurer que le contrôleur est prêt avant de créer des ressources Ingress.
