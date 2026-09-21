# RewardLens: Same Accuracy, Different Visual Evidence Dependence in Multimodal Judges

*ICLR 2027 paper_v2. Active English draft. Source of truth for claims, RQs, and forbidden language: `PAPER_BLUEPRINT.md`. Chinese Section 3 working draft: `section3_measurement_framework_zh.md`. Formal statements and complete proofs: `section3_theorems_and_proofs.md` (Appendix).*

**Skeleton freeze (2026-09-16).** Identification → measurement → accuracy-equivalence → behavioral decomposition. Best-of-N is a secondary downstream diagnostic, not a primary RQ. Matching uses predeclared \(|\Delta A^S|\le 1\) pp; do not write *preregistered*. No ninth model, no new factor, no new benchmark, no Audit↔BoN item join, no threshold reselection.

**Abstract.** *[Finalize last. Working claim, not copy-edited:]* Two multimodal judges can be equally accurate on a static preference benchmark and still respond differently when the visual evidence that should matter actually changes. RewardLens measures that gap with factor-specific relevant and irrelevant interventions. Invariance is desirable only when the changed evidence is irrelevant.

---

## 1. Introduction

Robust multimodal evaluation is not simply about making judgments stable. A judge should remain stable when irrelevant visual evidence changes, but it should change its judgment when the evidence that determines the correct preference changes. Conventional preference accuracy collapses these behaviors into a single outcome score.

RewardLens asks whether judges that look equivalent under static accuracy remain equivalent under controlled visual interventions. They do not.

The counterintuitive facts are already in the frozen eight-model audit; they do not require a new experiment.

**Equal accuracy can conceal unequal evidence dependence.** On Attribute, Phi-3.5-Vision and LLaVA-OneVision have identical static accuracy, \(A^S=80.5\%\), so \(\Delta A^S=0\). When the queried color actually changes, their relevant-adaptation rates differ by \(15.1\) percentage points. Two judges that are indistinguishable on a conventional benchmark are not interchangeable once the visual evidence that should matter is edited.

**Correctness preservation is not decision stability.** Gemma on Spatial looks almost perfectly invariant by correctness (\(\mathrm{II}=0.979\)) while still changing its predicted letter on \(16.5\%\) of irrelevant edits (\(F_I=0.165\)). A model can appear stable because it is still *right*, and yet be unstable as a *decision*.

**Invariance is not always desirable.** Under a relevant Attribute edit, Qwen changes its prediction on every triplet (\(F_R=1\)) and does not lose correctness: changing the answer is exactly the correct behavior. Under a relevant Count edit, the same model changes its prediction on only \(17\%\) of triplets, while correctness changes on \(83\%\). Staying consistent is the failure, because the gold preference flipped and the letter did not. The robustness default \(\text{invariance}=\text{good}\) is therefore incomplete:

> Invariance is desirable only when the changed evidence is irrelevant. Relevant change should trigger adaptation; irrelevant change should trigger invariance.

We treat these as behavioral facts about interventional response, not as claims about internal causal grounding.

The attractive sentence is:

> Two judges can be equally accurate yet behaviorally different exactly when the visual evidence changes.

The identification fact the paper defends is that \(D_f\) is recovered from static accuracy if and only if it is constant on every accuracy fiber (Theorem 1). An exact static-accuracy tie with unequal RA is then a certificate that the observed fiber is not constant. The same fiber also yields a reconstruction lower bound: any map from \(A^S\) alone to RA must err by at least \(\delta/2\) on that pair (Proposition 2).

**Research questions (frozen).**

