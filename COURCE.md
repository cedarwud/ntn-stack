## LEO Satellite Handover: A4/A5/D2 Events and MR vs Non-MR (Traditional & AI)

Audience: RAN/NTN engineers and researchers
Length: 32 slides (bullet points and tables)

---

### Slide 1 — Title & Goals
- Title: Handover in LEO NTN: A4/A5/D2, Traditional vs AI-enhanced
- Goals:
  - Summarize 3GPP A4/A5/D2 measurement events for HO triggers
  - Compare Measurement Report (MR)-based and Non-MR-based HO (traditional & AI)
  - Map to LEO NTN specifics: moving beams, ephemeris, long RTT, Doppler
  - Provide design checklists and literature pointers

---

### Slide 2 — References Used (Selected)
- 3GPP TS 38.331 RRC (Rel-18+): Events A4, A5, D2; SIB19 movingReferenceLocation
- 3GPP NTN overview: https://www.3gpp.org/technologies/ntn-overview
- ETSI TR 21.918 (Rel-18): NTN mobility and measurement updates
- MDPI (2023): ML-Based HO in NTN — https://www.mdpi.com/2079-9292/12/8/1759
- arXiv (2025): Handover Delay Minimization in NTN — https://arxiv.org/abs/2501.17331
- MDPI (2025): Location-Based HO with Particle Filter & RL — https://www.mdpi.com/2079-9292/14/8/1494
- ResearchGate (2022): Handover Solutions for 5G LEO Satellite Networks

---

### Slide 3 — Outline (5 Topics)
1) 3GPP Measurement Events (A4/A5/D2)
   - A4: trigger & params
   - A5: Th1/Th2 logic
   - D2: moving refs (SIB19)
   - CHO/L3 filter/offsets
2) MR-based Handover (Traditional)
   - Pipeline
   - A4 vs A5 tuning
   - CHO/RA/TA-Doppler
   - KPIs/trade-offs
3) MR-based Handover (AI-Enhanced)
   - Supervised (features/labels)
   - RL (policy/safety)
   - Offline → shadow → online
   - Drift/rollback/fallback
4) Non-MR-based Handover (Traditional)
   - D2 cfg (Th1/Th2/HysLoc)
   - Rules: edge/elev/link-budget
   - Kinematic trajectory
   - MR fallback (uncertainty)
5) Non-MR-based Handover (AI-Enhanced)
   - Trajectory (LSTM/Kalman/PF)
   - Bandit / multi-agent RL
   - Uncertainty gating
   - Mixed A5+D2+CHO (guards)

---

### Slide 4 — Topic 1 Outline: 3GPP Measurement Events
- A4: Neighbor better than threshold (RSRP/RSRQ/RS-SINR)
- A5: Serving below Th1 & neighbor above Th2
- D2: Distance-based using moving references (LEO/ephemeris)
- Parameters: Hys, thresholds, TTT, Ofn/Ocn
- NTN hooks: SIB19 ephemeris, CHO, moving beams

- Event comparison (high level):

| Event | Enter condition (summary) | Leave condition (summary) | Primary inputs | Typical LEO use |
|---|---|---|---|---|
| A4 | Neighbor metric above threshold (with offsets, minus Hys) | Neighbor metric falls below threshold (plus Hys) | RSRP/RSRQ/SINR, Ofn, Ocn, Hys | Quick neighbor upgrade; intra-frequency, overlapping beams |
| A5 | Serving below Th1 AND neighbor above Th2 | Serving recovers OR neighbor falls below Th2 | Mp, Mn, Hys, Th1, Th2, Ofn, Ocn | Stable inter-beam/inter-sat HO |
| D2 | UE far from serving moving ref AND close to candidate moving ref | Serving distance falls OR candidate distance grows | Ml1, Ml2, HysLocation, Th1, Th2, ephemeris | Predictive HO aligned with beam motion |

---

### Slide 5 — Event A4 (Neighbor > Threshold)
- Concept: Trigger when neighbor’s metric exceeds configured threshold
- Variables: Mn, Ofn, Ocn, Hys, Thresh
- Enter: Mn + Ofn + Ocn − Hys > Thresh
- Leave: Mn + Ofn + Ocn + Hys < Thresh
- Notes: Works for CondEvent A4; candidate PSCell/SCG in CHO
- Variables detail table:

