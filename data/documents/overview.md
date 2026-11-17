# GetDP overview

## What GetDP is

GetDP (General environment for the treatment of Discrete Problems) is a finite-element solver for discretizing de Rham complexes in one, two and three dimensions. It uses conforming finite elements, including nodal, edge, face and volume elements.

Although GetDP was originally developed for computational electromagnetics, the reference manual describes it as a general-purpose solver for multiphysics problems. Applications include electromagnetic, thermal, acoustic and mechanical problems, as well as coupled problems and lumped circuit elements.

Supported model dimensions and analysis regimes include:

- 1D, 2D, 2D axisymmetric and 3D formulations.
- Steady-state, transient, time-harmonic and multi-harmonic regimes.
- Eigenvalue problems and coupled physical formulations.

The software is designed around a close relationship between the mathematical formulation of a discrete problem and its textual representation. A problem is described by the user in an ASCII `.pro` file.

## Main concepts

A GetDP problem is assembled from named objects. The main object types are:

| Object | Purpose |
|---|---|
| `Group` | Defines topological entities and regions of the model. |
| `Function` | Defines global or piecewise expressions and physical quantities. |
| `Constraint` | Defines constraints on function spaces and formulations. |
| `FunctionSpace` | Defines the discrete spaces and unknown quantities. |
| `Jacobian` | Defines geometric mappings used in integration. |
| `Integration` | Defines numerical integration methods. |
| `Formulation` | Defines the equations to assemble and solve. |
| `Resolution` | Defines the solution procedure and operations. |
| `PostProcessing` | Defines quantities derived from the computed solution. |
| `PostOperation` | Defines output and export operations. |

The objects have dependencies: for example, a formulation can refer to groups, functions, constraints, function spaces, Jacobians and integration methods. Objects must be defined before other objects refer to them.

A typical model-definition flow is:

1. Define the physical and geometric regions.
2. Define material properties, source terms and other functions.
3. Define constraints and discrete function spaces.
4. Define Jacobian and integration methods.
5. Define the mathematical formulation.
6. Define the resolution procedure.
7. Define post-processing quantities and output operations.

## Typical applications in the reference manual

The tutorials cover examples such as:

- Electrostatic field around a microstrip line.
- Thermal conduction in a radiator with fins.
- Magnetostatic and magneto-quasistatic electromagnet models.
- Full-wave modelling of a rectangular waveguide.
- Global quantities in electrostatics.
- Magneto-thermal modelling of a three-phase busbar.
- Circuit coupling in 2D and 3D.
- A transformer model using a template library.
- Tree-cotree and Coulomb gauging.

These examples illustrate that GetDP is a modelling environment: users define the problem and numerical formulation rather than selecting only from a fixed catalogue of pre-built analyses.

## Related software

GetDP uses the Gmsh mesh format. Gmsh can also provide a graphical front-end for geometry construction, mesh generation, launching computations and visualization of results.

## Source and version

This document is an original summary based on the **GetDP Reference Manual 4.0.0 (November 16, 2026)**.

- Official project: https://getdp.info/
- Reference manual: https://getdp.info/doc/texinfo/getdp.txt
- Issue tracker: https://gitlab.onelab.info/getdp/getdp/issues

The reference manual identifies Patrick Dular and Christophe Geuzaine as its authors and gives copyright as 1997–2026. This file summarizes the manual; it is not a replacement for the full reference.