- **RQ1 (Identification).** Does static preference accuracy identify how a multimodal judge responds to task-relevant and task-irrelevant visual changes? In general, no. This is Theorem 1, with Proposition 2 as the quantitative counterpart.
- **RQ2 (Empirical equivalence).** Can real judges with identical or nearly identical static accuracy exhibit materially different intervention behavior? Yes, within the frozen eight-model set, including an Attribute exact tie and a predeclared 1 pp census.
- **RQ3 (Behavioral decomposition).** What structure is hidden when judge behavior is summarized only by correctness-based metrics? The eight-state \(\pi_{bri}\) and the prediction flips \(F_R,F_I\) show that static correctness, intervention-conditioned correctness, and decision stability are three different objects.

Best-of-N utility is retained as a secondary diagnostic. This paper does not stand or fall on incremental regression of downstream \(U\) on \(A^S+\mathrm{PFC}+\mathrm{PSC}\).

---

## 2. Related Work

**Preference accuracy as a proxy.** VL-RewardBench, RewardBench 2, and Multimodal RewardBench 2 treat pairwise accuracy as an informative correlate of downstream selection, including Best-of-N. We do not claim that \(A^S\) is useless. We claim that it does not identify interventional behavior.

**Shortcuts and right-for-the-right-reasons.** Geirhos et al. and Ross, Hughes, and Doshi-Velez developed this distinction for task models. A reward model evaluates *other* models' outputs; a spurious judge can launder shortcuts into selection and RL. RewardLens is a judge audit, not a CLEVR VQA leaderboard.

**Sensitivity versus invariance.** Complementary work on multimodal reasoning notes that answer-level correctness does not imply correct visual grounding. RewardLens makes the dual requirement explicit: adapt when the queried factor changes, stay when a structurally matched irrelevant edit is applied.

---

## 3. Measurement Framework

Let \(J\) be a pairwise judge emitting \(\hat Y\in\{A,B\}\). Factors are \(f\in\{\text{Count},\text{Attribute},\text{Presence},\text{Spatial}\}\). Matching, equivalence, and identification are *within factor*. Complete proofs are in the Appendix (`section3_theorems_and_proofs.md`).

### 3.1 Two accuracies

**Static accuracy** is pairwise preference accuracy on an independent natural-image set (TallyQA for Count; GQA otherwise):

\[
A^S_f(J)=P(\hat Y=Y^\star\mid \text{static}_f).
\]

Audit bases are never used to compute \(A^S\). The symbol \(A\) in the frozen confirmatory plan is this quantity.

**Audit-base accuracy.** On a complete controlled triplet, write binary correctness bits \(B,R,I\in\{0,1\}\) for base, relevant, and irrelevant. The eight-state object is

\[
\pi_{bri}=P(B=b,R=r,I=i).
\]

\[
A^B_f(J)=P(B=1)=\sum_{r,i}\pi_{1ri}.
\]

\(A^B\) is diagnostic. It is never called static accuracy and is never used for matching.

### 3.2 Factor-specific interventional profile

\[
\mathrm{RA}_f(J)=P(R=1\mid B=1)=\mathrm{PFC_{cond}},\qquad
\mathrm{II}_f(J)=P(I=1\mid B=1)=\mathrm{PSC_{cond}}.
\]

\[
D_f(J)=\bigl(\mathrm{RA}_f(J),\mathrm{II}_f(J)\bigr).
\]

Frozen joint metrics remain \(\mathrm{PFC}=P(B=1\land R=1)=A^B\cdot\mathrm{RA}\) and \(\mathrm{PSC}=P(B=1\land I=1)=A^B\cdot\mathrm{II}\). RA and II are marginal projections of the base-correct 2×2. They constrain, but do not generally identify, the joint coupling (Proposition 3). Empirical counts are \(N_{bri}\); theoretical probabilities remain \(\pi_{bri}\).

### 3.3 Measurement maps and identification fibers

Fix a nonempty class of judges \(\mathcal J\). Define

\[
\mathcal A_f(J)=A_f^S(J),\qquad
\mathcal D_f(J)=D_f(J)=\bigl(RA_f(J),II_f(J)\bigr).
\]

The *accuracy fiber* at \(a\in[0,1]\) is