| Symbol | Definition | Unit | LEO NTN Tip |
|---|---|---|---|
| Mn | Neighbor cell/beam measurement | dBm (RSRP) / dB (RSRQ,SINR) | Use per-beam filtered RSRP with longer window |
| Ofn | Measurement object (frequency) offset | dB | Correct inter-frequency bias |
| Ocn | Cell/beam-specific offset | dB | Balance asymmetric beam footprints |
| Hys | Event hysteresis | dB | Increase to avoid edge ping-pong (2–4 dB) |
| Thresh | A4 threshold | same as Mn | Start near edge budget − margin |

- Numeric example (RSRP):
  - Given Mn = −95 dBm, Ofn = +2 dB, Ocn = +1 dB, Hys = 3 dB, Thresh = −97 dBm
  - Check enter: −95 + 2 + 1 − 3 = −95 dBm > −97 dBm → A4 ENTERS
  - Check leave: −95 + 2 + 1 + 3 = −89 dBm < −97 dBm? No → stays until drop below −97 dBm with +Hys
- Practical notes:
  - Prefer A4 for quick neighbor upgrades on overlapping beams
  - Add TimeToTrigger (TTT) to damp fast fluctuations under satellite motion


---

### Slide 6 — Event A5 (Serving < Th1, Neighbor > Th2)
- Enter: (Mp + Hys < Th1) AND (Mn + Ofn + Ocn − Hys > Th2)
- Leave: (Mp − Hys > Th1) OR (Mn + Ofn + Ocn + Hys < Th2)
- Use: Inter-beam/inter-satellite HO; fewer false triggers vs A4
- Tune: Hys, Th1, Th2, TTT

- Engineering trade-offs:
  - A5 reduces false positives by coupling serving degradation with neighbor improvement
  - Risk of late HO if Th1 too high or Hys too large; tune jointly with TTT
- Example thresholds & timing:

| Scenario | Th1 (dBm) | Th2 (dBm) | Hys (dB) | TTT (ms) | Rationale |
|---|---:|---:|---:|---:|---|
| Moderate speed, medium RTT | −97 | −95 | 3 | 160 | Stability vs latency balance |
| High speed, long RTT | −95 | −94 | 4 | 240 | Earlier trigger on serving drop |
| Dense beams | −98 | −96 | 2 | 120 | Reduce ping-pong with lower Hys |

- Numeric example:
  - Mp = −101 dBm, Hys = 3 dB, Th1 = −97 → Mp + Hys = −98 < −97 ✓
  - Mn = −95 dBm, Ofn = 2, Ocn = 1, Th2 = −96 → −95 + 2 + 1 − 3 = −95 > −96 ✓
  - A5 ENTERS; Leaving when (Mp − Hys > Th1) OR (Mn + Ofn + Ocn + Hys < Th2)
- Tip: Pair A5 with CHO to pre-arm execution and reduce HO delay

---

### Slide 7A — Event D2 (Distance-Based, NTN)
- Distance to moving reference locations using SIB19 ephemeris + epoch
- Enter: (Ml1 − Hys > Th1) AND (Ml2 + Hys < Th2)
- Leave: (Ml1 + Hys < Th1) OR (Ml2 − Hys > Th2)
- Benefits: Predictive HO aligned with beam geometry; less noisy than RSRP

- Inputs & mapping to TS 38.331/SIB19:

### Slide 7B — Event D2 Inputs & Pseudo-code
- Inputs & mapping to TS 38.331/SIB19:

| Element | Source | Purpose |
|---|---|---|
| movingReferenceLocation | SIB19 (serving cell) | Defines serving moving reference for Ml1 |
| referenceLocation | MeasObjectNR | Defines candidate moving reference for Ml2 |
| epoch time & ephemeris | SIB19/MeasObjectNR | Propagate satellite positions |
| UE position/time | UE GNSS / network | Compute distances to moving references |
| hysteresisLocation | reportConfigNR | Hys for D2 event |
| distanceThreshFromReference1/2 | reportConfigNR | Th1/Th2 for D2 |

- Pseudo-code:
  1) Get sat positions at epoch t from ephemeris
  2) Compute moving reference points for serving and candidate
  3) Ml1 = distance(UE_pos(t), serving_moving_ref(t))
  4) Ml2 = distance(UE_pos(t), candidate_moving_ref(t))
  5) If (Ml1 − Hys > Th1) AND (Ml2 + Hys < Th2) → ENTER; corresponding LEAVE conditions



