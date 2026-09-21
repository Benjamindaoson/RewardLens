# RewardLens — PAPER_BLUEPRINT.md

> **状态：论文 V2 冻结蓝图**
>
> 本文件用于冻结 RewardLens 的论文定位、研究问题、理论对象、主张层级、核心证据、图表结构、写作边界与章节组织。
>
> 后续正文、摘要、Introduction、Results、Discussion、Conclusion 均必须与本文件保持一致。
>
> 除非发现实验完整性问题或现有数字错误，否则不再改变论文主问题、不再增加新的主 Research Question、不再用新的 exploratory result 替换已经冻结的主结果。
>
> 本文件是论文骨架的 source of truth。`iclr2027_paper_v2.md` 是英文写作面；中文母稿按本文件第 42 节顺序撰写。

---

# 0. 论文当前定位

RewardLens 不再定位为：

- 一个新的 multimodal reward benchmark；
- 一个声称比 preference accuracy 更好的 leaderboard metric；
- 一个证明模型“真正看了正确视觉证据”的内部机制工具；
- 一个主要依赖 Best-of-N downstream prediction 成立的论文。

RewardLens 当前正式定位为：

> **一篇关于 multimodal judge evaluation 的 measurement / identification paper。**

论文研究的核心问题是：

> **一个静态 preference accuracy 分数，究竟能够识别多少关于 multimodal judge 在视觉证据变化时的行为？**

RewardLens 的核心发现是：

\[
\boxed{
\text{相同或近似相同的静态准确率，并不意味着相同的视觉干预行为。}
}
\]

更正式地说：

\[
\boxed{
A_f^S(J)\ \text{does not identify}\ D_f(J)
}
\]

其中：

- \(A_f^S(J)\)：模型 \(J\) 在 factor \(f\) 对应的**独立静态评测集**上的 preference accuracy；
- \(D_f(J)\)：模型面对受控视觉干预时表现出的 factor-specific selective visual evidence dependence。

定义：

\[
D_f(J)
=
\bigl(
RA_f(J),
II_f(J)
\bigr)
\]

其中：

- \(RA\)：Relevant Adaptation；
- \(II\)：Irrelevant Invariance。

---

# 1. 冻结标题

## 主标题

# **RewardLens: Same Accuracy, Different Visual Evidence Dependence in Multimodal Judges**

中文工作标题：

> **RewardLens：相同准确率，不同视觉证据依赖——多模态评判模型的干预式测量**

该标题的作用是直接突出论文最反直觉、最容易记住的经验发现：

\[
\boxed{
\text{Same accuracy}
\neq
\text{same intervention behavior}
}
\]

正文中的正式理论表述仍然使用：

\[
A_f^S(J)
\text{ does not identify }
D_f(J).
\]

---

# 2. 一句话母命题

论文所有章节必须服务于下面这一句话：

> **A scalar preference score can collapse multimodal judges that are behaviorally distinct under controlled visual interventions.**

中文：

> **单一 preference accuracy 会把在受控视觉干预下行为明显不同的 multimodal judges 压缩成看似等价的模型。**

RewardLens 的作用不是简单增加一个新分数，而是把这种被 scalar score 压缩掉的行为重新展开。

---

# 3. 最重要的概念洞察

论文围绕三个逐层递进的 measurement insight 展开。

## Insight 1

\[
\boxed{
\text{Same accuracy}
\neq
\text{same visual evidence dependence}
}
\]

两个模型可以具有完全相同或极其接近的 static preference accuracy，却在相关视觉证据改变后表现出明显不同的 adaptation。

---

## Insight 2

\[
\boxed{
\text{Correctness preservation}
\neq
\text{decision stability}
}
\]

模型在 intervention 后是否仍然“答对”，和它是否真的改变了自己的预测，是两个不同的 behavioral observables。

---

## Insight 3

\[
\boxed{
\text{Invariance is not always desirable.}
}
\]

对于 irrelevant visual change：

\[
\text{desired behavior}
=
\text{invariance}
\]

而对于 relevant visual change：

\[
\text{desired behavior}
=
\text{adaptation}
\]

因此，multimodal judge 的理想行为不是“越稳定越好”，而是：

\[
\boxed{
\text{selectively stable}
}
\]

即：

> **面对无关变化保持稳定，面对真正相关的证据变化正确改变判断。**

这是 RewardLens 最核心的概念基础。

---

# 4. Research Questions

最终只保留三个主 RQ。

Best-of-N 不再作为主 RQ。

---

## RQ1 — Identification

### English

> **Does static preference accuracy identify how a multimodal judge responds to task-relevant and task-irrelevant visual changes?**

### 中文

> **静态 preference accuracy 能否识别 multimodal judge 对任务相关与任务无关视觉变化的选择性响应？**

理论回答：

\[
\boxed{
\text{No, in general.}
}
\]

该问题由 Measurement Framework 与 Theorem 1（纤维刻画）+ Proposition 2（重构下界）回答。原 Proposition 1 是充分条件方向的口号，已被 Theorem 1 的充要条件取代。

---

## RQ2 — Empirical Equivalence

### English

> **Can real multimodal judges with identical or nearly identical static accuracy exhibit materially different intervention behavior?**

### 中文

> **真实 multimodal judges 在静态 accuracy 相同或近似相同时，是否仍会表现出显著不同的视觉干预行为？**

核心证据：

1. exact static-accuracy tie；
2. predeclared 1pp accuracy-matching census；
3. post-hoc matching-tolerance sensitivity。

---

## RQ3 — Behavioral Decomposition

### English

> **What intervention behavior is hidden when multimodal judges are summarized only by correctness-based metrics?**

### 中文

> **当 multimodal judge 的行为仅由 correctness-based 指标概括时，哪些干预行为结构会被压缩掉？**

核心分析：

- joint audit-state distribution；
- prediction flip；
- correctness transition vs literal prediction change。

---

# 5. Secondary Question — Downstream Utility

Best-of-N 正式降级为：

> **Secondary Downstream Diagnostic**

研究问题：

> RewardLens behavioral measures 与 downstream Best-of-N utility 之间是否存在描述性关联？

允许的结论：

> RewardLens dependency measures are descriptively associated with downstream Best-of-N utility, but the present eight-model study does not establish that they consistently outperform conventional accuracy or provide independent predictive validity beyond it.