\[
\mathcal F_f(a)=\bigl\{J\in\mathcal J:\mathcal A_f(J)=a\bigr\}.
\]

We say that \(D_f\) is identified by \(A_f^S\) on \(\mathcal J\) if there exists \(g:[0,1]\to[0,1]^2\) with \(\mathcal D_f=g\circ\mathcal A_f\) on \(\mathcal J\).

**Theorem 1 (Identification fiber).** \(D_f\) is identified by \(A_f^S\) on \(\mathcal J\) if and only if \(D_f\) is constant on every fiber \(\mathcal F_f(a)\).

*Proof.* If \(D_f=g\circ A_f^S\) and \(J,J'\in\mathcal F_f(a)\), then \(D_f(J)=g(a)=D_f(J')\). Conversely, on each nonempty fiber set \(g(a)\) to the common value of \(D_f\); empty fibers may be assigned arbitrarily. \(\square\)

**Corollary.** An exact static-accuracy tie with unequal \(D_f\) is a certificate of non-identification. On the frozen eight-model class, Phi and LLaVA on Attribute occupy the same fiber \(A^S=0.805\) with \(\lvert\Delta\mathrm{RA}\rvert=15.1\) pp, so \(D_f\) is not constant on \(\mathcal F_{\mathrm{Attr}}(0.805)\). The title claim is this certificate, not a slogan.

### 3.4 Accuracy-only reconstruction lower bound

Theorem 1 is qualitative. The same exact tie is also a quantitative obstruction.

**Proposition 2 (Reconstruction lower bound).** Let \(h:[0,1]\to[0,1]\) be any predictor of RA from static accuracy alone. If \(A_f^S(J_1)=A_f^S(J_2)=a\) and \(\lvert RA_f(J_1)-RA_f(J_2)\rvert=\delta\), then

\[
\max\bigl\{\lvert RA_f(J_1)-h(a)\rvert,\ \lvert RA_f(J_2)-h(a)\rvert\bigr\}\ \ge\ \frac{\delta}{2}.
\]

*Proof.* \(\delta\le\lvert RA_1-h(a)\rvert+\lvert RA_2-h(a)\rvert\le 2\max\{\cdots\}\). \(\square\)

The Attribute exact tie has \(\delta=15.1\) pp, so any accuracy-only reconstruction of RA must err by at least \(7.55\) pp on at least one of Phi or LLaVA. The bound is attained by the midpoint predictor.

The \(\varepsilon\)-class used in Results is a *tolerance neighborhood* of exact fibers, not a replacement for Theorem 1:

\[
\mathcal E_{f,\epsilon}
=
\bigl\{
(J_i,J_j):
\bigl|A^S_f(J_i)-A^S_f(J_j)\bigr|\le\epsilon
\bigr\}.
\]

The predeclared primary band is \(\epsilon=1\) percentage point. Other examined values \(\epsilon\in\{0,0.5,2,3,5\}\) are post-hoc sensitivity. They are not a new matching rule. On a coordinate \(M\in\{\mathrm{RA},\mathrm{II},\mathrm{PFC}\}\),

\[
\widehat{\mathrm{Diam}}_M(\mathcal E_{f,\epsilon})
=
\sup_{(J_i,J_j)\in\mathcal E_{f,\epsilon}}
\bigl|M_f(J_i)-M_f(J_j)\bigr|,
\]

with the supremum taken over the observed model set. We never claim a mathematical limit as \(\epsilon\to 0\); we report that dispersion remains substantial across the examined tolerances.

### 3.5 Sharp partial identification of joint correctness

Condition on \(B=1\) and write \(q_{ri}=P(R=r,I=i\mid B=1)\). Then \(RA=q_{10}+q_{11}\) and \(II=q_{01}+q_{11}\). Let \(z=q_{11}\).

**Proposition 3 (Fréchet bounds).** Given \((RA,II)\), the base-correct joint is compatible with these margins if and only if

