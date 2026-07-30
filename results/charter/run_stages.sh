#!/bin/bash
# Outage-resilient campaign chain: each stage retried up to 12 times with
# 5-min backoff (network drops / provider outages). All completed work is
# in the call cache, so a retry only re-pays the failed call onward.
cd /Users/mac/Downloads/intent_drift_v1
run_stage () {
  local stage=$1 log=results/charter/campaign_$1.log
  for attempt in $(seq 1 12); do
    if python3 run_charter.py campaign --stage "$stage" >> "$log" 2>&1; then
      echo "$(date '+%H:%M') stage $stage done (attempt $attempt)" >> results/charter/run_stages.log
      return 0
    fi
    echo "$(date '+%H:%M') stage $stage failed attempt $attempt — sleeping 300s" >> results/charter/run_stages.log
    sleep 300
  done
  echo "stage $stage exhausted 12 attempts — giving up" >> results/charter/run_stages.log
  return 1
}
run_stage retest && run_stage controls && run_stage v2
