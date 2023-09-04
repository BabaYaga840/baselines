#!/bin/bash

python -u -O train.py \
--rollout.num_envs=8 \
--rollout.num_buffers=2  \
--rollout.num_steps=128 \
--ppo.bptt_horizon=8 \
--ppo.num_minibatches=16 \
--wandb.entity=soumojit_048 \
--wandb.project=nmmo \
--train.opponent_pool=pool.json \
--train.num_steps=1000 \
--env.num_maps=100 \
--env.team_size=8 \
--env.num_teams=16 \
--env.num_npcs=256 \
--env.num_learners=16 \
"${@}"