中文：

> RewardLens 的证据依赖指标与 downstream Best-of-N utility 存在描述性关联，但当前八模型研究不能证明这些指标稳定优于传统 accuracy，也不能证明其在 accuracy 之外具有独立预测效度。

必须明确：

\[
RQ_{\text{downstream}}
\]

不是论文成立的前提。

---

# 6. 核心符号体系

全文禁止继续使用一个模糊的 \(A\)。

---

## 6.1 Independent Static Accuracy

定义：

\[
A_f^S(J)
\]

表示模型 \(J\) 在视觉因素 \(f\) 所对应的**独立冻结 static benchmark** 上的 preference accuracy。

其中：

\[
f\in
\{
\text{Count},
\text{Attribute},
\text{Spatial},
\text{Presence}
\}.
\]

注意：

Count 的独立 static source 与其他因素不同，因此：

> 不得将跨 factor 数值差异直接解释为 factor 的因果作用。

---

## 6.2 Audit-base Accuracy

定义：

\[
A_f^B(J)
=
P(C_B=1).
\]

其中：

- \(B\)：audit triplet 的 base variant；
- \(C_B\in\{0,1\}\)：base judgment 是否正确。

必须始终写：

> `audit-base accuracy`

不能称：

> `static accuracy`

因为 forensic analysis 已经证明：

\[
\boxed{
A_f^S \neq A_f^B
}
\]

且 32/32 个 model × factor 条目均不相等。

典型反例：

Qwen Count：

\[
A^S=0.915,
\]

\[
A^B=1.000,
\]

\[
RA=0.17.
\]

因此：

\[
A^S\cdot RA
=
0.15555
\]

并不等于真实：

\[
PFC=0.17.
\]

---

# 7. RewardLens Audit 定义

对于每个 controlled audit triplet：

\[
(B,R,I)
\]

其中：

- \(B\)：base；
- \(R\)：task-relevant visual intervention；
- \(I\)：task-irrelevant visual intervention。

定义正确性变量：

\[
C_B,C_R,C_I\in\{0,1\}.
\]

---

## 7.1 Relevant Adaptation

定义：

\[
RA_f(J)
=
P(C_R=1\mid C_B=1).
\]

解释：

> 在 base 判断正确的前提下，当真正决定 preference 的视觉证据发生变化时，judge 是否能够正确适应。

---

## 7.2 Irrelevant Invariance

定义：

\[
II_f(J)
=
P(C_I=1\mid C_B=1).
\]

解释：

> 在 base 判断正确的前提下，当任务无关视觉因素改变时，judge 是否能够继续保持正确。

---

## 7.3 Selective Visual Evidence Dependence

定义：

\[
\boxed{
D_f(J)
=
\bigl(
RA_f(J),
II_f(J)
\bigr)
}
\]

RewardLens 测量的是：

> **behavioral selective visual evidence dependence**

而不是：

- internal attention；
- latent causal representation；
- true model reasoning；
- “模型真正看了什么”。

---

# 8. PFC / PSC 的地位

定义：

\[
PFC
=
P(C_B=1,C_R=1)
\]

\[
PSC
=
P(C_B=1,C_I=1).
\]

在相同 audit population、相同 complete-triplet rule 与相同 abstention convention 下：

\[
\boxed{
PFC=A^B\cdot RA
}
\]

\[
\boxed{
PSC=A^B\cdot II
}
\]

forensic reconstruction：

> 32/32 model × factor，160/160 canonical entries 完全重构通过。

因此理论上：

- PFC / PSC 可以保留为 unconditional operational metrics；
- 但它们不是独立于 \(A^B,RA,II\) 的新 behavioral dimension；
- Abstract 和理论主线不再突出 PFC / PSC。

禁止写：

\[
PFC=A^S\cdot RA
\]

或：

\[
PSC=A^S\cdot II.
\]

---

# 9. Proposition 1 — Static-Score Non-identification

> **Superseded as the main-text statement (2026-09-16).** Keep this section as the original slogan. The paper now uses Theorem 1 (fiber iff), Proposition 2 (reconstruction LB), Proposition 3 (Fréchet), and Lemma 4 (XOR). See §46 and `section3_theorems_and_proofs.md`. Three RQs unchanged.

## 正式定位

该命题是一个 measurement / identification proposition。

不要包装成“深奥的大理论”。

其作用是明确说明：

> 一个 observational/static score 在没有额外结构假设时，不能识别模型在 intervention distributions 上的行为。

---

## Proposition 1

> **Proposition 1 (Static-Score Non-identification).**  
> Let \(A_f^S(J)\) denote the performance of judge \(J\) on an observational static evaluation distribution for factor \(f\), and let
>
> \[
> D_f(J)
> =
> \bigl(
> RA_f(J),
> II_f(J)
> \bigr)
> \]
>
> denote its behavioral response under matched relevant and irrelevant intervention distributions. Without additional structural assumptions linking behavior on the static and intervention distributions, \(A_f^S(J)\) does not point-identify \(D_f(J)\).

中文：

> **命题 1（静态分数不可识别性）**  
> 如果没有额外结构假设把 static evaluation distribution 上的行为与 relevant / irrelevant intervention distributions 上的行为连接起来，那么独立静态准确率 \(A_f^S(J)\) 无法 point-identify judge 的选择性视觉证据依赖 \(D_f(J)\)。

---

## 证明思路

1. \(A_f^S\) 仅约束 judge 在 static observational distribution 上的平均正确性；
2. \(RA_f\) 和 \(II_f\) 依赖 judge 在不同 intervention distributions 上的条件行为；
3. 除非额外假设这些分布上的行为存在结构联系，否则 static score 无法唯一恢复 intervention response；
4. 因此多个具有相同 \(A_f^S\) 的 judges 可以对应不同的 \(D_f\)。

形式上：

\[
A_f^S(J_1)
=
A_f^S(J_2)
\]

不推出：

\[
D_f(J_1)
=
D_f(J_2).
\]

---

# 10. Accuracy-equivalence Class

为了连接理论与实证，定义观测模型集合：

\[
\mathcal J_{\mathrm{obs}}.
\]

