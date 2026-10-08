# Benchmark protocol — do not estimate

Run the identical 60-second project on an A100 80 GB and an H100 80 GB.  Use
the same saved `LUCA_ACCADEMIA` reference, `LUCA_IT_ACCADEMIA` voice preset,
script, seed, native resolution, DMD2 step count and screen asset.

| GPU | on-demand price/h | wall time | GPU h | final seconds | real cost/final min | peak VRAM | native/final resolution | identity | lip-sync | hands | movement | artifacts | decision |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| A100 80 GB |  |  |  | 60 |  |  | 720p / 1080p |  |  |  |  |  |  |
| H100 80 GB |  |  |  | 60 |  |  | 720p / 1080p |  |  |  |  |  |  |

Use the actual hourly price charged by the selected RunPod pod at the time of
the test.  `real cost/final min = hourly price × GPU hours ÷ final minutes`.
Reject any result that fails visual publishing quality even when it is cheaper.