| Element | Source | Purpose |
|---|---|---|
| movingReferenceLocation | SIB19 (serving cell) | Defines serving moving reference for Ml1 |
| referenceLocation | MeasObjectNR | Defines candidate moving reference for Ml2 |
| epoch time & ephemeris | SIB19/MeasObjectNR | Propagate satellite positions |
- Parameter impacts on KPIs:

| Parameter | Increases | Decreases | Notes |
|---|---|---|---|
| Hys | Stability | Responsiveness | Too high → late HO |
| TTT | Stability | False triggers | Scale with RTT & dynamics |
| Th1 (A5) | HO delay | False positives | Lower for earlier HO |
| Th2 (A5) | Target quality | HO chance | Add load-aware bias |
| Ofn/Ocn | Coverage balance | Bias errors | Calibrate per beam |

- Suggested starting grid (LEO trials): Hys ∈ {2,3,4} dB; TTT ∈ {120,160,240} ms; Th1/Th2 by link budget − margins

| UE position/time | UE GNSS / network | Compute distances to moving references |
| hysteresisLocation | reportConfigNR | Hys for D2 event |
| distanceThreshFromReference1/2 | reportConfigNR | Th1/Th2 for D2 |

- Pseudo-code:
  1) Get sat positions at epoch t from ephemeris
  2) Compute moving reference points for serving and candidate
  3) Ml1 = distance(UE_pos(t), serving_moving_ref(t))
  4) Ml2 = distance(UE_pos(t), candidate_moving_ref(t))

  5) If (Ml1 − Hys > Th1) AND (Ml2 + Hys < Th2) → ENTER; corresponding LEAVE conditions as spec

### Slide 7C — Event D2 Example & Notes
- Numeric example:
  - Th1 = 100 km, Th2 = 60 km, Hys = 5 km; Ml1 = 120 km, Ml2 = 50 km
  - 120 − 5 > 100 ✓ and 50 + 5 < 60 ✓ → D2 ENTERS (pre-emptive HO viable)
- Notes:
  - Use UE position covariance to inflate Hys if GNSS error is large
  - Combine D2 with CHO for on-time execution under high RTT
  - Consider periodic ephemeris refresh cadence



- Numeric example:
  - Th1 = 100 km, Th2 = 60 km, Hys = 5 km; Ml1 = 120 km, Ml2 = 50 km
  - 120 − 5 > 100 ✓ and 50 + 5 < 60 ✓ → D2 ENTERS (pre-emptive HO viable)
- Notes:
- KPI definitions & targets:

| KPI | Definition | Typical Target | Notes |
|---|---|---|---|
| HOP | #HOs / time or distance | Context-dependent | Too high → instability |
| HOF | Failed HOs / total HOs | < 2–5% | Includes T310 expiry, RA fail |
| Ping-pong | HO back within τ | < 5–10% | τ e.g., 30–60 s |
| HOD | Time from trigger→RQ | As low as possible | Reduce with CHO/CFRA |
| Throughput | DL/UL average | Maximize | Avoid HO during bursts |

  - Use UE position covariance to inflate Hys if GPS error is large
  - Combine D2 with CHO for on-time execution under high RTT

---

### Slide 8A — NTN Adaptations for Events
- Long RTT → increase TTT; conservative Hys
- Moving beams → combine D2 with A4/A5; CHO usage
- Technique selection:

| Approach | Data needs | Pros | Cons | Where to use |
|---|---|---|---|---|
| Heuristic (A4/A5 tuning) | Low | Simple, explainable | Limited adaptivity | Baseline, safety fallback |
| Supervised ML | Moderate (labeled) | Data-efficient, fast infer | Labeling cost, drift | Dynamic thresholds/target select |
| RL (SAC/DQN/PPO) | High (sim logs) | Learns timing & strategy | Training complexity | High dynamics, long-horizon control |

- Offsets (Ofn/Ocn) per-beam calibration
- L3 filtering windows extended; GNSS/timing uncertainty considered

- Parameter mapping by regime:

