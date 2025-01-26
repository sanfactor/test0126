import json
import sys

def format_response():
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    format_response()
