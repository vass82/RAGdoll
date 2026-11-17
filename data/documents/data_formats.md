# GetDP input and output files

This document summarizes the file formats described by the GetDP reference manual. It distinguishes the user-authored problem definition, mesh input, internal processing files and exported result formats.

## Problem definition: `.pro`

A GetDP problem is described in an ASCII text file, conventionally using the `.pro` extension.

The file contains the objects that define the problem, such as groups, functions, constraints, function spaces, formulations, resolutions and post-processing operations. A `.pro` file can include other files, so a model can be split into reusable pieces while the command line still names a single main problem file.

Example command shape:

```bash
getdp model.pro -solve ResolutionName
```

The input file's base name is used when creating intermediate files.

## Mesh input: `.msh`

GetDP expects input meshes in the native Gmsh mesh file format. By default, GetDP looks for a mesh whose base name matches the problem file, with the `.msh` extension.

The mesh can be overridden on the command line:

```bash
getdp model.pro -msh other_mesh.msh -solve ResolutionName
```

The `-msh_scaling VALUE` option multiplies all mesh-node coordinates by the specified value.

Gmsh is also used in the tutorials to construct geometry and generate meshes.

## Internal pre-processing file: `.pre`

The `.pre` file is generated during pre-processing. It stores information needed by the processing stage for a selected resolution, including degrees of freedom, unknowns, fixed values and initial values.

The manual describes it as an internal format. It is not normally a user-authored input file.

## Internal result file: `.res`

The `.res` file is generated during processing. It stores the computed solution, or a portion of it if the program was interrupted.

The file contains solution records associated with degree-of-freedom data and time-step information. The manual describes the `.res` structure as an internal format.

The `-res` command-line option can load processing results from one or more files.

## Exported post-processing data

GetDP can export computed fields using Gmsh post-processing formats. The manual mentions both list-based and model-based Gmsh post-processing formats.

Other output formats can be selected in post-processing operations. Examples include:

- `Table`
- `NodeTable`
- `RegionTable`
- Other formats supported by the relevant `PostOperation` options.

Table-oriented output can be useful when importing numerical results into tools such as Python or MATLAB.

The output format is selected as part of the post-operation definition in the `.pro` file; it is not simply determined by the `.res` file format.

## File-format summary

| Extension / format | Role | Usually created by |
|---|---|---|
| `.pro` | Textual problem definition | User |
| `.msh` | Mesh input in Gmsh format | Gmsh or another compatible mesh source |
| `.pre` | Internal pre-processing data | GetDP |
| `.res` | Internal computed solution data | GetDP |
| Gmsh post-processing formats | Visualization-oriented result export | GetDP post-processing |
| `Table`, `NodeTable`, etc. | Tabular result export | GetDP post-processing |

## Source and version

Based on the GetDP Reference Manual 4.0.0 (November 16, 2026):

- https://getdp.info/doc/texinfo/getdp.txt
- Gmsh: https://gmsh.info/
