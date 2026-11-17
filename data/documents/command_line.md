# GetDP command-line interface

## General syntax

GetDP is a command-line-driven program. It takes one problem-definition file followed by options:

```bash
getdp FILENAME OPTIONS
```

`FILENAME` is the ASCII `.pro` file containing the problem definition. The file can include other files, but only one main problem file is supplied on the command line.

The base name of the problem file is used for intermediate files generated during pre-processing, resolution and processing.

## Main execution stages

The command-line workflow is built around three main stages.

### Pre-processing: `-pre`

```bash
getdp model.pro -pre ResolutionName
```

Pre-processing prepares the selected resolution. It creates the geometric database from the mesh, identifies degrees of freedom and sets up constraints. The stage generates a `.pre` file.

### Processing: `-cal`

```bash
getdp model.pro -pre ResolutionName -cal
```

Processing executes the operations defined in the selected `Resolution`, such as matrix assembly and system solution. It requires pre-processing to have been performed previously or as part of the same command.

### Post-processing: `-pos`

```bash
getdp model.pro -pos PostOperationName
```

This executes one or more selected `PostOperation` objects. Processing must already have been performed, or be included in the same command invocation.

### Combined solve

The `-solve` option combines pre-processing and processing for a selected resolution:

```bash
getdp model.pro -solve ResolutionName
```

A post-operation can then be run separately:

```bash
getdp model.pro -pos PostOperationName
```

## Other useful options

| Option | Meaning |
|---|---|
| `-msh FILE` | Read a mesh from the specified `.msh` file instead of the default mesh name. |
| `-msh_scaling VALUE` | Multiply all mesh-node coordinates by a value. |
| `-split` | Save processing results in separate files, one per time step. |
| `-res FILE...` | Load processing results from files. |
| `-name STRING` | Set the default generic base name for mesh, pre-processing and processing files. |
| `-restart` | Restart an interrupted time-stepping resolution. |
| `-solver FILE` | Specify a solver option file; its format depends on the enabled linear-algebra toolkit. |
| `-slepc` | Use SLEPc instead of ARPACK as eigensolver. |
| `-order VALUE` | Set the maximum interpolation order. |
| `-bin` | Select binary output format. |
| `-check` | Check the problem structure interactively. |
| `-v` / `-verbose INTEGER` | Set the verbosity level; zero suppresses processing messages. |
| `-cpu` | Report CPU times for operations. |
| `-info` | Display version information. |
| `-version` | Display the version number. |
| `-help` | Display basic usage and available options. |

The manual documents additional options, including Gmsh data reading, progress reporting, ONELAB communication and setting constants from the command line.

## Example: generate a mesh and solve a tutorial

The electrostatic microstrip tutorial uses Gmsh to generate a 2D mesh, then GetDP to solve the problem and export a post-processing result:

```bash
gmsh microstrip.geo -2
getdp microstrip.pro -solve Ele -pos Map
```

Here `Ele` identifies the resolution and `Map` identifies the post-operation in the tutorial.

## Source and version

Based on the GetDP Reference Manual 4.0.0 (November 16, 2026):

- https://getdp.info/doc/texinfo/getdp.txt
