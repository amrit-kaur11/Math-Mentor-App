# Linear Algebra Basics

## Matrices
A matrix is a rectangular array of numbers.
An $m \times n$ matrix has $m$ rows and $n$ columns.

## Determinants
The determinant of a $2 \times 2$ matrix $A = \begin{pmatrix} a & b \\ c & d \end{pmatrix}$ is given by $\det(A) = ad - bc$.
- If $\det(A) = 0$, the matrix is singular (no inverse).
- If $\det(A) \neq 0$, the matrix is invertible.

## Systems of Linear Equations
Can be represented as $Ax = B$.
Cramer's Rule: For a system of $n$ linear equations with $n$ variables, if $\det(A) \neq 0$, there is a unique solution.
$x_i = \frac{\det(A_i)}{\det(A)}$ where $A_i$ is the matrix formed by replacing the $i$-th column of $A$ with the column vector $B$.
