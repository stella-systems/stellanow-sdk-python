#!/usr/bin/env bash
for script_file in $(ls -1 ci/*.sh | grep -v ci/common.sh | sort ) ; do
  sh ${script_file} $1
done
