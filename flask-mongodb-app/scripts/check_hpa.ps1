# PowerShell diagnostic script to check HPA and metrics-server for this project

param()

Write-Host "Checking Kubernetes context and namespace..."
kubectl config current-context

Write-Host "\nListing HPAs in 'default' namespace..."
kubectl get hpa -n default || kubectl get hpa -A

Write-Host "\nDescribing the flask-app HPA..."
kubectl describe hpa flask-app-hpa -n default

Write-Host "\nChecking deployment and pods for 'flask-app'..."
kubectl get deployment flask-app -n default -o wide
kubectl get pods -l app=flask-app -n default -o wide

Write-Host "\nChecking resource usage via kubectl top (requires metrics-server)..."
kubectl top nodes
kubectl top pods -n default

Write-Host "\nChecking metrics API availability..."
try {
  $raw = kubectl get --raw "/apis/metrics.k8s.io/v1beta1" 2>$null
  if ($raw) { Write-Host "metrics.k8s.io API reachable" }
  else { Write-Host "metrics.k8s.io API not reachable" }
} catch {
  Write-Host "metrics.k8s.io API not reachable or error occurred"; Write-Host $_
}

Write-Host "\nListing apiservices for metrics..."
kubectl get apiservices | Select-String metrics

Write-Host "\nIf metrics are missing, consider installing or enabling metrics-server. For minikube: 'minikube addons enable metrics-server'"