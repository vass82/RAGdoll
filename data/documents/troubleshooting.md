# GetDP troubleshooting and frequently asked questions

This document summarizes selected questions answered in the GetDP reference manual. It is not an exhaustive troubleshooting guide.

## GetDP cannot find or read my mesh

GetDP expects input meshes in the native Gmsh mesh file format. By default, the mesh file uses the same base name as the `.pro` problem file and the `.msh` extension.

To specify a different mesh explicitly, use:

```bash
getdp model.pro -msh path/to/mesh.msh -solve ResolutionName
```

Check that the mesh exists, is readable and is in a supported Gmsh mesh format.

## How can I visualize computed results?

By default, GetDP outputs fields in Gmsh post-processing formats. The manual mentions list-based and model-based output.

Other formats can be selected in post-processing operations. `Table` and `NodeTable` are examples of tabular formats that can be imported into tools such as Python or MATLAB.

Gmsh can be used to construct geometry, generate meshes, launch computations and visualize results.

## How can I change the linear solver?

The available choices depend on the linear-solver toolkit enabled when GetDP was compiled.

For PETSc-based solvers, options can be supplied through the command line, a solver option file, a `.petscrc` file in the user's home directory, or the `SetGlobalSolverOptions[]` command in a `Resolution` field.

For Sparskit-based solvers, options can be supplied on the command line or through a solver option file. The manual also describes a `solver.par` file in the working directory.

The exact options depend on the selected solver backend.

## How can I report a bug?

The manual asks users to report issues through the GetDP issue tracker:

https://gitlab.onelab.info/getdp/getdp/issues

A useful report should include:

- A precise description of the problem.
- Sample input files that reproduce the issue.
- The GetDP version.
- The operating-system version.

Before reporting, consult the manual's FAQ and issue tracker to see whether the problem is already known.

## Which operating systems are supported?

The reference manual states that GetDP runs on Windows, macOS, Linux and most Unix variants.

## Where can I find more information?

The official project website is:

https://getdp.info

It provides access to the reference manual and project information. The source repository contains the tutorials and build documentation.

## Source and version

Based on the GetDP Reference Manual 4.0.0 (November 16, 2026):

- https://getdp.info/doc/texinfo/getdp.txt
- https://getdp.info/
- https://gitlab.onelab.info/getdp/getdp/issues