\[
\max(0,RA+II-1)\ \le\ z\ \le\ \min(RA,II),
\]

with \(q_{11}=z\), \(q_{10}=RA-z\), \(q_{01}=II-z\), and \(q_{00}=1-RA-II+z\). The interval is *sharp*: every \(z\) in it is a legal coupling.

*Proof.* Nonnegativity of the four coordinates is necessary and sufficient; rearranging yields the Fréchet–Hoeffding bounds for two Bernoullis with means \(RA\) and \(II\). \(\square\)

Thus \((RA,II)\) partially identifies the joint, with one coupling degree of freedom. The interval collapses to a point whenever \(II=1\) (then \(z=RA\)) or \(RA=0\) (then \(z=0\)), among other boundary cases. Qwen Count has \(RA=0.17\), \(II=1\), hence \(z=0.17\) uniquely: Figure 2(c) *localizes* an already-identified joint, and is not a proof of joint non-identification. Phi Attribute has \(RA=0.849\), \(II=0.892\), hence \(z\in[0.741,0.849]\). RA and II therefore constrain, but do not generally identify, the joint coupling.

### 3.6 Binary response algebra

Let \(\Delta Y_X=\mathbf 1[\hat Y_X\neq\hat Y_B]\), \(\Delta G_X=\mathbf 1[Y_X\neq Y_B]\), and \(\Delta C_X=\mathbf 1[C_X\neq C_B]\) for \(X\in\{R,I\}\), where \(Y_X\) is gold and \(C_X=\mathbf 1[\hat Y_X=Y_X]\).

**Lemma 4 (Binary response algebra).** For every triplet and every \(X\in\{R,I\}\),

\[
\Delta C_X=\Delta Y_X\oplus\Delta G_X.
\]

Hence \(\Delta G_X=0\) implies \(\Delta C_X=\Delta Y_X\), and \(\Delta G_X=1\) implies \(\Delta C_X=1-\Delta Y_X\).

*Proof.* Over \(\mathbb F_2\), \(C_X=1\oplus(\hat Y_X\oplus Y_X)=C_B\oplus\Delta Y_X\oplus\Delta G_X\). XOR both sides with \(C_B\). \(\square\)

On RewardLens, irrelevant gold stays (\(\Delta G_I=0\)), so correctness change *is* prediction change. Relevant gold flips (\(\Delta G_R=1\)), so

\[
\text{when gold flips, staying invariant is exactly the correctness failure.}
\]

Qwen Attribute (\(F_R=1\), correctness change \(=0\)) and Qwen Count (\(F_R=0.17\), correctness change \(=0.83\)) are two empirical realizations of this identity. Averaging gives \(F_R=P(\Delta Y_R=1)\) and \(F_I=P(\Delta Y_I=1)\). These are not identified by \(\pi_{bri}\) alone: the eight-state records correctness bits, not letter flips. Figure 3 is the empirical display of Lemma 4. Figure 2 does not include it.

---

## 4. RewardLens Interventions

Fix \((q,y_A,y_B)\). Render a CLEVR-style base scene, then two structurally matched relevant and irrelevant edits.

- **Relevant.** Change only the queried factor so the gold preference *flips*.
- **Irrelevant.** Apply a design-matched edit that does *not* change the queried answer, so the gold preference *stays*.

A judge with correct evidence dependence, given a correct base decision, should flip on relevant and stay on irrelevant. Design matching (same slot, shape, size, material, displacement, render seed, camera, lights) is a check that the two edits are comparable as *controls*. It does not define semantic relevance; semantic relevance is defined by whether gold flips. We additionally quantify realized pixel-change magnitude as a diagnostic, not as the matcher.

**Count.** “How many \(\langle\)COLOR\(\rangle\) objects are there?” Relevant: add one target-color object. Irrelevant: add one matched non-target-color object.