对 factor \(f\) 和 tolerance \(\epsilon\)，定义：

\[
\mathcal E_{f,\epsilon}
=
\left\{
(J_i,J_j):
|A_f^S(J_i)-A_f^S(J_j)|
\leq
\epsilon
\right\}.
\]

定义 observed RA dispersion：

\[
\widehat{\Delta}_{RA,f}(\epsilon)
=
\left\{
|RA_f(J_i)-RA_f(J_j)|:
(J_i,J_j)\in
\mathcal E_{f,\epsilon}
\right\}.
\]

可以报告：

\[
\operatorname{median}
\widehat{\Delta}_{RA}(\epsilon)
\]

以及：

\[
\max
\widehat{\Delta}_{RA}(\epsilon).
\]

可以定义有限观测模型集合上的 empirical behavioral diameter：

\[
\widehat{\operatorname{Diam}}_{RA}
(\mathcal E_{f,\epsilon})
=
\max_{(J_i,J_j)\in\mathcal E_{f,\epsilon}}
|RA_f(J_i)-RA_f(J_j)|.
\]

---

## 重要限制

不得写：

\[
\lim_{\epsilon\to0}
\operatorname{Diam}
(\mathcal E_{\epsilon})
>0
\]

因为：

- 模型集合有限；
- exact-zero pair 只有一组；
- 没有 asymptotic evidence。

允许写：

> In the observed model set, behavioral dispersion remains nonzero even under exact static-accuracy matching.

以及：

> As a post-hoc sensitivity analysis, substantial RA dispersion remains across the examined matching tolerances.

---

# 11. 主 Claim Hierarchy

所有论文主张按以下强弱顺序冻结。

---

## C1 — 核心理论／测量结论

### Strong claim

> **Static preference accuracy does not, in general, identify selective visual evidence dependence.**

中文：

> **静态 preference accuracy 在一般情况下无法识别 multimodal judge 的选择性视觉证据依赖。**

理论形式：

\[
\boxed{
A_f^S(J)
\not\Rightarrow
D_f(J).
}
\]

---

## C2 — 方法结论

### Strong claim

> RewardLens uses controlled relevant and irrelevant visual interventions to make selective visual evidence dependence behaviorally observable.

中文：

> RewardLens 通过任务相关与任务无关的受控视觉干预，使被静态准确率压缩的选择性视觉证据依赖行为变得可观测。

---

## C3 — 主实证结论

### Strong claim

> Real multimodal judges with identical or nearly identical static accuracy can exhibit materially different relevant adaptation.

中文：

> 真实 multimodal judges 即使拥有相同或近似相同的静态 accuracy，也可以表现出显著不同的 relevant adaptation。

---

## C4 — Behavioral decomposition

### Strong but post-hoc-supported conceptual result

> Correctness, correctness preservation, and literal decision stability are distinct behavioral observables.

形式：

\[
\boxed{
\text{Static correctness}
\neq
\text{intervention-conditioned correctness}
\neq
\text{decision stability}.
}
\]

---

## C5 — Downstream

### Secondary only

> RewardLens measures are descriptively associated with Best-of-N utility, but current evidence does not establish consistent predictive superiority over static accuracy.

不得提升为主 claim。

---

# 12. 主证据冻结

---

## Evidence 1 — Exact Static-Accuracy Tie

### Attribute: Phi vs LLaVA-OneVision

\[
\Delta A^S=0.
\]

同时：

\[
|\Delta RA|
=
15.1\text{ pp}.
\]

并且：

\[
\Delta pix_{\mathrm{relevant}}
=
0.118
\]

小于：

\[
\Delta pix_{\mathrm{irrelevant}}
=
0.179.
\]

因此：

> relevant intervention 的 edit magnitude 并没有比 irrelevant intervention 更大。

这是当前最干净的 headline example。

建议正文顺序：

> **先 Attribute exact tie，再 Spatial extreme effect。**

---

## Evidence 2 — Predeclared 1pp Matching Census

冻结 matching rule：

\[
|\Delta A^S|
\leq
1\text{ percentage point}.
\]

结果：

\[
n=7
\]

qualifying within-factor pairs。

其中：

\[
\operatorname{median}
|\Delta RA|
=
15.1\text{ pp}
\]

\[
\max
|\Delta RA|
=
38.6\text{ pp}.
\]

该结果保持原始主结果地位。

统一使用：

> **predeclared**

不得使用：

> preregistered

除非存在正式公开、带时间戳的 preregistration。

---

## Evidence 3 — Spatial Large-Effect Contrast

Skywork vs Phi：

\[
\Delta A^S
\approx
0.35\text{ pp}
\]

但：

\[
|\Delta RA|
=
38.6\text{ pp}.
\]

这是 observed 1pp set 中最大的 RA gap。

但必须同时报告 caveat：

> Spatial relevant edits on average exhibit larger pixel change than irrelevant edits.

因此 Spatial 是：

> strongest effect-size example

而不是：

> cleanest control example。

---

## Evidence 4 — Post-hoc Matching-Tolerance Sensitivity

结果：

| \(\epsilon\) | pairs | median \(|\Delta RA|\) | max \(|\Delta RA|\) | status |
|---:|---:|---:|---:|---|
| 0 | 1 | 15.1pp | 15.1pp | post-hoc |
| 0.5pp | 4 | 25.6pp | 38.6pp | post-hoc |
| **1pp** | **7** | **15.1pp** | **38.6pp** | **predeclared** |
| 2pp | 11 | 15.1pp | 38.6pp | post-hoc |
| 3pp | 15 | 15.1pp | 51.6pp | post-hoc |
| 5pp | 32 | 15.1pp | 51.6pp | post-hoc |

允许的总结：

> Behavioral dispersion remains substantial across the examined static-accuracy matching tolerances.

不允许：

> “\(\epsilon\to0\) 时 dispersion 不收敛。”

---

# 13. Joint Audit-State Decomposition

定义完整 audit behavior：

\[
\pi_{bri}
=
P(C_B=b,C_R=r,C_I=i)
\]

其中：

\[
b,r,i\in\{0,1\}.
\]

共有 8 个状态：

\[
000,\,
001,\,
010,\,
011,\,
100,\,
101,\,
110,\,
111.
\]

必须明确：

