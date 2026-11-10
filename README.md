# Mon Projet K8s - Entraînement CKA

Ce projet est un environnement d'entraînement pratique pour préparer la certification **CKA (Certified Kubernetes Administrator)**. Il déploie une application FastAPI connectée à Redis, avec du monitoring (Prometheus/Grafana) sur un cluster Kind.

## 🎯 Objectifs CKA couverts
- **Namespaces** : Isolation des ressources.
- **ConfigMaps & Secrets** : Gestion de la configuration.
- **PersistentVolumeClaims (PVC)** : Persistance des données (Redis).
- **Probes** : Résilience applicative (`readinessProbe`, `livenessProbe`).
- **Deployments & Services** : Exposition réseau (ClusterIP, LoadBalancer).
- **Monitoring** : Installation de Helm charts (Prometheus/Grafana).

## 🚀 Commandes utiles (Aide-mémoire CKA)
```bash
# Créer un namespace
kubectl create namespace mon-app

# Voir toutes les ressources d'un namespace
kubectl get all -n mon-app

# Dépanner un pod
kubectl describe pod <nom-du-pod> -n mon-app
kubectl logs <nom-du-pod> -n mon-app

# Vérifier les événements du cluster
kubectl get events -n mon-app --sort-by='.metadata.creationTimestamp'
