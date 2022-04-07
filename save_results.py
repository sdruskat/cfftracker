import requests
import argparse
import time


def retrieve_cff_files(token):
    """Retrieves CITATION.cff files from GitHub via the GitHub API.
    Expects a directory ./data to exist.
    """
    for i in range(100):
        print(f'Getting page {i} ...')
        query_url = 'https://api.github.com/search/code?per_page=100&page=' + str(i) + '&q=filename:CITATION.cff'
        headers = {
            'accept': 'application/vnd.github.v3+json',
            'Authorization': 'token ' + token
        }
        response = requests.get(query_url, headers=headers)
        if response.status_code == 200:
            response_json = response.json()
            print(f"Total results: {response_json['total_count']}")
            items = response_json['items']
            print(f'Found {len(items)} items.')
            for item in items:
                durl = item['html_url'].replace('blob', 'raw')
                if durl:
                    dr = requests.get(durl, allow_redirects=True)
                    with open('/home/stephan/src/cfftracker/data/' + item['repository']['full_name'].replace('/', '_') + '_CITATION.cff', 'wb') as cff:
                        cff.write(dr.content)
            print(f'Sleeping for 1.5 minutes.')
            time.sleep(90)
        else:
            print(f'Not OK, Code: {response.status_code}: {response.reason}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, required=True, help='GitHub API Token')
    args = parser.parse_args()
    retrieve_cff_files(args.token)
