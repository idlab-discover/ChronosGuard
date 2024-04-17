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
   echo "Syntax: run.sh [-h|r|d|t|a|g|k|y|q|e]"
   echo "options:"
   echo "h     Print this Help."
   echo "r     Set the number of repetitions."
   echo "d     The deployment to use: '1pod|2pod|3pod|4pod|teastore|onlineboutique'."
   echo "t     The topology to use: 'cluster|cluster-delay'."
   echo "a     Use Pod Anti-Affinity rules in the deployment'."
   echo "g     Use generator as dependency'."
   echo "k     Skip KS'."
   echo "y     Skip Diktyo'."
   echo "q     Skip Qos'."
   echo "e     Skip extra Diktyo'."
   echo
}

############################################################
############################################################
# Main program                                             #
############################################################
############################################################

# Set variables
NUM_REPETITIONS=10
DEPLOYMENTS=("1pod" "2pod" "3pod" "4pod" "teastore" "onlineboutique")
DEPLOYMENT="1pod"
DEPLOYMENT_DIR="monolith"
SORTING=("kahn" "reverse_kahn" "alternate_kahn" "cycle")
NODE_NAME=".ids.ilabt-imec-be.wall2.ilabt.iminds.be"
TOPOLOGIES=("cluster" "cluster-delay" "edge-fog-cloud")
TOPOLOGY="cluster"
POD_NAMES=("allinoneapi")
SLEEP=480 # 8 minutes
COUNT=0
LOCUST_PID=0
FIRST_POD_CHAIN="preprocessingbinaryapi:8001"
affinity=false
SKIP_KS=false
SKIP_DIKTYO=false
SKIP_QOS=false
SKIP_EXTRA_DIKTYO=false
ADD_GENERATOR=false

############################################################
# Process the input options. Add options as needed.        #
############################################################
# Get the options
while getopts ":h:r:d:t:a:g:k:y:q:e:" option; do
  case $option in
    h) # display Help
      Help
      exit;;
    a) # Use Pod Anti-Affinity rules
      echo "Use Anti-affinity rules..."
      affinity=$OPTARG;;
    g) # Use Generator as dependency
      echo "Use Generator as dependency..."
      ADD_GENERATOR=$OPTARG;;
    k) # Skip KS
      echo "Skipping KS..."
      SKIP_KS=$OPTARG;;
    y) # Skip Diktyo
      echo "Skipping Diktyo..."
      SKIP_DIKTYO=$OPTARG;;
    q) # Skip QoS
      echo "Skipping QoS..."
      SKIP_QOS=$OPTARG;;
    e) # Skip Extra Diktyo
      echo "Skipping Extra Diktyo..."
      SKIP_EXTRA_DIKTYO=$OPTARG;;
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

        # Modify pod names to wait
        POD_NAMES=("preprocessingallbinary" "multiclasszerodayapi")

      elif [[ "$OPTARG" == "3pod" ]]; then
        DEPLOYMENT_DIR="multi-stage-ids-with-3-pods"
        FIRST_POD_CHAIN="preprocessingbinaryapi:8005"

        # Modify pod names to wait
        POD_NAMES=("preprocessingbinaryapi" "preprocessingmulticlassapi" "zerodayapi")

      elif [[ "$OPTARG" == "4pod" ]]; then
        DEPLOYMENT_DIR="multi-stage-ids-with-4-pods"
        FIRST_POD_CHAIN="preprocessingapi:8000"

        # Modify pod names to wait
        POD_NAMES=("preprocessingapi" "binaryapi" "multiclassapi" "zerodayapi")

      elif [[ "$OPTARG" == "teastore" ]]; then
        DEPLOYMENT_DIR="deployment-teastore"
        FIRST_POD_CHAIN="teastore-webui:8080"

        # add 3 extra sorting algorithms
        SORTING=("kahn" "reverse_kahn" "alternate_kahn" "cycle" "tarjan" "reverse_tarjan" "alternate_tarjan")

        # Modify pod names to wait
        POD_NAMES=("teastore-db" "teastore-registry" "teastore-persistence" "teastore-auth"
        "teastore-image" "teastore-recommender" "teastore-webui")

      elif [[ "$OPTARG" == "onlineboutique" ]]; then
        DEPLOYMENT_DIR="deployment-online-boutique"
        FIRST_POD_CHAIN="frontend:80"

        # add 3 extra sorting algorithms
        SORTING=("kahn" "reverse_kahn" "alternate_kahn" "cycle" "tarjan" "reverse_tarjan" "alternate_tarjan")

        # Modify pod names to wait
        POD_NAMES=("recommendationservice" "productcatalogservice" "cartservice" "adservice"
        "paymentservice" "shippingservice" "currencyservice" "redis-cart"
        "checkoutservice" "frontend" "emailservice")

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
  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deleting pods..."
    kubectl delete -f ks/deployment-ks.yaml
  else # affinity is true
    echo "Anti-affinity is true, deleting pods..."
    kubectl delete -f ks/anti-affinity/deployment-ks.yaml
  fi
  # Wait for pods to be deleted
  sleep 5
}

