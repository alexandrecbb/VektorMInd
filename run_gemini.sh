#!/bin/bash

# tgi
# train
export GEMINI_API_KEY="AIzaSyA4KsJN9jLeq2zddE593xNDzDaHKEK4DEQ"

python run.py sim \
--market-data-path data/03_model_input/tsla.pkl \
--start-time 2016-01-15 \
--end-time 2016-02-12 \
--run-model train \
--config-path config/tsla_gemini_config.toml \
--checkpoint-path data/06_train_checkpoint \
--result-path data/05_train_model_output
# # train-checkpoint
# python run.py sim-checkpoint \
# -ckp /workspace/FinMem-LLM-StockTrading/data/06_train_checkpoint \
# -rp data/05_train_model_output \
# -cp config/tsla_gemini_config.toml \
# -rm train


# # test
# python run.py sim \
# -mdp data/03_model_input/tsla.pkl \
# -st 2022-10-07 \
# -et 2023-04-10 \
# -rm test \
# -cp config/tsla_gemini_config.toml \
# -tap  ./data/06_train_checkpoint  \
# -ckp ./data/08_test_checkpoint \
# -rp ./data/09_results
# # test-checkpoint
# python run.py sim-checkpoint \
# -ckp /workspace/FinMem-LLM-StockTrading/data/06_train_checkpoint \
# -rp data/05_train_model_output \
# -cp config/tsla_gemini_config.toml \
# -rm test
# save file
# python save_file.py
