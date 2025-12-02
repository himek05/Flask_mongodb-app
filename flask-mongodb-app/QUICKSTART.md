# Quick Start Guide

Fast-track deployment instructions for the Flask-MongoDB application on Kubernetes.

## Prerequisites Check

```bash
# Check Python
python3 --version
# Required: Python 3.8+

# Check Docker
docker --version
# Required: Docker 20.10+

# Check Kubernetes (Minikube or Docker Desktop)
minikube version
# OR
kubectl version

# Check kubectl
kubectl version --client
# Required: kubectl 1.23+
```

## Local Setup (Part 1)

### Quick Setup on Windows

```powershell
# Navigate to project directory
cd flask-mongodb-app

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Set environment variable
$env:MONGODB_URI = "mongodb://localhost:27017/"
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

# Run Flask
flask run

# Test in another terminal
curl http://localhost:5000/
curl -X POST -H "Content-Type: application/json" -d '{"test":"data"}' http://localhost:5000/data
curl http://localhost:5000/data
```

### Quick Setup on macOS/Linux

```bash
cd flask-mongodb-app

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

docker run -d -p 27017:27017 --name mongodb mongo:latest

export MONGODB_URI="mongodb://localhost:27017/"
export FLASK_APP="app.py"
export FLASK_ENV="development"

flask run

# Test in another terminal
curl http://localhost:5000/
```

## Kubernetes Setup (Part 2)

### 1. Start Kubernetes Cluster

**For Minikube:**
```bash
minikube start --cpus=4 --memory=4096 --driver=docker
# Wait for cluster to be ready (1-2 minutes)
minikube status
```

**For Docker Desktop:**
- Enable Kubernetes in Docker Desktop settings
- Wait for "Kubernetes is running"

### 2. Build Docker Image

```bash
# For Minikube: use Minikube's Docker daemon
minikube docker-env | source  # macOS/Linux
# OR
minikube docker-env | Invoke-Expression  # Windows PowerShell

# Build the image
docker build -t flask-mongodb-app:latest .

# Verify image
docker images | grep flask-mongodb-app
```

**For Docker Desktop:**
```bash
docker build -t flask-mongodb-app:latest .
```

### 3. Deploy to Kubernetes

```bash
# Deploy MongoDB (includes PV, PVC, StatefulSet, Service)
kubectl apply -f k8s/mongodb-statefulset.yaml

# Wait for MongoDB to be ready
kubectl wait --for=condition=ready pod -l app=mongodb --timeout=300s

# Deploy Flask (includes Deployment, Service, HPA)
kubectl apply -f k8s/flask-deployment.yaml

# Wait for Flask to be ready
kubectl rollout status deployment/flask-app

# Apply Flask service and HPA
kubectl apply -f k8s/flask-service-hpa.yaml
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods
# Expected: mongodb-0 (Running), 2 flask-app pods (Running)

# Check services
kubectl get svc
# Expected: mongodb (ClusterIP: None), flask-app (NodePort)

# Check HPA
kubectl get hpa
# Expected: REFERENCE=Deployment/flask-app, TARGETS=<cpu usage>, MINPODS=2, MAXPODS=5

# Check detailed info
kubectl get all
```

### 5. Access the Application

**Option A: Port Forward (works on all platforms)**
```bash
kubectl port-forward svc/flask-app 5000:5000 &

# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/data
```

**Option B: Minikube Service URL**
```bash
minikube service flask-app --url
# Copy the URL and test
curl <minikube-url>/
```

**Option C: NodePort (Docker Desktop)**
```bash
# Port 30500 is exposed on localhost
curl http://localhost:30500/
```

### 6. Test the Application

```bash
# 1. Health check
curl http://localhost:5000/health
# Expected: {"status": "healthy"}

# 2. Root endpoint
curl http://localhost:5000/
# Expected: Welcome message with timestamp

# 3. Insert data
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"John Doe","department":"IT"}' \
  http://localhost:5000/data
# Expected: {"status": "Data inserted", "id": "..."}

# 4. Retrieve data
curl http://localhost:5000/data
# Expected: [{"name":"John Doe","department":"IT"}]

# 5. Insert more data
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"Jane Smith","department":"HR"}' \
  http://localhost:5000/data

curl http://localhost:5000/data
# Expected: Both records returned
```