| Regime | Speed | RTT | Suggested TTT | Suggested Hys | Notes |
|---|---|---|---:|---:|---|
| Low dynamics | Pedestrian | Moderate | 80–160 ms | 2 dB | Standard filtering OK |
| Medium dynamics | Vehicular | High | 160–240 ms | 3 dB | Slightly earlier A5 Th1 |
- Feature dictionary (examples):

| Feature | Type | Description |
|---|---|---|
| RSRP_s, RSRP_n[k] | Numeric | Serving/neighbor beam levels |
| RSRQ_s, SINR_s | Numeric | Serving quality metrics |
| dRSRP/dt | Numeric | Trend (slope) to anticipate edges |
| UE_speed, heading | Numeric | From GNSS/IMU |
| Elevation_s, Elevation_n[k] | Numeric | Geometry cues |
| BeamID_s, BeamID_n[k] | Categorical | Encoded target IDs |
| Load_target | Numeric | Target load estimate |
| TimeToEdge_pred | Numeric | From D2/trajectory models |

| High dynamics | Aeronautical/Maritime | High | 240–320 ms | 3–4 dB | Prefer A5+D2 mixed policy |
- Execution timeline example (NTN):

| Phase | Typical duration | Key risks | Mitigations |
|---|---:|---|---|
| High dynamics | Aeronautical/Maritime | High | 240–320 ms | 3–4 dB | Prefer A5+D2 mixed policy |

### Slide 8B — NTN Techniques & Feature Set
- Technique selection:

| Approach | Data needs | Pros | Cons | Where to use |
|---|---|---|---|---|
| Heuristic (A4/A5 tuning) | Low | Simple, explainable | Limited adaptivity | Baseline, safety fallback |
| Supervised ML | Moderate (labeled) | Data-efficient, fast infer | Labeling cost, drift | Dynamic thresholds/target select |
| RL (SAC/DQN/PPO) | High (sim logs) | Learns timing & strategy | Training complexity | High dynamics, long-horizon control |

- Feature dictionary (examples):

| Feature | Type | Description |
|---|---|---|
| RSRP_s, RSRP_n[k] | Numeric | Serving/neighbor beam levels |
| RSRQ_s, SINR_s | Numeric | Serving quality metrics |
| dRSRP/dt | Numeric | Trend (slope) to anticipate edges |
| UE_speed, heading | Numeric | From GNSS/IMU |
| Elevation_s, Elevation_n[k] | Numeric | Geometry cues |
| BeamID_s, BeamID_n[k] | Categorical | Encoded target IDs |
| Load_target | Numeric | Target load estimate |
| TimeToEdge_pred | Numeric | From D2/trajectory models |

| Event satisfaction | TTT 120–240 ms | Spurious trigger | Filtering, Hys tuning |
| RRC Reconfig prep | < 50 ms | Missing CHO | Maintain candidate cache |
| RA (CFRA) | 20–100 ms+ RTT | Collisions, timing | CFRA, extended window |
| Path switch | 10–50 ms | Core delay | Pre-allocate, fast UPF rule |
| Bearer resume | 10–30 ms | Packet loss | Duplication buffers |


- Filtering tips:
  - Increase L3 filter window; avoid over-smoothing near beam edges
  - Use per-beam Ofn/Ocn to correct persistent bias

---

### Slide 9 — Topic 2 Outline: MR-based HO (Traditional)
- A4 vs A5 HO count & ping-pong (illustrative):

| Policy | HOs/UE/hour | Ping-pong % | HOF % |
|---|---:|---:|---:|
| A4-only | 14.2 | 12.5 | 4.1 |
| A5 (tuned) | 9.8 | 5.3 | 3.2 |
| A5 + D2 + CHO | 8.5 | 3.8 | 2.6 |

- Note: Values illustrative; tune per network

- HO pipeline: measure→report→decide→execute
- Event selection: A4 vs A5
- Types: inter-beam, inter-sat, inter-frequency
- Execution: CFRA/RA, make-before-break vs break-before-make
- KPIs: HOP, HOF, ping-pong, throughput/latency

---

### Slide 10A — MR-based HO Pipeline
- UE measures: RSRP/RSRQ/SINR per beam/cell
- Config: A4/A5 with Hys, TTT, Ofn/Ocn
- Reports: periodic/aperiodic; reportQuantity
- Decision: neighbor ranking; CHO list
- Execute: RRC Reconf; RA; path switch