delete_pods_diktyo() {
  # $1 = sorting algorithm
  echo "Delete Diktyo..."
  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deleting pods..."
    kubectl delete -f networkAware/deployment-network-aware.yaml
  else # affinity is true
    echo "Anti-affinity is true, deleting pods..."
    kubectl delete -f networkAware/anti-affinity/deployment-network-aware.yaml
  fi

  echo "Delete Diktyo AppGroup..."
  if [[ "$ADD_GENERATOR" == false ]]; then
    kubectl delete -f "networkAware/app-group-crd/$1.yaml"
  else # generator is true
    kubectl delete -f "networkAware/app-group-crd/generator/$1.yaml"
  fi

  # Wait for pods and AppGroup to be deleted
  sleep 5
}


delete_pods_diktyo_qos() {
  # $1 = sorting algorithm
  echo "Delete Diktyo (QoS)..."
  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deleting pods..."
    kubectl delete -f networkAware/qos/deployment-qos.yaml
  else # affinity is true
    echo "Anti-affinity is true, deleting pods..."
    kubectl delete -f networkAware/qos/anti-affinity/deployment-qos.yaml
  fi

  echo "Delete Diktyo AppGroup..."
  if [[ "$ADD_GENERATOR" == false ]]; then
    kubectl delete -f "networkAware/app-group-crd/$1.yaml"
  else # generator is true
    kubectl delete -f "networkAware/app-group-crd/generator/$1.yaml"
  fi

  # Wait for pods and AppGroup to be deleted
  sleep 5
}


delete_pods_diktyo_priority() {
  # $1 = sorting algorithm
  echo "Delete Diktyo (Priority)..."
  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deleting pods..."
    kubectl delete -f networkAware/priority/deployment-priority.yaml
  else # affinity is true
    echo "Anti-affinity is true, deleting pods..."
    kubectl delete -f networkAware/priority/anti-affinity/deployment-priority.yaml
  fi

  echo "Delete Diktyo AppGroup..."

  if [[ "$ADD_GENERATOR" == false ]]; then
    kubectl delete -f "networkAware/app-group-crd/$1.yaml"
  else # generator is true
    kubectl delete -f "networkAware/app-group-crd/generator/$1.yaml"
  fi

  # Wait for pods and AppGroup to be deleted
  sleep 5
}


delete_pods_qos() {
  echo "Delete QoS..."
  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deleting pods..."
    kubectl delete -f qos/deployment-qos.yaml
  else # affinity is true
    echo "Anti-affinity is true, deleting pods..."
    kubectl delete -f qos/anti-affinity/deployment-qos.yaml
  fi

  # Wait for pods to be deleted
  sleep 5
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
  elif [[ "$DEPLOYMENT" == "teastore" ]]; then
    kubectl scale deployment/teastore-db --replicas="$1"
    kubectl scale deployment/teastore-registry --replicas="$1"
    kubectl scale deployment/teastore-persistence --replicas="$1"
    kubectl scale deployment/teastore-auth --replicas="$1"
    kubectl scale deployment/teastore-image --replicas="$1"
    kubectl scale deployment/teastore-recommender --replicas="$1"
    kubectl scale deployment/teastore-webui --replicas="$1"
  elif [[ "$DEPLOYMENT" == "onlineboutique" ]]; then
    kubectl scale deployment/adservice --replicas="$1"
    kubectl scale deployment/cartservice --replicas="$1"
    kubectl scale deployment/checkoutservice --replicas="$1"
    kubectl scale deployment/currencyservice --replicas="$1"
    kubectl scale deployment/emailservice --replicas="$1"
    kubectl scale deployment/frontend --replicas="$1"
    kubectl scale deployment/paymentservice --replicas="$1"
    kubectl scale deployment/productcatalogservice --replicas="$1"
    kubectl scale deployment/recommendationservice --replicas="$1"
    kubectl scale deployment/redis-cart --replicas="$1"
    kubectl scale deployment/shippingservice --replicas="$1"
  fi
}

