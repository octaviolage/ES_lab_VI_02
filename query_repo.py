from os import environ

import requests

MAX_QUERY_ATTEMPTS = 10
AFTER_PREFIX = ', after: {cursor}'
OUTPUT = 'data/repositories.csv'

# We choose the first 20 repositories to avoid 502 errors from GitHub GraphQL API.
QUERY = """
    {
      search(query: "language:java,stars:>100", type: REPOSITORY, first: 20 {after}) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          ... on Repository {
            nameWithOwner
            url
            createdAt
            stargazers {
              totalCount
            }
            releases {
              totalCount
            }
            primaryLanguage {
              name
            }
          }
        }
      }
    }
    """


def export_csv(repos: list) -> None:
    """
    This function exports the list of repositories to a CSV file.
    """
    with open(OUTPUT, 'w') as f:
        f.write('nameWithOwner,url,createdAt,stargazers,releases\n')
        for repo in repos:
            f.write('{},{},{},{},{}\n'.format(
                repo['nameWithOwner'],
                repo['url'],
                repo['createdAt'],
                repo['stargazers']['totalCount'],
                repo['releases']['totalCount']
            ))
    return OUTPUT


def query_runner(query: str, token: str, attemp=1) -> dict:
    """
    This function runs a query against the GitHub GraphQL API and returns the result.
    """
    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    response = requests.post(url, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 502 and attemp <= MAX_QUERY_ATTEMPTS:
        print('Attemp {}/{} get Error 502. Retrying...'.format(attemp, MAX_QUERY_ATTEMPTS))
        return query_runner(query, token, attemp + 1)
    elif response.status_code == 502 and attemp > MAX_QUERY_ATTEMPTS:
        print('Error 502. Maximum number of attempts reached. Try again later.')
        exit(1)
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(response.status_code, query))


def get_repos(token: str, after: str) -> list:
    """
    This function returns a list of the most popular repositories on GitHub and their caracteristics.
    """
    query = QUERY.replace('{after}', after)
    result = query_runner(query, token)

    if 'data' in result:
        return result['data']
    else:
        print(result)
        raise Exception('Error getting repositories. Message: {}. \n {}'.format(result['message'], query))


def generate_repo_csv(results: int, token: str=None) -> str:
    if not token:
        if 'GITHUB_TOKEN' in environ:
            token = environ['GITHUB_TOKEN']
        else:
            raise Exception(
                "You need to set the GITHUB_TOKEN environment variable or pass your token as an argument")

    after = '' # Pagination
    repositories = [] # List of repositories
    # The process is repeated until there are amount of results wanted
    while (len(repositories) < results):
        response = get_repos(token, after)
        repositories.extend(response['search']['nodes'])
        if response['search']['pageInfo']['hasNextPage']:
            cursor = response['search']['pageInfo']['endCursor']
            after = AFTER_PREFIX.format(cursor=f'"{cursor}"')
    return export_csv(repositories)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Query the GitHub GraphQL API to get most popular repositories.')
    parser.add_argument('--token', '-t', help='GitHub access token')
    parser.add_argument('--results', '-r', help='Number of results to return', type=int, default=100)
    args = parser.parse_args()

    generate_repo_csv(args.results, args.token)