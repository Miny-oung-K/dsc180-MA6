## Exercise 5: ridge vs persistence

I would deploy persistence if the goal is to minimize the average number of rides by which the daily forecast is off. On the starter's H2 2012 test set, ridge raised R² from 0.5099 to 0.5833, an increase of 0.0734, but its MAE was 947.1 rides versus 840.1 for persistence. That is 107.0 more rides of absolute error per day on average. The higher R² means ridge reduced squared error, which gives large misses more weight. If those misses are especially costly, that gain is worth investigating. For a daily forecast judged by absolute error, yesterday's count is the better choice on these results.

The numbers above come from the assignment's starter results. Update this comparison against the final `reports/metrics.json` after the team's feature and validation work is complete.
