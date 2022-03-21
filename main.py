import os, shutil, subprocess
from datetime import datetime as dt

import pandas as pd
from git import Repo

from query_repo import generate_repo_csv

NUM_REPO = 5
REPO_PATH = 'data/repos'
CK_METRICS = 'data/ck_metrics'
OUTPUT = 'output'
OUTPUT_FILE = 'output/output.csv'
INPUT_FILE = 'output/repositories.csv'

def log_print(message: str):
    print('{}: {}'.format(
        dt.now().strftime('%Y-%m-%d %H:%M:%S'),
        message)
    )

def remove_old_files():
    if 'repos' in os.listdir('data'):
        for folder in os.listdir(REPO_PATH):
            shutil.rmtree(REPO_PATH + folder, ignore_errors=True)
    else:
        os.mkdir(REPO_PATH)
    if 'ck_metrics' in os.listdir('data'):
        for folder in os.listdir(CK_METRICS):
            shutil.rmtree(CK_METRICS + folder, ignore_errors=True)
    else:
        os.mkdir(CK_METRICS)


if __name__ == '__main__':
    rp_list = pd.DataFrame()
    if 'repositories.csv' not in os.listdir(OUTPUT):
        log_print('Generating repositories.csv')
        generate_repo_csv(NUM_REPO)
    else:
        log_print('Reading repositories')
        rp_list = pd.read_csv(INPUT_FILE)
        if len(rp_list) != NUM_REPO:
            log_print('Generating new repositories.csv')
            generate_repo_csv(NUM_REPO)
            rp_list = pd.read_csv(INPUT_FILE)

    output = pd.DataFrame(columns=['nameWithOwner','url','createdAt','stargazers',
        'releases','loc','cbo','dit','lcom'])
    if 'output.csv' in os.listdir(OUTPUT):
        output = pd.read_csv(OUTPUT_FILE)

    rp_list = rp_list[rp_list['alreadyRead'] == False]
    for row in rp_list.itertuples():
        remove_old_files()
        repo_name = row.nameWithOwner.split('/')[1]
        repo_path = 'data/repos/{}'.format(repo_name)
        ck_metrics_path = 'data/ck_metrics/{}'.format(repo_name)

        Repo.clone_from(row.url, 'data/repos/{}'.format(repo_name))

        subprocess.call(["java", "-jar", "data/ckRunner.jar", repo_path, "true", "0",
            "False", ck_metrics_path])
        ck_metrics = pd.read_csv(ck_metrics_path + 'class.csv')

        loc = ck_metrics['lcom'].sum()
        cbo = ck_metrics['cbo'].median()
        dit = ck_metrics['dit'].median()
        lcom = round(ck_metrics['lcom'].median(),2)

        output = output.append({'nameWithOwner': row.nameWithOwner,
            'url': row.url, 'createdAt': row.createdAt, 'stargazers': row.stargazers,
            'releases': row.releases, 'loc': loc, 'cbo': cbo, 'dit': dit, 'lcom': lcom},
            ignore_index=True)
        output.to_csv(OUTPUT_FILE, index=False)
        try:
            row.alreadyRead = True
        except:
            log_print('Error updating alreadyRead column')
            rp_list.loc[rp_list['nameWithOwner'] == row.nameWithOwner, 'alreadyRead'] = True
        
        input('Press Enter to continue...')
        shutil.rmtree(repo_path, ignore_errors=True)
        shutil.rmtree(ck_metrics_path, ignore_errors=True)