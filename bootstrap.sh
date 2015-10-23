#!/bin/bash

#export https_proxy=https://proxy.domain.com:8080
#export http_proxy=http://proxy.domain.com:8080

apt-get update
apt-get install -y unzip ansible python-virtualenv python-dev

#sudo cp /home/vagrant/src/cacert.crt /usr/local/share/ca-certificates/
#sudo update-ca-certificates

tar xzvf src/util/AESCrypt-GUI-3.10-Linux-x86_64-Install.tgz
sudo /home/vagrant/AESCrypt-GUI-3.10-Linux-x86_64-Install --mode silent

#cp /home/vagrant/src/keypair.pem.aes /home/vagrant/.ssh/keypair.pem.aes
#aescrypt -d /home/vagrant/.ssh/keypair.pem.aes
#chmod 600 /home/vagrant/.ssh/keypair.pem

#cd src/

# terraform is one orchestration option
wget --quiet https://dl.bintray.com/mitchellh/terraform/terraform_0.5.3_linux_amd64.zip
sudo unzip terraform_0.5.3_linux_amd64.zip -d /usr/bin
#aescrypt -d terraform.tfvars.aes
#terraform plan
#terraform apply
#terraform show # to get the floating IP
#ssh -i ~/.ssh/hosautomation-hosp.pem ubuntu@
#sed -i "s/[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*/$(terraform show | grep -Po 'address\s*=\s*\K[^$]*')/" ansible/hosts

# heat is another orchestration option
virtualenv venv
chown -R vagrant:vagrant venv
# python virtualenv in ~/venv
apt-get install -y libffi-dev libssl-dev
/home/vagrant/venv/bin/pip install python-heatclient pyopenssl ndg-httpsclient pyasn1
#aescrypt -d stackrc_v3.aes
#source stackrc_v3
#/home/vagrant/venv/bin/heat stack-create onboarding-stack -f heat-automation.yaml
#/home/vagrant/venv/bin/heat output-show onboarding-stack automation_public_ip 2>&1 | grep -o '[^"]*'
#ssh -i ~/.ssh/hosautomation-hosp.pem ubuntu@
#sed -i "s/[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*/$(/home/vagrant/venv/bin/heat output-show onboarding-stack automation_public_ip 2>&1 | grep -o '[^"]*')/" src/ansible/hosts

#aescrypt -d openstack.v2.conf.json.aes openstack.v3.conf.json.aes als.conf.json.aes ucmdb.conf.json.aes
#ansible-playbook -i ansible/hosts-dev ansible/playbook.yml