**Attribute.** “What color is the \(\langle\)SHAPE\(\rangle\)?” Relevant: recolor the unique queried shape. Irrelevant: the same color transition on a matched non-target.

**Presence.** “Is there a \(\langle\)COLOR SHAPE\(\rangle\)?” Relevant: remove the target. Irrelevant: remove a matched non-target.

**Spatial.** “Is X left of Y?” Relevant: move the referent until left becomes right. Irrelevant: the same world displacement on a distractor.

FAST_TRACK_AUDIT_V1: 200 PASS triplets per factor (800 triplets, 2400 images), \(320\times 240\), Blender 2.79b, 128 Cycles samples. Audit is procedural from a blank `base_scene.blend`. It is not a re-render of GQA, COCO, or TallyQA photographs. Physical identity is SHA256 of raw image bytes. The source-identity gate is \(\mathcal I_{\text{Audit-source}}\cap\mathcal I_{\text{Downstream}}=\varnothing\).

Pixel-change fraction (256 px) is that diagnostic. On Attribute, mean relevant pixel-change is \(0.118\) and mean irrelevant pixel-change is \(0.179\): the relevant edit is *smaller*. On Spatial, mean relevant pixel-change is \(0.375\) versus \(0.265\) irrelevant. Spatial is therefore *not* pixel-magnitude-matched; it remains design-matched, and we report the realized pixel gap as a caveat rather than as a contradiction of the protocol.

---

## 5. Experimental Setup

Eight open judges covering at least four families: Qwen3-VL-4B-Instruct, Gemma-3-4B-IT, Molmo-7B-D, Skywork-VL-Reward-7B, Idefics3-8B, Phi-3.5-Vision, LLaVA-OneVision-Qwen2-7B, InternVL3-8B. No ninth model.

Static \(A^S\): 200 items / factor. Downstream \(U(N=8)\): 200 questions / factor, frozen pools, image-disjoint from static *within source*. Count uses TallyQA; Attribute, Presence, Spatial use GQA. Pairwise audit is binary A/B.

Inference is frozen. This draft does not rerun models.

---

## 6. Results

All numerical claims below are from frozen Phase II artifacts and the 2026-09-16 forensic reconstruction. Eight-state reconstruction matches canonical RA/II/PFC/PSC on 160/160 cells within \(10^{-12}\). Figure 2 is the candidate main empirical figure (`fig2_same_accuracy_different_behavior`). Figure 3 is the Lemma 4 display (`fig3_correctness_vs_prediction`); it is not part of Figure 2.

### 6.1 Headline: an Attribute exact tie

\[
A^S_{\mathrm{Attribute}}(\text{Phi})
=
A^S_{\mathrm{Attribute}}(\text{LLaVA})
=80.5\%,
\]

\[
\mathrm{RA}_{\mathrm{Attribute}}(\text{Phi})=84.9\%,
\quad
\mathrm{RA}_{\mathrm{Attribute}}(\text{LLaVA})=100\%,
\]

\[
\bigl|\mathrm{RA}_{\mathrm{Attribute}}(\text{Phi})
-
\mathrm{RA}_{\mathrm{Attribute}}(\text{LLaVA})\bigr|
=15.1\text{ pp}.
\]

Hence, on the observed set,

\[
\widehat{\mathrm{Diam}}_{\mathrm{RA}}(\mathcal E_{\mathrm{Attribute},0})\ge 15.1\text{ pp}.
\]

This is the empirical certificate of Theorem 1: \(D_f\) is not constant on \(\mathcal F_{\mathrm{Attr}}(0.805)\). By Proposition 2, any function of \(A^S\) alone that tries to reconstruct RA must err by at least \(7.55\) pp on at least one of these two models. The static scores are not approximately close; they are identical. On the same factor, mean relevant pixel-change (\(0.118\)) is smaller than mean irrelevant pixel-change (\(0.179\)). The RA gap cannot be dismissed as “the relevant edit was a larger visual shock.”

