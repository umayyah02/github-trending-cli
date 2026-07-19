# GitHub Trending Repositories CLI

A command-line tool that shows trending GitHub repositories, right from
your terminal. Filter by time window (day, week, month, or year), sorted
by star count — no browser, no authentication required.

```
$ python -m trending_repos.cli --duration day --limit 5

Trending Repositories (last day)
----------------------------------------------------
1. torvalds/linux ★ 1,204 [C]
   Linux kernel source tree
   https://github.com/torvalds/linux

2. openai/example-repo ★ 980 [Python]
   Example description text here
   https://github.com/openai/example-repo
...
```

## Requirements

- Python 3.9 or later
- No GitHub account or API token needed

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/umayyah02/github-trending-cli.git
   cd github-trending-cli
   ```

2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

That's it — no build step, no config files.

## Usage

Run the tool as a Python module from the project root:

```
python -m trending_repos.cli
```

With no flags, this shows the top 10 trending repositories from the
past week.

### Options

| Flag | Type | Default | Allowed values |
|---|---|---|---|
| `--duration` | string | `week` | `day`, `week`, `month`, `year` |
| `--limit` | integer | `10` | Positive integer, capped at 100 |

### Examples

Top 20 repositories from the past month:
```
python -m trending_repos.cli --duration month --limit 20
```

Top 3 repositories from today:
```
python -m trending_repos.cli --duration day --limit 3
```

Requesting more than 100 results prints a warning and caps the count
at 100 (the GitHub Search API's per-page maximum) rather than failing:
```
python -m trending_repos.cli --limit 500
```

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success, including the "no results found" case |
| `1` | A handled error (invalid input, network failure, API error) |
| `2` | Unrecognized command-line flag (argparse's own default behavior) |

## How "trending" is defined

Results are filtered by repository **creation date** within the
selected time window (e.g. `--duration week` means "created in the
last 7 days"), then sorted by star count, descending.

## Rate limits

This tool makes unauthenticated requests to the GitHub Search API,
which allows 60 requests per hour per IP address. If you hit the
limit, the tool will report it clearly and tell you when it resets.

## Running the tests

```
pip install pytest
python -m pytest tests/ -v
```

## Project structure

```
trending_repos/
├── cli.py            # Argument parsing, orchestration, entry point
├── github_client.py  # GitHub API requests and error handling
├── formatter.py       # Converts repository data into display text
└── date_utils.py      # Duration string → date cutoff conversion
```

## License

See [LICENSE](LICENSE).