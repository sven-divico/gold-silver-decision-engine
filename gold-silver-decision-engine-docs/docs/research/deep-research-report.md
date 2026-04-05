# Silver mispricing vs gold: recurring conditions, indicators, and backtestable hypotheses

This document is a research foundation for a rules-based system that aims to detect when **silver is mispriced relative to gold**. It is not investment advice and intentionally avoids generic precious-metals commentary.

## Executive summary

A defensible way to think about “silver mispricing vs gold” is: **gold is often the primary macro/monetary signal**, while **silver is a higher-volatility hybrid of monetary + industrial exposure**, which can drift away from gold under identifiable regimes—then later “catch up” or overshoot. This framing is consistent with empirical research finding that (a) the gold–silver relationship is not stable, and (b) gold can “drive” silver, especially during extreme episodes rather than normal conditions. citeturn13view1turn37view1

Across major historical episodes (late-1979/1980, 2008–2011, 2020, and post-2020), the most repeatable pattern is **regime-dependent ratio behavior**:

- In **acute liquidity stress** (margin calls, “sell what you can,” funding pressure), silver tends to be hit harder than gold and can look **cheap vs gold** (ratio spikes/widens). This pattern is explicitly described for gold’s own drawdowns during disorderly selling and heavy leverage unwind, and for silver in multiple historical stress narratives. citeturn26view3turn28search2turn37view3  
- In **early precious-metals bull phases**, gold often moves first; silver lags and later catches up, compressing the ratio. The 2011 episode is described as investors explicitly buying silver on “catch-up” logic after gold made successive all-time highs while silver remained below its 1980 nominal peak. citeturn37view1turn13view1  
- In **speculative “froth” conditions**, silver can overshoot (ratio compresses sharply), then mean-revert violently (ratio widens again). The 2011 peak and subsequent rapid drop illustrate this dynamic, with explicit commentary on heavy selling, triggered sell-stops, and extreme ratio compression followed by widening. citeturn37view2turn37view1  
- In **industrial slowdowns / strong-dollar tightening**, silver’s industrial component can add drag relative to gold, making silver look **cheap vs gold** for extended periods (ratio stays elevated). Silver’s industrial role and structural demand drivers are well documented, but the sign and timing depend on whether the industrial channel is strengthening (e.g., electrification/solar) or weakening (PMI/recession). citeturn29view0turn1view1  

For a practical hypothesis engine, a useful conclusion is: **the gold/silver ratio is necessary but not sufficient**. The system should condition ratio signals on a small set of regime indicators that proxy for (1) liquidity stress, (2) macro opportunity cost (real rates/USD), (3) industrial cycle, and (4) positioning/flows.

## Structural relationship between gold and silver

Gold’s role is structurally closer to a “monetary asset”: it is widely described as highly liquid, no one’s liability, and used as an investment and reserve asset, with diversification and liquidity properties emphasized by market research and central-bank analysis. citeturn26view2turn27view0turn26view3

Silver is structurally closer to a “hybrid”: it is simultaneously a precious metal and a major industrial input, with industrial demand tied to electrical/electronics, photovoltaics, grid infrastructure, and vehicle electrification—drivers explicitly highlighted in industry research as key demand pillars. citeturn29view0turn1view1

These structural differences matter for relative pricing because they imply different dominant marginal buyers/sellers across regimes:

- **Safe-haven channel (gold-first)**: During geopolitical/policy uncertainty and stress, gold is often expected to perform as a safe haven, supported by its lack of default risk and by official-sector demand dynamics; central banks’ increasing gold purchases are cited as an important factor in recent years. citeturn27view0turn26view2  
- **Industrial channel (silver-sensitive)**: When industrial expectations deteriorate, silver can underperform even if gold is supported by macro uncertainty; when green-capex/industry accelerates, silver can outperform gold. citeturn29view0turn1view1  

Supply tends to amplify this asymmetry. A key structural claim in industry research is that **a large fraction of silver supply is by-product** (i.e., tied to base-metals/gold mining economics), whereas gold’s supply/demand and market depth differ materially; silver recycling shares and market size comparisons are also emphasized as differences between the metals. citeturn1view1turn26view3

Market microstructure reinforces the “gold-first, silver-beta” tendency. The **entity["company","CME Group","derivatives exchange operator"]**’s materials describe large, liquid benchmark futures contracts for both metals (gold and standard 5,000-oz silver), while the **entity["organization","London Bullion Market Association","precious metals trade assoc"]** documents OTC market conventions and benchmark-setting processes. citeturn21search4turn21search1turn12search2turn12search0

