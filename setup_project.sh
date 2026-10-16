#!/usr/bin/env bash
set -eu

mkdir -p \
  src/engine \
  src/ai \
  src/gui \
  assets \
  tests \
  docs

touch \
  src/__init__.py \
  src/engine/__init__.py \
  src/ai/__init__.py \
  src/gui/__init__.py \
  tests/__init__.py

printf 'Project directories and package files are ready.\n'
