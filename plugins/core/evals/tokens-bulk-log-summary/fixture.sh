#!/usr/bin/env bash
# Scaffold for the eval case: a 12,000-line nightly log with two failures in the middle.
set -euo pipefail
mkdir -p ci
awk 'BEGIN{for(i=1;i<=12000;i++){
  if(i==5210) print "FAIL test_bank_withdraw: expected balance 50, got 0";
  else if(i==9033) print "FAIL test_trade_cancel: timeout after 30s";
  else printf "PASS test_case_%05d (0.%03ds)\n", i, i%1000 }}' > ci/nightly-2026-11-10.log
