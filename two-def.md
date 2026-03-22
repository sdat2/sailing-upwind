# Two-Deflector Model

The [base model](README.md) makes a sharp asymmetry: the sail is treated as a
momentum deflector acting on a column of air, while the centreboard is given
infinite lateral resistance — leeway is forbidden by assumption.
That is equivalent to giving the water-foil infinite area.

This note removes that assumption.
The centreboard is modelled as a finite **lifting surface** whose side-force
grows with leeway angle, introducing leeway $\alpha$ as a second equilibrium
variable alongside boat speed $v$.

---

## Coordinate frame

| symbol | meaning |
|--------|---------|
| $x'$ | along the boat's heading (positive = forward) |
| $y'$ | across the boat (positive = to leeward) |
| $\theta$ | heading angle from true wind |
| $\alpha$ | leeway angle (drift to leeward, $\alpha > 0$) |

The boat's actual track over water is $\theta + \alpha$ from the wind.

---

## Forces

### Sail (momentum deflector — unchanged)

The sail presents area $a_s |\sin\theta|$ to the wind. Decomposing the full
2-D momentum-flux change gives both components:

$$F_{\text{sail},x'} = \rho_a \, a_s \, v_s^2 \, |\sin\theta|(D_s - \cos\theta)$$

$$F_{\text{sail},y'} = \rho_a \, a_s \, v_s^2 \, \sin^2\theta \qquad \text{(leeward push)}$$

The $y'$ component is what the base model discards by assuming infinite
lateral resistance.

### Centreboard (lifting surface)

Applying the pure deflector equation to the centreboard fails: it predicts
no side-force until the leeway exceeds $\arccos(D_c) \approx 12°$, far more
than real boats experience. A centreboard is an efficient low-drag foil that
generates lift linearly with angle of attack — thin-flat-plate theory gives:

$$C_L = 2\pi\sin\alpha \approx 2\pi\alpha, \qquad C_D = \frac{C_L^2}{\pi \cdot \mathrm{AR}}$$

where $\mathrm{AR} = \text{span}^2 / A_c$ is the aspect ratio ($\mathrm{AR} \approx 6$ for a dinghy centreboard).
The dynamic pressure of the sideways water flow is $\tfrac{1}{2}\rho_w A_c v^2$, giving:

$$F_{\text{cb},y'} = \tfrac{1}{2}\rho_w A_c \cdot 2\pi\sin\alpha \cdot v^2 \qquad \text{(windward restoring force)}$$

$$F_{\text{cb},x'} = -\tfrac{1}{2}\rho_w A_c \cdot \frac{(2\pi\sin\alpha)^2}{\pi \cdot \mathrm{AR}} \cdot v^2 \qquad \text{(induced drag)}$$

### Hull drag (unchanged)

$$F_{\text{hull}} = -(1-D_h)\,\rho_w\,A_h\,v^2$$

---

## Equilibrium

Setting net forward and lateral forces to zero:

$$\underbrace{\rho_a a_s v_s^2 \sin\theta(D_s-\cos\theta)}_{\text{sail drive}} - \underbrace{\frac{2\pi^2 \rho_w A_c \sin^2\!\alpha}{\mathrm{AR}}\,v^2}_{\text{CB induced drag}} = \underbrace{(1-D_h)\rho_w A_h v^2}_{\text{hull drag}} \tag{1}$$

$$\underbrace{\rho_a a_s v_s^2 \sin^2\!\theta}_{\text{sail side-force}} = \underbrace{\pi \rho_w A_c \sin\alpha \cdot v^2}_{\text{CB lift}} \tag{2}$$

Two equations in two unknowns $(v, \alpha)$ — solved numerically for each
heading $\theta$.

---

## Results for the Laser Pico

Centreboard: $A_c = 0.125\ \text{m}^2$, $\mathrm{AR} = 6$.

| $\theta$ (°) | $v$ (m/s) | $\alpha$ (°) | $u = v\cos(\theta+\alpha)$ (m/s) |
|:---:|:---:|:---:|:---:|
| 33 | 0.76 | 7.7 | 0.57 |
| 45 | 1.92 | 2.0 | 1.31 |
| 56 | 2.85 | 1.2 | 1.53 |
| 62 | 3.29 | 1.0 | 1.49 |
| 73 | 4.12 | 0.8 | 1.11 |

**Optimal heading: $\theta_\text{opt} = 57.0°$, leeway $\alpha = 1.2°$,
effective track $58.2°$ from wind.**

True upwind speed: **1.53 m/s** (2.97 knots).

Compared with the one-deflector model ($\theta_\text{opt} = 56.8°$,
$u_\text{max} = 1.59$ m/s), the optimal heading is virtually unchanged — confirming that the base model's closed-form cubic gives the right answer to good
accuracy. The upwind speed is slightly *lower* because centreboard induced drag
adds a small forward-resistance penalty.

### Sensitivity to centreboard size

| $A_c$ (m²) | $\theta_\text{opt}$ (°) | Leeway (°) | $u_\text{max}$ (m/s) |
|:---:|:---:|:---:|:---:|
| 0.05 | 57.3 | 3.1 | 1.43 |
| 0.10 | 57.1 | 1.5 | 1.51 |
| 0.125 | 57.0 | 1.2 | 1.53 |
| 0.20 | 57.0 | 0.8 | 1.55 |
| 0.30 | 57.0 | 0.5 | 1.57 |
| 1.00 | 56.8 | 0.2 | 1.59 |

As $A_c \to \infty$ the leeway $\to 0$ and the result converges to the
one-deflector model, as expected.
Smaller centreboard → more leeway → more induced drag → lower upwind speed and
a very slightly wider optimal heading, consistent with the intuition that a
boat with a poor centreboard should bear away slightly.

---

## What the model still cannot do

* The sail side-force ($F_{\text{sail},y'}$) in this derivation assumes air
  exits *axially* — a rough approximation that over-states the leeward push
  at very large $\theta$. A full 2-D deflector would require tracking the
  exit direction of the air.
* Hull side-drag (the water resistance opposing leeway from the hull itself,
  not just the centreboard) is ignored.
* Heel angle and its effect on effective sail area and underwater body are
  ignored.
* The thin-plate $C_L = 2\pi\alpha$ formula holds only for small $\alpha$ and
  attached flow — reasonable for $\alpha < 5°$ but the model should not be
  trusted at larger leeway.

---

## Code

The model lives in
[`sailing_upwind/two_deflector.py`](sailing_upwind/two_deflector.py).

```python
from sailing_upwind.two_deflector import TwoDeflectorParams, optimal_angle

p = TwoDeflectorParams(
    v_s=4.0,      # wind speed m/s
    a_s=5.1,      # sail area m^2
    rho_a=1.225,
    D_s=0.895,    # sail drag coefficient
    A_c=0.125,    # centreboard area m^2
    AR_c=6.0,     # centreboard aspect ratio
    D_h=0.9,      # hull drag coefficient
    rho_w=1000.0,
    A_h=0.0343,   # hull frontal area m^2
)

theta_opt, v_opt, alpha_opt = optimal_angle(p)
```
