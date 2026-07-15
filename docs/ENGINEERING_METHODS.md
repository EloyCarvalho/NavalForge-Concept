# Engineering methods and limits

## Units and coordinates

- SI units are mandatory in the core.
- Longitudinal coordinate `x`: transom to bow.
- Transverse coordinate `y`: centreline positive to starboard in engineering data.
- Vertical coordinate `z`: baseline upward in engineering data.
- Three.js payload: `X=longitudinal`, `Y=vertical upward`, `Z=transverse`.

## Weights and centres

For each active mass point:

\[
LCG=\frac{\sum w_i x_i}{\sum w_i},\quad
TCG=\frac{\sum w_i y_i}{\sum w_i},\quad
VCG=\frac{\sum w_i z_i}{\sum w_i}
\]

Quantity, item margin, source, confidence, revision and status remain explicit.

## Parametric hull and hydrostatics

The level-1 hull is a symmetric V-bottom with deadrise, chine, flare, bow rise
and longitudinal beam distribution. Each transverse section is integrated as
horizontal strips. Section properties are integrated longitudinally with the
trapezoidal rule.

Calculated values include volume, displacement, waterplane, wetted area, LCB,
LCF, KB, BM, KM, coefficients, TPC and MTC.

## Equilibrium

Bounded nonlinear least squares solves mean draft and trim for:

\[
\Delta(T,\theta)=W,\qquad LCB(T,\theta)=LCG
\]

Mass and longitudinal-centre residuals are returned with convergence status.

## Stability and free surface

\[
GM_T=KB+BM_T-KG-FSC
\]

For rectangular tanks, the transverse free-surface inertia is:

\[
I_{FS}=\frac{l b^3}{12}
\]

The GZ curve is a wall-sided preliminary estimate. It must not be used as a
statutory intact-stability curve without verified inclined geometry.

## Resistance and plane

The version uses a transparent Savitsky-inspired prismatic planing screen,
ITTC-1957 friction coefficient, appendage percentage and aerodynamic drag. It
reports Froude number, dynamic trim, wetted dimensions, components, power and
application warnings. It is not presented as a validated full Savitsky solver.

## Power and propulsion

\[
P_E=R_T V
\]

\[
P_{installed}=\frac{P_E}{\eta_p\eta_t}
(1+m_{sea})(1+m_{growth})(1+m_{reserve})
\]

Engine records and prices in this repository are synthetic demonstrations.

## Structure

Preliminary plate screening follows:

\[
t=s\sqrt{\frac{k p}{\sigma_{allow}}}
\]

This does not address complete rule pressure, stiffener section modulus,
buckling, fatigue, welds, HDPE creep or laminate engineering.
