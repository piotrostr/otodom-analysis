#!/bin/bash

KEYWORD=restaurant

curl -L -X GET -G \
   "https://maps.googleapis.com/maps/api/place/nearbysearch/json" \
   -d location=54.382920,18.611969 \
   -d key=$GOOGLE_MAPS_API_KEY \
   -d keyword=$KEYWORD \
   -d radius=1500 \
   -d page_token="AUacShgszXS90hT44tdETxQJDUOVu5yjQa-97uJXrCDYKNXHprWyPXQpmBLkelHxpgMIUkx7PQUunqyvQAgt08IxkcXok4-nBsbUJyprxcRW8Ul9EnUlES1ITYnN0ddkK0ZX6rymsUUPF9OdefBXh6ye0nwomMSwr3wm4rZFWJujNEV-xx-QSOk8Xcp-ImbTSmx6rPPPzjEFUiIb_JO9Ju-msMrDDMTlh8OQXFkX93brVmUhMufcbHM5J3UQBpbdywgGegyxCKRQKDt6Jl3p5b_nLtYQqJkHnaaDuNbS-GtHOfzXCy12RET8mLvnE1iSOLuWwKS97ksyIS8S_4zc0FozsMEc2WhvDbG_etY_Vor8T4wlDWd0VyopXi_SuXvK1JhgIUFVKEYFFeBgbX8jFT-TsKGUW3Xg8WqfPy2shXb6ApLPZ2U9U6RCmtgIQtVB" \
   -d max_result_count=60 \
   | jq '.results | length'

