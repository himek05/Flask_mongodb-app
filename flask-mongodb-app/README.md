# Flask MongoDB Kubernetes Assignment

This project demonstrates a complete setup of a Flask application connected to MongoDB deployed on Kubernetes with proper authentication, persistent storage, autoscaling, and resource management.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Part 1: Local Setup](#part-1-local-setup)
3. [Part 2: Kubernetes Setup](#part-2-kubernetes-setup)
4. [DNS Resolution in Kubernetes](#dns-resolution-in-kubernetes)
5. [Resource Requests and Limits](#resource-requests-and-limits)
6. [Design Choices](#design-choices)
7. [Testing Scenarios](#testing-scenarios)
8. [Troubleshooting](#troubleshooting)

## Project Structure

```
flask-mongodb-app/
├── app.py                           # Flask application with MongoDB integration
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Multi-stage Docker build
├── .env                             # Environment variables for local development
├── k8s/
│   ├── mongodb-statefulset.yaml    # MongoDB StatefulSet with authentication
│   ├── flask-deployment.yaml       # Flask application deployment
│   └── flask-service-hpa.yaml      # Flask service and HPA configuration
└── README.md                        # This file
```

---

## Part 1: Local Setup

### Prerequisites

- Python 3.8 or later
- Docker
- Pip

### Step-by-Step Instructions

#### 1. Create Project Directory

```bash
mkdir flask-mongodb-app
cd flask-mongodb-app
```

#### 2. Set Up Virtual Environment

On Windows:
```powershell
python -m venv venv
venv\Scripts\activate
```

On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Benefits of Virtual Environment:**
- **Isolation**: Each project has its own Python packages, preventing version conflicts
- **Reproducibility**: Ensures the same environment across different machines
- **Security**: Prevents accidental modification of system Python packages
- **Easy Management**: Simplifies dependency management and testing
- **Clean Uninstall**: Just delete the venv directory to remove all packages

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Set Up MongoDB Using Docker

```bash
docker pull mongo:latest
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

This will start a MongoDB instance accessible on localhost:27017.

#### 5. Set Environment Variables

Create a `.env` file with:
```
MONGODB_URI=mongodb://localhost:27017/
```

On Windows:
```powershell
$env:MONGODB_URI = "mongodb://localhost:27017/"
```

On macOS/Linux:
```bash
export MONGODB_URI="mongodb://localhost:27017/"
```

#### 6. Run the Flask Application

On Windows:
```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
flask run
```

On macOS/Linux:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

The Flask application should now be running on `http://localhost:5000`.

#### 7. Test the Application

**GET request to / endpoint:**
```bash
curl http://localhost:5000/
```

Response:
```
Welcome to the Flask app! The current time is: <Date and Time>
```

**POST request to /data endpoint:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"sampleKey":"sampleValue"}' http://localhost:5000/data
```

Response:
```json
{"status": "Data inserted", "id": "<mongodb-object-id>"}
```

**GET request to /data endpoint:**
```bash
curl http://localhost:5000/data
```

Response:
```json
[{"sampleKey": "sampleValue"}]
```

---

## Part 2: Kubernetes Setup

### Prerequisites

- Docker Desktop with Kubernetes enabled, or
- Minikube installed and running
- kubectl command-line tool
- Helm (optional, for package management)

### Step 1: Build and Push Docker Image

#### Build the Docker Image

```bash
# Navigate to the project directory
cd flask-mongodb-app

# Build the image
docker build -t flask-mongodb-app:latest .
```

#### Push to Container Registry (Optional for Local Kubernetes)

For local Kubernetes (Minikube/Docker Desktop), you can use the local image directly. If using a remote registry:

```bash
# Tag the image
docker tag flask-mongodb-app:latest <your-registry>/flask-mongodb-app:latest

# Login to registry
docker login

# Push the image
docker push <your-registry>/flask-mongodb-app:latest
```

**Note:** For Minikube, if the image is not in a registry, use `imagePullPolicy: Never` in the deployment (already configured in our YAML files).

### Step 2: Start Kubernetes Cluster

#### If using Minikube:
```bash
minikube start --driver=docker --cpus=4 --memory=4096
minikube docker-env  # To use Minikube's Docker daemon
```

#### If using Docker Desktop:
Enable Kubernetes in Docker Desktop settings and ensure it's running.

### Step 3: Deploy MongoDB StatefulSet

MongoDB will be deployed with:
- Authentication enabled (admin user)
- Persistent storage using PV and PVC
- Health checks for reliability
- Resource requests and limits

Deploy the MongoDB StatefulSet:
```bash
kubectl apply -f k8s/mongodb-statefulset.yaml
```

Verify MongoDB is running:
```bash
kubectl get statefulsets
kubectl get pods -l app=mongodb
kubectl get svc mongodb
```

Wait for the pod to be running (may take a minute):
```bash
kubectl get pods -w
```

### Step 4: Build and Load Docker Image into Minikube

If using Minikube:
```bash
# Switch to Minikube's Docker daemon
minikube docker-env | Invoke-Expression  # On Windows PowerShell
# eval $(minikube docker-env)  # On macOS/Linux

# Build the image in Minikube's Docker
docker build -t flask-mongodb-app:latest .
```

### Step 5: Deploy Flask Application

Deploy the Flask application with 2 replicas:
```bash
kubectl apply -f k8s/flask-deployment.yaml
```

Verify the deployment:
```bash
kubectl get deployments
kubectl get pods -l app=flask-app
kubectl get svc flask-app
```

### Step 6: Deploy Flask Service and HPA

The Flask service exposes the application, and HPA enables auto-scaling:
```bash
kubectl apply -f k8s/flask-service-hpa.yaml
```

Verify the service and HPA:
```bash
kubectl get svc flask-app
kubectl get hpa
```

### Step 7: Access the Application

#### For Minikube:
```bash
# Get the service URL
minikube service flask-app --url

# Or access directly
kubectl port-forward svc/flask-app 5000:5000
# Then visit http://localhost:5000
```

#### For Docker Desktop:
```bash
# Access via NodePort (port 30500)
curl http://localhost:30500/
```

#### Port Forwarding (works for both):
```bash
kubectl port-forward svc/flask-app 5000:5000 &
curl http://localhost:5000/
```

### Step 8: Test All Endpoints

```bash
# Test health endpoint
curl http://localhost:5000/health

# Test root endpoint
curl http://localhost:5000/

# Insert data
curl -X POST -H "Content-Type: application/json" -d '{"name":"John","age":30}' http://localhost:5000/data

# Retrieve data
curl http://localhost:5000/data
```

---

## DNS Resolution in Kubernetes

### Overview

Kubernetes provides an internal DNS system that automatically resolves service names to their cluster IP addresses. This enables seamless inter-pod communication without hardcoding IP addresses.

### How DNS Resolution Works

1. **DNS Server**: Every Kubernetes cluster runs a DNS server (CoreDNS by default) that maintains records of all services and pods.

2. **Service DNS Names**: Services are automatically assigned DNS names in the format:
   ```
   <service-name>.<namespace>.svc.cluster.local
   ```
   - `<service-name>`: The name of the Kubernetes service
   - `<namespace>`: The namespace where the service is deployed
   - `svc.cluster.local`: Standard suffix for all services

3. **Examples**:
   - MongoDB Service: `mongodb.default.svc.cluster.local` or simply `mongodb` (same namespace)
   - Flask Service: `flask-app.default.svc.cluster.local` or `flask-app`

### Configuration for Flask-MongoDB Connection

In our deployment, the Flask application connects to MongoDB using:
```
mongodb://admin:securepassword123@mongodb:27017/?authSource=admin
```

**Explanation:**
- `mongodb` is resolved by the DNS server to the MongoDB service's cluster IP
- The MongoDB service uses a `ClusterIP: None` (headless service) for StatefulSet compatibility
- The application can connect without knowing the actual pod IP addresses
- If MongoDB pod is restarted, DNS automatically resolves to the new pod

### DNS Query Flow

```
Flask Pod requests "mongodb"
    ↓
Container DNS resolver (127.0.0.11:53 or /etc/resolv.conf)
    ↓
CoreDNS server in kube-system namespace
    ↓
CoreDNS checks its database for "mongodb.default.svc.cluster.local"
    ↓
Returns ClusterIP (internal service IP)
    ↓
Network packets routed to MongoDB service
    ↓
Service forwards to MongoDB pod(s)
```

### Service Discovery in Our Setup

**MongoDB Service (Headless Service):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: mongodb
spec:
  clusterIP: None  # Headless service for StatefulSet
  selector:
    app: mongodb
  ports:
    - port: 27017
      targetPort: 27017
```

**Why Headless Service?**
- StatefulSets require headless services to maintain stable network identities
- Each pod gets a unique DNS name: `mongodb-0.mongodb.default.svc.cluster.local`
- Enables direct pod-to-pod communication if needed

**Flask Service (ClusterIP Service):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-app
spec:
  type: NodePort  # Exposes on all nodes
  selector:
    app: flask-app
  ports:
    - port: 5000
      targetPort: 5000
      nodePort: 30500
```

### Testing DNS Resolution

```bash
# Get a shell in a Flask pod
kubectl exec -it <flask-pod-name> -- /bin/bash

# Test DNS resolution
nslookup mongodb
# Should resolve to the service cluster IP

# Test connectivity to MongoDB
curl -v mongodb:27017
# Connection should be established
```

---

## Resource Requests and Limits

### Overview

Kubernetes resource requests and limits ensure efficient cluster resource utilization and application stability.

### Key Concepts

#### Resource Requests
- **Definition**: The minimum amount of CPU and memory a container is guaranteed to receive
- **Use Case**: 
  - Kubernetes scheduler uses this to decide which node to place the pod on
  - Ensures the node has enough resources before scheduling
  - Prevents over-subscription of nodes
- **Example**: A Flask container requests 0.2 CPU and 250Mi memory

#### Resource Limits
- **Definition**: The maximum amount of CPU and memory a container is allowed to use
- **Use Case**:
  - Prevents a pod from consuming excessive resources
  - Protects the node and other pods from resource starvation
  - Triggers pod eviction if limits are exceeded
- **Example**: A Flask container is limited to 0.5 CPU and 500Mi memory

### Resource Units Explained

**CPU:**
- `1` CPU = 1 vCPU (virtual CPU)
- `0.1` CPU = `100m` (millicores)
- Supports fractional CPUs: `0.2`, `0.5`, `1.5`, etc.

**Memory:**
- `Mi` = Mebibyte (1,048,576 bytes)
- `Gi` = Gibibyte (1,073,741,824 bytes)
- `M` = Megabyte (1,000,000 bytes)
- `G` = Gigabyte (1,000,000,000 bytes)

### Our Configuration

**Flask Application:**
```yaml
resources:
  requests:
    cpu: "0.2"        # 200 millicores
    memory: "250Mi"   # 250 Mebibytes
  limits:
    cpu: "0.5"        # 500 millicores
    memory: "500Mi"   # 500 Mebibytes
```

**MongoDB:**
```yaml
resources:
  requests:
    cpu: "0.2"        # 200 millicores
    memory: "250Mi"   # 250 Mebibytes
  limits:
    cpu: "0.5"        # 500 millicores
    memory: "500Mi"   # 500 Mebibytes
```

### Resource Configuration Best Practices

1. **Right-Sizing Requests:**
   - Set requests slightly lower than actual peak usage
   - This leaves room for occasional spikes (limits)
   - Enables better scheduling across cluster

2. **Setting Limits:**
   - Limits should be 2-3x the requests
   - Too tight limits: application crashes/restarts
   - Too loose limits: wasted resources

3. **Monitoring:**
   - Use `kubectl top pods` to monitor actual usage
   - Adjust requests/limits based on observed metrics
   - Use tools like Prometheus for detailed metrics

### Example: Calculating Resources

For a Flask application with:
- Average CPU usage: 0.15 CPU
- Peak CPU usage: 0.35 CPU
- Average memory: 200Mi
- Peak memory: 400Mi

**Recommended Configuration:**
```yaml
requests:
  cpu: "0.15"        # Close to average
  memory: "200Mi"    # Close to average
limits:
  cpu: "0.5"         # > peak with buffer
  memory: "500Mi"    # > peak with buffer
```

### Resource Quota (Optional)

For namespace-level resource management:
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: default
spec:
  hard:
    requests.cpu: "4"
    requests.memory: "2Gi"
    limits.cpu: "10"
    limits.memory: "4Gi"
```

---

## Design Choices

### 1. **MongoDB StatefulSet vs Deployment**

**Choice:** StatefulSet

**Rationale:**
- StatefulSets maintain stable network identities (Pod DNS names)
- Enables persistent storage mounting per pod
- Supports ordered startup/shutdown
- MongoDB is a stateful application requiring stable identities

**Alternatives Considered:**
- Deployment with shared storage: Would complicate MongoDB replication setup
- Standalone pod: No auto-recovery on failure

### 2. **Headless Service for MongoDB**

**Choice:** Headless Service (clusterIP: None)

**Rationale:**
- Allows StatefulSet pods to have stable DNS names
- Each pod gets unique DNS: `mongodb-0.mongodb.default.svc.cluster.local`
- Enables direct pod discovery and communication
- Required for MongoDB replica sets (not used here, but good practice)

**Alternatives:**
- Regular ClusterIP Service: Would work but loses stable pod identities

### 3. **NodePort Service for Flask**

**Choice:** NodePort Service (port 30500)

**Rationale:**
- Exposes Flask application outside the cluster
- Simple for local testing on Minikube/Docker Desktop
- No external load balancer required
- Easy port mapping (30500)

**Alternatives:**
- LoadBalancer: Requires external load balancer (overkill for demo)
- ClusterIP: Only accessible within cluster (not suitable for this use case)
- Ingress: More complex, not needed for single application

### 4. **PersistentVolume and PersistentVolumeClaim**

**Choice:** Local PersistentVolume with hostPath

**Rationale:**
- MongoDB data persistence across pod restarts
- Simple setup for single-node Minikube/Docker Desktop
- Adequate for development and testing

**Alternatives:**
- Cloud-managed persistent storage (EBS, GCE persistent disks): Better for production
- emptyDir volumes: Loses data on pod restart (unacceptable for databases)

### 5. **MongoDB Authentication**

**Choice:** Root user authentication with initialization script

**Rationale:**
- Security best practice: Never run without authentication
- Root user created during initialization
- Additional Flask user (admin) with limited privileges
- Credentials stored in Kubernetes Secrets

**Alternatives:**
- LDAP/OIDC: More complex, not required for assignment
- SSL/TLS certificates: Good practice but not required for internal cluster communication

### 6. **Resource Requests and Limits Sizing**

**Choice:** 
- Request: 0.2 CPU, 250Mi memory
- Limit: 0.5 CPU, 500Mi memory

**Rationale:**
- Based on typical Flask and MongoDB lightweight usage
- 2.5x ratio provides headroom for spikes
- Allows multiple pods on single development machine
- Good balance between protection and flexibility

**Alternatives:**
- Higher limits: Would consume more resources
- No limits: Risks node resource exhaustion

### 7. **HPA Configuration**

**Choice:** 
- Min: 2 replicas
- Max: 5 replicas
- Scale at: 70% CPU utilization

**Rationale:**
- 2 replicas provide basic redundancy
- 5 max prevents runaway scaling
- 70% is moderate threshold (not too aggressive)
- CPU metric is most reliable for scaling decisions

**Alternatives:**
- Memory-based scaling: Less predictable than CPU
- Custom metrics: More complex setup
- Lower CPU threshold (e.g., 50%): More frequent scaling, higher cost

### 8. **Multi-Stage Docker Build**

**Choice:** Multi-stage Dockerfile with builder pattern

**Rationale:**
- Smaller final image (no pip cache, build tools)
- Faster deployment to cluster
- Separates build and runtime concerns
- Reduces security attack surface (no build tools in runtime)

**Alternatives:**
- Single stage: Larger image, simpler to understand
- Alpine base image: Even smaller but less compatible

---

## Testing Scenarios

### Test 1: Basic Connectivity and Endpoints

**Objective:** Verify Flask application responds to all endpoints

**Steps:**
```bash
# Test health endpoint
kubectl port-forward svc/flask-app 5000:5000 &
curl http://localhost:5000/health

# Test root endpoint
curl http://localhost:5000/

# Test data endpoint (empty initially)
curl http://localhost:5000/data
```

**Expected Results:**
```
Health: {"status": "healthy"}
Root: Welcome to the Flask app! The current time is: ...
Data: []
```

**Status:** ✓ PASS (if all endpoints respond correctly)

---

### Test 2: Database Insert and Retrieval

**Objective:** Verify MongoDB integration and data persistence

**Steps:**
```bash
# Insert data
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"Alice","role":"Engineer"}' \
  http://localhost:5000/data

curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"Bob","role":"Manager"}' \
  http://localhost:5000/data

# Retrieve data
curl http://localhost:5000/data

# Verify MongoDB persistence by checking pod restarts
kubectl delete pod mongodb-0
# Wait for pod restart
kubectl get pods -w

# Retrieve data again
curl http://localhost:5000/data
```

**Expected Results:**
```json
// After POST requests
[
  {"name":"Alice","role":"Engineer"},
  {"name":"Bob","role":"Manager"}
]

// Data persists after pod restart
[
  {"name":"Alice","role":"Engineer"},
  {"name":"Bob","role":"Manager"}
]
```

**Status:** ✓ PASS (if data persists after pod restart)

---

### Test 3: Pod Replica Management

**Objective:** Verify deployment maintains 2 replicas

**Steps:**
```bash
# Check initial replicas
kubectl get pods -l app=flask-app

# Delete one pod
kubectl delete pod <flask-pod-name>

# Observe new pod creation
kubectl get pods -l app=flask-app -w

# Verify service routes to both
kubectl get endpoints flask-app
```

**Expected Results:**
```
Initial: 2 running pods
After deletion: New pod starts immediately
Endpoints: Both pod IPs listed
```

**Status:** ✓ PASS

---

### Test 4: Horizontal Pod Autoscaling (HPA) - High Load Test

**Objective:** Verify HPA scales pods when CPU exceeds 70%

**Steps:**

1. **Monitor HPA:**
```bash
kubectl get hpa -w
```

2. **Generate Load in One Pod:**
```bash
# Get Flask pod name
POD_NAME=$(kubectl get pods -l app=flask-app -o jsonpath='{.items[0].metadata.name}')

# Execute CPU-intensive operation
kubectl exec -it $POD_NAME -- python -c "
import time
import hashlib
start = time.time()
while time.time() - start < 120:  # Run for 2 minutes
    hashlib.sha256(b'test' * 10000).hexdigest()
"
```

3. **Monitor Pod Scaling:**
```bash
# In another terminal
kubectl get pods -l app=flask-app -w
kubectl top pods -l app=flask-app
```

4. **Stop Load:**
```bash
# Stop the CPU-intensive operation (Ctrl+C)
# Wait 5 minutes for scale-down
kubectl get pods -l app=flask-app -w
```

**Expected Results:**
```
Initial: 2 pods
During load: 3, 4, or 5 pods (up to max)
CPU utilization: > 70%
After load: Scale back down to 2 pods after ~5 minutes
```

**Status:** ✓ PASS (if scaling behavior matches expectations)

---

### Test 5: Health Check and Self-Healing

**Objective:** Verify liveness and readiness probes

**Steps:**
```bash
# Check pod status
kubectl describe pod <flask-pod-name>
# Look at "Conditions" and "Probes" sections

# Simulate unhealthy state by breaking MongoDB connection
kubectl exec -it $MONGODB_POD -- mongod --shutdown

# Watch Flask pod behavior
kubectl get pods -l app=flask-app -w
# Pod should transition to not ready, then restart

# Verify recovery
# Wait for pod to restart
kubectl get pods -l app=mongodb -w
```

**Expected Results:**
```
Before outage: All conditions Ready/True
During outage: Pod shows not Ready
After restart: Pod recovers and becomes Ready again
```

**Status:** ✓ PASS (if pod auto-restarts on failure)

---

### Test 6: Cross-Pod Communication via DNS

**Objective:** Verify DNS resolution within cluster

**Steps:**
```bash
# Get into a Flask pod
kubectl exec -it <flask-pod-name> -- /bin/bash

# Inside pod: test DNS resolution
nslookup mongodb
# Should resolve to service IP

# Test MongoDB connectivity
mongo -u admin -p securepassword123 --authenticationDatabase admin mongodb://mongodb:27017/

# Inside MongoDB shell
db.flask_db.insertOne({test: "data"})
db.flask_db.findOne()
exit
```

**Expected Results:**
```
DNS: mongodb resolves to service IP (e.g., 10.x.x.x)
MongoDB: Successfully connected with credentials
Data: Can insert and retrieve data
```

**Status:** ✓ PASS

---

### Test 7: Resource Limits Enforcement

**Objective:** Verify resource limits prevent excessive usage

**Steps:**
```bash
# Monitor resource usage
kubectl top pods -l app=flask-app

# Check resource configuration
kubectl get pod <flask-pod-name> -o yaml | grep -A 5 resources

# Verify limits are applied correctly
# Expected: requests 0.2cpu/250Mi, limits 0.5cpu/500Mi
```

**Expected Results:**
```
Resource configuration matches specification
CPU/Memory usage within limits
No OOMKilled or CPU throttling errors
```

**Status:** ✓ PASS

---

### Test 8: Persistent Volume Persistence

**Objective:** Verify data survives pod restarts

**Steps:**
```bash
# Insert test data
curl -X POST -H "Content-Type: application/json" \
  -d '{"test":"persistence"}' \
  http://localhost:5000/data

# Delete MongoDB StatefulSet
kubectl delete statefulset mongodb

# Delete PVC to simulate restore from same storage
# kubectl delete pvc mongodb-pvc  # Don't do this for this test

# Recreate StatefulSet
kubectl apply -f k8s/mongodb-statefulset.yaml

# Wait for MongoDB to restart
kubectl get pods -w

# Verify data is still there
curl http://localhost:5000/data
```

**Expected Results:**
```json
Data persists after MongoDB pod restart:
[
  {"test":"persistence"}
]
```

**Status:** ✓ PASS

---

## Issues Encountered and Solutions

### Issue 1: MongoDB Connection Timeout

**Symptom:** Flask pod unable to connect to MongoDB

**Solutions Tried:**
1. Verified MongoDB service is running: `kubectl get svc mongodb`
2. Checked pod logs: `kubectl logs mongodb-0`
3. Verified credentials in Deployment env variables
4. Ensured proper DNS resolution: `kubectl exec -it <pod> -- nslookup mongodb`

**Resolution:** Ensure MongoDB pod is fully ready before Flask pods attempt connection. HPA and readiness probes help prevent this.

### Issue 2: PersistentVolume Not Binding

**Symptom:** PVC remains Pending

**Solutions Tried:**
1. Checked available PVs: `kubectl get pv`
2. Verified storage class exists: `kubectl get storageclass`
3. Checked PVC logs: `kubectl describe pvc mongodb-pvc`

**Resolution:** For Minikube, use `storageClassName: standard`. For Docker Desktop, ensure volumes are enabled.

### Issue 3: Image Pull Failures

**Symptom:** Flask pod stuck in ImagePullBackOff

**Solution:** Use `imagePullPolicy: Never` for local images not pushed to registry. Build image in Minikube's Docker daemon.

### Issue 4: HPA Not Scaling

**Symptom:** Pod count doesn't increase despite high CPU

**Solutions Tried:**
1. Verified HPA is created: `kubectl get hpa`
2. Checked metrics-server: `kubectl get deployment metrics-server -n kube-system`
3. Waited for initial metrics collection (usually 1-2 minutes)

**Resolution:** Metrics-server may not be installed. Install with:
```bash
# For Minikube
minikube addons enable metrics-server

# For Docker Desktop
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## Cleanup

To clean up all resources:

```bash
# Delete all Kubernetes resources
kubectl delete -f k8s/

# Delete the local MongoDB Docker container (if running separately)
docker stop mongodb
docker rm mongodb

# Deactivate Python virtual environment
deactivate
```

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/)

---

## Summary

This assignment demonstrates:
✓ Complete Flask-MongoDB application with proper error handling
✓ Docker containerization with multi-stage builds
✓ Kubernetes deployment with StatefulSet and Deployment patterns
✓ Database persistence with PV and PVC
✓ Service discovery and DNS resolution
✓ Horizontal Pod Autoscaling based on metrics
✓ Resource requests and limits for efficient usage
✓ Health checks and self-healing capabilities
✓ Secure database authentication
✓ Comprehensive testing and troubleshooting documentation

