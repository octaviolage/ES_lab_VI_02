import os, shutil, subprocess
import numpy as np
from datetime import datetime as dt

import pandas as pd
from git import Repo

from query_repo import generate_repo_csv

NUM_REPO = 1000
REPOS_FOLDER = 'data/repos/'
METRICS_FOLDER = 'data/ck_metrics/'
CK_RUNNER = 'data/ckRunner.jar'
INPUT = 'data/repositories.csv'
OUTPUT = 'output/analysis.csv'
COLUMNS = ['nameWithOwner', 'url', 'createdAt', 'stargazers',
            'releases', 'loc', 'cbo', 'dit', 'lcom']


def remove_cache_files():
    if os.path.exists(REPOS_FOLDER):
        for child in os.listdir(REPOS_FOLDER):
            shutil.rmtree(REPOS_FOLDER + child, ignore_errors=True)
    else:
        os.mkdir(REPOS_FOLDER)
    if os.path.exists(METRICS_FOLDER):
        for child in os.listdir(METRICS_FOLDER):
            os.remove(METRICS_FOLDER + child)
    else:
        os.mkdir(METRICS_FOLDER)


def log_print(message):
    now = dt.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{now} - {message}')


if __name__ == '__main__':
    rp_list = pd.DataFrame()
    if os.path.exists(INPUT):
        log_print('Reading repositories')
        rp_list = pd.read_csv(INPUT)
    else:
        log_print('Generating repositories.csv')
        generate_repo_csv(NUM_REPO)

    if len(rp_list) != NUM_REPO:
        log_print('Generating new repositories.csv')
        generate_repo_csv(NUM_REPO)

    rp_list = pd.read_csv(INPUT)
    rp_unread = rp_list[rp_list['alreadyRead'] == False]
    if os.path.exists(OUTPUT):
        output = pd.read_csv(OUTPUT)
        if len(output) + len(rp_unread) != NUM_REPO:
            rp_list['alreadyRead'] = False
            rp_unread = rp_list
            output = pd.DataFrame(columns=COLUMNS)
    else:
        output = pd.DataFrame(columns=COLUMNS)

    for row in rp_unread.itertuples():
        remove_cache_files()
        repo_name = row.nameWithOwner.split('/')[1]
        repo_path = REPOS_FOLDER + repo_name
        ck_metrics_path = METRICS_FOLDER + repo_name
        log_print(f'Cloning {repo_name} / {repo_path}')
        Repo.clone_from(row.url, repo_path, filter='blob:none')

        log_print(f'Running CK metrics on {repo_name}')
        subprocess.call(["java", "-jar", CK_RUNNER, repo_path, "true", "0", "False", ck_metrics_path])

        metrics = pd.read_csv(ck_metrics_path + 'class.csv')
        loc = metrics['loc'].sum()
        cbo = metrics['cbo'].median()
        dit = metrics['dit'].median()
        lcom = metrics['lcom'].median()

        output = pd.concat([output, pd.DataFrame([[row.nameWithOwner, row.url, row.createdAt, row.stargazers,
            row.releases, loc, cbo, dit, lcom]], columns=COLUMNS)])
        output.to_csv(OUTPUT, index=False)
        rp_list.loc[rp_list['nameWithOwner'] == row.nameWithOwner, 'alreadyRead'] = True
        rp_list.to_csv(INPUT, index=False)
        # input('Press enter to continue')

    remove_cache_files()

    log_print('Done')
