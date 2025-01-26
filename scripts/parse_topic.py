import json
import sys

def parse_topic_id():
    data = json.load(sys.stdin)
    # Handle both single topic and list of topics
    if isinstance(data, list):
        if data:  # Get the first topic if it's a list
            print(data[0]['topic_id'])
    else:  # Single topic object
        print(data['topic_id'])

if __name__ == '__main__':
    parse_topic_id()
