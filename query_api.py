# SPDX-FileCopyrightText: 2021 Stephan Druskat <mail@sdruskat.net>
# SPDX-License-Identifier: MIT

import requests
from datetime import date
import csv
import re
import os
from time import sleep


sleep_time = 10


def query():
    # Retrieve the total count of CITATION.cff files on GitHub via the GitHub API
    token = os.environ.get('GITHUB_TOKEN')
    query_url = 'https://api.github.com/search/code?q=version+path%3ACITATION.cff'
    response = requests.get(query_url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    response_json = response.json()
    # Catch if the total_count key doesn't exist and try again
    try:
        count = response_json['total_count']

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
    except KeyError:
        print('No field "total_count" found in API reponse, retrying in ' + str(sleep_time) + ' seconds...')
        sleep(sleep_time)
        query()


if __name__ == "__main__":
    query()
