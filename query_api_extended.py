# SPDX-FileCopyrightText: 2021 Stephan Druskat <mail@sdruskat.net>
# SPDX-License-Identifier: MIT

from urllib.parse import urlparse
from urllib.parse import parse_qs
import requests
from datetime import datetime, date
import csv
import re
import os
import time
import json
import calendar
import typing as t
import urllib
from pathlib import Path

backoff_power = 1


def get_search_result(g):
    pass


def respect_rate_limits(headers):
    rate_limit_response = requests.get('https://api.github.com/rate_limit', headers=headers)
    data = rate_limit_response.json()
    search_resources = data['resources']['search']
    remaining = search_resources['remaining']
    if remaining > 2:
        pass
    else:
        # Be defensive and wait now
        reset_timestamp = search_resources['reset']
        reset_timegm = calendar.timegm(datetime.fromtimestamp(reset_timestamp).timetuple())
        sleep_time = reset_timegm - calendar.timegm(time.gmtime()) + 5  # Wait extra 5 secs. to be safe
        print(f'Waiting {sleep_time} seconds.')
        time.sleep(sleep_time)


def get_query_response(query_url: str, headers: t.Dict[str, str]) -> requests.Response:
    # First up, wait 1 second
    time.sleep(1)
    # Then, check rate limits
    respect_rate_limits(headers)
    response = requests.get(query_url, headers=headers)
    status = response.status_code
    if status == 200 and response is not None:
        print(f'Successful query response for {query_url}.')
        return response
    elif status == 200 and response is None:
        print(f'Status 200, but response is None. Retrying {query_url} in 10 secs.')
        time.sleep(10)
        get_query_response(query_url, headers)
    elif status == 403:  # Potential secondary rate limiting
        # Save error
        with open('errors.json', 'a') as error_file:
            error_file.write(f'{datetime.now()}\nHEADERS: {response.headers}\n\nBODY: {json.dumps(response.json(), indent=4, ensure_ascii=False)}')
        try:
            retry_after = response.headers['Retry-After']
        except KeyError:
            global backoff_power
            retry_after = 2 ** backoff_power  # Exponential backoff
            backoff_power += 1
        print(f'403 status. Retrying after {retry_after} secs.')
        time.sleep(retry_after)
        get_query_response(query_url, headers)
    else:
        print(f'Something went wrong! Status code {status}.')
        print(f'HEADERS: {response.headers}')
        print(f'BODY:    {response.json()}')


def write_stats(response_json):
    count = response_json['total_count']
    print(f'Found a total of {count} files.')

    # Write a new line in the csv file containing the current date and the count
    with open('cff_counts.csv', 'a+', newline='') as csv_file:
        today = str(date.today())
        csv.writer(csv_file).writerow([today, count])

    # Write a file with just the current_count in it so that it can be reused elsewhere
    with open('current_count.txt', 'w') as countfile:
        countfile.write(str(count))

    # Replace the current count in README.md
    readme = 'README.md'
    # Read in the file
    with open(readme, 'r') as fi:
        readme_data = fi.read()

    # Replace the target string
    readme_data = re.sub(r'## Current count: \d+', '## Current count: ' + str(count), readme_data)

    # Write the file out again
    with open(readme, 'w') as fo:
        fo.write(readme_data)


def save_cff_file(dir_name, subdir_name, full_html_url: str, url):
    # url response includes a query called 'ref' that contains the blob hash
    parsed_url = urlparse(url)
    _hash = parse_qs(parsed_url.query)['ref'][0]

    # Get any subdirectory info
    _dir_info = ''
    m = re.search(f'https://github.com/.*/blob/{_hash}(/.*)?/CITATION.cff', full_html_url)
    if m:
        _dir_info = m.group(1)
        if _dir_info is not None:
            if _dir_info.startswith('/'):
                _dir_info = _dir_info[1:]
            if _dir_info.endswith('/'):
                _dir_info = _dir_info[:-1]
            _dir_info = _dir_info.replace('/', '-')
        else:
            _dir_info = ''

    # Create path for hash, and optionally directory info for CFF file in repo
    if not _dir_info:
        subdir_path = f'data/cffs/{dir_name}/{subdir_name}/{_hash}'
    else:
        subdir_path = f'data/cffs/{dir_name}/{subdir_name}/{_hash}/{_dir_info}'
    try:
        Path(subdir_path).mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        # The subdirectory with this blob hash already exists, i.e., CITATION.cff contains the same bytes contents
        return
    # Prepare URL
    raw_url = full_html_url.\
        replace('https://github.com/', 'https://raw.githubusercontent.com/').\
        replace('/blob/', '/')
    response = urllib.request.urlopen(raw_url)
    cff_data = response.read()  # a `bytes` object

    with open(f'{subdir_path}/CITATION.cff', 'wb') as of:
        of.write(cff_data)
        print(f'Written {subdir_path}/CITATION.cff.')