deploy_locust() {
  # $1 = repetition number
  echo "Deploying locust..."
  kubectl apply -f flow_generator.yaml
  # Wait 2 seconds for deployment
  sleep 2
  kubectl patch deployment flowgenerator -p '{"spec": {"template": {"spec": {"nodeSelector": {"kubernetes.io/hostname": "n'"$1${NODE_NAME}"'"}}}}}'
  # Wait 45 seconds for patch
  sleep 45
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
  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deploying pods..."
    kubectl apply -f ks/deployment-ks.yaml
  else # affinity is true
    echo "Anti-affinity is true, deploying pods..."
    kubectl apply -f ks/anti-affinity/deployment-ks.yaml
  fi

  # sleep 5 seconds after deploying pods...  then, wait for specific pods to be ready
  sleep 5
  for pod in "${POD_NAMES[@]}"
    do
      echo "Waiting for pod $pod to be ready..."
      kubectl wait pods -l app="$pod" --for condition=Ready
      echo "$pod ready"
    done
  echo "Printing get pods..."
  kubectl get pods -o wide
}

deploy_diktyo_pods() {
  # $1 = sorting algorithm
  echo "Deploy AppGroup for Diktyo..."
  if [[ "$ADD_GENERATOR" == false ]]; then
    kubectl apply -f networkAware/app-group-crd/"$1".yaml
  else # generator is true
    kubectl apply -f networkAware/app-group-crd/generator/"$1".yaml
  fi

  # Wait for the CRD to be fulfilled by the controller
  sleep 5

  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deploying pods..."
    kubectl apply -f networkAware/deployment-network-aware.yaml
  else # affinity is true
    echo "Anti-affinity is true, deploying pods..."
    kubectl apply -f networkAware/anti-affinity/deployment-network-aware.yaml
  fi

  # sleep 5 seconds after deploying pods...  then, wait for specific pods to be ready
  sleep 5
  for pod in "${POD_NAMES[@]}"
    do
      echo "Waiting for pod $pod to be ready..."
      kubectl wait pods -l app="$pod" --for condition=Ready
      echo "$pod ready"
    done
  echo "Printing get pods..."
  kubectl get pods -o wide
}

deploy_diktyo_qos_pods() {
  # $1 = sorting algorithm
  echo "Deploy AppGroup for Diktyo..."
  if [[ "$ADD_GENERATOR" == false ]]; then
    kubectl apply -f networkAware/app-group-crd/"$1".yaml
  else # generator is true
    kubectl apply -f networkAware/app-group-crd/generator/"$1".yaml
  fi

  # Wait for the CRD to be fulfilled by the controller
  sleep 5

  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deploying pods..."
    kubectl apply -f networkAware/qos/deployment-qos.yaml
  else # affinity is true
    echo "Anti-affinity is true, deploying pods..."
    kubectl apply -f networkAware/qos/anti-affinity/deployment-qos.yaml
  fi

  # sleep 5 seconds after deploying pods...  then, wait for specific pods to be ready
  sleep 5
  for pod in "${POD_NAMES[@]}"
    do
      echo "Waiting for pod $pod to be ready..."
      kubectl wait pods -l app="$pod" --for condition=Ready
      echo "$pod ready"
    done
  echo "Printing get pods..."
  kubectl get pods -o wide
}