\[
\sum_{r,i}
\pi_{1ri}
=
A^B
\]

而不是：

\[
A^S.
\]

---

## 13.1 Base-correct 区域的四个关键状态

### 111

\[
B=1,R=1,I=1
\]

解释：

> base 正确、relevant 后仍正确、irrelevant 后仍正确。

可以理解为：

> fully successful audit state。

---

### 101

\[
B=1,R=0,I=1
\]

解释：

> base 正确；面对应该影响判断的 relevant change 时失败；面对 irrelevant change 时仍然正确。

这是当前 forensic 中最有信息的失败模式。

---

### 110

\[
B=1,R=1,I=0
\]

解释：

> 能适应 relevant change，但受到 irrelevant visual change 干扰。

---

### 100

\[
B=1,R=0,I=0
\]

解释：

> relevant adaptation 和 irrelevant invariance 均失败。

---

# 14. 八状态核心例子

---

## Qwen Count

\[
101=166
\]

\[
111=34
\]

总计：

\[
A^B=1.
\]

因此：

\[
RA
=
\frac{34}{200}
=
0.17.
\]

这个结果不能只写成：

> Qwen Count RA = 0.17.

更有解释力的是：

> 在 200 个 base-correct Count audit triplets 中，166 个集中于 101 状态：模型在 irrelevant change 后保持正确，但在真正需要改变判断的 relevant change 后没有正确适应。

---

## InternVL Count

类似地：

\[
101=164
\]

\[
111=36.
\]

说明低 RA 主要由相关变化下 failure 构成，而不是 irrelevant instability。

---

## Gemma Spatial

\[
101=143
\]

\[
111=0.
\]

且：

\[
RA=0.
\]

解释：

> 在 base-correct Spatial cases 中，没有一例进入 111；绝大多数质量集中在 101，即 irrelevant 后仍正确，但 relevant 后不能正确适应。

---

## Qwen Attribute

\[
111=200.
\]

显示 Attribute 上可能接近饱和。

因此论文不能只看 aggregated RA/II，还要展示 factor × model 的 behavioral-state structure。

---

# 15. Prediction Dynamics

定义：

\[
\hat Y_B,\hat Y_R,\hat Y_I
\]

分别为模型在 base、relevant、irrelevant variant 上的实际 A/B prediction。

定义：

\[
F_R
=
P(\hat Y_R\neq\hat Y_B)
\]

\[
F_I
=
P(\hat Y_I\neq\hat Y_B).
\]

---

# 16. Correctness Change 与 Prediction Change

必须区分：

\[
C_R\neq C_B
\]

和：

\[
\hat Y_R\neq\hat Y_B.
\]

二者不是同一事件。

这是 RQ3 的核心。

---

## Example — Qwen Attribute

\[
F_R=1.
\]

即 relevant intervention 后：

> 100% 改预测。

但是：

\[
\text{correctness change}=0.
\]

原因：

> relevant visual evidence 改变后，gold preference 也改变；模型同步改变答案，因此 correctness 保持正确。

---

## Example — Qwen Count

\[
F_R=0.17.
\]

即：

> 只有 17% 的 relevant intervention 后真正换预测。

但：

\[
\text{correctness change}=0.83.
\]

因此：

> 83% 样本里，模型预测本身没有变化，但因为 relevant intervention 已经改变了正确答案，模型从正确变成错误。

这支撑：

\[
\boxed{
\text{staying invariant can itself be the failure.}
}
\]

---

# 17. Irrelevant Flip

因为：

\[
gold_I\equiv gold_B
\]

所以 irrelevant intervention 的理想行为通常是：

\[
\hat Y_I=\hat Y_B.
\]

但：

\[
II
\]

只条件在：

\[
C_B=1.
\]

而：

\[
F_I
\]

覆盖所有 complete triplets。

因此可以出现：

> high II but non-trivial prediction instability。

例如：

Gemma Spatial：

\[
II=0.979
\]

但：

\[
F_I=16.5\%.
\]

说明：

> correctness-conditioned invariance 与 literal decision stability 是不同的 measurement objects。

---

# 18. 数据身份与完整性

论文内部不需要展开全部 forensic history，但必须保证方法与 Appendix 可解释 physical disjointness。

冻结事实：

\[
\boxed{
\mathcal I_{\text{Audit-source}}
\cap
\mathcal I_{\text{Downstream}}
=
\varnothing
}
\]

且最终：

- Audit PNG SHA 与 downstream image SHA：0 overlap；
- logical ID：0 overlap；
- source_id：0 overlap；
- image_id：0 overlap。

Audit：

> 从 CLEVR / Blender 空白 scene 程序化生成。

不是：

> GQA / COCO / TallyQA 自然图片的重渲染。

Downstream：

> 使用 GQA / VG / TallyQA 等自然图像 source。

因此：

> Audit 与 Downstream 不进行 item-level join。

任何 future analysis 都不得仅凭数字 `example_id` 进行跨 split 对齐。

---

# 19. 一个必须记录的历史完整性教训

早期 Downstream v1：

- logical ID overlap = 0；
- physical SHA overlap = 196。

原因主要是：

> TallyQA `vg:1032` 与 GQA `1032` 指向相同 VG image bytes。

冻结 Downstream v2 在替换 197 行后：

\[
physical\ overlap=0.
\]

该问题已经修复。

论文正文无需详细讲历史版本。

可以在 Artifact / Appendix 说明：

> final frozen manifests were verified using physical image hashes rather than logical identifiers alone。

---

# 20. 不得混淆 Audit Carrier

HF / archive 中曾出现：

- Count audit 标记为 `carrier=tallyqa`
- 其他 factor 标记为 `gqa`

该字段是历史 metadata 误标。

Audit 实际是：

> CLEVR / Blender controlled render。

因此：

> `carrier` 字段不得用于 audit physical source identity。

后续 public artifact 应做 metadata correction。

---

# 21. Pair Graph 的论文地位

Pair graph analysis 明确标记：

> **exploratory**

当前发现包括：

- Skywork 使用 scalar scoring，因此 tournament 结构天然 transitive；
- cycle rate = 0；
- Condorcet frequency = 1；
- generative pairwise judges 存在大量 triangle cycles；
- 部分模型 pool cycle frequency 可达到 58%–96%；
- Molmo 最不稳定；
- N2/N4/N8 selection stability 存在明显差异。

