#!/usr/bin/env bash
set -e
#./run.sh -r 5 -d 1pod -t cluster > logs/cluster_1pod.log 2>&1

############################################################
# Help                                                     #
############################################################
Help()
{
   # Display Help
   echo "Script to automate testing network-aware ML-IDS deployment."
   echo
   echo "Syntax: run.sh [-h|r|d|t]"
   echo "options:"
   echo "h     Print this Help."
   echo "r     Set the number of repetitions."
   echo "d     The deployment to use: '1pod|2pod|3pod|4pod'."
   echo "t     The topology to use: 'cluster|cluster-delay'."
   echo
}

############################################################
############################################################
# Main program                                             #
############################################################
############################################################

# Set variables
NUM_REPETITIONS=10
DEPLOYMENTS=("1pod" "2pod" "3pod" "4pod")
DEPLOYMENT="1pod"
DEPLOYMENT_DIR="monolith"
SORTING=("kahn" "reverse_kahn" "alternate_kahn" "cycle")
NODE_NAME=".ids.ilabt-imec-be.wall2.ilabt.iminds.be"
TOPOLOGIES=("cluster" "cluster-delay")
TOPOLOGY="cluster"
SLEEP=480 # 8 minutes
COUNT=0
LOCUST_PID=0
FIRST_POD_CHAIN="preprocessingbinaryapi:8001"

############################################################
# Process the input options. Add options as needed.        #
############################################################
# Get the options
while getopts ":h:r:d:t:" option; do
  case $option in
    h) # display Help
      Help
      exit;;
    r) # Enter the repetitions
      NUM_REPETITIONS=$OPTARG;;
    d) # Enter the deployment
      if [[ ! " ${DEPLOYMENTS[@]} " =~ " ${OPTARG} " ]]; then
        echo "Error: '$OPTARG' is not a valid deployment."
        exit
      fi
      if [[ "$OPTARG" == "1pod" ]]; then
        DEPLOYMENT_DIR="monolith"
        FIRST_POD_CHAIN="allinoneapi:8004"
      elif [[ "$OPTARG" == "2pod" ]]; then
        DEPLOYMENT_DIR="multi-stage-ids-with-2-pods"
        FIRST_POD_CHAIN="preprocessingallbinary:8001"
      elif [[ "$OPTARG" == "3pod" ]]; then
        DEPLOYMENT_DIR="multi-stage-ids-with-3-pods"
        FIRST_POD_CHAIN="preprocessingbinaryapi:8005"
      elif [[ "$OPTARG" == "4pod" ]]; then
        DEPLOYMENT_DIR="multi-stage-ids-with-4-pods"
        FIRST_POD_CHAIN="preprocessingapi:8000"
      fi
      DEPLOYMENT=$OPTARG;;
    t) # Enter the topology
      if [[ ! " ${TOPOLOGIES[@]} " =~ " ${OPTARG} " ]]; then
        echo "Error: '$OPTARG' is not a valid topology."
        exit
      fi
      TOPOLOGY=$OPTARG;;
    \?) # Invalid option
      echo "Error: Invalid option"
      exit;;
  esac
done

############################################################
# Functions                                                #
############################################################

delete_pods_ks() {
  echo "Delete KS..."
  kubectl delete -f ks/
}

delete_pods_diktyo() {
  # $1 = sorting algorithm
  echo "Delete Diktyo..."
  kubectl delete -f networkAware/deployment-network-aware.yaml

  echo "Delete Diktyo AppGroup..." # it should work since it's deletion, otherwise delete specific AppGroup: kahn, reverse_kahn, alternate_kahn, cycle
  kubectl delete -f "networkAware/app-group-crd/$1.yaml" # OR: kubectl delete -f networkAware/app-group-crd/cycle.yaml
}

delete_locust() {
  echo "Delete locust..."
  kubectl delete -f flow_generator.yaml
  if [[ "$LOCUST_PID" != "0" ]]; then
    echo "Killing locust..."
    kill "$LOCUST_PID"
  fi
  # Wait for locust to be deleted
  sleep 5
}

scale_pods() {
  #  $1 = number of pods
  echo "Scaling pods to $1..."
  if [[ "$DEPLOYMENT" == "1pod" ]]; then
    kubectl scale deployment/allinoneapi --replicas="$1"
  elif [[ "$DEPLOYMENT" == "2pod" ]]; then
    kubectl scale deployment/preprocessingallbinary --replicas="$1"
    kubectl scale deployment/multiclasszerodayapi --replicas="$1"
  elif [[ "$DEPLOYMENT" == "3pod" ]]; then
    kubectl scale deployment/preprocessingbinaryapi --replicas="$1"
    kubectl scale deployment/preprocessingmulticlassapi --replicas="$1"
    kubectl scale deployment/zerodayapi --replicas="$1"
  elif [[ "$DEPLOYMENT" == "4pod" ]]; then
    kubectl scale deployment/preprocessingapi --replicas="$1"
    kubectl scale deployment/binaryapi --replicas="$1"
    kubectl scale deployment/multiclassapi --replicas="$1"
    kubectl scale deployment/zerodayapi --replicas="$1"
  fi
}

