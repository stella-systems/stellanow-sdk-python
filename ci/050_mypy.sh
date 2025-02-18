#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source ${DIR}/common.sh


header Lunching mypy - Typing check
mypy --ignore-missing-imports --check-untyped-defs stellanow_sdk_python
echo ok
