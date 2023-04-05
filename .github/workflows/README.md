# GitHub Actions CI/CD workflows

## Python Checks
The Python-Checks workflow will run a series of checks on the python code
in this repository.

### Bandit
The Bandit workflow will run the Bandit security linter tool against this 
project. A failed run indicates that Bandit found at least one vulnerability.

### Black
The workflow outlined in `black.yml` checks to ensure that the Python style
for this project is consistent and fully implemented in all Python files.
For more information about this workflow, see
https://black.readthedocs.io/en/stable/github_actions.html

## CodeQL-Analysis
The codeql-analysis workflow the CodeQL semantic code analysis engine to help
find security issues very early on in the development process. See
[CodeQL](https://securitylab.github.com/tools/codeql) for more details.

## Deploy
Deploys the project to the correct GIVE environment within Cloud.gov. The
deploy workflow will run unit-tests and only deploy if those test are
successful. Deployment will also only be triggered in the 18F repository. This
will prevent forks from needlessly running workflows that will always fail
(forks won't be able to authenticate into the dev environment).

## Stale Items
The stale-items workflow will run once per day and mark issues and PR's as
stale if they have not seen any activity over the last 30 days. After being
marked stale for 5 days, the workflow will close the item.

## Unit Tests
The unit-tests workflow will install the project runtime dependencies and run
the unit test suite against the code. This workflow is used to run unit tests
for the application against pull requests before merging takes place. Additional
unit testing will take place on merging.