deploy_locust() {
  # $1 = repetition number
  echo "Deploying locust..."
  kubectl apply -f flow_generator.yaml
  kubectl patch deployment flowgenerator -p '{"spec": {"template": {"spec": {"nodeSelector": {"kubernetes.io/hostname": "n'"$1${NODE_NAME}"'"}}}}}'
  sleep 30
  echo "Waiting for locust on node $i to be ready..."
  kubectl wait pods -l app="flowgenerator" --for condition=Ready
  LOCUST_POD_NAME=$(kubectl get pods --namespace default -l "app=flowgenerator" -o jsonpath="{.items[-1].metadata.name}" --field-selector=status.phase=Running)
  echo "$LOCUST_POD_NAME deployed"
  echo "Forwarding port 8089..."
  kubectl port-forward "$LOCUST_POD_NAME" 8089:8089 >/dev/null 2>&1 &
  LOCUST_PID=$!
  sleep 5
}

deploy_ks_pods() {
  echo "Deploy pods for KS..."
  kubectl apply -f ks/
  # Hardcoded sleep 5 seconds to wait for the pods to be ready
  sleep 10
  echo "Printing get pods..."
  kubectl get pods -o wide
}

deploy_diktyo_pods() {
  # $1 = sorting algorithm
  echo "Deploy pods for Diktyo..."
  kubectl apply -f networkAware/app-group-crd/"$1".yaml
  # Wait for the CRD to be fulfilled by the controller
  sleep 5
  kubectl apply -f networkAware/deployment-network-aware.yaml
  # Hardcoded sleep 5 seconds to wait for the pods to be ready
  sleep 10
  echo "Printing get pods..."
  kubectl get pods -o wide
}

run_experiment() {
  # $1 = results_csv_directory
  # $2 = repetition number
  COUNT=$((COUNT+1))
  echo "------  Starting experiment  $COUNT ------"
  start_load_generator "$1" "$2"
  echo "Waiting for load generator to finish..."
  sleep "$SLEEP"
  copy_results_from_locust "$1"
}

start_load_generator() {
  # $1 = results_csv_directory
  # $2 = repetition number
  echo "Starting load generator for repetition $2 and save dir $1..."
  curl -sS "http://localhost:8089/swarm" --data-raw "host=http://${FIRST_POD_CHAIN}&run_csv_directory=$1&run_number=$2" >/dev/null
}

copy_results_from_locust() {
  # $1 = results_csv_directory
  echo "Copying results from $LOCUST_POD_NAME..."
  kubectl cp "default/$LOCUST_POD_NAME:/app/data/results/$1" "results/$1"
}

############################################################
echo "Starting automation with '$NUM_REPETITIONS' repetitions, '$DEPLOYMENT' deployment and '$TOPOLOGY' topology..."
# Move to correct deployment folder
cd "$DEPLOYMENT_DIR" || exit

# loop through the number of repetitions
for i in $(seq "$NUM_REPETITIONS")
do
  echo "Starting repetition $i of $NUM_REPETITIONS"
  if [[ "$DEPLOYMENT" == "1pod" ]]; then
    echo "Automating MONOLITH: only executing KS scheduler"
    # KS scheduler
    deploy_locust "$i"
    deploy_ks_pods
    run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_initial" "$i"
    scale_pods 5
    run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_scale-up" "$i"
    scale_pods 2
    run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_scale-down" "$i"
    delete_pods_ks
    delete_locust
  else
    echo "Automating $DEPLOYMENT: executing KS scheduler and Diktyo"
    # KS scheduler
    echo "Starting KS..."
    deploy_locust "$i"
    deploy_ks_pods
    run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_initial" "$i"
    scale_pods 5
    run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_scale-up" "$i"
    scale_pods 2
    run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_scale-down" "$i"
    delete_pods_ks
    # Diktyo scheduler
    for algo in "${SORTING[@]}"
    do
      if [[ "$DEPLOYMENT" == "2pod" && "$algo" == "alternate_kahn" ]]; then
        echo "Skipping alternate_kahn for 2pod deployment..."
        continue
      fi
      echo "Starting Diktyo with $algo..."
      deploy_diktyo_pods "$algo"
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_${algo}_initial" "$i"
      scale_pods 5
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_${algo}_scale-up" "$i"
      scale_pods 2
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_${algo}_scale-down" "$i"
      delete_pods_diktyo "$algo"
    done
    delete_locust
  fi
done