Finally, published empirical work directly supports your “gold leads, silver follows” framing: a prominent study analyzing 1970–2011 finds the relationship is not stable in normal periods and that gold can drive silver in long-run dynamics, especially during extreme episodes. citeturn13view1

## Operational definitions of relative mispricing

Your backtesting system needs a definition that (a) is measurable, (b) can be evaluated out-of-sample, and (c) does not assume a single invariant “fair” ratio. Below are compatible definitions that can coexist in the same engine as separate hypotheses.

**Core variable definitions (engine-friendly)**  
Let:
- `GSR_t = GoldPrice_t / SilverPrice_t` (gold/silver ratio)
- `ΔGSR_t` = change or return of the ratio over horizon `t`
- `z(GSR)_t` = standardized deviation vs a rolling window (e.g., 3y)

**Mispricing as extreme ratio level**  
Silver is “cheap vs gold” when `GSR_t` is unusually high relative to its own history; “expensive vs gold” when unusually low. This is the simplest operationalization and is explicitly referenced in industry commentary during stress episodes (e.g., “multi-decade high” ratio signals undervaluation of silver vs gold). citeturn30view1turn35news40  
Limitation: extremes can persist for long stretches if the regime shifted (non-stationarity), which is exactly what the academic literature warns about. citeturn13view1

**Mispricing as deviation from a regime-conditioned expectation**  
Define a conditional model (even a simple linear/GLM or tree) where the expected ratio level or ratio change depends on indicators such as USD strength, equity volatility, and macro regime. The key rationale is that cointegration/price discovery itself can be regime-dependent: one study explicitly concludes gold and silver are cointegrated only under **weak dollar and high volatility** conditions, with gold dominating silver in that state. citeturn19search0  
Mispricing is then the residual: `ε_t = actual(GSR_t) − expected(GSR_t | regime_t)`.

**Mispricing as lead–lag error (gold momentum not yet reflected in silver)**  
Define a rolling mapping from gold moves to expected silver response (e.g., rolling beta, Granger-causality-inspired lag model). Mispricing is the shortfall/excess of silver relative to that mapping. “Gold drives silver” and “catch-up” narratives are explicitly documented in research and in the 2011 episode write-up. citeturn13view1turn37view1  
Limitation: the mapping itself shifts across regimes and across sources (spot vs futures vs ETFs).

**Mispricing as overshoot during speculative compression**  
When silver catches up rapidly, the ratio can compress beyond levels supported by fundamentals, then snap back. The 2011 episode documents ratio contraction “towards 30:1” and below 32, followed by widening to 56 by year-end, alongside a rapid 30% silver drawdown in six trading days after the peak. citeturn37view1turn37view2

**Mispricing as microstructure dislocation**  
Define mispricing as a wedge between gold and silver caused by *financing, delivery constraints, margin policy, or geographic benchmark segmentation*—even if “fundamentals” are unchanged. Commodity-market stability work emphasizes how volatility and margin calls can create liquidity demand and stress propagation; precious-metals commentary also highlights leveraged and rule-based trading in volatility spikes. citeturn28search2turn26view3turn21news47  
Operational proxies include: futures–spot spreads, lease rates, ETF premium/discount behavior, and abrupt margin requirement changes.

## Indicator candidates and data practicality

The table below focuses on *observable* indicators that can be integrated into a Python hypothesis engine. “Directionality” is deliberately framed as **conditional**—because the same indicator can imply different outcomes under different regimes.

