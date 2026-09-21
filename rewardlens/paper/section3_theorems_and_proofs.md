# Appendix — Formal statements and proofs for Section 3

These four results upgrade the measurement framework. They do not change the frozen RQs, the predeclared 1 pp matching rule, or Figure 2. Empirical numbers are witnesses, not part of the proofs.

Notation is as in Section 3. The class of judges under discussion is a nonempty set \(\mathcal J\) of binary pairwise judges (legal labels \(\{A,B\}\)). Factor \(f\) is held fixed; we omit it when unambiguous. Completeness, abstention, and the complete-triplet convention are as in the frozen `compute_audit_metrics` implementation.

---

## Theorem 1 (Identification fiber)

**Setup.** Fix a factor \(f\). Define the measurement maps

\[
\mathcal A_f:\mathcal J\to[0,1],\qquad
\mathcal A_f(J)=A_f^S(J),
\]

\[
\mathcal D_f:\mathcal J\to[0,1]^2,\qquad
\mathcal D_f(J)=D_f(J)=\bigl(RA_f(J),II_f(J)\bigr).
\]

The *accuracy fiber* at \(a\in[0,1]\) is

\[
\mathcal F_f(a)=\bigl\{J\in\mathcal J:\mathcal A_f(J)=a\bigr\}.
\]

We say that \(D_f\) is *identified by* \(A_f^S\) on \(\mathcal J\) if there exists a function \(g:[0,1]\to[0,1]^2\) such that \(\mathcal D_f(J)=g\bigl(\mathcal A_f(J)\bigr)\) for every \(J\in\mathcal J\). Equivalently: \(A_f^S(J)\) point-identifies \(D_f(J)\) on \(\mathcal J\).

**Theorem 1.** \(D_f\) is identified by \(A_f^S\) on \(\mathcal J\) if and only if \(D_f\) is constant on every fiber \(\mathcal F_f(a)\).

