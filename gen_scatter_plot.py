import os
from datetime import datetime as dt

import matplotlib.pyplot as plt
import pandas as pd

QUALITY_COLUMNS = ['cbo', 'dit', 'lcom']
METRIC_COLUMNS = [
  'stargazers',
  'releases',
  'loc',
  'age'
  ]


def age_calculator(created_at: str) -> float:
    now = dt.now()
    created_at = dt.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
    return (now - created_at).days / 365.25


plt.style.use('_mpl-gallery')
if not os.path.exists('/plots/'):
    os.makedirs('/plots/')

# make the data
df = pd.read_csv('output/analysis.csv')
df = df.dropna().sort_values(by=['stargazers'], ascending=False)[:1000]
df['age'] = df['createdAt'].apply(age_calculator)

for quality_column in QUALITY_COLUMNS:
    for metric_column in METRIC_COLUMNS:
        fig, ax = plt.subplots()
        x = df[metric_column]
        y = df[quality_column]
        ax.scatter(x, y, alpha=0.5)
        ax.set(
            xlabel=metric_column,
            ylabel=quality_column
        )
        plt.savefig(f'plots/{metric_column}_{quality_column}.png', dpi=300, bbox_inches='tight')
        plt.close()

print('Done')