但这些结果研究的是：

> pairwise preference coherence

而不是：

> selective visual evidence dependence。

因此：

- 不进入主 RQ；
- 不进入主 conclusion；
- 最多 Appendix；
- 正文最多一句 exploratory note。

---

# 22. Deployment / Commercial Interpretation

允许在 Discussion 中解释 RewardLens 的实际意义，但不得声称已经估计真实商业损失。

可以定义 conditional intervention risk：

\[
R_{\mathrm{int}}(J\mid B=1)
=
\sum_f
\pi_f^r L_f^r
\bigl(
1-RA_f(J)
\bigr)
+
\sum_f
\pi_f^i L_f^i
\bigl(
1-II_f(J)
\bigr).
\]

其中：

- \(\pi_f^r\)：相关变化在某部署环境中的权重；
- \(L_f^r\)：相关变化 adaptation failure 的业务损失；
- \(\pi_f^i\)：无关变化发生权重；
- \(L_f^i\)：受到无关变化干扰的业务损失。

允许的推论：

> 两个 static-accuracy-equivalent judges，如果 \(D_f\) 不同，那么在某些合法 deployment weighting 下可以具有不同的 conditional intervention risk。

因此：

\[
\boxed{
\text{same static accuracy}
\notRightarrow
\text{same deployment suitability}
}
\]

只能写：

> can incur deployment selection regret

不能写：

> will incur deployment regret。

这部分是 Decision Implication，不是主实验结果。

---

# 23. 论文主图冻结

---

## Figure 1 — RewardLens Measurement Setup

目标：

> 一张图说明 static benchmark 与 intervention audit 的不同。

建议结构：

### Left

Static evaluation：

\[
X
\rightarrow
J
\rightarrow
\hat Y
\]

输出：

\[
A^S.
\]

### Right

RewardLens audit：

```text
Base B
  |
  |-- Relevant intervention --> R
  |
  └-- Irrelevant intervention -> I
```

输出：

\[
RA,\ II
\]

以及：

\[
\pi(B,R,I).
\]

图中明确：

\[
A^S\neq A^B.
\]

---

## Figure 2 — Same Accuracy, Different Intervention Behavior

### Panel A — Accuracy-equivalence scatter

横轴：

\[
|\Delta A^S|
\]

纵轴：

\[
|\Delta RA|.
\]

重点标记：

* Phi vs LLaVA Attribute；
* Skywork vs Phi Spatial；
* predeclared 1pp region。

---

### Panel B — Matching-tolerance sensitivity

横轴：

\[
\epsilon
=
0,\ 0.5,\ 1,\ 2,\ 3,\ 5
\]

纵轴：

\[
\operatorname{median}
|\Delta RA|
\]

可同时显示 max。

必须明确：

> 1pp = predeclared primary analysis

其他：

> post-hoc sensitivity。

---

### Panel C — Joint Audit-State Decomposition

使用 stacked bar，而不是复杂 Sankey。**不要把 prediction-flip 塞进 Figure 2。** Figure 2 停在 joint correctness；Figure 3 才是 correctness response \(\neq\) prediction response。

Legend 写 correctness states，不写 prediction mechanism：

```text
111 — correct on B, R, I
101 — correct on B and I, wrong on R
other states
```

Caption 再解释：Under the binary RewardLens construction, a base-correct 101 case corresponds to retaining the base decision when the relevant intervention flips the gold preference.

柱顺序冻结为 narrative pairing：

```text
LLaVA Attribute | Phi Attribute
Qwen Attribute  | Qwen Count
InternVL Count  | Gemma Spatial
```

经验计数用 \(N_{bri}\)；Section 3 理论继续用 \(\pi_{bri}\)。

重点颜色突出 \(101\) 与 \(111\)。

**冻结 caption。**

> **Figure 2: Same accuracy, different intervention behavior.**
> **(a)** Pairwise gaps in independent static accuracy \(A^S\) and Relevant Adaptation (RA) for within-factor judge pairs. Red markers denote pairs satisfying the predeclared \(|\Delta A^S|\le 1\) pp rule. Phi–LLaVA on Attribute form an exact static-accuracy tie but differ by 15.1 pp in RA; Skywork–Phi on Spatial differ by 0.35 pp in static accuracy and 38.6 pp in RA.
> **(b)** Median and maximum \(|\Delta RA|\) among qualifying pairs across the examined matching tolerances. The 1 pp threshold is the predeclared primary analysis; all other tolerances are post-hoc sensitivity analyses.
> **(c)** Joint correctness-state counts for representative model–factor cells. State \(111\) denotes correctness on base, relevant, and irrelevant conditions; state \(101\) denotes base correctness and irrelevant correctness but failure after the relevant intervention. Gray contains the remaining six joint states. The panel illustrates joint-state structure rather than introducing a new scalar metric.

---

# 24. Figure 3 — Correctness vs Decision Stability

Drawn 2026-09-16 from Lemma 4. File: `rewardlens/paper/figures/fig3_correctness_vs_prediction.{pdf,png,svg}`. Script: `rewardlens/scripts/make_fig3_lemma4.py`. Frozen forensics only. Do not merge into Figure 2. Do not change Section 3 theory.

**(a)** Geometry of \(\Delta C=\Delta Y\oplus\Delta G\). Gold stays \(\Rightarrow\) \(\Delta C=\Delta Y\); gold flips \(\Rightarrow\) \(\Delta C=1-\Delta Y\).

**(b)** All 32 relevant model–factor cells lie on \(P(\Delta C_R=1)=1-F_R\) (exact: max \(|F_R+\Delta C_R-1|=0\)). Qwen Attribute, Qwen Count, Gemma Spatial annotated.

**(c)** Same identity, two realizations: Qwen Attribute \(F_R=1\), \(\Delta C=0\); Qwen Count \(F_R=0.17\), \(\Delta C=0.83\).

主结论：

\[
\boxed{
\text{prediction change and correctness change are distinct.}
}
\]

When gold flips they are not merely distinct: they are complementary.

---

# 25. Results 章节冻结结构

## 5.1 Equal Static Accuracy Can Hide Different Relevant Adaptation

