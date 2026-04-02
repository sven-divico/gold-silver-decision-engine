# Calculator Specification

## Purpose
Define the first calculator scope for the Gold & Silver Decision Engine.

## Calculator modules in MVP

### 1. Gold vs Silver Purchase Comparison
Compare a simple purchase scenario for physical gold and physical silver.

#### Inputs
- gold purchase amount in EUR
- silver purchase amount in EUR or net metal value equivalent
- silver VAT rate (default 19%)
- optional future price change assumption in percent
- optional holding period in years
- optional purchase premium field placeholder, but default to 0 in MVP
- optional sale discount field placeholder, but default to 0 in MVP

#### Outputs
- effective acquisition value for gold
- effective acquisition value for silver
- silver VAT amount paid
- required price increase for silver to recover VAT handicap
- scenario value after assumed price change
- absolute and percentage comparison summary

### 2. Gold/Silver Ratio Display
A simple ratio module.

#### Inputs
- gold price per ounce
- silver price per ounce

#### Outputs
- current gold/silver ratio
- simple status label:
  - elevated
  - neutral
  - compressed

### 3. Historical Ratio View
Display a chart based on stored daily or periodic data.

#### Outputs
- time series chart of gold/silver ratio
- current ratio
- historical min, max, average over selected dataset

## Formula notes

### Silver VAT
For a private buyer in Germany:
- silver VAT is part of the purchase cost
- VAT is treated as a sunk cost for the scenario comparison
- no resale VAT recovery is assumed for private selling in the calculator

### Required silver appreciation to offset VAT
If net silver value is `N` and VAT rate is `v`, then total cost is:

`total_cost = N * (1 + v)`

To recover this cost ignoring spreads, future net silver value must equal `total_cost`.

Required appreciation over the initial net value:

`required_appreciation = v`

For a 19% VAT rate, required appreciation is 19% ignoring other frictions.

## Ratio status rules for MVP
Use simple rule thresholds that can later be refined.

- elevated: ratio > 80
- neutral: ratio between 60 and 80 inclusive
- compressed: ratio < 60

These are heuristic labels, not predictive signals.

## Explicit assumptions
- no investment advice
- no spread handling in MVP unless manually entered later
- no tax modeling beyond the silver VAT entry effect
- no automatic legal interpretation engine
- no live price execution

## Edge cases
- reject zero or negative prices
- reject zero silver price in ratio calculation
- validate percentage inputs
- show assumptions clearly in UI