| Indicator | Rationale (why it might detect mispricing) | Silver “cheap vs gold” signal (typical) | Silver “expensive vs gold” signal (typical) | Practicality and limitations |
|---|---|---|---|---|
| Gold/silver ratio level (`GSR`) | Direct relative price; extremes recur in documented episodes (e.g., March 2020; early 2011 compression). citeturn30view1turn37view1 | High `GSR` (ratio spike/widening) | Low `GSR` (ratio compression) | Easy to compute; regime non-stationarity is the main failure mode. citeturn13view1 |
| Ratio z-score (`z(GSR)`) | Normalizes level to a rolling regime; supports “extreme vs recent norm” hypotheses. citeturn13view1 | Positive, large z | Negative, large magnitude z | Needs stable window choice; sensitive to structural breaks. |
| Ratio momentum (`ΔGSR`) | Stress often appears as rapid widening; froth as rapid compression (2011, 2020 patterns). citeturn37view2turn30view1 | Fast widening | Fast compression | Momentum can persist; useful when paired with regime filter. |
| Gold lead / silver lag feature | Empirical work finds gold can drive silver, especially in extreme episodes; 2011 narrative explicitly frames catch-up. citeturn13view1turn37view1 | Gold breakout + silver under-response | Silver outperforming after gold stalls | Requires careful lag specification; highly regime-dependent. |
| Gold vs silver momentum divergence | Captures “gold monetary bid” without silver confirmation (risk-off) vs “silver beta bid” (risk-on). citeturn27view0turn1view1 | Gold strong, silver weak/flat | Silver strong, gold flat | Needs normalization (vol scaling) because silver volatility is higher. citeturn37view1turn1view1 |
| Equity volatility / stress proxy (e.g., VIX) | Disorderly selling and deleveraging episodes link to volatility spikes and liquidation dynamics. citeturn26view3turn22search0turn28search2 | High volatility + ratio widening | Low volatility + ratio compressing | Readily available; volatility is not perfectly predictive, but useful for regime classification. citeturn22search0turn26view3 |
| Metal-specific implied vol (e.g., gold ETF vol, silver ETF vol) | Measures metal-specific risk premia; divergence can indicate silver-specific stress/froth; methodology formalized by Cboe. citeturn25view3 | Silver implied vol >> gold implied vol | Silver implied vol unusually low vs gold | Availability changes over time; index histories may involve relaunches and methodology updates. citeturn25view3 |
| USD strength proxy | Research explicitly ties cointegration/price discovery regime to weak USD + high volatility; WGC discusses USD as a key gold driver. citeturn19search0turn26view0 | Strong USD often coincides with ratio widening (conditional) | Weak USD often supports compression (conditional) | Choice of USD index matters (DXY vs REER); interaction terms matter more than raw level. citeturn26view0turn19search0 |
| Real rates / real yields proxy | Gold demand narratives emphasize opportunity cost and the role of real rates; link can change depending on official-sector demand. citeturn26view0turn27view0turn26view3 | Rising real yields tends to pressure silver more (conditional) | Falling real yields tends to support both; silver can catch up | Relationship not stable; central bank flows can weaken the simple real-rate link. citeturn27view0 |
| Credit / margin stress proxies | Commodity-market stability analysis highlights margin calls and liquidity demand spikes during volatility, affecting derivative-linked metals. citeturn28search2turn21news47 | Stress up + ratio widening | Stress down + ratio compressing | Many choices (spreads, repo, funding indices); risk of overfitting. |
| Silver industrial cycle proxy (PMI/industrial production) | Silver’s industrial demand is repeatedly emphasized (PV, grid, electronics); downturns drag silver vs gold. citeturn29view0turn1view1 | Weakening industrial proxy + high ratio | Strengthening industrial proxy + compressing ratio | PMIs are noisy; but useful as a regime feature not a standalone trigger. |
| PV/green-demand proxy | Silver demand is materially linked to PV and electrification; “thrifting/substitution” in PV can be a structural shock. citeturn29view0turn17news38 | Negative shock to PV silver intensity can keep silver cheap | Positive shock (growth without thrifting) can push silver rich | Proxies can be indirect; avoid overfitting to one sector. citeturn29view0turn17news38 |
| ETF/ETP holdings & flows divergence | Documented large silver ETP inflows (2020) and record holdings; gold ETF flows also documented as key drivers. citeturn30view1turn30view3turn26view1turn26view3 | Gold inflows strong while silver flows lag/outflow | Silver inflows surge (risk of froth) | Holdings data availability differs by product; flows can be reflexive. |
| Futures positioning (COT categories) | Gold commentary connects drawdowns to very high net long speculative positions and margin dynamics; CFTC provides positioning breakdowns. citeturn26view3turn4search14turn4search6 | Silver spec longs washed out relative to gold | Silver spec longs crowded (overshoot risk) | Needs normalization and careful lagging; positioning can remain extreme. |
| Exchange rules / margin changes | Margin hikes can force deleveraging; documented in commodity markets generally and in recent precious-metal volatility. citeturn28search2turn21news47 | Post-hike liquidation pushes silver cheap | Pre-hike leverage build can push silver rich | Harder to encode historically unless you archive margin bulletins/news. |
| Physical-market tightness proxies (lease rates, benchmark spreads) | Tight spot market, benchmark premia, and lease-rate increases have been reported during recent silver runs; can indicate dislocation. citeturn32news39turn29view0 | If tightness is gold-specific, silver can lag | Silver tightness can signal froth/shortage dynamics | Often proprietary/high-friction; may be “late” indicators. |

**Implementation reality:** indicators tied to *public price series + broad macro data + COT + ETF holdings* are typically easiest to productionize; indicators tied to *lease rates, physical premia, and margin schedules* tend to be higher-friction but can add important explanatory power in stress/froth regimes. This trade-off is consistent with commodity market vulnerability work highlighting opacity, concentration, and leverage in commodity ecosystems. citeturn28search2turn27view0