Equal accuracy can conceal unequal evidence dependence.

### 6.2 Predeclared 1 pp census

The primary matching rule remains \(|\Delta A^S_f|\le 1\) pp. That band contains 7 within-factor pairs:

| factor | pair | \(\Delta A^S\) (pp) | \(\lvert\Delta\mathrm{RA}\rvert\) (pp) |
|---|---|---:|---:|
| Attribute | Phi–LLaVA | 0.00 | 15.1 |
| Count | Molmo–Phi | 1.00 | 1.4 |
| Presence | Qwen–LLaVA | 1.00 | 2.0 |
| Presence | Molmo–Idefics3 | 0.50 | 25.6 |
| Presence | Molmo–InternVL | 0.50 | 25.6 |
| Presence | Idefics3–InternVL | 1.00 | 0.0 |
| Spatial | Skywork–Phi | 0.35 | 38.6 |

Median \(\lvert\Delta\mathrm{RA}\rvert=15.1\) pp; maximum \(38.6\) pp. The 1 pp rule is not moved after seeing these numbers.

### 6.3 Spatial large-effect case, with caveat

Skywork versus Phi on Spatial: \(\Delta A^S=0.35\) pp and \(\lvert\Delta\mathrm{RA}\rvert=38.6\) pp (\(\mathrm{RA}=0.86\) vs \(0.47\)). This is the largest predeclared-band gap. Spatial relevant edits have larger mean pixel-change than irrelevant edits (\(0.375\) vs \(0.265\)), and a pixel-matched subset is underpowered (\(n=56/200\)). We therefore treat Attribute as the design-control headline and Spatial as a large-effect case with an explicit pixel-magnitude caveat, not as a substitute for the exact tie.

### 6.4 Post-hoc tolerance sensitivity

For examined \(\epsilon\in\{0,0.5,1,2,3,5\}\) pp, median \(\lvert\Delta\mathrm{RA}\rvert\) among qualifying pairs remains on the order of \(15\) pp (exactly \(15.1\) at \(\epsilon=0\) and at the predeclared \(\epsilon=1\)). Dispersion remains substantial across the examined tolerances. Other \(\epsilon\) are sensitivity only.

### 6.5 Joint intervention-state structure