- Step-by-step with indicative timing:
  1) Measurement collection (L1/L3 filtering) → continuous
  2) Event evaluation (A4/A5/D2) with TTT → 80–320 ms
  3) Report generation (reportQuantity: RSRP/RSRQ/SINR, add neighbors) → aperiodic/event
  4) gNB decision (rank targets, CHO check, load bias) → < 50 ms
  5) RRC Reconfiguration (HO/CHO) → signaling latency (RTT-aware)
- Traditional execution detail:
  - Pre-config CHO candidates: N strongest beams + 1 reserve inter-sat
  - RA resources: allocate CFRA preambles per beam set
  - Timing advance: preset bounds from geometry; Doppler pre-compensation
  - UL BWP: pre-activate target-compatible numerology
  - Backhaul: ensure target gNB path ready; minimize HOD

  6) RA procedure (CFRA preferred) → RA window enlarged in NTN
  7) Path switch/core update → minimize HOD

### Slide 10B — MR-based HO Reporting & Timeline
- Reporting fields (selected):

| Item | Example values | Purpose |
|---|---|---|
| reportQuantity | rsrp, rsrq, sinr | What metrics to include |
| triggerType | event, periodic | Event-based (A4/A5/D2) vs periodic |
| reportAddNeighMeas | true/false | Include neighbor details in report |
| maxReportCells | e.g., 4–8 | Limit payload size |
| ttt | 80–320 ms | Debounce spurious triggers |

- Execution timeline (NTN):

| Phase | Typical duration | Key risks | Mitigations |
|---|---:|---|---|
| Event satisfaction | TTT 120–240 ms | Spurious trigger | Filtering, Hys |
| RRC prep | < 50 ms | Missing CHO | Candidate cache |
| RA (CFRA) | 20–100 ms+ RTT | Collisions, timing | CFRA, ext. window |
| Path switch | 10–50 ms | Core delay | Pre-allocate, fast UPF rule |
| Bearer resume | 10–30 ms | Packet loss | Duplication buffers |


- Reporting fields (selected):

| Item | Example values | Purpose |
|---|---|---|
| reportQuantity | rsrp, rsrq, sinr | What metrics to include |
| triggerType | event, periodic | Event-based (A4/A5/D2) vs periodic |
| reportAddNeighMeas | true/false | Include neighbor details in report |
| maxReportCells | e.g., 4–8 | Limit payload size |
| ttt | 80–320 ms | Debounce spurious triggers |

- Practical:
  - Maintain CHO list to avoid decision-time delays
  - Apply load-aware bias (+β dB) to reduce HO into congested beams

---
- Measurement stability tips:
  - Use multi-window filtering: short for responsiveness, long for stability
  - Gate HO during critical UL/DL bursts unless risk of outage is high
  - Apply per-beam hysteresis asymmetrically if coverage skewed


### Slide 11 — A4 vs A5 in NTN
- A4 pros: simple, fast; cons: ping-pong at edges
- A5 pros: stable dual-condition; cons: may trigger late
- Practice: A5 for inter-beam; A4 for dense co-beams

---

### Slide 12 — Parameter Tuning (Traditional)
- Hys: 2–4 dB for LEO
- TTT: 80–320 ms (RTT-aware)
- Ofn/Ocn: per-frequency/beam bias
- L3 filtering: a=0.5–0.9; extended windows
- Load-aware Th2 adjustment

---

### Slide 13 — Execution Options in NTN
- CHO: pre-configured candidates + conditions (A4/A5/D2)
- DAPS/make-before-break when feasible
- RA: CFRA with beam sweep; enlarged RA window
- Timing: large TA + Doppler compensation; UL BWP preset
- Core: efficient path switch to reduce HOD

---

### Slide 14 — KPIs and Trade-offs
- Supervised ML configuration example:

| Component | Choice |
|---|---|
| Model | XGBoost (depth 6, 200 trees) |
| Labels | Best target/no-HO from oracle planner |
| Features | Slide 15/16 dictionary |
| Output | ΔTh1, ΔTh2, target rank |
| Inference budget | < 2 ms per UE per eval |
| Update | Nightly with drift check |

- KPIs: HOP, HOF, Ping-pong rate, throughput, latency
- Trade-offs: TTT vs ping-pong; Hys vs late HO; CHO size vs overhead

---

