# Broker
Broker(s) collect substrate advertisement information models (delegations) from AMs, aggregate them together and make them available to orchestrator(s) via a query interface. They also issue reservations for resources to orchestrators to be redeemed at appropriate AMs.

## Configuration
`config.site.broker.yaml` depicts an example config file for a Broker.

## Deployment
Broker must deploy following containers:
- Neo4j
- Postgres Database
- Policy Enforcement Function (TBD)
- Broker

`docker-compose.yml` file present in this directory brings up all the required containers

### Setup Broker
Run the `setup.sh` script to set up a Broker. User is expected to specify following parameters:
- Directory name for Broker
- Neo4j Password to be used
- Path to the config file for Broker


#### Production
```
./setup.sh broker password ./config.broker.yaml
```
#### Development
```
./setup.sh broker password ./config.broker.yaml dev
```

### Environment and Configuration

The script `setup.sh` generates directory for the Broker, which has `.env` file which contains Environment variables for `docker-compose.yml` to use
User is expected to update `.env` file as needed and update volumes section for broker in `docker-compose.yml`.

Following files must be checked to update any of the parameters
1. `.env` from [env.template](env.template) - Environment variables for `docker-compose.yml` to use
2. `config.yaml` updated to reflect the correct information

#### .env
Modify the default values for each to correspond to your desired deployment. The UID and GID based entries should correspond to the values of the user responsible for running the code as these will relate to shared volumes from the host to the running containers.
NOTE: bolt, http and https ports for Neo4J should be changed when launching multiple CF Actors on same host

```
# docker-compose environment file
#
# When you set the same environment variable in multiple files,
# here’s the priority used by Compose to choose which value to use:
#
#  1. Compose file
#  2. Shell environment variables
#  3. Environment file
#  4. Dockerfile
#  5. Variable is not defined

# Neo4J configuration
NEO4J_DATA_PATH_DOCKER=/data
NEO4J_DATA_PATH_HOST=./neo4j/data
NEO4J_GID=1000
NEO4J_HOST=neo4j
NEO4J_IMPORTS_PATH_DOCKER=/imports
NEO4J_IMPORTS_PATH_HOST=./neo4j/imports
NEO4J_LOGS_PATH_DOCKER=/logs
NEO4J_LOGS_PATH_HOST=./neo4j/logs
NEO4J_PASS=password
NEO4J_UID=1000
NEO4J_USER=neo4j
NEO4J_dbms_connector_bolt_advertised__address=0.0.0.0:8687
NEO4J_dbms_connector_bolt_listen__address=0.0.0.0:8687
NEO4J_dbms_connector_http_advertised__address=0.0.0.0:8474
NEO4J_dbms_connector_http_listen__address=0.0.0.0:8474
NEO4J_dbms_connector_https_advertised__address=0.0.0.0:8473
NEO4J_dbms_connector_https_listen__address=0.0.0.0:8473

# postgres configuration
POSTGRES_HOST=database
POSTGRES_PORT=5432
POSTGRES_USER=fabric
POSTGRES_PASSWORD=fabric
PGDATA=/var/lib/postgresql/data/pgdata
POSTGRES_DB=broker
```
#### config.yaml
The parameters depicted below must be checked/updated before bring any of the containers up.
```
runtime:
  - plugin-dir: ./plugins
  - kafka-server: broker1:9092
  - kafka-schema-registry-url: http://schemaregistry:8081
  - kafka-key-schema: /etc/fabric/message_bus/schema/key.avsc
  - kafka-value-schema: /etc/fabric/message_bus/schema/message.avsc
  - kafka-ssl-ca-location:  /etc/fabric/message_bus/ssl/cacert.pem
  - kafka-ssl-certificate-location:  /etc/fabric/message_bus/ssl/client.pem
  - kafka-ssl-key-location:  /etc/fabric/message_bus/ssl/client.key
  - kafka-ssl-key-password:  fabric
  - kafka-security-protocol: SSL
  - kafka-group-id: fabric-cf
  - kafka-sasl-producer-username:
  - kafka-sasl-producer-password:
  - kafka-sasl-consumer-username:
  - kafka-sasl-consumer-password:
  - prometheus.port: 11000
neo4j:
  url: bolt://broker-neo4j:8687
  user: neo4j
  pass: password
  import_host_dir: /usr/src/app/neo4j/imports/
  import_dir: /imports

actor:
  - type: broker
  - name: broker
  - guid: broker-guid
  - description: Broker
  - kafka-topic: broker-topic
  - policy:
      - module: fabric.actor.core.policy.broker_simpler_units_policy
      - class: BrokerSimplerUnitsPolicy
      - properties:
        - queue.type: fifo

peers:
  - peer:
    - name: orchestrator
    - type: orchestrator
    - guid: orchestrator-guid
    - kafka-topic: orchestrator-topic
  - peer:
    - name: net1-am 
    - guid: net1-am-guid
    - type: authority
    - kafka-topic: net1-am-topic
  - peer:
    - name: site1-am
    - guid: site1-am-guid
    - type: authority
    - kafka-topic: site1-am-topic
```
#### broker
Update `docker-compose.yml` to point to correct volumes for the Broker.

```
    volumes:
      - ./neo4j:/usr/src/app/neo4j
      - ./config.yaml:/etc/fabric/actor/config/config.yaml
      - ./logs/:/var/log/actor
      - ../../../secrets/snakeoil-ca-1.crt:/etc/fabric/message_bus/ssl/cacert.pem
      - ../../../secrets/kafkacat1.client.key:/etc/fabric/message_bus/ssl/client.key
      - ../../../secrets/kafkacat1-ca1-signed.pem:/etc/fabric/message_bus/ssl/client.pem
      - ./pubkey.pem:/etc/fabric/message_bus/ssl/credmgr.pem
```
### Run
Bring up all the required containers
```
cd broker
docker-compose up -d
```