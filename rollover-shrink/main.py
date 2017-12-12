import requests

import time
from urllib.parse import quote_plus
import json

BASE_URL = 'http://elasticsearch:9200'

ALIAS = 'ad_data'
INDEX_TEMPLATE_NAME = 'ad_data_template'
INITIAL_INDEX_NAME = quote_plus('<logstash-{now/d}-1>')
CONTENT_TYPE_JSON_HEADER = {'Content-Type': 'application/json'}
TEMPLATE = {
    "index_patterns": ["logstash-*"],
    "settings": {
        "number_of_shards":   3,
        "number_of_replicas": 1,
        "refresh_interval": "45s",
        "translog": {
            "durability": "async",
            "sync_interval": "45s"
        }
    },
    "aliases": {
        "ad_data": {}
    },
    "mappings": {
        "doc": {
            "properties": {
                "bid.ad_url": {
                    "type": "keyword"
                },
                "bid.id": {
                    "type": "keyword"
                },
                "bid.publisher": {
                    "type": "keyword"
                },
                "bid.targeting.demographic.age_range": {
                    "type": "keyword"
                },
                "bid.targeting.demographic.gender": {
                    "type": "keyword"
                },
                "bid.targeting.device.os": {
                    "type": "keyword"
                },
                "bid.targeting.device.type": {
                    "type": "keyword"
                },
                "bid.targeting.geo.country": {
                    "type": "keyword"
                },
                "bid.targeting.geo.region": {
                    "type": "keyword"
                },
                "bid.targeting.geo.zip": {
                    "type": "keyword"
                },
                "bid.type": {
                    "type": "keyword"
                },
                "click.bid_id": {
                    "type": "keyword"
                },
                "click.type": {
                    "type": "keyword"
                },
                "win.bid_id": {
                    "type": "keyword"
                },
                "win.type": {
                    "type": "keyword"
                }
            }
        }
    }
}
SHRINK_PREP_SETTINGS = {
    "settings": {
        "index.routing.allocation.require._name": "main",
        "index.blocks.write": True
    }
}
SHRINK_SETTINGS = {
    "settings": {
        "index.number_of_shards": 1,
        "index.codec": "best_compression"
    }
}
ROLLOVER_CONDITIONS = {
    "conditions": {
        "max_age": "7d",
        "max_docs": 10000
    }
}


def main():
    # Check if Elasticsearch is up
    while True:
        try:
            requests.get(BASE_URL)
            break
        except requests.exceptions.RequestException as e:
            time.sleep(1)

    print("== Elasticsearch is up")

    # Check if the rollover index already exists, otherwise
    # install our template and create the rollover index
    index_exists_resp = requests.head(f'{BASE_URL}/{ALIAS}')
    if index_exists_resp.status_code == 404:
        # Install the template
        requests.put(f'{BASE_URL}/_template/{INDEX_TEMPLATE_NAME}',
                     data=json.dumps(TEMPLATE), headers=CONTENT_TYPE_JSON_HEADER)
        # Create index
        requests.put(f'{BASE_URL}/{INITIAL_INDEX_NAME}',
                     headers=CONTENT_TYPE_JSON_HEADER)

    # Every 30 seconds try to rollover the index
    # If succesfull start the shrinking process
    while True:
        rollover_resp = requests.post(f'{BASE_URL}/{ALIAS}/_rollover', data=json.dumps(ROLLOVER_CONDITIONS),
                                      headers=CONTENT_TYPE_JSON_HEADER).json()

        if rollover_resp['rolled_over']:
            print("== Starting the shrinking process")

            # Prepare the index for shrinking
            requests.put(f'{BASE_URL}/{rollover_resp["old_index"]}/_settings',
                         data=json.dumps(SHRINK_PREP_SETTINGS),
                         headers=CONTENT_TYPE_JSON_HEADER)

            # Wait for the shards to relocate
            while True:
                cluster_health_resp = requests.get(
                    f'{BASE_URL}/_cluster/health').json()

                if cluster_health_resp['relocating_shards'] == 0:
                    break

                time.sleep(1)

            # Start shrinking
            requests.post(f'{BASE_URL}/{rollover_resp["old_index"]}/_shrink/{rollover_resp["old_index"]}-shrink',
                          data=json.dumps(SHRINK_SETTINGS), headers=CONTENT_TYPE_JSON_HEADER)

        time.sleep(30)


if __name__ == '__main__':
    main()
