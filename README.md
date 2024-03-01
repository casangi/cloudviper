# cloudviper
Cloud-native container orchestration system configurations for the DPS pilot

---
Before its refactoring into the multi-layered VIPER prototype under active development today, the CASA Next-Generation Infrastructure ([CNGI](https://cngi-prototype.readthedocs.io/en/latest/benchmarking.html#Commercial-Cloud)) prototype was deployed and scale-tested on commercial cloud resources using kubernetes. Since this concept will be revisited and expanded in the context of the ALMA unmitigated cube imaging pilot for the Data Processing System concept, these prior experiments have finally found their way into source control as a starting point for further development. That is this repository's raison d'etre.

The files in this repo are the configurations that were in use the last time we administered a kubernetes cluster via [kops](https://kops.sigs.k8s.io/) and [helm](https://helm.sh/) on [AWS](https://aws.amazon.com/console/).

This process essentially followed [the official documentation](https://kubernetes.io/docs/tasks/tools/) from kubernetes (when the kops documentation was still hosted there). Of course there are other ways to interact with k8s via cloud providers (such as e.g, [Amazon EKS](https://aws.amazon.com/eks/) or open-source shims like [dask-kubernetes](https://docs.dask.org/en/latest/deploying-kubernetes.html), etc.) and we might evolve these configurations to make use of those, as well as following other methods to deploy on premises.

## Creating a cluster

We relied on this relatively simple workflow to create our own kubernetes cluster with kops, 
Of course, this presumes the prior configuration of appropriately-permissioned accounts, existence of various SDKs, and so forth.
```
export KOPS_CLUSTER_NAME=test.k8s.local
export KOPS_STATE_STORE=s3://cngi-kops-state
kops create cluster --name=${KOPS_CLUSTER_NAME} --node-count=0 --node-size=m5dn.xlarge --master-size=t3.small --zones=us-east-1a
kops create secret --name ${KOPS_CLUSTER_NAME} sshpublickey admin -i $KEYFILE
kops edit ig --name=$KOPS_CLUSTER_NAME master-us-east-1a
kops edit ig --name=$KOPS_CLUSTER_NAME nodes
kops create ig --name=$KOPS_CLUSTER_NAME workers --subnet us-east-1a
# manually add cloudLabels to the spec of every config
# manually add a script to disable hyperthreading to workers config
# manually add taints to workers config plus extra entries to request spot instances
kops update cluster --name=${KOPS_CLUSTER_NAME} --yes
```
This should show some encouraging output such as:
```
Cluster is starting.  It should be ready in a few minutes.
Suggestions:
 * validate cluster: kops validate cluster --wait 10m
 * list nodes: kubectl get nodes --show-labels
 * ssh to the master: ssh -i $KEYFILE ubuntu@api.test.k8s.local
 * the ubuntu user is specific to Ubuntu. If not using Ubuntu please use the appropriate user based on your OS.
 * read about installing addons at: https://kops.sigs.k8s.io/operations/addons.
```
Once it had been confirmed that services are accessible and the deployment can scale up workers, the helm charts provided by the [dask project](https://github.com/dask/helm-chart)) can be used to deploy a custom pod configuration:
```
helm install dask dask/dask --version 2024.1.1 -f config.yaml
helm upgrade dask dask/dask --version 2021.1.1 -f config.yaml
```
Configurations can be explored from the management console via commands such as `kops get cluster --full -o yaml`

## Description

The main services used to perform these scale tests were S3 (object storage) and EC2 (compute nodes). Test data were uploaded to the storage service in various formats and then a  cluster was provisioned using compute instances communicating over a virtual network coordinated by kubernetes (demonstrated above). The proxy server and control plane were hosted on a single linux workstation on premises at one of the NRAO sites. It took several iterations, but we converged on a cluster configuration with the following properties tracked by the initial commits to this repository, and further described below:
- confined to the us-east-1 region for responsiveness and (relative) simplicity
- using public images to run Linux (Ubuntu 20.04) in each virtual machine instance
- kubernetes cluster provisioned using a variety of [instance types](https://aws.amazon.com/ec2/instance-types/)
- modeled after the [Pangeo deployment](https://medium.com/pangeo/pangeo-cloud-costs-part1-f89842da411d) and actively managed via kops and kubectl
- testing software deployed using public [docker images](https://hub.docker.com/u/daskdev) extended with our project dependencies
- coordination services managed by a single node (a t3.small, $0.0209/hour dedicated pricing)
- jupyter kernel and dask scheduler processes ran on a single network- and storage-optimized node (usually a m5dn.4xlarge, $1.088/hour)
- dask worker nodes were hosted on a variety of instance types, from free-tier to the largest available compute- and memory-optimized machines
We never had more than one or two interactive user sessions active at a time, but in principle this could scale out quite a lot more than that. The worker node pool made use of [spot pricing](https://aws.amazon.com/ec2/spot/pricing/) whenever possible to keep costs down, and the resources were always suspended/destroyed when not in active use.

The largest scale we achieved during experimentation was “all of the available spot instances in the service region” which if I recall correctly was about a dozen bare metal machines of the type we requested, or ~1200 vCPUs. During systematic experiments the largest scale of a single benchmark we reached on the commercial cloud was 32 dask worker nodes processing with 256 threads and over 2TB of RAM, saturation of which was limited by the size of available test datasets at the time. No GPU-equipped servers were rented for this testing, although various types remain available and will be explored in future tests.