首先讲：

Phi vs LLaVA Attribute：

\[
\Delta A^S=0
\]

\[
|\Delta RA|=15.1pp.
\]

强调：

\[
\Delta pix_{rel}
<
\Delta pix_{irr}.
\]

这是论文最干净的 empirical witness。

---

## 5.2 Near-Accuracy Matches Show Substantial Behavioral Dispersion

讲 predeclared：

\[
|\Delta A^S|\le1pp.
\]

结果：

\[
n=7
\]

\[
median|\Delta RA|=15.1pp
\]

\[
max|\Delta RA|=38.6pp.
\]

Spatial Skywork–Phi 作为 maximum effect。

---

## 5.3 Sensitivity to the Accuracy-Matching Tolerance

明确 post-hoc。

报告：

\[
\epsilon=0\rightarrow5pp.
\]

不得重新选择新的“最佳 threshold”。

---

## 5.4 Joint Intervention States Reveal What Marginal Metrics Collapse

展示：

\[
\pi(B,R,I).
\]

重点：

\[
101
\]

vs：

\[
111.
\]

解释低 RA 是由哪些具体行为状态构成。

---

## 5.5 Correctness and Decision Stability Are Distinct

展示：

\[
F_R,F_I.
\]

重点使用 Qwen Count / Attribute。

核心句：

> Changing the answer can be exactly the correct behavior under a relevant intervention, while remaining invariant can itself be the failure.

---

## 5.6 Secondary Downstream Diagnostic

Best-of-N。

必须克制。

不要用：

> RewardLens predicts utility better than accuracy.

---

# 26. Discussion 需要回答的四个问题

---

## D1. RewardLens 到底测什么？

回答：

> behavioral selective visual evidence dependence。

不是：

> internal causal grounding。

---

## D2. 为什么 static accuracy 不够？

因为 static outcome score 只观察：

> 一个静态 distribution 上的 correctness。

而 intervention audit 观察：

> 模型面对证据变化时如何改变或保持自己的行为。

---

## D3. 为什么不是所有 invariance 都好？

因为：

\[
Relevant
\Rightarrow
Adapt
\]

\[
Irrelevant
\Rightarrow
Remain\ invariant.
\]

“稳定”不是 universal objective。

“selective stability” 才是。

---

## D4. 为什么商业部署会关心？

因为不同场景对：

* spatial failure；
* attribute failure；
* presence failure；
* irrelevant sensitivity

具有不同业务成本。

所以：

\[
\text{equal accuracy}
\]

并不保证：

\[
\text{equal deployment suitability}.
\]

---

# 27. Limitations

必须主动写。

---

## L1 — Behavioral, not mechanistic

RewardLens 不识别：

* internal causal mechanism；
* latent representation；
* attention causal role；
* “模型到底在内部看了什么”。

它只测：

> intervention-level observable behavior。

---

## L2 — Spatial Edit Magnitude

Spatial relevant edits 平均比 irrelevant edits大。

因此：

> Spatial headline effect 不能被描述为已经排除了 intervention magnitude confound。

Attribute exact-tie 是更干净的 supporting case。

---

## L3 — Cross-factor Carrier Confound

Count 与其他 factors 的 independent static carrier 不同。

因此：

> cross-factor numerical differences 不能被直接解释为 factor 的 causal effect。

---

## L4 — Eight Models for Downstream Inference

八模型足以：

> 展示 empirical existence / accuracy-equivalent contrasts。

但不足以：

> 做强 downstream predictive-validity claim。

因此 RQ2 legacy regression 保持 secondary。

---

## L5 — Human Intervention Validity

如果 dual-human audit 在截稿前完成：

> 报告真实结果。

如果未完成：

> 明确写 frozen annotation package exists but full human validation remains pending。

绝不能伪造。

---

## L6 — Orientation Swap

如果 orientation swap 未完成：

> 明确作为 robustness limitation。

不得隐含已经验证 reciprocal consistency。

---

# 28. 明确禁止的表述

正文、摘要、图注、Conclusion 全文搜索并禁止以下表达：

```text
RewardLens measures true visual reasoning
RewardLens proves the judge uses the correct visual evidence internally
correct for the right visual reason
true grounding
causal grounding
internal grounding
RewardLens outperforms accuracy
RewardLens predicts Best-of-N better than accuracy
independent predictive validity beyond accuracy
PFC predicts utility better than accuracy
factor causes the behavioral difference
Spatial magnitude confound is ruled out
preregistered
```

除非未来真的有相应证据。

---

# 29. 推荐替代表述

统一使用：

```text
selective visual evidence dependence
behavioral evidence dependence
interventional behavior
controlled visual intervention
relevant adaptation
irrelevant invariance
behavioral diagnostic
measurement dimension
static-score non-identification
accuracy-equivalent judges
joint intervention-state structure
decision stability
post-hoc sensitivity analysis
predeclared matching rule
secondary downstream diagnostic
```

---

# 30. Introduction 的逻辑顺序

Introduction 不先写历史综述。

第一段直接提出反直觉问题：

> Multimodal evaluation should not simply reward stable judgments. A judge should remain stable when irrelevant visual evidence changes, but should change when the evidence that determines the correct preference changes.

第二段：

> Conventional preference accuracy cannot distinguish these behaviors.

第三段提出：

\[
A^S
\not\Rightarrow
D.
\]

第四段介绍 RewardLens：

\[
Relevant
\rightarrow
Adapt
\]

\[
Irrelevant
\rightarrow
Invariant.
\]

第五段给最强 empirical result：

\[
\Delta A^S=0
\]

但：

\[
|\Delta RA|=15.1pp.
\]

再给 1pp census：

\[
n=7,
\quad
median=15.1pp.
\]

第六段列 contributions。

---

# 31. Introduction 最重要的反直觉句

建议保留：

> **For multimodal judges, being equally accurate does not imply behaving equivalently when the visual evidence changes.**

以及：

> **Invariance is desirable only when the changed evidence is irrelevant; when relevant evidence changes, staying invariant can itself be the failure.**

这两句承担论文“让 reviewer 想继续读”的作用。

---

# 32. Contributions 最终建议

控制在 3–4 条。

---

## Contribution 1 — Measurement Problem

