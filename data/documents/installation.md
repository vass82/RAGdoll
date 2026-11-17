# Obtaining and installing GetDP

## Where to obtain GetDP

The GetDP reference manual states that source code and pre-compiled binaries are available from the official project website:

- https://getdp.info
- Source releases and snapshots: https://getdp.info/src/

The manual lists Windows, macOS and Linux binary packages. It also notes that GetDP packages are available through various Linux and BSD distributions, including Debian, Fedora and Ubuntu.

The exact package name, available version and optional solver features depend on the distribution and package build. Consult the relevant package repository and the official GetDP website for current instructions.

## Building from source

The reference manual describes a CMake-based build process.

At a high level:

1. Obtain the source code, either from a stable source release or the Git repository.
2. Configure the build with CMake.
3. Select optional modules and solver integrations through CMake options as needed.
4. Build and install the configured targets according to the source tree's README and the GetDP compilation documentation.

The manual gives the following repository as the source-code location:

```bash
git clone https://gitlab.onelab.info/getdp/getdp.git
cd getdp
git pull
```

`git pull` is relevant when updating an existing checkout; it is not required immediately after a fresh clone.

## Build tools and optional dependencies

The manual identifies CMake and a C++ compiler as build requirements. A Fortran compiler may also be required, depending on the selected modules and solvers.

The documented CMake options include optional integrations and capabilities such as:

- ARPACK and SLEPc eigensolvers.
- BLAS/LAPACK.
- PETSc and Sparskit linear solvers.
- Gmsh-related functions.
- GSL functions.
- MPI parallelization through PETSc/SLEPc.
- OpenMP support for some functions (described as experimental).
- Python functions and Python wrappers.
- Octave functions.

These are build-time options, not a statement that every binary package enables every feature. The actual capabilities depend on how GetDP was compiled.

## Verifying an installation

After installing GetDP, invoke the executable with its help or version option:

```bash
getdp -help
getdp -version
```

The command-line interface is described in `command_line.md`.

## Important note

This summary does not prescribe a universal operating-system-specific installation command. Package-manager instructions and available build options can change between releases and distributions. Use the official project site and the README in the source distribution for current, exact instructions.

## Source and version

Based on the GetDP Reference Manual 4.0.0 (November 16, 2026):

- https://getdp.info/doc/texinfo/getdp.txt
- https://getdp.info/src/
- https://gitlab.onelab.info/getdp/getdp
- https://gitlab.onelab.info/getdp/getdp/-/wikis/GetDP-compilation
