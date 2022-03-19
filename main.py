import os, shutil, subprocess
import numpy as np

import pandas as pd
from git import Repo

from query_repo import generate_repo_csv

NUM_REPO = 1
REPO_PATH = 'data/repos'
CK_METRICS = 'data/ck_metrics'
OUTPUT = 'output'

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
        print('Generating repositories.csv')
        generate_repo_csv(NUM_REPO)
    else:
        print('Reading repositories')
        rp_list = pd.read_csv(OUTPUT + '/repositories.csv')
        if len(rp_list) != NUM_REPO:
            print('Generating new repositories.csv')
            generate_repo_csv(NUM_REPO)
            rp_list = pd.read_csv('data/repositories.csv')

    rpna_list = rp_list[rp_list['cbo'].isna()]

    for row in rpna_list.itertuples():
        remove_old_files()
        repo_name = row.nameWithOwner.split('/')[1]
        repo_path = 'data/repos/{}'.format(repo_name)
        ck_metrics_path = 'data/ck_metrics/{}'.format(repo_name)
        Repo.clone_from(row.url, 'data/repos/{}'.format(repo_name))

        subprocess.call(["java", "-jar", "data/ckRunner.jar", repo_path, "true", "0", "False", ck_metrics_path])
        
        input('Press Enter to continue...')
        shutil.rmtree(repo_path, ignore_errors=True)
        shutil.rmtree(ck_metrics_path, ignore_errors=True)