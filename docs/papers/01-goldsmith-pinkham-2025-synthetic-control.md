# Goldsmith-Pinkham & Lyu (2025): Causal Inference in Financial Event Studies

> **MUST READ BEFORE BUILDING EVENT STUDY MODULE**
> PDF: https://arxiv.org/pdf/2511.15123
> HTML: https://arxiv.org/html/2511.15123v1

## Why This Paper Matters to Us

This paper proves that our current event_study.py (Market Model → AR → CAR) produces
**biased estimates** when the factor model is wrong — which it almost always is.
They propose synthetic control as the fix.

---

## 1. Setup: What We're Trying to Measure

**Individual Treatment Effect:**
```
τ_i(s,t) = R_{i,t}(s) - R_{i,t}(∞)
```
- R_{i,t}(s) = return if security i was treated at time s
- R_{i,t}(∞) = counterfactual return (no treatment)
- This is what we want but can't observe directly

**Average Treatment Effect on Treated (ATT):**
```
τ(s,t)^ATT = E[R_{i,t}(s) - R_{i,t}(∞) | T_i = s]
```

**Event-Time ATT (what event studies estimate):**
```
θ_κ^ATT = Σ_{s∈S} w_s · τ^ATT(s, s+κ)
```
- κ = periods after event
- w_s = weight on each event cohort

**Cumulative ATT (our CAR equivalent):**
```
θ_H^CATT = Σ_{κ=0}^H θ_κ^ATT
```

---

## 2. The Standard Approach (What We Currently Do)

**Assumption: Linear Factor Model**
```
E[R_{it}(∞) | T_i = s] = α_s + β_s · F_t
```

**Abnormal Return (our AR):**
```
AR_{it} = R_{it} - (α̂_i + β̂_i · F_t^o)
```
Where F_t^o = observable factors (e.g., market return in CAPM)

**Pre-event estimation:**
```
R_{it} = α_i + β_i · F_t^o + ε_{it},  for t < T_i - δ
```

---

## 3. THE PROBLEM: Bias Decomposition

**AR Estimator Bias (Equation 29):**
```
τ^AR(s,t) - τ^ATT(s,t) = (α_s - α̃_s) + (β_s·F_t - β̃_s·F_t^o) + ε_{st}
```

**In plain English:** The bias has two parts:
1. `(α_s - α̃_s)` — wrong intercept (estimation error)
2. `(β_s·F_t - β̃_s·F_t^o)` — wrong factor structure × factor realization

**Corollary 1:** Bias INCREASES with |F_t| — volatile market periods = MORE bias

**This means:** During COVID, rate hikes, or market crashes, our event study
is MOST biased — exactly when regulation events are most common.

---

## 4. THE FIX: Synthetic Control Estimator

**Definition 5:**
```
τ̂^synth(s,t) = R_{s,t} - Σ_{j∈C} ω̂_j · R_{j,t}
```

**Weight optimization (pre-event matching):**
```
ω̂ = argmin_ω Σ_{t<s-δ} [R_{s,t} - Σ_{j∈C} ω_j · R_{j,t}]²
subject to: ω_j ≥ 0
```

**In plain English:** Instead of using a market model, find a weighted portfolio
of control stocks that perfectly tracks the treated stock before the event.
Then the divergence after = treatment effect.

**Key result (Proposition 1, Part 1):**
```
τ̂^synth(s,t) - τ^ATT(s,t) →^p 0  as n_s, n_c, T_pre → ∞
```
Synthetic control is CONSISTENT even when the factor model is WRONG.

---

## 5. Alternative: GSynth (Interactive Fixed Effects)

**Model:**
```
R_{it}(∞) = α_i + λ_i' · F_t + ε_{it}
```
Where F_t = unobserved factors estimated by PCA

**Steps:**
1. Estimate factors from control units only
2. Cross-validate number of factors r
3. Project treated unit onto estimated factors
4. Counterfactual = α̂_i + λ̂_i' · F̂_t

Also consistent: θ̂^gs - θ^ATT →^p 0

---

## 6. Simulation Results

**Setup:** 500 firms, 239 pre-event days, 1 event day, treatment=3%, rate=10%
```
r_{it} = r_f + β_{mkt}·(r_mkt - r_f) + β_{smb}·r_smb + ε_{it}
β_{mkt}, β_{smb} ~ N(1, 0.3²)
ε_{it} ~ N(0, 0.1²)
```

| Scenario | CAPM Bias | Correct Model | Synthetic Control |
|----------|-----------|---------------|-------------------|
| Random assignment + timing | Small | ~0 | ~0 |
| Selection + random timing | LARGE | Small | ~0 |
| Random assignment + timing selection | LARGE | Small | ~0 |
| Both selection | VERY LARGE | Medium | ~0 |

**Takeaway:** Synthetic control works in ALL scenarios. CAPM fails when
assignment or timing is non-random — which is ALWAYS true for regulations.

---

## 7. Implications for Our Project

1. **Replace Market Model with Synthetic Control** for CAR estimation
2. **Current event_study.py is biased** — especially for:
   - Long event windows ([-5, +5])
   - Events during volatile periods
   - Regulations targeting specific sectors (non-random assignment)
3. **Control portfolio construction** is the key engineering task
4. **Short-horizon ([-1, +1]) with random timing is still okay** — but we can't
   guarantee random timing for regulation events
5. **Buy-and-Hold Abnormal Returns (BHAR)** have additional variance drag bias
   for geometric returns (Lemma 1)

---

## 8. What We Need to Build

```python
# Instead of:
AR = R_treated - (alpha + beta * R_market)  # biased

# Do:
weights = optimize(R_treated_pre == sum(w * R_controls_pre))  # pre-event match
AR = R_treated_post - sum(weights * R_controls_post)          # consistent
```
