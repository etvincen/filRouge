# Projet Fil Rouge - Etienne Vincent

## Méthodologie pour lancer l'application

- Démarrer l'instance EC2 t2.medium
- Se connecter à l'instance en SSH à l'aide de la clef PEM
- Cloner ce repository dans l'instance EC2 au niveau de /home/ubuntu
- run `cd filRouge/`
- run `virtualenv venv`
- run `source venv/bin/activate`
- run `pip install -r requirements.txt`

- `sudo iptables-restore < /etc/iptables.conf`
- `./run.sh`

## Notes

La fluidité de l'application peut-être impactée par les règles d'Iptables. Pour faire un test sans restrictions, changer la politique en exécutant: `sudo iptables --policy INPUT ACCEPT`

#### Endpoint Swagger:
- <ec2_DNS>:24222/swaggerUI
#### Endpoints 
GET - curl ec2-XX-XX-XXX-XX.eu-west-1.compute.amazonaws.com:24222/get_json/<filename.json>
POST - curl -F file=@./<filename.ext> ec2-XX-XX-XXX-XX.eu-west-1.compute.amazonaws.com:24222/json
#### PORT : 24222


