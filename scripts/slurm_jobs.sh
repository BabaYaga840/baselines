#!/bin/bash

# Get all running jobs
running_jobs=$(sacct | grep RUN | grep -v .batch | awk '{print $1}')

# Loop through each job ID
for job_id in $running_jobs; do
  # Find the log file
  log_file=$(find sbatch/ -name "${job_id}.log")

  # Grep the experiment directory
  experiment_dir=$(grep -m 1 "Experiment directory" "$log_file" | awk -F': ' '{print $2}')

  # Print job_id and experiment_dir
  echo "$job_id, $experiment_dir"
done