## Episode pattern review

This section focuses on “what changed in the relationship,” not generic history.

**Late-1979 to 1980: concentration, rule changes, and forced liquidation dynamics**  
The 1979–1980 silver crisis is a clear case where silver decoupled from typical macro drivers due to concentrated positioning and market structure. A detailed historical record documents large, financed long silver futures positions associated with the Hunt network, including a reported long silver futures position totaling ~50 million ounces in Aug–Sep 1979 at one broker and very large total controlled quantities by year-end. citeturn14view0turn16view0  
The same record documents exchange-level actions and their price impact: on Jan 7, 1980, with spot silver at $35.80, COMEX imposed position limits; spot silver reached an intraday high of $50.36 on Jan 17; and on Jan 21, COMEX imposed a rule prohibiting new orders except liquidation of existing positions—followed by a $10 drop the next day and a collapse to $10.80 by Mar 27, 1980. citeturn16view0  
For your engine, this episode primarily informs: (a) how market-structure shocks can dominate ratio behavior, and (b) why “mispricing” can be driven by forced liquidation and exchange constraints, not slow-moving fundamentals. citeturn16view0turn28search6

**2008: industrial + investor duality and crisis underperformance**  
The **entity["book","World Silver Survey 2009","silver market report"]** describes 2008 as exceptionally volatile, with investors driving silver above $20/oz in the first half (high $20.92 in March) and a collapse to $8.88 in late October as the economic outlook deteriorated. citeturn34view0  
In parallel, gold-focused research notes that gold itself can be pressured during disorderly selling and that gold experienced multiple 15%–25% pullbacks during 2008, even though it later stood out versus many assets. citeturn26view3  
For your relative framework, the key pattern is: **crisis deleveraging can hit silver harder than gold**, widening the ratio and creating a potential “silver discount” regime—especially when industrial demand expectations are weakening at the same time. citeturn34view0turn28search2turn1view1

**2011: catch-up compression, then violent mean reversion**  
The **entity["book","World Silver Survey 2012","silver market report"]** provides a very explicit description of the gold–silver ratio dynamics in 2011. It notes the gold:silver ratio narrowed markedly to below 32 in late April; separately it describes the ratio contracting “towards 30:1” in early 2011 (levels last seen in 1980), attributing much of the move to investors buying silver on “catch-up” beliefs as gold made successive all-time highs from 2008 onward while silver remained below its nominal 1980 peak. citeturn37view1  
It also documents the overshoot/mean-reversion mechanics: silver peaked on April 28 and then dropped to $34.20 on May 6—a 30% fall in six trading days—amid extremely heavy turnover and triggered sell-stops. citeturn37view2  
By end-2011, the ratio had widened back to 56. citeturn37view1  
This is a high-signal episode for your system because it contains both:  
1) a **detectable lead–lag/catch-up narrative**, and  
2) a **detectable froth/positioning unwind** phase after rapid compression. citeturn37view1turn37view2

**2020: liquidity shock, record ratio spike, and investment-flow regime shift**  
A 2020 silver market update notes the gold:silver ratio fell from its multi-decade high of 127 in March 2020 to 97.8 by end-June, while highlighting heavy silver ETP inflows and a sharp silver rebound after a mid-March drop. citeturn30view1  
The same source reports global silver ETP holdings of 925 Moz as of June 30, 2020, along with supply-chain disruptions and elevated premiums in physical products—classic microstructure signals of stress and demand shock. citeturn30view1  
Gold-focused commentary from March 19, 2020 attributes gold volatility to massive liquidations across assets, magnified by leveraged/rule-based trading, and explicitly discusses margin/positioning dynamics in COMEX futures and the role of volatility spikes. citeturn26view3  
A later silver market summary states that 2020 investment inflows were a chief driver of silver’s strong year, that silver-backed ETP holdings exceeded one billion ounces for the first time, and that ETP holdings grew by 331 Moz in 2020. citeturn30view3  
Engine takeaway: the 2020 episode is a canonical example of **liquidity-stress-driven ratio spike (silver discount)** followed by a **catch-up/mean-reversion** phase fueled by investment flows. citeturn30view1turn26view3turn30view3

