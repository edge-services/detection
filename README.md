
# edge-detection service for Edge Computing

## Register Detection Service with IBM Edge Application Manager (OpenHorizon)

    - Make sure IEAM Agent is installed on the system that you are using to register edge service (detection) and can access IEAM Hub
    - Clone GIT repo - https://github.com/edge-services/detection.git
    - Go inside "horizon" folder
    - Run following commands (CLI for openhorizon)

```

export ARCH=arm64
eval $(hzn util configconv -f hzn.json) 

$hzn exchange service publish -f service.definition.json -P 
<!-- $hzn exchange service list -->
<!-- $hzn exchange service remove ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH} -->

$hzn exchange service addpolicy -f service.policy.json ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH}
<!-- $hzn exchange service listpolicy ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH} -->
<!-- $hzn exchange service removepolicy ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH} -->

$hzn exchange deployment addpolicy -f deployment.policy.json ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION}
<!-- $hzn exchange deployment listpolicy ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION} -->
<!-- $hzn exchange deployment removepolicy ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION} -->

```

### Pre-requisites for the Edge Device (Raspberry Pi 4 in this case)

  - [Raspbian 64 bit OS](https://www.makeuseof.com/install-64-bit-version-of-raspberry-pi-os/)
  - Connect a Webcam and make sure following command works
    - raspistill -o test.jpg
  - [Install OpenHorizon Agent (IEAM Agent)](https://github.com/open-horizon/anax/tree/master/agent-install)
    - Below command worked :

```
sudo bash ./agent-install.sh -i . -u $HZN_EXCHANGE_USER_AUTH 

```

  - Export following at Edge Devices or put this at the end of ~/.bashrc (Please change the IP and USER_AUTH)
 
```
export HZN_EXCHANGE_URL=http://169.38.91.92:3090/v1/
export HZN_FSS_CSSURL=http://169.38.91.92:9443/
export CERTIFICATE=agent-install.crt
export HZN_ORG_ID=myorg
export HZN_EXCHANGE_USER_AUTH=admin:HjWsfSKGB9XY3XhLQPOmqpJ6eLWN3U

```

### Commands to test everything's ok

```
curl http://<REPLACE_WITH_HUB_IP>:3090/v1/admin/version
hzn version
hzn exchange service list
hzn agreement list

```

## Register Edge Node with the Hub

  - Create a detection.policy.json file with following content

```
{
  "properties": [
    { "name": "hasCamera", "value": true },
    { "name": "detection", "value": true },
    { "name": "openhorizon.allowPrivileged", "value": true }    
  ],
  "constraints": [
  ]
}
```
  - Run below command for registering

```
hzn register --policy detection.policy.json

```

  - A few useful Horizon commands

```
hzn service log -f detection

hzn unregister -f

hzn agreement list
hzn node list -v
hzn exchange user list

hzn --help
hzn node --help
hzn exchange pattern --help

```

## Detection Docker (Standalone - for testing)

- Create an .env file 
- Run docker image for Edge-Detection

```

sudo docker run --rm -it --name detection  \
  --privileged \
  --device /dev/video0 \
  --device /dev/mem   \
  --device /dev/vchiq \
  -v /opt/vc:/opt/vc  \
  -v /tmp:/tmp \
  --env-file .env \
  sinny777/detection_arm64:latest
    
```

## Refrences

- [OpenHorizon Agent Install](https://github.com/open-horizon/anax/tree/master/agent-install)
- [RPi4 64 bit OS Install - Advance users](https://qengineering.eu/install-raspberry-64-os.html)