**Proof.** (\(\Rightarrow\)) Suppose \(D_f=g\circ A_f^S\). If \(J,J'\in\mathcal F_f(a)\), then \(A_f^S(J)=A_f^S(J')=a\), hence \(D_f(J)=g(a)=D_f(J')\).

(\(\Leftarrow\)) Suppose \(D_f\) is constant on every fiber. For each \(a\) with \(\mathcal F_f(a)\neq\varnothing\), pick any \(J_a\in\mathcal F_f(a)\) and set \(g(a)=D_f(J_a)\); the value does not depend on the representative. For \(a\) with empty fiber, set \(g(a)\) arbitrarily (e.g. \((0,0)\)). Then for every \(J\in\mathcal J\), \(J\in\mathcal F_f(A_f^S(J))\), so \(D_f(J)=g(A_f^S(J))\). \(\square\)

**Corollary (empirical certificate).** If there exist \(J_1,J_2\in\mathcal J\) with \(A_f^S(J_1)=A_f^S(J_2)\) and \(D_f(J_1)\neq D_f(J_2)\), then \(D_f\) is not identified by \(A_f^S\) on \(\mathcal J\).

On the frozen eight-model set, Phi and LLaVA on Attribute satisfy \(A^S=0.805\) and \(\lvert\Delta\mathrm{RA}\rvert=15.1\) pp. The observed Attribute fiber at \(0.805\) is therefore not constant, which is an empirical certificate of Theorem 1, not a new matching rule.

The \(\varepsilon\)-class \(\mathcal E_{f,\varepsilon}\) used in Results is a *tolerance* neighborhood of exact fibers. It is an empirical device. Theorem 1 is about exact fibers \(\mathcal F_f(a)\). We never write \(\lim_{\varepsilon\to 0}\mathrm{Diam}(\mathcal E_\varepsilon)>0\).

---

## Proposition 2 (Accuracy-only reconstruction lower bound)

**Setup.** Let \(h:[0,1]\to[0,1]\) be any (possibly data-dependent) predictor that attempts to reconstruct RA from static accuracy alone: the reconstructed value for a judge with \(A_f^S=a\) is \(h(a)\).

**Proposition 2.** Suppose \(J_1,J_2\in\mathcal J\) satisfy \(A_f^S(J_1)=A_f^S(J_2)=a\) and \(\lvert RA_f(J_1)-RA_f(J_2)\rvert=\delta\). Then for every \(h\),

\[
\max\bigl\{\lvert RA_f(J_1)-h(a)\rvert,\ \lvert RA_f(J_2)-h(a)\rvert\bigr\}\ \ge\ \frac{\delta}{2}.
\]

**Proof.** Write \(r_i=RA_f(J_i)\). The triangle inequality gives

\[
\delta=\lvert r_1-r_2\rvert
\le
\lvert r_1-h(a)\rvert+\lvert r_2-h(a)\rvert
\le
2\max\bigl\{\lvert r_1-h(a)\rvert,\ \lvert r_2-h(a)\rvert\bigr\}.
\]

Divide by 2. \(\square\)

**Witness.** The Attribute exact tie has \(\delta=15.1\) pp, hence any accuracy-only reconstruction of RA must err by at least \(7.55\) pp on at least one of Phi or LLaVA. The bound is sharp in the abstract: \(h(a)=(r_1+r_2)/2\) attains \(\delta/2\) on both coordinates.

The result is a minimax statement about the *map* from \(A^S\) to RA. It does not claim that no other covariates could reconstruct RA.

---

## Proposition 3 (Sharp partial identification of the base-correct joint)

**Setup.** Condition on \(C_B=1\) (equivalently \(B=1\) when \(B\) denotes base correctness). Let

\[
q_{ri}=P(C_R=r,C_I=i\mid C_B=1),\qquad r,i\in\{0,1\}.
\]

Then \(RA=q_{10}+q_{11}\) and \(II=q_{01}+q_{11}\), and \(\sum_{r,i}q_{ri}=1\). Write \(z=q_{11}\).

**Proposition 3.** Given \((RA,II)\in[0,1]^2\) with \(RA+II\le 2\), the vector \((q_{00},q_{01},q_{10},q_{11})\) is compatible with these margins if and only if

\[
z\in\bigl[\max(0,RA+II-1),\ \min(RA,II)\bigr],
\]

with

\[
q_{11}=z,\quad
q_{10}=RA-z,\quad
q_{01}=II-z,\quad
q_{00}=1-RA-II+z.
\]

The interval is *sharp*: every \(z\) in it produces a unique probability vector with the given margins. In particular, the identified set for \(q_{11}\) is exactly the Fréchet–Hoeffding bounds for two Bernoulli random variables with means \(RA\) and \(II\).

**Proof.** Nonnegativity of the four coordinates is necessary and sufficient for a probability vector with those affine relations. \(q_{11}=z\ge 0\), \(q_{10}=RA-z\ge 0\), \(q_{01}=II-z\ge 0\), and \(q_{00}=1-RA-II+z\ge 0\) rearrange to \(z\le RA\), \(z\le II\), \(z\ge 0\), and \(z\ge RA+II-1\). Hence \(z\in[\max(0,RA+II-1),\min(RA,II)]\). Conversely, any such \(z\) yields four nonnegative numbers summing to \(1\), so the bounds are attained. \(\square\)

**Consequences.**

1. \((RA,II)\) *partially* identifies the base-correct joint, with one coupling degree of freedom.
2. If the interval degenerates to a point, the joint is *point-identified* by the margins. This occurs whenever \(II=1\) (then \(z=RA\)), or \(RA=1\) (then \(z=II\)), or \(RA=0\) (then \(z=0\)), or \(II=0\) (then \(z=0\)), or \(RA+II=1\) with one of the Fréchet ends binding in a singleton.
3. Qwen Count has \(RA=0.17\), \(II=1\), hence \(z\in\{0.17\}\). Figure 2(c) *localizes* this already-identified joint (\(N_{111}=34\), \(N_{101}=166\)); it is not a proof of joint non-identification.
4. Phi Attribute has \(RA=0.849\), \(II=0.892\), hence \(z\in[0.741,0.849]\), a nontrivial interval: the same \(D_f\) is compatible with more than one coupling.

RA and II therefore constrain, but do not generally identify, the joint coupling. That is Proposition 3, not a slogan about “hiding 101.”

---

## Lemma 4 (Binary response algebra)

**Setup.** For variant \(X\in\{B,R,I\}\), let \(\hat Y_X\in\{A,B\}\) be the judge’s prediction and \(Y_X\in\{A,B\}\) the gold preference. Define correctness \(C_X=\mathbf 1[\hat Y_X=Y_X]\) and

\[
\Delta Y_X=\mathbf 1[\hat Y_X\neq\hat Y_B],\qquad
\Delta G_X=\mathbf 1[Y_X\neq Y_B],\qquad
\Delta C_X=\mathbf 1[C_X\neq C_B].
\]

Identify the binary alphabet with \(\mathbb F_2=\{0,1\}\) so that addition is XOR, written \(\oplus\). Then \(\hat Y_X=\hat Y_B\oplus\Delta Y_X\) and \(Y_X=Y_B\oplus\Delta G_X\).

**Lemma 4.** For every triplet and every \(X\in\{R,I\}\),

\[
\Delta C_X=\Delta Y_X\oplus\Delta G_X.
\]

In particular:

- if gold is unchanged (\(\Delta G_X=0\)), then \(\Delta C_X=\Delta Y_X\);
- if gold flips (\(\Delta G_X=1\)), then \(\Delta C_X=1-\Delta Y_X\).

**Proof.** Over \(\mathbb F_2\),

\[
C_X=\mathbf 1[\hat Y_X=Y_X]
=1\oplus(\hat Y_X\oplus Y_X)
=1\oplus(\hat Y_B\oplus\Delta Y_X\oplus Y_B\oplus\Delta G_X)
=C_B\oplus\Delta Y_X\oplus\Delta G_X,
\]

where the last step uses \(C_B=1\oplus(\hat Y_B\oplus Y_B)\). Therefore \(C_X\oplus C_B=\Delta Y_X\oplus\Delta G_X\), which is \(\Delta C_X=\Delta Y_X\oplus\Delta G_X\). If \(\Delta G_X=0\), XOR with 0 is the identity. If \(\Delta G_X=1\), XOR with 1 is complementation, i.e. \(1-\Delta Y_X\) in \(\{0,1\}\). \(\square\)

**RewardLens specializations.** On the frozen audit, irrelevant gold satisfies \(Y_I=Y_B\), hence \(\Delta G_I=0\) and \(\Delta C_I=\Delta Y_I\): correctness change and prediction change coincide. Relevant gold is constructed to flip, hence \(\Delta G_R=1\) and \(\Delta C_R=1-\Delta Y_R\): *staying invariant is exactly the correctness failure*. Averaging over complete triplets,

\[
P(\Delta C_R=1)=1-F_R^{\mathrm{rel}},
\]

when gold flips on every relevant item (the RewardLens relevant design). Qwen Attribute (\(F_R=1\), correctness change \(=0\)) and Qwen Count (\(F_R=0.17\), correctness change \(=0.83\)) are two empirical realizations of the same identity, not two unrelated anecdotes.

The lemma uses only that the label set is binary. It does not use CLEVR, pixel-change, or any neural assumption. It does *not* recover \(F_R,F_I\) from \(\pi_{bri}\): the eight-state records \((C_B,C_R,C_I)\), whereas \(\Delta Y_X\) is a statement about \(\hat Y\). Figure 3 is the empirical display of this lemma. Figure 2 does not include it.

---

## What these results do not say

- They do not identify internal causal grounding.
- They do not claim \(A^S\) is useless.
- They do not claim RA/II outperform \(A^S\) at Best-of-N.
- Proposition 3 is about the *base-correct* 2×2, not the full eight-state including \(C_B=0\).
- Theorem 1 is on a specified class \(\mathcal J\); the eight-model set is one class, not all possible judges.
