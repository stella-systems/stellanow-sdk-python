#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source ${DIR}/common.sh

header Fortmating code
if [[ ${CHECK} == "check" ]]; then
  ruff check  ./stellanow_sdk_python --quiet
else
   ruff check  ./stellanow_sdk_python
fi
echo OK
