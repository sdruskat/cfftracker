import pandas as pd
import matplotlib.pyplot as plt


cff_counts = pd.read_csv('cff_counts.csv', parse_dates=["date"])
cff_counts.drop_duplicates(subset=['date'])
plot = cff_counts.set_index('date').plot(figsize=(12,8), legend=False, style='o-')
plot.set_xlabel('Search date')
plot.set_ylabel('Number of `CITATION.cff` files found on GitHub')
plot.set_ylim(bottom=0)
plt.savefig("cff_counts.png")
