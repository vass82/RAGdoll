# Defining a problem in GetDP

## The `.pro` problem-definition file

A GetDP model is described in a plain-text `.pro` file. The file is a structured collection of objects that represents the mathematical formulation of the discrete problem.

The main object types are:

1. `Group`
2. `Function`
3. `Constraint`
4. `FunctionSpace`
5. `Jacobian`
6. `Integration`
7. `Formulation`
8. `Resolution`
9. `PostProcessing`
10. `PostOperation`

The object definitions are connected through references. A definition must appear before another object refers to it.

## Typical object responsibilities

### Group

Groups define topological entities and regions of the model. They are commonly used to identify physical regions, boundaries, electrodes, coils or other geometrical subsets.

### Function

Functions define global or piecewise expressions. They can represent material properties, source terms, coefficients and other expressions used in the model.

### Constraint

Constraints specify restrictions on function spaces and formulations. They are used, for example, to prescribe values or impose relationships among degrees of freedom.

### FunctionSpace

A function space defines the discrete quantities involved in a formulation, including the unknown fields and their approximation spaces.

### Jacobian and Integration

A `Jacobian` defines the geometric mapping used for integration. An `Integration` defines the numerical integration method.

### Formulation

A formulation defines the system of equations to be assembled. It brings together the relevant groups, functions, constraints, function spaces, Jacobians and integration methods.

### Resolution

A resolution describes how the system is processed. Its operations can include matrix generation, system solving, time stepping and other solution procedures.

### PostProcessing and PostOperation

`PostProcessing` defines quantities derived from the computed solution. `PostOperation` specifies how those quantities are evaluated, displayed or exported.

## Recommended reading sequence

The reference manual suggests that new users can start by running the demo problems distributed with GetDP, then inspect their `.pro` files and compare them with the short and complete examples. The detailed syntax chapters can be consulted as new constructs are encountered.

A practical learning sequence is therefore:

1. Run a small tutorial.
2. Inspect its `.geo` and `.pro` files.
3. Identify the regions and physical functions.
4. Follow the function-space and formulation definitions.
5. Locate the resolution operation.
6. Inspect the post-processing and output definitions.
7. Consult the reference manual for unfamiliar syntax or object types.

## Source and version

Based on the GetDP Reference Manual 4.0.0 (November 16, 2026):

- https://getdp.info/doc/texinfo/getdp.txt
