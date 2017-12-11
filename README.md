# Zemanta challenge: Real-time Business Data Analytics

This repo is the source code to my solution for 2017 Zemanta challenge: Real-time Business Data Analytics.

## Project

* Elasticsearch for log storage
* Kibana for visualization
* Logstash as a processing pipeline
* Docker Compose for orchestrating the containers

## Running the project

Since I'm using Docker running the project is just two commands:

```bash
docker-compose build
docker-compose up
```

Before running the `up` command it is good to change the `ES_JAVA_OPTS` and `LS_JAVA_OPTS` environment variables.
`ES_JAVA_OPTS` should set the JVM heap size to half of the total memory available on the machine. `LS_JAVA_OPTS` should be set to around 15% of the total
memory available.

Once all containers are running, the Elasticsearch API is available at `localhost:9200` and Kibana is avilable at `localhost:5601`. When running for the first time Kibana takes a couple of minutes to set up.

Switch to branch `horizontal-scale` to see how to make Elasticsearch horizontally scalable. The commands slightly change since now we are booting
two additional Elasticsearch nodes.

```bash
docker-compose build
docker-compose up --scale elasticsearch-worker=2
```

### Inserting documents

Documents can be inserted using the `bid_request_generator` available on [GitHub](https://github.com/hamaxx/bid_request_generator). Once set up you can run it with the following command:

```bash
./bin/bid_request_generator 10000 1 | nc localhost 5000
```

We pipe the output from the generator to `localhost:5000` since that is where Logstash is listening for input.

### Querying

The suggested queries are available in the [queries.txt](./queries.txt) file. 
Each query can be copied to Kibana DevTools and ran from there (including the `GET _search` header). DevTools are available on this [link](localhost:5601/app/kibana#/dev_tools/console).