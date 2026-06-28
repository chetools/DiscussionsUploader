# Choked Flow: A Complete Derivation from First Principles

---

## Part 1: What Is the Speed of Sound?

### The Physical Picture

Sound is a **pressure disturbance** that propagates through a medium. When you create a small compression somewhere in a gas, that compressed region pushes on the gas next to it, compressing that region, which pushes on the next, and so on. The disturbance travels — but the gas molecules themselves only jiggle locally.

The key intuition: **the speed of sound is the speed at which a small pressure disturbance travels through the fluid.** This matters enormously for choked flow, because pressure changes downstream can only communicate upstream by traveling at this speed.

### Setting Up the Problem — The Moving Wave Frame

Consider a weak pressure pulse (a sound wave) moving through a tube at speed $c$ into still gas. Jumping into the reference frame moving with the wave, the wave is stationary and the gas flows through it:

- Gas approaches from the right at speed $c$, with properties $\rho$, $p$, $T$
- Gas leaves on the left slightly altered: velocity $c - dv$, pressure $p + dp$, density $\rho + d\rho$

### Conservation of Mass (Continuity)

Mass flow in must equal mass flow out:

$$\rho \, A \, c = (\rho + d\rho) \, A \, (c - dv)$$

Expanding the right side and dropping the second-order term $d\rho \, dv$:

$$\boxed{\rho \, dv = c \, d\rho} \tag{1}$$

### Conservation of Momentum

The net pressure force per unit area equals the rate of change of momentum flux:

$$p - (p + dp) = \rho c \left[(c - dv) - c\right]$$

$$\boxed{dp = \rho c \, dv} \tag{2}$$

### The Speed of Sound Emerges

Substituting equation (1) into equation (2) — replacing $dv = c \, d\rho / \rho$:

$$dp = \rho c \cdot \frac{c \, d\rho}{\rho} = c^2 \, d\rho$$

$$\boxed{c^2 = \frac{dp}{d\rho}} \tag{3}$$

The speed of sound squared is the rate of change of pressure with respect to density. A **stiffer**, less compressible gas — where pressure responds sharply to compression — carries sound faster. A highly compressible gas carries it slower.

---

## Part 2: Why the Ratio of Heat Capacities Appears

### Isothermal vs. Adiabatic — Newton's Famous Error

The key question is what thermodynamic process the gas undergoes as the sound wave compresses it.

**Newton** assumed **isothermal** compression (constant temperature), giving $p/\rho = RT = \text{const}$, so $dp/d\rho = RT$. His prediction was consistently ~18% too low compared to experiment.

**Laplace** corrected this: sound waves oscillate so rapidly that there is **no time for heat to flow** between compressed (warmer) and rarefied (cooler) regions. The process is **adiabatic** — and because it is also reversible, it is **isentropic** (constant entropy). The temperature actually rises during compression, making the pressure response stiffer, which is exactly why sound travels faster than Newton predicted.

### Deriving the Isentropic Relation $p = K\rho^\gamma$

Starting from the first law of thermodynamics for unit mass, with $dq = 0$ (adiabatic):

$$0 = C_v \, dT + p \, dv_s \tag{4}$$

where $v_s = 1/\rho$ is specific volume. Differentiating the ideal gas law $p v_s = RT$:

$$p \, dv_s + v_s \, dp = R \, dT \tag{5}$$

Substituting (5) into (4) to eliminate $dT$:

$$0 = C_v (p \, dv_s + v_s \, dp) + R \, p \, dv_s$$

Applying Mayer's relation $C_p - C_v = R$, so $C_v + R = C_p$:

$$0 = C_p \, p \, dv_s + C_v \, v_s \, dp$$

Dividing through by $C_v \, p \, v_s$ and introducing $\gamma = C_p / C_v$:

$$\frac{dp}{p} + \gamma \frac{dv_s}{v_s} = 0 \tag{6}$$

Integrating:

$$p \, v_s^{\gamma} = \text{const}$$

Since $v_s = 1/\rho$:

$$\boxed{p \, \rho^{-\gamma} = \text{const} \quad \Longleftrightarrow \quad p = K\rho^{\gamma}} \tag{7}$$

### Completing the Speed of Sound

Differentiating $p = K\rho^\gamma$ with respect to $\rho$:

$$\frac{dp}{d\rho} = K \gamma \rho^{\gamma - 1} = \gamma \cdot \frac{p}{\rho}$$

Substituting into equation (3) and using the ideal gas law $p/\rho = RT$:

$$\boxed{c = \sqrt{\frac{\gamma p}{\rho}} = \sqrt{\gamma R T}} \tag{8}$$

The ratio $\gamma = C_p/C_v$ is not a bookkeeping constant — it encodes the physical fact that sound propagation is adiabatic. It is the entire reason Laplace's result is faster than Newton's by a factor of $\sqrt{\gamma}$. For air at $T = 293$ K: $c \approx 343$ m/s.

---

## Part 3: The Mach Number and Compressible Flow

### Definition

$$\boxed{M = \frac{v}{c}} \tag{9}$$

The Mach number compares the local flow speed to the local speed of sound.

- $M < 1$: **subsonic**
- $M = 1$: **sonic**
- $M > 1$: **supersonic**

### Why It Governs Everything

Pressure information travels at the speed of sound. If $M < 1$, pressure signals can travel upstream (against the flow) because sound is faster than the flow. If $M \geq 1$, **pressure signals cannot travel upstream** — the flow outruns them entirely. This single fact is the physical origin of choking, and will come into focus in Part 5.

---

## Part 4: Flow Through a Varying-Area Duct

### Governing Equations

For steady, adiabatic, frictionless (isentropic) flow in a duct whose cross-sectional area $A$ varies slowly, three equations govern the flow.

**Continuity** — mass flow $\dot{m} = \rho A v$ is constant. Taking the logarithm and differentiating:

$$\frac{d\rho}{\rho} + \frac{dA}{A} + \frac{dv}{v} = 0 \tag{10}$$

**Euler's equation** (frictionless momentum balance):

$$dp + \rho v \, dv = 0 \tag{11}$$

**Isentropic sound-speed relation:**

$$dp = c^2 \, d\rho \tag{12}$$

### Deriving the Area–Velocity Relation

From (12) and (11): $d\rho = -\rho v \, dv / c^2$, so:

$$\frac{d\rho}{\rho} = -\frac{v^2}{c^2} \cdot \frac{dv}{v} = -M^2 \frac{dv}{v}$$

Substituting into (10):

$$-M^2 \frac{dv}{v} + \frac{dA}{A} + \frac{dv}{v} = 0$$

$$\boxed{\frac{dA}{A} = (M^2 - 1)\frac{dv}{v}} \tag{13}$$

### Reading the Physics

The sign of $(M^2 - 1)$ controls everything:

**Subsonic ($M < 1$):** $(M^2 - 1) < 0$, so $dA$ and $dv$ have *opposite* signs. To accelerate the gas ($dv > 0$) you need $dA < 0$ — a **converging** duct. This is the familiar garden-hose nozzle intuition: squeeze it and the water speeds up.

**Supersonic ($M > 1$):** $(M^2 - 1) > 0$, so $dA$ and $dv$ have the *same* sign. To accelerate the gas you need $dA > 0$ — a **diverging** duct. This is counterintuitive but arises because in supersonic flow, the density drops so rapidly that the area must *widen* to accommodate the thinning gas and still conserve mass.

**Sonic ($M = 1$):** $(M^2 - 1) = 0$, so $dA = 0$. The area must be at a **minimum** — a **throat**. Sonic conditions can only occur at the narrowest point of the duct.

This structural result has a critical consequence: to accelerate a gas from subsonic to supersonic, you need a converging section (to reach $M = 1$ at the throat) followed by a diverging section (to continue accelerating to $M > 1$). This is the **converging–diverging (de Laval) nozzle**.

---

## Part 5: Isentropic Stagnation Relations

### Stagnation Conditions

Stagnation (or total) conditions — denoted with subscript 0 — are the conditions the gas would reach if brought to rest adiabatically. In a large upstream reservoir, the gas is essentially at rest and its conditions are the stagnation conditions $p_0$, $T_0$, $\rho_0$.

### Temperature Relation

From conservation of energy (constant stagnation enthalpy), $h_0 = h + v^2/2$. For an ideal gas $h = C_p T$:

$$C_p T_0 = C_p T + \frac{v^2}{2}$$

Converting the velocity to a Mach number using $v^2 = M^2 c^2 = M^2 \gamma R T$ and $C_p = \gamma R / (\gamma - 1)$:

$$\boxed{\frac{T_0}{T} = 1 + \frac{\gamma - 1}{2} M^2} \tag{14}$$

Since the right-hand side is always $\geq 1$, stagnation temperature is always **greater than or equal to** static temperature. Bringing the gas to rest converts kinetic energy to thermal energy — it warms up to $T_0$, not cools.

### Pressure and Density Relations