> We formalize a limitation of static preference evaluation: static accuracy does not, in general, identify selective visual evidence dependence.

---

## Contribution 2 — RewardLens Audit

> We introduce RewardLens, a controlled intervention audit that separates Relevant Adaptation from Irrelevant Invariance.

---

## Contribution 3 — Empirical Non-identification

> Across eight multimodal judges, models with identical or nearly identical static accuracy exhibit substantial differences in relevant adaptation.

证据：

\[
\Delta A^S=0
\Rightarrow
|\Delta RA|=15.1pp
\]

以及：

\[
|\Delta A^S|\le1pp
\Rightarrow
median|\Delta RA|=15.1pp.
\]

---

## Contribution 4 — Behavioral Decomposition

> We show that correctness-based summaries further collapse distinct decision dynamics, which can be recovered through joint intervention states and prediction-flip analysis.

---

# 33. Abstract 的信息顺序

Abstract 最后写。

必须包含：

1. Problem；
2. selective adaptation / invariance；
3. exact accuracy tie；
4. predeclared 1pp census；
5. RewardLens 是 complementary behavioral diagnostic；
6. 不把 downstream superiority 当 headline。

Abstract 不再突出：

* PFC；
* PSC；
* RQ3 legacy；
* 复杂 downstream regression；
* pair graph。

---

# 34. Related Work 要形成的四个区分

Related Work 必须回答 RewardLens 和以下工作有什么不同：

### 1. Multimodal reward benchmarks

它们主要回答：

> judge 是否选对。

RewardLens：

> judge 对 relevant / irrelevant visual evidence change 如何响应。

---

### 2. Visual grounding / shortcut work

RewardLens 不声称识别 internal grounding。

它做的是：

> controlled behavioral intervention audit。

---

### 3. Robustness / invariance work

普通 robustness 常默认：

> prediction invariance 是 desirable。

RewardLens 的区别：

> invariance 只对 irrelevant changes desirable；relevant changes 应产生 adaptation。

---

### 4. Judge / reward-model downstream utility

RewardLens 不把：

> better downstream prediction

作为成立前提。

它首先是：

> measurement diagnostic。

---

# 35. 主模型集合冻结

最终八模型：

1. Qwen3-VL-4B-Instruct
2. Gemma-3-4B-it
3. Molmo-7B-D-0924
4. Skywork-VL-Reward-7B
5. Idefics3-8B-Llama3
6. Phi-3.5-Vision-Instruct
7. LLaVA-OneVision-Qwen2-7B
8. InternVL3-8B

不新增第 9 个模型。

---

# 36. 主实验规模冻结

每模型：

* Static：800
* Audit：2400
* Downstream pools：800
* Pair edges：22,400

不重新推理。

不改变：

* thresholds；
* manifests；
* frozen model outputs；
* matching definition；
* factor definitions。

---

# 37. Forensic 分析地位

所有：

`forensics_20260916`

分析均属于：

> **post-hoc forensic analysis of frozen Phase II artifacts**

它们：

* 不改变主实验；
* 不修改 manifest；
* 不改变 predeclared 1pp analysis；
* 不修改模型 outputs；
* 不产生新的训练或 inference。

进入正文时必须明确区分：

### Predeclared

1pp matching analysis。

### Post-hoc

* \(\epsilon=0,0.5,2,3,5\) sensitivity；
* eight-state decomposition；
* prediction flip；
* pair graph exploratory。

---

# 38. Artifact 修复

HF 中存在两个 metadata 问题。

---

## 38.1 Audit file path

前四模型：

`canonical_model_artifacts.csv`

历史上可能错误指向 800-row `static.jsonl`。

真正 audit 文件：

* Qwen：`qwen_full_audit.jsonl`
* 其他前四模型：`full_audit.jsonl`

修复方式：

> 追加 corrected manifest / metadata correction note。

不得静默覆盖历史证据。

说明：

> **Artifact metadata correction only; no experiment output, metric, manifest, or scientific result changed.**

---

## 38.2 Audit carrier

历史 archive 把：

* Count → tallyqa
* 其他 → gqa

误写到 Audit carrier。

实际 Audit：

> CLEVR / Blender procedural rendering。

需纠正 metadata。

---

# 39. 目前不再做的研究

从本文件冻结后，不再扩：

```text
第 9 个模型
新 benchmark
新 visual factor
新 main RQ
Audit ↔ BoN item-level join
更多模型级小样本 regression
事后寻找更漂亮 threshold
把 pair graph 拉成新论文主线
重新训练
重新跑 static
重新跑 audit
修改 manifests
修改主 metrics
```

---

# 40. 唯一还允许补的实验

如果时间允许，仅限 validation：

### P0

Human intervention-validity audit。

### P1

Orientation swap robustness。

这两项即使未完成，也不得阻塞 paper_v2 写作。

---

# 41. 建议最终章节结构

```text
1. Introduction

2. Related Work

3. Measurement Framework
   3.1 Static Preference Accuracy
   3.2 Relevant Adaptation and Irrelevant Invariance
   3.3 Selective Visual Evidence Dependence
   3.4 Proposition 1: Static-Score Non-identification

4. RewardLens
   4.1 Controlled Visual Interventions
   4.2 Factors and Triplet Construction
   4.3 Evaluation Protocol
   4.4 Models and Frozen Experimental Design
   4.5 Metrics and Denominators

5. Results
   5.1 Equal Static Accuracy Can Hide Different Relevant Adaptation
   5.2 Near-Accuracy Matches Show Substantial Behavioral Dispersion
   5.3 Sensitivity to Accuracy-Matching Tolerance
   5.4 Joint Intervention States Reveal What Marginal Metrics Collapse
   5.5 Correctness and Decision Stability Are Distinct
   5.6 Secondary Downstream Best-of-N Diagnostic

6. Discussion
   6.1 What RewardLens Measures
   6.2 Why Invariance Is Not Always Desirable
   6.3 Implications for Judge Selection and Deployment
   6.4 What RewardLens Does Not Establish

7. Limitations

8. Conclusion
```

Appendix：

```text
A. Full model × factor tables
B. Bootstrap details
C. Post-hoc equivalence sensitivity
D. Full eight-state distributions
E. Prediction-flip tables
F. Pair-graph exploratory analysis
G. Integrity / physical-disjoint audit
H. Intervention validity / orientation robustness
I. Artifact provenance
```

