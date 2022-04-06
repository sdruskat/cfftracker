import requests
import argparse


def retrieve_cff_files(token):
    """Retrieves CITATION.cff files from GitHub via the GitHub API.
    Expects a directory ./data to exist.
    """
    query_url = 'https://api.github.com/search/code?q=filename:CITATION.cff'
    response = requests.get(query_url, headers={'Authorization': 'token ' + token})
    if response.status_code == 200:
        response_json = response.json()
        items = response_json['items']
        print(f'Found {len(items)} items.')
        for item in items:
            durl = item['html_url'].replace('blob', 'raw')
            if durl:
                dr = requests.get(durl, allow_redirects=True)
                with open('./data/' + item['repository']['full_name'].replace('/', '_') + '_CITATION.cff', 'wb') as cff:
                    cff.write(dr.content)

    else:
        print(f'Not OK, Code: {response.status_code}: {response.reason}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, required=True, help='GitHub API Token')
    args = parser.parse_args()
    retrieve_cff_files(args.token)