Write counts as \(N_{bri}=\#\{(B,R,I)=(b,r,i)\}\) and keep \(\pi_{bri}\) for probabilities in Section 3. Figure 2c uses counts.

On Qwen Count, \(A^B=1\), \(N_{101}=166\), \(N_{111}=34\), so \(\mathrm{RA}=34/200=0.17\) and \(\mathrm{II}=1\). Proposition 3 then gives \(z\in\{0.17\}\): the base-correct joint is *point-identified* by the margins. Figure 2(c) localizes that already-identified joint; it is not a proof of joint non-identification. In words: on 166 of 200 base-correct Count triplets the relevant intervention is failed while the irrelevant intervention is still correct. That is correctness state \(101\). Under the binary RewardLens construction, a base-correct \(101\) case corresponds to retaining the base decision when the relevant intervention flips the gold preference; that interpretation is not the definition of the state. InternVL Count is almost the same map (\(N_{101}=164\), \(N_{111}=36\)).

Gemma Spatial is likewise a Fréchet boundary: \(N_{111}=N_{110}=0\), \(N_{101}=143\), so among base-correct Spatial triplets \(RA=0\) and \(z=0\) uniquely. Attribute, by contrast, is near-pure \(111\) for Qwen and LLaVA (\(N_{111}=200\)). Phi Attribute has \(RA=0.849\), \(II=0.892\), hence a nontrivial interval \(z\in[0.741,0.849]\): the same \(D_f\) is compatible with more than one coupling.

This is a joint correctness-state decomposition, not a prediction-mechanism claim. Literal decision changes \(F_R,F_I\) are a separate object (Section 6.6 / Figure 3).

### 6.6 Prediction flip: staying invariant can be the failure

Audit labels are binary A/B. Lemma 4 is the identity \(\Delta C_X=\Delta Y_X\oplus\Delta G_X\). Figure 3 is the empirical display of that identity. “Another wrong” is possible on relevant only when gold flips; the scripts do not assume it away.

**Qwen Attribute.** \(F_R=1\). Gold flips (\(\Delta G_R=1\)), so \(\Delta C_R=1-\Delta Y_R\). The model changes its letter on every relevant edit, and correctness does not fall: changing the answer is the correct behavior.

**Qwen Count.** \(F_R=0.17\), while the correctness transition is \(0.83\): 166 of 200 items go from correct to incorrect with *unchanged* prediction, because gold flipped and the letter did not. Staying invariant is the failure. This is the same identity as Attribute, not a second phenomenon.

**Gemma Spatial.** \(\mathrm{II}=0.979\) while \(F_I=0.165\). Irrelevant gold stays (\(\Delta G_I=0\)), so \(\Delta C_I=\Delta Y_I\) itemwise, but the *rates* \(1-\mathrm{II}\) and \(F_I\) still differ because II is conditioned on \(B=1\) and \(F_I\) is not. Correctness-conditioned invariance looks almost perfect; decisions still move. On relevant, \(\mathrm{RA}=0\) because all 146 base-correct items keep their letter; \(F_R=0.27\) is entirely already-wrong items switching to the other wrong letter.

High correctness invariance is not decision stability. Under relevant visual changes, changing the answer can be exactly the correct behavior, while staying consistent can be the failure.

### 6.7 Secondary downstream diagnostic

Factor-wise Best-of-N (\(N=8\)) was collected on image-disjoint natural-image pools. In the present eight-model study, adding PFC/PSC to \(A^S\) does not establish consistent leave-one-family-out superiority over \(A^S\) alone (family-clustered intervals include zero on three of four factors; Count’s interval is small). RewardLens measures remain descriptively associated with downstream utility. This paper does not claim that evidence-dependence scores replace static accuracy as a deployment predictor. Downstream \(U\) is extra context, not the life of the result.

Pair-graph coherence (cycles, Condorcet, Copeland) is exploratory and stays in the appendix / future work.

---

## 7. Discussion and Limitations

The conceptual point is not that we introduced two more acronyms. It is that interventional evaluation has a signed requirement: adapt to relevant evidence, stay under irrelevant evidence. Theorem 1 says \(D_f\) is identified by \(A^S\) only if it is constant on accuracy fibers; Proposition 2 turns an exact tie into a reconstruction lower bound. Within correctness space, RA and II are Fréchet-constrained projections of the base-correct 2×2 (Proposition 3). Prediction flips are a separate decision-level response, related to correctness change by the XOR identity of Lemma 4, and are not identified by \(\pi_{bri}\) alone. Level 3 is therefore two complementary objects, \(\pi(B,R,I)\) and \(F_R,F_I\), not a single uncompressed truth.

**Behavioral, not internal grounding.** \(D_f\) describes how preferences move under controlled edits. It does not identify which pixels, objects, or attention heads caused the score.

**\(A^S\neq A^B\).** Matching on audit-base accuracy would be a different, easier, and invalid test.

**Spatial pixel magnitude.** Spatial is the weakest matched pair by realized pixel-change. The protocol remains design-matched. Attribute is the cleaner pixel-control, including the exact tie.

**Count / GQA source split.** Count static and downstream are TallyQA; the other three factors are GQA. Factor identity and dataset source co-vary on Count. SHA-manifest `carrier=tallyqa/gqa` on *audit* rows is a metadata mislabel: audit images are CLEVR renders.

**n = 8.** Family-level downstream inference is underpowered. That is a reason to keep Best-of-N secondary, not a reason to add a ninth model in order to rescue a regression.

**Human intervention-validity audit.** A frozen 80-triplet/factor dual-annotator sample (320 triplets) is the remaining P0 validation of whether relevant edits really change the queried evidence and irrelevant edits really do not. Labels are not invented and are not substituted by a model. If the audit is incomplete at submission, this is a limitation, not a silent skip.

**Orientation swap** is P1 robustness, not a blocker.

We do not collect: a ninth model, a new benchmark, a new visual factor, a regenerated main experiment, Audit↔BoN item-level joins, a new matching threshold, or pair-graph as a main line.

---

## 8. Conclusion

Static preference accuracy identifies factor-specific interventional behavior if and only if that behavior is constant on every accuracy fiber. In the frozen RewardLens audit, two judges occupy the same Attribute fiber and still differ by \(15.1\) pp in RA, so any accuracy-only reconstruction of RA must err by at least \(7.55\) pp on at least one of them. A judge can look invariant by correctness and still change its decisions; and under relevant edits, invariance itself can be the failure. The measurement is a controlled relevant/irrelevant protocol. The headline evidence is an Attribute exact tie and a predeclared 1 pp census whose median \(\lvert\Delta\mathrm{RA}\rvert\) is \(15.1\) pp. The finer evidence is the Fréchet structure of the base-correct joint and the XOR split between correctness change and prediction change.

---

## Figure captions

**Figure 1.** Controlled RewardLens-CLEVR interventions (base / relevant / irrelevant) for Count, Attribute, Presence, Spatial. Real renders, not illustrations.

**Figure 2.** Same accuracy, different intervention behavior. **(a)** Pairwise gaps in independent static accuracy \(A^S\) and Relevant Adaptation (RA) for within-factor judge pairs. Red markers denote pairs satisfying the predeclared \(|\Delta A^S|\le 1\) pp rule. Phi–LLaVA on Attribute form an exact static-accuracy tie but differ by 15.1 pp in RA; Skywork–Phi on Spatial differ by 0.35 pp in static accuracy and 38.6 pp in RA. **(b)** Median and maximum \(|\Delta\mathrm{RA}|\) among qualifying pairs across the examined matching tolerances. The 1 pp threshold is the predeclared primary analysis; all other tolerances are post-hoc sensitivity analyses. **(c)** Joint correctness-state counts for representative model–factor cells. State \(111\) denotes correctness on base, relevant, and irrelevant conditions; state \(101\) denotes base correctness and irrelevant correctness but failure after the relevant intervention. Gray contains the remaining six joint states. The panel illustrates joint-state structure rather than introducing a new scalar metric.

**Figure 3 (not Figure 2).** Binary response algebra (Lemma 4). **(a)** Geometry of \(\Delta C=\Delta Y\oplus\Delta G\). When gold stays, correctness change equals prediction change; when gold flips, they sum to one. Qwen Attribute and Qwen Count occupy opposite ends of the gold-flip line. **(b)** All 32 model–factor cells under relevant interventions lie on \(P(\Delta C_R=1)=1-F_R\) (exact on the frozen audit). **(c)** The same identity, two realizations: Qwen Attribute changes its letter on every relevant Attribute edit and does not lose correctness; Qwen Count keeps the letter on 83% of relevant Count edits and loses correctness. \(F_R\) and \(F_I\) are not identified by \(\pi_{bri}\) and are not added to Figure 2.

---

## Notes for the next writing pass

- Abstract last.
- Do not write *preregistered*.
- Do not touch Figure 2.
- Figure 3 is drawn from Lemma 4 (`fig3_correctness_vs_prediction`); do not fold it into Figure 2.
- Do not call eight-state a mechanism.
- Do not write *magnitude-matched edits* as if Spatial pixel-change were matched; keep *design-matched* / *structurally matched*, with pixel-change as a diagnostic.
- Do not promote pair-graph or BoN incremental validity to the main claim.
- Human audit: report rates only after dual annotation exists; otherwise keep the limitation paragraph.
