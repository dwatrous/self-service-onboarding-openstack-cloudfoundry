# Self-service onboarding tool that composes the OpenStack and Stackato (CloudFoundry)
This repository contains a self-service onboarding tool that composes the OpenStack and Stackato (CloudFoundry) REST APIs into a single REST API. It is designed to deploy easily on top of OpenStack and CloudFoundry for the REST API and web front end respectively.

A visio diagram in the docs folder illustrates interactions and deployment details.

If this is used as a basis for a production deployment, there are various files that contain sensitive data, such as credentials, keypairs and SSL keys. It's important to protect these, which can be accomplished using AESCrypt (http://software.danielwatrous.com/encryption-of-secrets-in-source-code-aescrypt-ansible/), or possibly http://docs.ansible.com/ansible/playbooks_vault.html. For example

To encrypt server key corresponding to SSL certificates
aescrypt -e ansible\roles\bottle\templates\onboarding.domain.com.key

To decrypt server key corresponding to SSL certificates
aescrypt -e ansible\roles\bottle\templates\onboarding.domain.com.key.aes

## Deploying
There are two provisioning options available for deployment of the REST API into OpenStack. One is OpenStack HEAT. The other is terraform. 

The included Vagrantfile and bootstrap.sh will create a VM prepared to deploy this application and the comments indicate the process.