**Post-2020: retail/institutional flow regimes and physical-market segmentation**  
In 2021, silver ETP holdings rose to a record high, with gains concentrated early in the year “benefiting from the social media focus on silver.” citeturn31view2  
More recently, reporting in 2025 ties silver outperformance and improved ratio levels to a tight spot market and tariff-linked premium dislocations between U.S. and London benchmarks, alongside increased lease rates—exactly the kind of microstructure regime that can produce temporary relative mispricings. citeturn32news39  
In early 2026, reporting highlights very large retail inflows into silver-backed ETFs and describes silver as a crowded trade—an environment consistent with overshoot risk and fragile positioning. citeturn17news47  
These post-2020 episodes matter because they demonstrate that mispricing signals may sometimes be **flow- and plumbing-driven**, not purely macro-driven. citeturn32news39turn17news47turn28search2

## Mechanisms and behavioral explanations

This section separates mechanisms with strong direct support in the sources from weaker-but-plausible hypotheses that should be treated explicitly as such in your engine (i.e., tested and rarely trusted by default).

### Mechanisms with relatively strong support

**Liquidity stress, margin calls, and forced liquidation (“sell what you can”)**  
Gold research attributes price drops during market selloffs to massive liquidations across assets and margin-driven unwinds of leveraged derivatives positions, citing concentrated selling in derivatives and high net-long positioning preceding pullbacks. citeturn26view3  
Commodity-market stability analysis emphasizes how commodity price shocks and volatility can create spikes in margin calls and increased liquidity demand—key conditions for forced selling and cross-asset contagion. citeturn28search2  
Silver’s 2011 narrative also explicitly references institutions “chasing dollars” near year-end and notes “lively silver lending” as balance-sheet support behavior—consistent with a liquidity-centric mechanism in precious metals. citeturn37view3  
Operational implication: the engine should treat **high-volatility + widening ratio** as a candidate “silver discount” state, and should test whether reversal timing improves when conditioning on stress proxies. citeturn26view3turn28search2turn30view1

**Gold’s safe-haven preference and official-sector bid**  
The **entity["organization","European Central Bank","eu central bank"]** explains gold’s safe-haven appeal based on its lack of counterparty default risk and limited/inelastic supply, and documents that gold performs well during stress episodes (high geopolitical risk, policy uncertainty, extreme equity volatility). citeturn27view0  
It also notes that central banks have increasingly purchased gold in recent years, likely linked to geopolitical tensions/sanctions concerns. citeturn27view0  
This supports a “gold-first” dynamic in uncertainty regimes that can widen the ratio before silver catches up. citeturn27view0turn37view1

**Silver’s hybrid demand and industrial drag**  
Industry research documents structural growth in silver industrial demand driven by grid infrastructure, vehicle electrification, photovoltaics, and AI-linked electronics, but also notes that demand can weaken with broader economic deterioration and that sector-specific changes (e.g., PV “thrifting/substitution”) can reduce silver loadings. citeturn29view0turn17news38  
This supports a mechanism where weak industrial expectations can keep silver cheap vs gold even if gold has a monetary bid. citeturn1view1turn29view0

**Speculative catch-up and overshoot dynamics in silver**  
The 2011 silver episode is described as having an “almost feverish” phase, with investors buying silver on catch-up beliefs and engaging in ratio trading, contributing to a dramatic contraction in the gold:silver ratio. citeturn37view1  
The same report documents how quickly that regime can reverse, with heavy liquidation and a sudden ratio widening. citeturn37view2turn37view1  
Operational implication: your engine should distinguish “catch-up” from “froth,” even though both look like ratio compression.

### Plausible but weaker hypotheses

**“Selling winners to raise cash” as a relative driver**  
Gold research explicitly argues gold may be sold to raise cash because it can be among the better-performing, more liquid assets during selloffs. citeturn26view3  
Extending this mechanism to relative gold vs silver (e.g., selling whichever has higher liquidity or lower funding cost) is plausible, but it needs explicit testing because it can cut either direction depending on where leverage is concentrated. citeturn28search2turn21news47

**Microstructure-driven dislocations from delivery constraints and benchmark segmentation**  
The ECB discusses gold market dynamics linked to physically settled futures preference and cross-market shipping (London ↔ New York) under tariff/uncertainty concerns, framing how physical constraints plus derivatives exposures can generate squeezes and margin stress. citeturn27view0  
For silver, reporting on U.S.–London benchmark premiums and lease rates suggests analogous dislocations can occur, but these are harder to model systematically and may be episodic. citeturn32news39  
In the engine, these should be treated as “optional high-alpha / high-variance” features, not core signals.

**Market power / corners / manipulation**  
The 1979–1980 episode demonstrates how concentrated positioning plus exchange rule changes can dominate price and ratio behavior. citeturn16view0turn14view0  
A survey of commodity manipulation economics explains how corners/squeezes and market power can distort prices beyond fundamentals. citeturn28search6  
These are real but rare; useful as “exception handling” rather than a recurring baseline.

