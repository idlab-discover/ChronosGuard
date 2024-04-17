#!/usr/bin/env bash

# Run as sudo user!
# sudo su

swapoff -a

# For internet connection in VWall
wget -O - -nv --ciphers DEFAULT@SECLEVEL=1 https://www.wall2.ilabt.iminds.be/enable-nat.sh | sudo bash

# Configure iptables to receive bridged network traffic: erases previous rules, proceed with caution.
cat <<EOF | sudo tee /etc/ufw/sysctl.conf
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

# OR
#sed -i 'net/bridge/bridge-nf-call-ip6tables = 1' /etc/ufw/sysctl.conf
#sed -i 'net/bridge/bridge-nf-call-iptables = 1' /etc/ufw/sysctl.conf
#sed -i 'net/bridge/bridge-nf-call-arptables = 1' /etc/ufw/sysctl.conf

echo "Installing Requirements for Kubernetes..."
apt-get update
apt-get install -y ebtables ethtool
apt-get install -y apt-transport-https
apt-get install -y curl ssh git
echo "Finishing... rebooting..."
reboot