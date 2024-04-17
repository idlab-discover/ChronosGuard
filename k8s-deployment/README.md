## Kubernetes Deployment

Directory overview:
```
├── README.md
├── automate-testing
│   └── run_v2.sh: Main bash script used to automate experiment execution.
├── infra-setup
│   └── init-phase-X.sh: Custom bash script to setup evaluation environment, such as configureing Kuberetes and emulating delays.
├── network-aware-scheduler: Diktyo K8s configuration files
├── monolith: K8s deployment files for monolith deployment strategy
│   ├── flow_generator.yaml
│   └── ks
│       └── deployment-ks.yaml
└── multi-stage-ids-with-X-pods: K8s deployment files for X-pod deployment strategy
    ├── flow_generator.yaml
    ├── ks
    │   └── deployment-ks.yaml
    └── networkAware
        ├─── deployment-network-aware.yaml
        └─── app-group-crd: K8s configuration files for queue sorting algorithms
```