---

# 42. 论文写作顺序

不要从 Introduction 开始。

建议：

### Step 1

写：

> Section 3 — Measurement Framework

先把：

\[
A^S,\ A^B,\ RA,\ II,\ D_f
\]

和 Proposition 1 写死。

### Step 2

写：

> Section 5 — Results

只用冻结数据。

### Step 3

写：

> Section 4 — RewardLens Method

确保所有 denominator、parse failure、complete-triplet 规则与实现一致。

### Step 4

写：

> Discussion + Limitations

主动封闭 reviewer 攻击面。

### Step 5

写：

> Introduction。

### Step 6

写：

> Related Work。

### Step 7

最后重写：

> Abstract + Title + Conclusion。

---

# 43. 论文最终必须让 reviewer 记住的三句话

## 句子 1

> **Two multimodal judges can be equally accurate yet behave differently exactly when the visual evidence changes.**

---

## 句子 2

> **Invariance is desirable only for irrelevant changes; for relevant changes, staying invariant can itself be the failure.**

---

## 句子 3

> **RewardLens complements static preference accuracy by making intervention behavior observable rather than reducing judge quality to another scalar leaderboard score.**

---

# 44. 最终科学故事

论文最终的逻辑链应该只有这一条：

\[
\boxed{
\text{Static Preference Accuracy}
}
\]

↓

\[
\boxed{
\text{Identification Blind Spot}
}
\]

↓

\[
\boxed{
\text{Controlled Relevant / Irrelevant Interventions}
}
\]

↓

\[
\boxed{
RA / II
}
\]

↓

\[
\boxed{
\text{Exact / Near Accuracy Matches with Different Behavior}
}
\]

↓

\[
\boxed{
\pi(B,R,I)
\text{ and Prediction Dynamics}
}
\]

↓

\[
\boxed{
\text{Correctness}
\neq
\text{Correctness Preservation}
\neq
\text{Decision Stability}
}
\]

最终结论：

> **Static preference accuracy tells us whether a judge is correct on a frozen evaluation distribution. RewardLens reveals whether its behavior changes appropriately when the visual evidence itself changes. These are different measurement questions, and real multimodal judges that appear equivalent under the first can differ substantially under the second.**

中文：

> **静态 preference accuracy 告诉我们一个 judge 在冻结评测分布上是否答对；RewardLens 则观察当视觉证据本身发生相关或无关变化时，它的行为是否以正确的方式改变。二者回答的是不同的 measurement question，而现实中的 multimodal judges 即使在前者上看似等价，在后者上仍可能表现出显著差异。**

---

# 45. Blueprint Freeze

从本文件冻结后，论文的主目标不是继续“寻找更大的数字”，而是：

\[
\boxed{
\textbf{把已经得到的 identification failure 讲清楚、证明清楚、测量清楚。}
}
\]

论文成功的标准不是：

> RewardLens 是否在所有指标上战胜 static accuracy。

而是：

> Reviewer 是否相信：
>
> 1. static accuracy 无法识别 intervention behavior；
> 2. RewardLens 测量的是一个清晰、不同且合理的 behavioral dimension；
> 3. 这种差异在真实 multimodal judges 中不仅存在，而且幅度足够大；
> 4. 该差异对于模型评估与部署选择具有现实意义；
> 5. 作者没有把 behavioral intervention evidence 夸大成内部 causal grounding。

如果这五点成立，RewardLens 就是一篇完整的 measurement / identification paper，而不是另一个普通 benchmark。

---

# 46. Theory upgrade (2026-09-16) — four formal results

Figure 2 remains frozen. Three RQs remain frozen. No new models, data, or RQs.

Proposition 1 (“\(A_f^S\) does not identify \(D_f\)”) is **superseded as the main-text statement** by four results, with complete proofs in `section3_theorems_and_proofs.md` and compact statements in `iclr2027_paper_v2.md` §3.

| Result | Role | Empirical witness |
|---|---|---|
| **Theorem 1** Identification fiber | \(D_f\) identified by \(A^S\) iff \(D_f\) constant on every \(\mathcal F_f(a)\) | Phi–LLaVA Attribute exact tie, \(\lvert\Delta\mathrm{RA}\rvert=15.1\) pp |
| **Proposition 2** Reconstruction lower bound | any \(h(A^S)\) of RA errs \(\ge\delta/2\) on an exact tie | \(\delta=15.1\) pp \(\Rightarrow\) \(\ge 7.55\) pp |
| **Proposition 3** Sharp Fréchet set for \(q_{11}\) | \(\max(0,RA+II-1)\le z\le\min(RA,II)\), sharp | Qwen Count \(z=\{0.17\}\) (Figure 2c localizes; not a non-id proof) |
| **Lemma 4** Binary response algebra | \(\Delta C_X=\Delta Y_X\oplus\Delta G_X\) | Qwen Attribute vs Qwen Count; Figure 3 grows from this lemma |

Chain (unchanged RQs):

\[
\text{Measurement maps}
\to
\text{Fiber characterization}
\to
\text{Reconstruction LB}
\to
\text{Sharp partial ID of joint}
\to
\text{Binary response algebra}
\]

Results supply witnesses. Figure 3 is drawn from Lemma 4; it is not part of Figure 2.

**Wording freeze.** Do not write “magnitude-matched edits.” Use **design-matched** / **structurally matched** relevant and irrelevant edits. Pixel-change is a diagnostic. Spatial \(0.375\) vs \(0.265\) is a realized pixel gap, not a protocol contradiction.

**Section 3 outline (replaces §41 item 3.4 only):**

```text
3.1 Two accuracies
3.2 Factor-specific interventional profile
3.3 Measurement maps and identification fibers (Theorem 1)
3.4 Accuracy-only reconstruction lower bound (Proposition 2) + \(\mathcal E_{f,\epsilon}\)
3.5 Sharp partial identification of joint correctness (Proposition 3)
3.6 Binary response algebra (Lemma 4)
```

Appendix adds the full proofs file. RQ1 is still Identification; it is now answered by Theorem 1 + Proposition 2, not by a one-line non-identification slogan.