## Regime map for a rules-based hypothesis engine

A practical approach is to define a small number of regimes and then evaluate hypotheses **within** regimes and **across** regime transitions. The table below is designed as a first-pass map for that.

| Regime | Typical gold vs silver behavior | Silver more likely… | Indicators that matter more in this regime | Why this regime produces mispricing |
|---|---|---|---|---|
| Acute crisis / liquidity stress | Gold relatively resilient; silver hit harder; ratio widens | Cheap vs gold | Equity vol/stress proxies; credit/margin stress; positioning; abrupt margin changes citeturn26view3turn28search2turn21news47 | Margin calls + deleveraging + liquidity demand; hybrid silver demand adds downside beta citeturn28search2turn1view1 |
| Early monetary-risk bid (gold-first) | Gold moves first; silver lags; ratio elevated then begins to compress | Cheap then mean-reverts | Gold momentum; ratio level + momentum; USD/real-rate direction; volatility state citeturn13view1turn26view0turn19search0 | Gold’s safe-haven/official-sector channel dominates first; silver catches up later citeturn27view0turn37view1 |
| Reflation / recovery (risk-on) | Silver outperforms; ratio compresses | Expensive vs gold late in regime | Industrial proxies (PMI); silver momentum; ETP inflows; implied vol compression citeturn29view0turn31view2turn25view3 | Silver’s cyclical/industrial leverage amplifies upside; flows reinforce trend citeturn29view0turn31view2 |
| Late-cycle speculative froth | Rapid silver catch-up overshoots; ratio compresses too far; crash risk | Expensive vs gold | Positioning extremes; ratio compression speed; silver implied vol; flow crowding citeturn37view2turn17news47turn25view3 | Reflexivity: leverage + momentum + “fear of missing out” then forced unwind citeturn37view1turn37view2 |
| Tightening / strong USD / high real rates | Both can struggle; silver often weaker; ratio can stay high | Cheap vs gold (persistent) | USD proxy; real yields; industrial weakness; risk sentiment citeturn26view0turn19search0turn29view0 | Opportunity cost + strong USD + industrial drag ⇒ silver underperforms citeturn1view1turn26view0 |
| Physical-market dislocation / policy shock | Location spreads and lease rates can distort relative pricing even if macro stable | Either, but unstable | Lease rates, futures–spot spreads, tariff/policy triggers citeturn32news39turn27view0 | Plumbing constraints and hedging demand can dominate temporarily citeturn28search2turn27view0 |

## Hypothesis catalog, prioritization, and implementation notes

Below are explicit hypothesis candidates intended for later backtesting. Each hypothesis should be evaluated on (a) performance, (b) stability across decades, and (c) dependence on regime filters, consistent with evidence that gold–silver dynamics vary materially by episode. citeturn13view1turn19search0

### Hypothesis candidates for backtesting