### Slide 15 — Topic 3 Outline: MR-based HO (AI-Enhanced)
- Supervised learning, RL
- Feature set: MR stats, velocity, Doppler, beam IDs, history
- Reward: HOF−, ping-pong−, throughput+, dwell-time+
- RL configuration example (SAC):

| Element | Setting |
|---|---|
| State | [RSRP vector, trends, speed, elevation, TimeToEdge_pred] |
| Action | {HO-now, wait, target-id, ΔTTT, ΔHys} |
| Reward | +throughput +dwell −HOF −ping-pong −delay |
| Training | Offline on digital twin logs + domain randomization |
| Safety | Action clipping; A5/CHO fallback; max HO rate |

- Deployment: online/offline, safety guards, fallback

---

### Slide 16 — Supervised ML for MR-based HO
- Labels: optimal target/HO/no-HO from oracle or simulation
- Models: XGBoost/LightGBM, shallow NN
- Pros: data-efficient; interpretable
- Cons: distribution shift; retraining cadence
- With A5: learn context-aware Th1/Th2 adjustments

---

### Slide 17 — RL for MR-based HO
- State: MR vectors, neighbor ranks, speed, elevation
- Action: HO now / wait / target; adjust TTT/Hys
- Reward: +throughput, +dwell, −HOF, −ping-pong, −delay
- Algorithms: SAC, DQN, PPO; safe RL

---
- Non-AI schedule table (example):

| Rule | Condition | Action |
|---|---|---|
| Beam-edge | TimeToEdge_pred < Δt_edge | Pre-emptive HO to best neighbor |
| Elevation | Elevation_target − Elevation_serving > Δelev | Candidate add to CHO |
| Link budget | RSRP_pred_target − RSRP_pred_serving > δ | Lower Th2 by δ_margin |
| GEO fallback | Ephemeris stale > T_max | Switch to MR-based policy |


### Slide 18 — AI Pipeline & Safeguards
- Offline training with digital twins; domain randomization
- Online: shadow mode; guarded activation
- Guardrails: min TTT, max HO rate, SINR floor; CHO fallback
- Drift detection; rollback triggers; XAI for ops

---

### Slide 19 — Topic 4 Outline: Non-MR-based HO (Traditional)
- Location/ephemeris triggers (D2)
- Scheduled HO on beam footprints
- Kinematic trajectory prediction (non-AI)
- RRC support: SIB19, movingReferenceLocation/referenceLocation
- Fallback to MR when position uncertainty high

- Non-MR AI: trajectory module example
  - LSTM(2×64) + Kalman update → predicts UE trajectory and TimeToEdge
  - Particle filter for beam assignment uncertainty
  - Outputs: dwell time per candidate, uncertainty σ
- Decision layer (bandit):
  - Context: [predicted dwell, load, elevation, uncertainty]
  - Arms: candidate beams
  - Policy: Thompson Sampling with safety constraints

---

### Slide 20 — D2-based HO in Practice
- Inputs: UE GNSS, SIB19 ephemeris, beam geometry
- Configure: Th1/Th2, HysLocation, TTT; CHO candidates
- Execution: pre-emptive HO before beam-edge crossing
- Benefit: lower HOF under rapid beam motion

---

### Slide 21 — Scheduled/Rule-based Non-MR HO
- Beam schedule: HO at footprint boundaries
- Elevation rule: target elevation > serving elevation + Δ
- Link budget rule: predicted RSRP_target − serving > margin
- Pros: predictable, low overhead; Cons: error sensitivity

---

### Slide 22 — Topic 5 Outline: Non-MR-based HO (AI-Enhanced)
- Mixed policy (A5 + D2 + CHO) — detailed logic:

| Step | Condition | Action |
|---|---|---|
| 1 | D2 Enter within Δt_pre | Arm CHO for target(s) |
| 2 | A5 Enter | Execute HO if CHO armed else arm & execute |
| 3 | D2 Leave imminent | Defer HO unless Mp below outage margin |
| 4 | Load high | Add +β to Th2; skip if target overloaded |
| 5 | Guard | Enforce min dwell τ, cap HO rate |

- Trajectory prediction: LSTM/Kalman/Particle filter
- Graph RL / Multi-agent RL over constellation-beam graph
- Contextual bandits for target selection
- Uncertainty-aware decisions with covariance
- Joint scheduling with load/backhaul predictions

