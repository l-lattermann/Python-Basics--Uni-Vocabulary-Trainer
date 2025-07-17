#!/bin/bash
cd "$(dirname "$0")"
./src_and_data/vocabulary_trainer.py
read -n 1 -s -r -p "Press any key to close..."