#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source ${DIR}/common.sh

header Autoflake
if [[ ${CHECK} == "check" ]]; then
  autoflake --remove-all-unused-imports --check --recursive --remove-unused-variables --in-place ./stellanow_sdk_python --exclude=__init__.py
else
  autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place ./stellanow_sdk_python --exclude=__init__.py
fi
echo OK