deploy_diktyo_priority_pods() {
  # $1 = sorting algorithm
  echo "Deploy AppGroup for Diktyo..."
  if [[ "$ADD_GENERATOR" == false ]]; then
    kubectl apply -f networkAware/app-group-crd/"$1".yaml
  else # generator is true
    kubectl apply -f networkAware/app-group-crd/generator/"$1".yaml
  fi

  # Wait for the CRD to be fulfilled by the controller
  sleep 5

  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deploying pods..."
    kubectl apply -f networkAware/priority/deployment-priority.yaml
  else # affinity is true
    echo "Anti-affinity is true, deploying pods..."
    kubectl apply -f networkAware/priority/anti-affinity/deployment-priority.yaml
  fi

  # sleep 5 seconds after deploying pods...  then, wait for specific pods to be ready
  sleep 5
  for pod in "${POD_NAMES[@]}"
    do
      echo "Waiting for pod $pod to be ready..."
      kubectl wait pods -l app="$pod" --for condition=Ready
      echo "$pod ready"
    done
  echo "Printing get pods..."
  kubectl get pods -o wide
}


deploy_qos_pods() {
  echo "Deploy pods for QoS Scheduler..."
  if [[ "$affinity" == false ]]; then
    echo "Anti-affinity is false, deploying pods..."
    kubectl apply -f qos/deployment-qos.yaml
  else # affinity is true
    echo "Anti-affinity is true, deploying pods..."
    kubectl apply -f qos/anti-affinity/deployment-qos.yaml
  fi

  # sleep 5 seconds after deploying pods...  then, wait for specific pods to be ready
  sleep 5
  for pod in "${POD_NAMES[@]}"
    do
      echo "Waiting for pod $pod to be ready..."
      kubectl wait pods -l app="$pod" --for condition=Ready
      echo "$pod ready"
    done
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
    if [[ "$SKIP_KS" == false ]]; then
      if [[ "$TOPOLOGY" == "edge-fog-cloud" ]]; then
        # Only deploy locust on edge nodes
        deploy_locust "$((7 + $i % 4))"
      else
        deploy_locust "$i"
      fi
      deploy_ks_pods
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_initial" "$i"
      scale_pods 5
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_scale-up" "$i"
      scale_pods 2
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_scale-down" "$i"
      delete_pods_ks
      delete_locust
    fi
  else
    echo "Automating $DEPLOYMENT: executing KS, Diktyo, QoS, Diktyo (Qos), Diktyo (Priority)"
      if [[ "$TOPOLOGY" == "edge-fog-cloud" ]]; then
        # Only deploy locust on edge nodes
        deploy_locust "$((7 + $i % 4))"
      else
        deploy_locust "$i"
      fi

    # KS scheduler only if skip is false
    if [[ "$SKIP_KS" == false ]]; then
      echo "Starting KS..."
      deploy_ks_pods
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_initial" "$i"
      scale_pods 5
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_scale-up" "$i"
      scale_pods 2
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_ks_scale-down" "$i"
      delete_pods_ks
    fi

    # Diktyo scheduler only if skip is false
    if [[ "$SKIP_DIKTYO" == false ]]; then
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
    fi

    # QoS scheduler only if skip is false
    if [[ "$SKIP_QOS" == false ]]; then
      echo "Starting QoS scheduler..."
      deploy_qos_pods
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_qos_initial" "$i"
      scale_pods 5
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_qos_scale-up" "$i"
      scale_pods 2
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_qos_scale-down" "$i"
      delete_pods_qos
    fi

    # Diktyo (QoS & Priority) scheduler only if skip is false
    # Assume generic sorting for AppGroup deployment. e.g., Kahn
    if [[ "$SKIP_EXTRA_DIKTYO" == false ]]; then
      algo="kahn"
      echo "Starting Diktyo (QoS) with AppGroup: $algo..."
      deploy_diktyo_qos_pods "$algo"
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_qos_initial" "$i"
      scale_pods 5
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_qos_scale-up" "$i"
      scale_pods 2
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_qos_scale-down" "$i"
      delete_pods_diktyo_qos "$algo"

      echo "Starting Diktyo (Priority) with AppGroup: $algo..."
      deploy_diktyo_priority_pods "$algo"
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_priority_initial" "$i"
      scale_pods 5
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_priority_scale-up" "$i"
      scale_pods 2
      run_experiment "${TOPOLOGY}_${DEPLOYMENT}_diktyo_priority_scale-down" "$i"
      delete_pods_diktyo_priority "$algo"
    fi

    # Delete locust after all experiments
    delete_locust
  fi
done