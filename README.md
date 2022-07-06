# Edge Detection Service - (Image Classifier)

## WORK IN PROGRESS

This repository can be used as a reference to creating ML or Deep learning models using Tensorflow, Keras or any library of your choice.  This one has code for creating Image classifier model that runs on IBM Watson Machine learning platform and can be configured to use runtime (CPU or GPU) as per your choice.  All the code to create and train the model is under the "build_code" folder.  Please note that whole of this code under "build_code" folder is zipped and deployed to IBM Watson Machine Learning platform and runs there.  

## RUN LOCALLY

  - Create virtual environment and activate it

```

virtualenv venv -p python3.8
source venv/bin/activate

#pip freeze > requirements.txt
pip install -r requirements.txt

```

### DEACTIVATE AND DELETE VIRTUAL ENV

```

deactivate
rmvirtualenv venv

```

## OpenHorizon Agent Installation

  - Make sure OpenHorizon / IEAM Hub is installed and running

$ cat /etc/os-release
$ uname -a

$ which bash
$ file /bin/bash

$ source agent-install.cfg
    OR
$ eval export $(cat agent-install.cfg)

    - fetch https://github.com/open-horizon/anax/releases installation files as per the distribution

$ wget https://github.com/open-horizon/anax/releases/download/v2.30.0-802/agent-install.sh
$ wget https://github.com/open-horizon/anax/releases/download/v2.30.0-802/horizon-agent-linux-deb-arm64.tar.gz
$ tar -xvzf horizon-agent-linux-deb-arm64.tar.gz 

curl -sSL http://169.38.91.92:9443/api/v1/objects/IBM/agent_files/agent-install.crt -u myorg/$HZN_EXCHANGE_USER_AUTH --insecure -o "agent-install.crt"

$ export HZN_EXCHANGE_NODE_AUTH="Gurvinders-MacBook-Pro:#1WaheguruJi"

$ sudo -s ./agent-install.sh -i . -u $HZN_EXCHANGE_USER_AUTH -p IBM/pattern-ibm.helloworld -w ibm.helloworld -o IBM -z horizon-agent-linux-deb-arm64.tar.gz

- Below command worked :

$ sudo bash ./agent-install.sh -i . -u $HZN_EXCHANGE_USER_AUTH 

## OpenHorison Service Setup

  ssh pi@raspbian.local
  password: 1SatnamW

  curl http://169.38.91.92:3090/v1/admin/version

  <!-- curl http://169.38.91.92:3090/edge-exchange/v1/admin/version -->

    - Login to the Hub Instance and check secrets.env file at root folder
    - Copy below information

EXCHANGE_ROOT_PW=9xRb93btxJ6p9zpfIQXtvWnQzzydsc
EXCHANGE_HUB_ADMIN_PW=RNQy3HxBNzsAH3jwLdsvd9DJNNEo5k
EXCHANGE_SYSTEM_ADMIN_PW=VZhd4K0qyHcGQDtk2Mu1Tlk1gaabYW
AGBOT_TOKEN=G6NtJgz6KWXkhNBnkdbJbnn0CtO8WV
EXCHANGE_USER_ADMIN_PW=HjWsfSKGB9XY3XhLQPOmqpJ6eLWN3U
HZN_DEVICE_TOKEN=utt4fRdrZP8qtnDHiyesrZiNhpReEe

    - Export following at Edge Devices (Please change the IP)
 
export HZN_EXCHANGE_URL=http://169.38.91.92:3090/v1/
export HZN_FSS_CSSURL=http://169.38.91.92:9443/
export CERTIFICATE=agent-install.crt
export HZN_ORG_ID=myorg
export HZN_EXCHANGE_USER_AUTH=admin:HjWsfSKGB9XY3XhLQPOmqpJ6eLWN3U

    - Put following content in "/etc/default/horizon" and in "agent-install.cfg"

HZN_EXCHANGE_URL=http://169.38.91.92:3090/v1
HZN_FSS_CSSURL=http://169.38.91.92:9443/
CERTIFICATE=agent-install.crt
HZN_ORG_ID=myorg
HZN_EXCHANGE_USER_AUTH=admin:HjWsfSKGB9XY3XhLQPOmqpJ6eLWN3U

% HZN_EXCHANGE_URL=http://169.38.91.92:3090/edge-exchange/v1/
% HZN_FSS_CSSURL=http://169.38.91.92:9443/edge-css/
% HZN_AGBOT_URL=http://169.38.91.92:3111/edge-agbot/
% HZN_SDO_SVC_URL=http://169.38.91.92:9008/edge-sdo-ocs/api

## Use Following commands to manage services and deployments

```

$ source agent-install.cfg
    OR
$ eval export $(cat agent-install.cfg)

cat /etc/default/horizon

export ARCH=$(hzn architecture)
eval $(hzn util configconv -f hzn.json) 

$hzn exchange service publish -f service.definition.json -P 
$hzn exchange service list
$hzn exchange service remove ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH}

$hzn exchange service addpolicy -f service.policy.json ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH}
$hzn exchange service listpolicy ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH}
$hzn exchange service removepolicy ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH}

$hzn exchange deployment addpolicy -f deployment.policy.json ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION}
$hzn exchange deployment listpolicy ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION}
$hzn exchange deployment removepolicy ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION}


hzn deploycheck policy -b ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION}

hzn deploycheck policy -b myorg/policy-edge-flows_1.0.0


export HZN_ORG_ID=myorg
export HZN_EXCHANGE_USER_AUTH=admin:HjWsfSKGB9XY3XhLQPOmqpJ6eLWN3U

$hzn register --policy security.policy.json

$hzn eventlog list -f

$hzn service log -f ${SERVICE_NAME}

$hzn unregister -f

$ hzn version
$ hzn agreement list
$ hzn node list -v
$ hzn exchange user list

hzn --help
hzn node --help
hzn exchange pattern --help

```

## OpenHorizon Agent Uninstall

```

sudo apt-get remove horizon-cli

```