Using the isentropic relations $p_0/p = (T_0/T)^{\gamma/(\gamma-1)}$ and $\rho_0/\rho = (T_0/T)^{1/(\gamma-1)}$:

$$\boxed{\frac{p_0}{p} = \left(1 + \frac{\gamma-1}{2}M^2\right)^{\gamma/(\gamma-1)}} \tag{15}$$

$$\boxed{\frac{\rho_0}{\rho} = \left(1 + \frac{\gamma-1}{2}M^2\right)^{1/(\gamma-1)}} \tag{16}$$

---

## Part 6: Critical Conditions and the Critical Pressure Ratio

### Critical Conditions at $M = 1$

Setting $M = 1$ in the stagnation relations gives the **critical conditions** (denoted $*$) — the values at a sonic throat:

$$\boxed{\frac{T^*}{T_0} = \frac{2}{\gamma + 1}} \tag{17}$$

$$\boxed{\frac{p^*}{p_0} = \left(\frac{2}{\gamma + 1}\right)^{\gamma/(\gamma-1)}} \tag{18}$$

$$\boxed{\frac{\rho^*}{\rho_0} = \left(\frac{2}{\gamma+1}\right)^{1/(\gamma-1)}} \tag{19}$$

### Numerical Values for Air ($\gamma = 1.4$)

$$\frac{T^*}{T_0} = \frac{2}{2.4} = 0.833$$

$$\frac{p^*}{p_0} = (0.833)^{3.5} \approx 0.528$$

$$\frac{\rho^*}{\rho_0} = (0.833)^{2.5} \approx 0.634$$

The critical temperature ratio of 0.833 means the gas at a sonic throat is **colder** than the reservoir — not hotter. As the gas accelerates through the converging nozzle, it expands and converts thermal energy into kinetic energy, so the static temperature falls. (The common misconception is that squeezing gas through a throat heats it; in reality the dominant effect is expansion and acceleration, not compression.)

The critical pressure ratio of **0.528** is the key number for engineering calculations: it tells you the minimum ratio $p_b/p_0$ at which the flow is not yet choked. For air, you need the downstream pressure to fall below about 52.8% of the upstream stagnation pressure before the nozzle chokes.

---

## Part 7: The Choking Phenomenon

### Progressively Lowering the Back Pressure

Consider a large reservoir at stagnation conditions $p_0$, $T_0$ exhausting through a converging nozzle into a region at back pressure $p_b$. Lower $p_b$ progressively from $p_0$ and track what happens:

**Stage 1 — $p_b$ slightly below $p_0$:** Flow is subsonic throughout. The throat pressure equals $p_b$ (downstream pressure is "felt" everywhere). As $p_b$ drops, the throat Mach number increases and the mass flow increases. Everything behaves intuitively.

**Stage 2 — $p_b$ reaches $p^* \approx 0.528\, p_0$:** The throat reaches exactly $M = 1$. Mass flow has reached its **maximum possible value**. This is the onset of choking.

**Stage 3 — $p_b$ drops below $p^*$:** The throat is at $M = 1$. Sound travels at speed $c$ upstream, but the gas at the throat moves downstream at exactly $c$. The net upstream propagation speed of any pressure signal is $c - c = 0$. **The throat is deaf to the lower back pressure.** The throat conditions — pressure, temperature, density, Mach number — stay locked at the critical values. Mass flow stays fixed at its maximum.

The gas exits the nozzle still at pressure $p^* > p_b$ and does the remainder of its expansion outside the nozzle, typically through oblique shock and expansion wave structures.

### In One Sentence

> Once the gas at the throat moves as fast as the pressure signals that would tell it to flow faster, it can no longer hear the downstream suction — and the flow rate freezes.

---

## Part 8: The Maximum (Choked) Mass Flow Rate

### Derivation

The mass flow at the throat is $\dot{m} = \rho^* A^* v^*$, where $v^* = c^* = \sqrt{\gamma R T^*}$ at $M = 1$.

From the critical relations:

$$v^* = \sqrt{\gamma R T_0 \cdot \frac{2}{\gamma + 1}} \tag{20}$$

$$\rho^* = \rho_0 \left(\frac{2}{\gamma+1}\right)^{1/(\gamma-1)} = \frac{p_0}{R T_0}\left(\frac{2}{\gamma+1}\right)^{1/(\gamma-1)} \tag{21}$$

Multiplying $\rho^* \cdot v^* \cdot A^*$ and collecting terms:

$$\boxed{\dot{m}_{\max} = A^* \, p_0 \sqrt{\frac{\gamma}{R T_0}\left(\frac{2}{\gamma+1}\right)^{(\gamma+1)/(\gamma-1)}}} \tag{22}$$

### Reading the Physics from Equation (22)

**$\dot{m}_{\max} \propto p_0$:** Mass flow scales linearly with upstream stagnation pressure. To push more gas through a choked restriction — a relief valve, a control orifice, a nozzle — you raise the upstream pressure. This is the correct and only effective lever once chocked.

**$\dot{m}_{\max} \propto A^*$:** Flow scales with throat area, as expected.

**$\dot{m}_{\max} \propto 1/\sqrt{T_0}$:** The $T_0$ is in the denominator. A **hotter** upstream reservoir gives a **lower** choked mass flow rate, despite the molecules moving faster. The dominant effect is density: $\rho_0 = p_0 / (RT_0)$ falls with rising temperature, and the density loss outweighs the velocity gain.

**No $p_b$ term anywhere:** Equation (22) is completely independent of back pressure — the mathematical signature of choking. Once choked, nothing downstream matters.

### The Discharge Coefficient in Practice

Equation (22) assumes a perfectly isentropic, one-dimensional flow with no losses. Real nozzles and orifices are characterized by a **discharge coefficient** $C_d$ (typically 0.6–0.9 for sharp-edged orifices, 0.95–0.99 for well-designed nozzles):

$$\dot{m}_{\text{actual}} = C_d \cdot \dot{m}_{\max} \tag{23}$$

---

## Part 9: The Converging–Diverging (de Laval) Nozzle

A purely converging nozzle can accelerate gas to at most $M = 1$ at its exit. To achieve **supersonic** flow, the area–velocity relation (13) requires:

1. A **converging** section to accelerate subsonic flow from the reservoir to $M = 1$ at the throat
2. A **diverging** section in which the now-supersonic flow continues to accelerate (since $(M^2-1) > 0$, widening accelerates the gas)

In the diverging section, both static temperature and static pressure continue to fall as the gas accelerates. The flow remains isentropic provided no shocks form.

For a given reservoir condition and throat area, the choked mass flow from equation (22) still applies — $A^*$ is the throat area regardless of what the diverging section does downstream of it.

---

## Part 10: Engineering Significance

### Relief Valves and Rupture Disks

When a pressure vessel relieves, gas almost always exits choked. Equation (22) sets the **maximum discharge rate**. Because $\dot{m}_{\max}$ depends only on upstream stagnation conditions and throat area, the sizing calculation is tractable and conservative — you do not need to know the downstream pipe pressure.

A critical safety point: once choked, **you cannot reduce an accidental release rate by doing anything downstream**. The only levers are upstream pressure and the size of the opening. This is a fundamental constraint in process hazard analysis.

### Control Valves and Restriction Orifices

A choked control valve delivers constant mass flow regardless of downstream pressure fluctuations — sometimes useful for flow regulation, sometimes a problem if the valve needs to modulate below the critical pressure ratio.

### Gas Pipeline Blowdown and Flare Systems

Flare header sizing and blowdown calculations depend on choked-flow rates through pipe restrictions. The independence from downstream pressure means the worst-case discharge (highest flow) occurs at or near the onset of choking and does not decrease as the downstream system fills.

---

## Summary: The Complete Logical Chain

| Step | Result | Equation |
|:---:|---|:---:|
| 1 | Mass + momentum conservation across a sound wave | $c^2 = dp/d\rho$ |
| 2 | Sound propagation is adiabatic → isentropic relation | $p = K\rho^\gamma$ |
| 3 | Speed of sound with heat-capacity ratio | $c = \sqrt{\gamma R T}$ |
| 4 | Mach number definition | $M = v/c$ |
| 5 | Varying-area duct analysis | $dA/A = (M^2-1)\,dv/v$ |
| 6 | $M=1$ requires $dA=0$ → sonic only at throat | — |
| 7 | Stagnation relations | Equations (14)–(16) |
| 8 | Critical ratio at $M=1$ | $p^*/p_0 \approx 0.528$ for air |
| 9 | Downstream pressure cannot propagate upstream through sonic throat | Choking mechanism |
| 10 | Maximum mass flow | $\dot{m}_{\max} = A^* p_0 \sqrt{\tfrac{\gamma}{RT_0}\left(\tfrac{2}{\gamma+1}\right)^{(\gamma+1)/(\gamma-1)}}$ |

The entire derivation rests on one elegant physical idea: **a flow chokes when it moves as fast as the information that would tell it to change.**
