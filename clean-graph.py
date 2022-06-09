# SPDX-FileCopyrightText: 2021 Stephan Druskat <mail@sdruskat.net>
# SPDX-License-Identifier: MIT

""" Produces a cleaned up graph from the CFF counts data.
"Cleaned up" in this case means that any drops in counts > 50 are simply removed from the data,
then the cleaned up data is plotted.

This is necessary, as the data retrieved via GitHub search includes steep drops in counts,
that are due to some unreliability in the GitHub Search API, caused by backend work done
while a query is run (p.c. Arfon Smith, GitHub).

To include drops in counts, adapt the DROP_CUTOFF value.
"""

import pandas as pd
import matplotlib.pyplot as plt


# Define the size of drops that should still be left in the dataframe
DROP_CUTOFF = 100


def remove_drops(_df):
    # Sort by date
    _df = _df.sort_values(by='date')
    _df = _df.reset_index(drop=True)

    # Iterate through rows, and record any drops in counts between two query results that are > DROP_CUTOFF
    drop_indices = []
    for index, row in _df.iterrows():
        this_count = row['count']
        if index > 0:
            previous_row = _df.iloc[[(int(index) - 1)]]
            prev_count = int(previous_row['count'])
            diff = prev_count - this_count
            if diff > DROP_CUTOFF:
                drop_indices.append(index)

    # Drop collected indices
    prev_len = len(_df)
    for index, row in _df.iterrows():
        if index in drop_indices:
            _df.drop(index, inplace=True)
    curr_len = len(_df)

    # Return whether the dataframe length has changed (i.e., whether any additional rows were dropped),
    # and the dataframe itself
    return (curr_len < prev_len), _df


# Read original dataframe
df = pd.read_csv('cff_counts.csv', parse_dates=["date"])
df.drop_duplicates(subset=['date'])

# Recursively run the cleaning function until the dataframe is cleaned
run = True
while run:
    run, df = remove_drops(df)

# Sort by date
df = df.sort_values(by='date')
df = df.reset_index(drop=True)

# Produce a plot and save to PNG
plot = df.set_index('date').plot(figsize=(12,8), legend=False, style='o-')
plot.set_xlabel(f'Search date\n(Artifactual drops in counts > {DROP_CUTOFF} due to temporal GitHub Search API '
                f'unreliability have been removed)')
plot.set_ylabel(f'Number of `CITATION.cff` files found on GitHub')
plot.set_ylim(bottom=0)
plt.savefig("cff_counts_clean.png")
