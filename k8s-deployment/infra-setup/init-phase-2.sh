#!/usr/bin/env bash

# Run as sudo user!
# sudo su
echo "Installing Docker..."
apt-get install -y docker.io

echo "Adding Kubernetes repository..."

curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add

cat <<EOF > /etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF

apt-get update

echo "Installing Kubernetes..."

# Install 1.22.4 version, works with Diktyo, currently migrating to 1.25...
apt-get install -qy kubelet=1.22.4-00 kubectl=1.22.4-00 kubeadm=1.22.4-00 # apt-get install -y kubelet kubeadm kubectl

# hold current version to avoid updates with apg-get upgrade
apt-mark hold kubelet kubeadm kubectl

echo "Done..."

# Notes

# Problem with Docker in VWall, solution:
#
# cd /etc/docker/
# touch daemon.json
# nano daemon.json
#
# {
# "exec-opts": ["native.cgroupdriver=systemd"]
# }
#
# systemctl daemon-reload
# systemctl restart docker
# systemctl restart kubelet
#

