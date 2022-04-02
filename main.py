import os, shutil, subprocess
from datetime import datetime as dt
import multiprocessing as mul

import pandas as pd
from git import Repo

from data.query_repo import generate_repo_csv

NUM_REPO = 1000

REPOS_FOLDER = 'data/repos/'
METRICS_FOLDER = 'data/ck_metrics/'
OUTPUT_FOLDER = 'output/'

CK_RUNNER = 'data/Runner.jar'
INPUT_FILE = 'data/repositories.csv'
OUTPUT = 'output/analysis.csv'

COLUMNS = ['nameWithOwner', 'url', 'createdAt', 'stargazers',
            'releases', 'loc', 'cbo', 'dit', 'lcom']


def log_print(message):
    now = dt.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{now} - {message}')


def already_processed(nameWithOwner: str) -> bool:
    if os.path.exists(OUTPUT):
        df = pd.read_csv(OUTPUT)
        return nameWithOwner in df['nameWithOwner'].values
    return False


def delete_cached_repos(repo_name: str):
    try:
        if os.path.exists(REPOS_FOLDER + repo_name):
            shutil.rmtree(REPOS_FOLDER + repo_name)
        if os.path.exists(METRICS_FOLDER + repo_name + 'class.csv'):
            os.remove(METRICS_FOLDER + repo_name + 'class.csv')
        if os.path.exists(METRICS_FOLDER + repo_name + 'method.csv'):
            os.remove(METRICS_FOLDER + repo_name + 'method.csv')
    except Exception as e:
        log_print(f'Error on exclude {repo_name} =/ ')


def run_ck_metrics(nameWithOwner: str, url: str, created_at: str, stargazers: int, releases: int) -> None:
    try:
        repo_name = nameWithOwner.replace('/', '@')
        delete_cached_repos(repo_name)

        # Assert that the repository isn't already in the output
        if not os.path.exists(f'{OUTPUT_FOLDER}{repo_name}.csv') and not already_processed(nameWithOwner):
            repo_path = REPOS_FOLDER + repo_name
            ck_metrics_path = METRICS_FOLDER + repo_name

            log_print(f'Cloning {nameWithOwner}')
            Repo.clone_from(url, repo_path, depth=1, filter='blob:none')

            log_print(f'Running CK metrics on {repo_name}')
            subprocess.call(["java", "-jar", CK_RUNNER, repo_path, "true", "0", "False", ck_metrics_path])

            metrics = pd.read_csv(ck_metrics_path + 'class.csv')
            loc = metrics['loc'].sum()
            cbo = metrics['cbo'].median()
            dit = metrics['dit'].median()
            lcom = metrics['lcom'].median()

            df = pd.DataFrame([[nameWithOwner, url, created_at, stargazers,
                releases, loc, cbo, dit, lcom]], columns=COLUMNS)
            df.to_csv(OUTPUT_FOLDER + repo_name + '.csv', index=False)

            shutil.rmtree(repo_path)
            os.remove(ck_metrics_path + 'class.csv')
            os.remove(ck_metrics_path + 'method.csv')

            return df
    
    except Exception as e:
        log_print(f'Error on {nameWithOwner}: {e}')
        delete_cached_repos(repo_name)


if __name__ == '__main__':
    rp_list = pd.DataFrame()

    # Create folders if they don't exist
    if not os.path.exists(OUTPUT): os.makedirs(OUTPUT_FOLDER)
    if not os.path.exists(REPOS_FOLDER): os.makedirs(REPOS_FOLDER)
    if not os.path.exists(METRICS_FOLDER): os.makedirs(METRICS_FOLDER)

    # Verify if the input file exists. If not, generate it.
    if os.path.exists(INPUT_FILE):
        log_print('Reading repositories')
    else:
        log_print('Generating repositories.csv')
        generate_repo_csv(NUM_REPO)

    # Read the input file
    rp_list = pd.read_csv(INPUT_FILE)

    # Verify if the input file is valid. If not, generate it.
    if len(rp_list) <= NUM_REPO:
        log_print('Generating new repositories.csv')
        generate_repo_csv(NUM_REPO)

    rp_list = rp_list.sort_values(by='stargazers', ascending=False)[:int(NUM_REPO*1.25)]
    # Declare the number of threads to use
    pool = mul.Pool(int(os.cpu_count())*3)

    # Get the input file and filter out the already read repositories
    rp_list = pd.read_csv(INPUT_FILE)

    # Run the CK metrics for each repository
    rows = list(rp_list.itertuples(name=None, index=False))
    results = pool.starmap(run_ck_metrics, rows)
    results = list(filter(lambda x: x is not None, results))

    # Build the output file for each repository analyzed in outut folder and remove
    output = pd.concat(results) if len(results) > 0 else pd.DataFrame(columns=COLUMNS)
    if os.path.exists(OUTPUT):
        output = pd.concat([output, pd.read_csv(OUTPUT)])
    for repo in os.listdir(OUTPUT_FOLDER):
        output = pd.concat([output, pd.read_csv(OUTPUT_FOLDER + repo)])
        os.remove(OUTPUT_FOLDER + repo)

    # Assert that the output file has not duplicates
    output = output.drop_duplicates()
    output = output.sort_values(by='stargazers', ascending=False)
    # Export the output file
    output.to_csv(OUTPUT, index=False)

    log_print('Done')
