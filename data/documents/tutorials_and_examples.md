# GetDP tutorials and example problems

The GetDP reference manual includes a tutorial sequence that introduces different classes of finite-element and multiphysics problems. The tutorials are useful both as runnable examples and as templates for understanding the structure of `.pro` files.

## Tutorial catalogue

| Tutorial | Subject | Main idea |
|---|---|---|
| 1 | Electrostatic field around a microstrip line | 2D electrostatics, scalar potential and Dirichlet constraints. |
| 2 | Thermal conduction in a radiator with fins | Thermal conduction model. |
| 3 | Magnetostatic model of an electromagnet | Magnetostatic finite-element formulation. |
| 3 bonus | Nonlinear magnetostatics | Nonlinear material behaviour and iterative loops. |
| 4 | Magneto-quasistatic electromagnet | Time-dependent or frequency-related electromagnetic modelling. |
| 5 | Full-wave rectangular waveguide | Full-wave electromagnetic formulation. |
| 6 | Global quantities in electrostatics | Floating potentials, charges and capacitance-related quantities. |
| 7 | Magneto-thermal three-phase busbar | Coupled electromagnetic and thermal modelling. |
| 8 | Circuit coupling in 2D and 3D | Coupling field formulations with circuit quantities. |
| 9 | Transformer using a template library | Reuse of a generic formulation and template library. |
| 10 | Tree-cotree and Coulomb gauging | Gauge treatment in electromagnetic formulations. |

## Example: electrostatic microstrip

The first tutorial models a 2D electrostatic microstrip line. It uses symmetry to model half of the geometry. A voltage is imposed on the microstrip, which is located above a dielectric substrate whose lower side is grounded.

The tutorial illustrates:

- An electrostatic model using electric scalar potential.
- Physical and abstract regions.
- A scalar function space with Lagrange elements.
- A Dirichlet constraint.

The geometry is described in a Gmsh `.geo` file and the physical problem in a GetDP `.pro` file.

The manual gives this command sequence:

```bash
gmsh microstrip.geo -2
getdp microstrip.pro -solve Ele -pos Map
```

## Example: magnetostatic electromagnet

The magnetostatic tutorial is one of the examples used to introduce magnetic vector-potential formulations. The tutorial files contain the geometry and mesh setup alongside the GetDP problem definition.

The manual also includes a bonus nonlinear magnetostatic example that demonstrates iterative loops in the problem definition.

## Example: coupled and reusable models

Later tutorials demonstrate more involved capabilities:

- Coupling thermal and electromagnetic models.
- Coupling field equations with circuit equations.
- Reusing generic formulations through a template library.
- Supporting multiple analysis regimes from a common model definition.

## Where to find the tutorial files

The reference manual points to tutorial files distributed with the GetDP source repository. The tutorial directory is:

https://gitlab.onelab.info/getdp/getdp/-/tree/master/tutorials

The manual's tutorial pages describe the corresponding `.geo` and `.pro` files and provide commands for running selected examples.

## Source and version

Based on the GetDP Reference Manual 4.0.0 (November 16, 2026):

- https://getdp.info/doc/texinfo/getdp.txt
- https://gitlab.onelab.info/getdp/getdp/-/tree/master/tutorials