| Hypothesis name | Description (testable rule idea) | Required inputs | Expected signal direction | Horizon | Best regime | Weakness / failure modes |
|---|---|---|---|---|---|---|
| Gold lead, silver lag | If gold breaks out (strong momentum) while silver lags, expect subsequent silver catch-up (ratio mean-reverts downward) | Gold & silver returns; ratio; volatility filter | Predict `ΔGSR < 0` after signal | Medium | Gold-first / early bull | Can fail in industrial slowdown or persistent tight USD regimes citeturn29view0turn26view0 |
| Extreme ratio mean reversion | Extremely high ratio implies silver “cheap”; extremely low implies silver “rich” | `GSR`, rolling percentiles/z-score | High ratio → `ΔGSR < 0`; low ratio → `ΔGSR > 0` | Medium/long | Works best outside structural breaks | Extremes can persist; regime shifts break stationarity citeturn13view1 |
| Ratio spike reversal under stress | If ratio spikes while volatility is extreme, expect later compression as liquidity normalizes | Ratio momentum + stress proxy | `ΔGSR < 0` after stress peak | Medium | Crisis → recovery | Timing is hard; can whipsaw if stress persists citeturn26view3turn30view1 |
| Liquidity stress silver discount | When broad stress/margin pressure rises, silver underperforms gold (ratio widens); after stress eases, reversal | Stress proxy; ratio; maybe margin-change events | Stress up → `ΔGSR > 0`, then reversal | Short→medium | Acute crisis | Needs robust stress measure; can be late citeturn28search2turn26view3 |
| Catch-up compression overshoot | After rapid ratio compression (silver surge), predict subsequent widening (silver mean-reverts down vs gold) | Ratio momentum; silver momentum; positioning proxy | Fast compression → `ΔGSR > 0` later | Short/medium | Late bull / froth | Can miss true secular shifts in silver demand citeturn29view0turn37view2 |
| Volatility divergence stress | If silver implied vol rises far above gold implied vol, it signals silver-specific stress → silver cheap vs gold | Metal implied vol indices; ratio | High spread → later `ΔGSR < 0` | Medium | Crisis / dislocation | Implied-vol series can change methodologies or availability citeturn25view3turn28search2 |
| Volatility divergence froth | If silver implied vol collapses while silver momentum surges, treat as complacent froth → reversal risk | Silver implied vol; silver momentum; flows | Complacency + surge → `ΔGSR > 0` later | Short | Late bull / froth | Requires robust vol estimate; can false-trigger citeturn37view2turn17news47 |
| USD + high vol cointegration state | Under weak USD + high volatility, treat gold as dominant; use gold moves to predict silver catch-up | USD proxy; equity vol; gold returns | Predict silver follows gold stronger | Medium | Weak USD + high vol | If USD proxy is mismeasured or volatility not “macro” driven, weakens citeturn19search0 |
| Tight USD + industrial weakness regime | Strong USD + weakening industrial proxy implies persistent silver underperformance | USD proxy; PMI/industrial proxy | Predict `ΔGSR > 0` (silver cheapening) | Medium | Tightening / slowdown | Can reverse if silver’s structural demand overwhelms cycle citeturn29view0turn26view0 |
| Industrial acceleration catch-up | Improving industrial proxy increases silver’s relative bid → ratio compresses | PMI/industrial proxy; ratio | `ΔGSR < 0` | Medium | Reflation/recovery | PMI noise; sector-specific thrifting can invert signal citeturn29view0turn17news38 |
| ETF flow divergence | Gold ETF inflows surge without silver participation → silver lag; later silver catch-up | Gold ETF flows; silver ETP flows/holdings | Divergence → subsequent compression | Medium | Gold-first | Flows are reflexive; data coverage varies by product citeturn26view3turn30view3 |
| Silver ETP crowding | Very rapid silver ETP inflows/retail crowding predict overshoot and later ratio widening | Silver ETF/ETP flows; sentiment | Crowding → `ΔGSR > 0` later | Short | Froth | Crowding can persist; hard to time peaks citeturn17news47turn31view2 |
| Positioning washout rebound | If silver managed-money net longs collapse while gold positioning stays firm, expect relative rebound | COT positioning; ratio | Washout → `ΔGSR < 0` later | Medium | Post-crisis | Positioning data weekly; can lag price citeturn4search14turn26view3 |
| Margin shock after leverage build | Margin hikes after large run-ups accelerate liquidation → ratio moves against silver | Margin-change events; futures price | Hike + leverage → `ΔGSR > 0` | Short | Dislocation | Requires constructing a historical margin-event dataset citeturn21news47turn28search2 |
| Year-end balance-sheet stress | Around year-end, “chasing dollars” and lending tightness can pressure silver → ratio widens, then reverses in Jan | Calendar features; funding proxy; ratio | Year-end → `ΔGSR > 0`, early-year reversal | Short | Funding stress | Seasonality may weaken in modern regimes; needs validation citeturn37view3 |
| Structural demand vs thrifting shock | When PV thrifting/substitution accelerates, silver may stay cheap relative to gold despite macro support | PV proxy; industry notes; ratio | Thrifting shock → `ΔGSR > 0` | Medium/long | Structural shift | Proxies can be weak; risk of narrative overfit citeturn29view0turn17news38 |

### Top indicator shortlist for an MVP engine

A credible “v1” shortlist should maximize: (1) availability over decades, (2) interpretability, (3) regime coverage, and (4) incremental value beyond the ratio alone.

1) **Gold/silver ratio level + z-score** — foundational relative price state, directly referenced in historical narratives and episodes. citeturn30view1turn37view1  
2) **Ratio momentum (widening/compression speed)** — helps separate slow drift from stress spikes and froth compression. citeturn37view2turn30view1  
3) **Equity volatility / stress proxy (e.g., VIX)** — a practical regime switch for “disorderly selling” vs normal conditions, consistent with gold’s behavior in volatility spikes. citeturn26view3turn22search0  
4) **USD strength proxy + real-yield proxy** — captures opportunity cost and the weak-USD/high-vol regime described in research; also explicitly used in gold outlook frameworks. citeturn26view0turn19search0turn27view0  
5) **One positioning/flow measure (COT or ETP holdings)** — catches leverage/crowding states that often define overshoot and forced unwind. citeturn4search14turn30view3turn17news47  