## Useful Commands

### Pod Management

```bash
# View pods
kubectl get pods
kubectl get pods -w  # Watch for changes

# Pod details
kubectl describe pod <pod-name>

# Pod logs
kubectl logs <pod-name>
kubectl logs -f <pod-name>  # Follow logs

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/bash

# Delete pod (auto-replaced by deployment)
kubectl delete pod <pod-name>
```

### Debugging

```bash
# Check resource usage
kubectl top pods
kubectl top nodes

# Check events
kubectl get events
kubectl get events --sort-by='.lastTimestamp'

# View YAML configuration
kubectl get deployment flask-app -o yaml
kubectl get pod <pod-name> -o yaml

# Describe resources
kubectl describe deployment flask-app
kubectl describe svc flask-app
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment flask-app --replicas=3

# View HPA status
kubectl get hpa
kubectl describe hpa flask-app-hpa

# Watch HPA in action
kubectl get hpa -w
```

### Deployment Management

```bash
# View deployment status
kubectl rollout status deployment/flask-app

# View rollout history
kubectl rollout history deployment/flask-app

# Rollback to previous version
kubectl rollout undo deployment/flask-app
```

## Cleanup

```bash
# Delete all Kubernetes resources
kubectl delete -f k8s/

# Verify all deleted
kubectl get all

# Stop Minikube (optional)
minikube stop

# Delete Minikube cluster (optional)
minikube delete

# Stop MongoDB container (local setup)
docker stop mongodb
docker rm mongodb
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status and events
kubectl describe pod <pod-name>

# View pod logs
kubectl logs <pod-name>

# Common issues:
# - Image not found: Ensure docker build was successful
# - CrashLoopBackOff: Check logs, database might not be ready
# - ImagePullBackOff: Use imagePullPolicy: Never for local images
```

### Flask Cannot Connect to MongoDB

```bash
# Check MongoDB pod is running
kubectl get pod -l app=mongodb

# Check service DNS resolution
kubectl exec -it <flask-pod> -- nslookup mongodb

# Test MongoDB connectivity
kubectl exec -it <flask-pod> -- bash
# Inside pod:
curl mongodb:27017

# Check environment variables in Flask
kubectl exec -it <flask-pod> -- env | grep MONGODB
```

### HPA Not Scaling

```bash
# Check metrics server
kubectl get deployment metrics-server -n kube-system

# For Minikube, enable metrics
minikube addons enable metrics-server

# Check HPA status
kubectl describe hpa flask-app-hpa

# View HPA events
kubectl get events | grep HorizontalPodAutoscaler
```

### Cannot Access Flask Application

```bash
# Check service endpoints
kubectl get endpoints flask-app

# Test service DNS
kubectl exec -it <flask-pod> -- nslookup flask-app

# Check service ports
kubectl get svc flask-app -o yaml | grep -A 5 ports

# Verify port forwarding
kubectl port-forward svc/flask-app 5000:5000 --address=127.0.0.1
# If stuck, try killing process:
# pkill -f "port-forward"
```

## Performance Tuning

### Increase Resource Limits

Edit `k8s/flask-deployment.yaml` and `k8s/mongodb-statefulset.yaml`:

```yaml
resources:
  requests:
    cpu: "0.5"        # Increased from 0.2
    memory: "500Mi"   # Increased from 250Mi
  limits:
    cpu: "1"          # Increased from 0.5
    memory: "1Gi"     # Increased from 500Mi
```

Apply changes:
```bash
kubectl apply -f k8s/
```

### Adjust HPA Parameters

Edit `k8s/flask-service-hpa.yaml`:

```yaml
spec:
  minReplicas: 3              # Increased from 2
  maxReplicas: 10             # Increased from 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60  # Lower from 70 for more aggressive scaling
```

Apply changes:
```bash
kubectl apply -f k8s/flask-service-hpa.yaml
```

## Next Steps

1. **Read the Full README**: See `README.md` for detailed information
2. **Understand Design Choices**: See `DESIGN_AND_TESTING.md` for architecture details
3. **Review Testing Scenarios**: Learn how to test the deployment
4. **Explore Kubernetes**: Try manual scaling, pod deletion, and monitoring
5. **Advanced**: Implement replica sets, network policies, or ingress

