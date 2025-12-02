# Kubernetes manifests for this project

This folder contains the Kubernetes manifests used for the sample Flask + MongoDB app.

Files of interest:
- `flask-deployment.yaml` - Deployment for the `flask-app` (includes resource requests/limits)
- `flask-service-hpa.yaml` - Service + HorizontalPodAutoscaler (HPA) for `flask-app`

Common problem: HPA appears missing or shows 0 metrics

Checklist to make the HPA work:

1. Ensure you are in the correct cluster context and namespace (manifests use `default`):

```bash
kubectl config current-context
kubectl get ns
kubectl get hpa -n default
```

2. Confirm the HPA exists and targets the `Deployment` named `flask-app`:

```bash
kubectl describe hpa flask-app-hpa -n default
```

3. Ensure the `metrics-server` is installed and functioning. If `kubectl top` returns errors, install or enable metrics-server.

- For `minikube`:

```bash
minikube addons enable metrics-server
```

- Generic install:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

If your kubelet uses self-signed certs (common in `kind` or custom clusters), you may need to allow insecure TLS for the metrics-server pod by adding the flag `--kubelet-insecure-tls` to the metrics-server container args.

4. The `Deployment` must specify CPU `requests` (HPA CPU utilization uses requests to compute utilization). The included `flask-deployment.yaml` already sets `requests.cpu: "0.2"` and `limits.cpu: "0.5"`.

5. If HPA still shows no metrics, check the HPA `status` and events for error messages:

```bash
kubectl get hpa flask-app-hpa -n default -o yaml
kubectl describe hpa flask-app-hpa -n default
```

Troubleshooting tips:
- Check `metrics-server` logs: `kubectl -n kube-system logs deploy/metrics-server`.
- If metrics-server fails to fetch node/pod metrics, confirm kubelets allow the metrics-server to scrape them (TLS or auth issues).

If you want, run the provided helper script `scripts/check_hpa.ps1` to run a set of diagnostics and summarize results.