### Top hypothesis shortlist for an MVP engine

These are prioritized because they are (a) explicit, (b) broadly testable with accessible data, and (c) directly supported by documented episode mechanics.

1) **Liquidity stress silver discount** — ratio widens in stress; reversal after stress peak. citeturn28search2turn26view3turn30view1  
2) **Gold lead, silver lag** — gold’s move predicts later silver catch-up under the right regime. citeturn13view1turn37view1  
3) **Extreme ratio mean reversion (regime-conditioned)** — use ratio extremes but only act when regime filter supports mean reversion. citeturn13view1turn19search0  
4) **Catch-up compression overshoot** — fast compression predicts later widening (post-froth mean reversion), strongly evidenced by 2011. citeturn37view2turn37view1  
5) **Positioning/flow washout vs crowding** — adds a second dimension to distinguish “cheap because forced selling” from “cheap because fundamentals.” citeturn26view3turn4search14turn31view2  

### Recommendations for building the decision engine

**Data model and observability-first design**  
Start with a “core dataset” that is robust and backfillable: gold and silver prices (same currency, same close convention), ratio features, equity volatility proxy, USD proxy, real-yield proxy, and either COT or ETP holdings. This is aligned with the strongest recurring mechanisms: liquidity stress, macro opportunity cost, and leverage/flows. citeturn26view3turn28search2turn4search14turn30view3  
Treat high-friction microstructure features (lease rates, location premia, margin changes) as an “overlay layer” that can be added once the engine is stable. citeturn32news39turn21news47turn28search2

**Regime labeling should be explicit and testable**  
Because gold–silver dynamics are not stable, your engine should not rank hypotheses globally without regime context. This is consistent with both academic findings (relationship appears in extreme periods, not normal periods) and episode documentation (2011 froth, 2020 stress spike). citeturn13view1turn37view1turn30view1  
A practical v1 regime classifier can be rule-based (e.g., stress = volatility above threshold; tightening = rising real yields and strong USD; industrial slowdown = PMI downtrending). Later versions can use learned classifiers, but rule-based regimes reduce overfitting risk early.

**Backtesting protocol**  
Use walk-forward evaluation and require hypotheses to demonstrate robustness across at least two major regimes (e.g., crisis + reflation). This is important because episodes like 1980 (market structure shock) and 2011 (speculative blow-off) can dominate in-sample fits and produce false confidence. citeturn16view0turn37view2turn13view1  
Include “episode scorecards” (performance by subperiod) so your leaderboard can reveal whether a hypothesis is a crisis-only trick or a genuinely multi-regime signal.

**Output of the research layer (what your engine should store)**  
Instead of storing only buy/hold/sell outputs, store a structured record for each hypothesis evaluation:
- hypothesis name + version
- signal definition (feature thresholds and lags)
- regime constraints
- performance summary overall and by regime/episode
- stability checks (parameter sensitivity, decay, turnover proxy)
This aligns with the goal of a hypothesis leaderboard rather than narrative commentary.

**Sources (high-value references used above)**  
- entity["organization","World Gold Council","gold industry body"] research on gold as a strategic asset and on March 2020 liquidation dynamics. citeturn26view2turn26view3turn26view0  
- entity["organization","The Silver Institute","silver industry association"] press releases and survey reports documenting ratio extremes, ETP flows/holdings, and industrial demand drivers. citeturn30view1turn30view3turn29view0turn33view0turn36view0  
- entity["company","Cboe Global Markets","options exchange operator"] methodology for volatility indices and definition of VIX as an implied-volatility measure. citeturn25view3turn22search0  
- entity["organization","Financial Stability Board","global financial regulator forum"] report on commodity-market vulnerabilities, margin calls, and liquidity stress propagation. citeturn28search2  
- entity["organization","Commodity Futures Trading Commission","us derivatives regulator"] commitments of traders reports as a positioning input. citeturn4search14turn4search6  
- entity["organization","London Bullion Market Association","precious metals trade assoc"] documentation of silver benchmark process and OTC market conventions. citeturn12search0turn12search2  
- Academic evidence on regime dependence and “gold drives silver”: Baur & Tran (2012) and related literature references. citeturn13view1turn13view2turn19search0  
- Historical microstructure episode documentation of 1979–1980 silver crisis and exchange rule constraints, including **entity["people","Nelson Bunker Hunt","silver market participant"]**, **entity["people","Herbert Hunt","silver market participant"]**, and **entity["people","Lamar Hunt","silver market participant"]**, and the **entity["people","Paul Volcker","fed chair"]** reference in crisis chronology. citeturn16view0turn14view0