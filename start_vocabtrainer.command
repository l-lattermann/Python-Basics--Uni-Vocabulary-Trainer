#!/bin/bash
cd "$(dirname "$0")"
./vocabulary_trainer.py
read -n 1 -s -r -p "Press any key to close..."