---

### Slide 23 — AI for Non-MR HO
- Trajectory & dwell prediction: LSTM + kinematic, particle filter
- Decision: contextual bandit; multi-agent RL coordinates inter-sat HO
- Safety: fallback to A5/CHO if uncertainty > threshold

---

### Slide 24 — Tables: Event-to-Use-Case Mapping
| Event | Metric | Best for | Notes |
|---|---|---|---|
| A4 | RSRP/RSRQ/SINR | Simple neighbor upgrade | Fast; can ping-pong on edges |
| A5 | Serving↓ & Neighbor↑ | Stable inter-beam HO | Reduced false triggers vs A4 |
| D2 | Distance to moving refs | Predictive LEO HO | Needs SIB19, GNSS, geometry |
- Risks & mitigations table:

| Risk | Cause | Mitigation |
|---|---|---|
| Ephemeris error | Outdated SIB19 | Reduce Th2, increase HysLocation, refresh cadence |
| Position error | GNSS noise | Inflate Hys by σ; fall back to MR |
| RA fail | Timing/Doppler | CFRA, extended window, pre-compensation |
| Drift (AI) | Data shift | Shadow mode, monitors, fast rollback |
| Load-induced HOF | Target busy | Load-aware bias; alternate candidate |


---

### Slide 25 — Tables: Parameter Heuristics (Start Points)
| Parameter | Terrestrial | LEO NTN Suggestion |
|---|---|---|
| Hys (dB) | 1–2 | 2–4 |
| TTT (ms) | 40–160 | 80–320 |
| Ofn/Ocn | Small | Per-beam/freq calibration |
| HysLocation | N/A | Tune vs position error σ |

---

### Slide 26 — Design Checklists
- Pre-trial: validate SIB19 ephemeris; UE GNSS accuracy budget
- Config: A5 + D2 + CHO; enable logging (MR, pos, ephemeris, HO)
- Trials: sweep Hys/TTT; monitor HOF/ping-pong
- Post: fit ML baselines; run shadow mode

---

### Slide 27 — Example Mixed Policy (A5 + D2 + CHO)
- If D2 Enter within Δt → pre-emptive HO via CHO
- Else if A5 Enter → execute; defer if D2 Leave imminent
- Guards: min dwell τ; cap HO rate/UE; load-aware +β dB to Th2

---

### Slide 28 — Risks & Mitigations
- Ephemeris/position errors → HysLocation + uncertainty margins
- Beam steering changes → faster CHO refresh cadence
- RA/TA issues → CFRA, extended RA windows
- Model drift → continuous eval and rollback plan

---

### Slide 29 — Implementation Notes (Standards)
- TS 38.331:
  - A4/A5: thresholds, hysteresis, TTT, offsets
  - D2: distance thresholds, hysteresisLocation; SIB19 hooks
  - CHO: conditional events & candidate cells
- Reporting: reportQuantity, reportAddNeighMeas, L3 filtering

---

### Slide 30 — Key Takeaways
- A5 default for inter-beam; complement with D2 for predictiveness
- Tune Hys/TTT for LEO; calibrate offsets per beam
- CHO reduces HOF in moving-beam scenarios
- AI learns context-aware thresholds/timing with guardrails

---

### Slide 31 — Further Reading
- TS 38.331: https://www.etsi.org/deliver/etsi_ts/138300_138399/138331
- ETSI TR 21.918 (NTN): https://www.etsi.org/deliver/etsi_TR/121900_121999/121918
- 3GPP NTN overview: https://www.3gpp.org/technologies/ntn-overview
- MDPI 2023: https://www.mdpi.com/2079-9292/12/8/1759
- MDPI 2025: https://www.mdpi.com/2079-9292/14/8/1494
- arXiv 2025: https://arxiv.org/abs/2501.17331
- ResearchGate 2022: https://www.researchgate.net/publication/363170633

---

### Slide 32 — Appendix: Abbreviations
- CHO: Conditional Handover; CFRA: Contention-Free Random Access
- HOF: Handover Failure; HOD: HO Delay; HOP: HO Probability
- SIB19: System Information Block with ephemeris/moving refs (NTN)
- Ofn/Ocn: Offset (frequency/cell); Hys: Hysteresis; TTT: Time To Trigger

