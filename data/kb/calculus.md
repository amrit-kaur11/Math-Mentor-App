# Basic Calculus

## Limits
The limit of a function $f(x)$ as $x$ approaches $c$ is the value that the function approaches as its input gets closer to $c$. L'Hôpital's Rule is often useful for limits of the form $0/0$ or $\infty/\infty$:
$\lim_{x \to c} \frac{f(x)}{g(x)} = \lim_{x \to c} \frac{f'(x)}{g'(x)}$

## Derivatives
The derivative measures the rate of change of a quantity.
### Standard Derivatives:
- $\frac{d}{dx}(x^n) = n x^{n-1}$
- $\frac{d}{dx}(\sin x) = \cos x$
- $\frac{d}{dx}(\cos x) = -\sin x$
- $\frac{d}{dx}(e^x) = e^x$
- $\frac{d}{dx}(\ln x) = \frac{1}{x}$
### Rules:
- Product Rule: $(uv)' = u'v + uv'$
- Quotient Rule: $(u/v)' = \frac{u'v - uv'}{v^2}$
- Chain Rule: $\frac{d}{dx} f(g(x)) = f'(g(x)) \cdot g'(x)$

## Simple Optimization
To find the maximum or minimum of a function $f(x)$:
1. Find the first derivative $f'(x)$.
2. Set $f'(x) = 0$ to find critical points.
3. Find the second derivative $f''(x)$.
- If $f''(c) > 0$, $f(x)$ has a local minimum at $c$.
- If $f''(c) < 0$, $f(x)$ has a local maximum at $c$.