def add_response_to_dataset(response):
    # Extract URL and add to list
    response_json = response.json()
    if 'items' in response_json:
        items = response_json['items']
        add_count = 0
        for item in items:
            repo = item['repository']
            full_html_url = item['html_url']
            url = item['url']
            qualified_name = repo['full_name']
            _spl = qualified_name.split('/')
            user = _spl[0]
            repo = _spl[1]
            save_cff_file(user, repo, full_html_url, url)

            with open('data/repositories.json', 'r') as jsonfile:
                data = json.load(jsonfile)
                users = data['repositories']
                if user in users:
                    this_user = users[user]
                    if repo in this_user:
                        pass
                    else:
                        this_user.append(repo)
                        print(f'Adding {str(user)}/{str(repo)}')
                        add_count += 1
                else:
                    users[user] = [repo]
                    print(f'Adding {str(user)}/{str(repo)}')
                    add_count += 1

            if data is not None:
                with open('data/repositories.json', 'w') as jsonfile_o:
                    json.dump(data, jsonfile_o)
            else:
                print(f'Data was None.')
        print(f'Added {add_count} to dataset file.')


def traverse_results(next_page_url, last_page_url, headers):
    if next_page_url:
        response = get_query_response(next_page_url, headers)
        if response is None:
            print(f'Response is None. Retrying {next_page_url} in 10 secs.')
            time.sleep(10)
            traverse_results(next_page_url, last_page_url, headers)
        elif not response.links:
            print(f'No links. Maybe paging was bad. Retrying {next_page_url} in 10 secs.')
            print(f'RESPONSE: {response}\n\n\n')
            time.sleep(10)
            traverse_results(next_page_url, last_page_url, headers)
        else:
            next_page_url = response.links['next']['url']
            last_page_url = response.links['last']['url']
            add_response_to_dataset(response)
            if next_page_url != last_page_url:
                traverse_results(next_page_url, last_page_url, headers)
    else:
        print('No URL for next page!')


def query():
    # Set up GitHub API calls
    token = os.environ.get('GITHUB_TOKEN')
    headers = {
        'Authorization': 'token ' + token,
        'UserAgent': 'sdruskat'
        }

    basic_query_url = 'https://api.github.com/search/code?q=filename:CITATION.cff+cff-version&per_page=100&accept=application/vnd.github+json'
    indexed_desc_query_url = basic_query_url + '&sort=indexed&order=desc'
    indexed_asc_query_url = basic_query_url + '&sort=indexed&order=asc'
    queries = [basic_query_url, indexed_desc_query_url, indexed_asc_query_url]

    for query_url in queries:
        # Retrieve the total count of CITATION.cff files on GitHub via the GitHub API
        initial_response = get_query_response(query_url, headers)
        response_headers = initial_response.headers
        initial_response_json = initial_response.json()
        try:
            write_stats(initial_response_json)
        except KeyError:
            # Wait 10 seconds then retry
            print('Could not retrieve total count from initial response, retrying in 10 secs.')
            time.sleep(10)
            query()

        add_response_to_dataset(initial_response)

        # Page through results, using pagination and relative links
        next_page_url = initial_response.links['next']['url']
        last_page_url = initial_response.links['last']['url']
        traverse_results(next_page_url, last_page_url, headers)


if __name__ == "__main__":
    query()
