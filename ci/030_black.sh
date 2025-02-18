#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source ${DIR}/common.sh

header Fortmating code
if [[ ${CHECK} == "check" ]]; then
  black ./stellanow_sdk_python -l 120 --check --diff --exclude '/input_roles\.py$'
else
  black ./stellanow_sdk_python -l 120 --exclude '/input_roles\.py$'
fi
echo OK
