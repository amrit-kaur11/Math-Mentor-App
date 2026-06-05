# Probability and Statistics

## Basic Probability
The probability of an event $A$ is denoted by $P(A)$. Let $\Omega$ be the sample space.
- $0 \le P(A) \le 1$
- $P(\Omega) = 1$
- For mutually exclusive events $A$ and $B$, $P(A \cup B) = P(A) + P(B)$.

## Conditional Probability
The probability of $A$ given $B$ has occurred is:
$P(A|B) = \frac{P(A \cap B)}{P(B)}$, for $P(B) > 0$.

## Bayes' Theorem
$P(A|B) = \frac{P(B|A) P(A)}{P(B)}$

## Common Mistakes
- Confusing mutually exclusive events with independent events. Mutually exclusive means they cannot happen at the same time ($P(A \cap B) = 0$). Independent means one event doesn't affect the other ($P(A \cap B) = P(A)P(B)$).
- Adding probabilities instead of multiplying for independent sequences. (e.g., rolling two 6s in a row is $\frac{1}{6} \times \frac{1}{6} = \frac{1}{36}$, not $\frac{1}{6} + \frac{1}{6}$).
