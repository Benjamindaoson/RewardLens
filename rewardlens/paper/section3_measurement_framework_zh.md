# 第 3 节　Measurement Framework（中文母稿）

> 依据 `PAPER_BLUEPRINT.md` 撰写，并按 2026-09-16 理论升级对齐英文 `iclr2027_paper_v2.md` 第 3 节。完整陈述与证明见 `section3_theorems_and_proofs.md`。禁止使用模糊符号 \(A\)，禁止写 \(PFC=A^S\cdot RA\)，禁止把 RewardLens 写成内部因果 grounding。三个 RQ 不变。Figure 2 冻结。Figure 3 从 Lemma 4 长出，本节不画图。

---

一个 multimodal judge \(J\) 接收图像、问题与一对候选回答，并输出 pairwise preference \(\hat Y\in\{A,B\}\)。视觉因素

\[
f\in\{\text{Count},\ \text{Attribute},\ \text{Spatial},\ \text{Presence}\}.
\]

本章的全部对象都带 factor 下标。经验匹配、等价类与识别命题都是 **within-factor** 的。Count 的独立 static source 是 TallyQA，其余三个因素是 GQA。

本章回答 RQ1：**静态 preference accuracy 能否识别 judge 对任务相关与任务无关视觉变化的选择性响应？** 答案由四个结果组成：

\[
\text{Measurement maps}
\ \to\
\text{Fiber characterization}
\ \to\
\text{Reconstruction lower bound}
\ \to\
\text{Sharp partial identification}
\ \to\
\text{Binary response algebra}.
\]

Results 只负责给现实 witness，不新增 RQ。

---

## 3.1　独立静态准确率与 audit-base 准确率

**独立静态准确率。** \(A_f^S(J)\) 是 \(J\) 在因素 \(f\) 所对应的**独立冻结 static benchmark** 上的 pairwise preference accuracy。Audit 的 base 图像从不进入 \(A_f^S\)。冻结 confirmatory plan 里的符号 \(A\)，在本文中一律写作 \(A_f^S\)。

**Audit-base 准确率。** 每个受控样本是 triplet \((B,R,I)\)。记正确性

\[
C_B,C_R,C_I\in\{0,1\}.
\]

\[
A_f^B(J)=P(C_B=1).
\]

必须始终称为 **audit-base accuracy**，不得称为 static accuracy。在冻结八模型四因素上，\(A_f^S\neq A_f^B\) 对全部 32 个条目成立。禁止写 \(PFC=A^S\cdot RA\)。

---

## 3.2　选择性视觉证据依赖

\[
RA_f(J)=P(C_R=1\mid C_B=1),\qquad
II_f(J)=P(C_I=1\mid C_B=1).
\]

\[
D_f(J)=\bigl(RA_f(J),\ II_f(J)\bigr).
\]

\(D_f\) 是 RewardLens 的测量对象：**behavioral selective visual evidence dependence**。它不识别内部注意力或真实推理轨迹。

\[
PFC=A^B\cdot RA,\qquad PSC=A^B\cdot II.
\]

八状态

\[
\pi_{bri}=P(C_B=b,C_R=r,C_I=i).
\]

经验计数记 \(N_{bri}\)。RA / II 是 base-correct 2×2 的边际投影；它们约束、但一般不能识别联合耦合（命题 3）。

---

## 3.3　定理 1：识别纤维

定义 measurement maps

\[
\mathcal A_f(J)=A_f^S(J),\qquad
\mathcal D_f(J)=D_f(J)=\bigl(RA_f(J),II_f(J)\bigr).
\]

Accuracy fiber：

\[
\mathcal F_f(a)=\bigl\{J:\mathcal A_f(J)=a\bigr\}.
\]

称 \(D_f\) 被 \(A_f^S\) 识别，当且仅当存在 \(g:[0,1]\to[0,1]^2\) 使 \(\mathcal D_f=g\circ\mathcal A_f\)。

**定理 1（Identification Fiber）。** \(D_f\) 被 \(A_f^S\) 识别，当且仅当 \(D_f\) 在每一个 \(\mathcal F_f(a)\) 上为常数。

这比“\(A_f^S\) 不识别 \(D_f\)”强：它给出必要且充分条件。

**推论（经验证书）。** 若存在 exact tie \(A_f^S(J_1)=A_f^S(J_2)\) 且 \(D_f(J_1)\neq D_f(J_2)\)，则不可识别。Phi–LLaVA 在 Attribute 上 \(A^S=0.805\)，\(|\Delta RA|=15.1\) pp，因此观测纤维上 \(D_f\) 不是常数。标题 *Same Accuracy, Different …* 就是这条定理的反例证书。

\(\mathcal E_{f,\epsilon}\) 是 exact fiber 的容差邻域，是经验装置。定理 1 谈的是 exact fiber。不写 \(\lim_{\epsilon\to 0}\mathrm{Diam}>0\)。Predeclared 主带仍是 \(\epsilon=1\) pp。

---

## 3.4　命题 2：仅用准确率重构的下界

设任意 \(h:[0,1]\to[0,1]\) 试图只从 \(A^S\) 恢复 RA。若 \(A_1=A_2=a\) 且 \(|RA_1-RA_2|=\delta\)，则

\[
\max\bigl\{|RA_1-h(a)|,\ |RA_2-h(a)|\bigr\}\ \ge\ \frac{\delta}{2},
\]

因为 \(\delta\le |RA_1-h(a)|+|RA_2-h(a)|\)。

Attribute exact tie 给出 \(\delta=15.1\) pp，因此任何只从 static accuracy 恢复 RA 的函数，在这两个模型中至少一个上误差

\[
\ge 7.55\text{ pp}.
\]

中点预测器达到该界。这比“accuracy 不完整”更有理论重量。它不声称没有其他协变量能重构 RA。

---

## 3.5　命题 3：联合正确性状态的 sharp 部分识别

条件于 \(B=1\)，令 \(q_{ri}=P(R=r,I=i\mid B=1)\)，\(z=q_{11}\)。则

\[
q_{11}=z,\quad q_{10}=RA-z,\quad q_{01}=II-z,\quad q_{00}=1-RA-II+z.
\]

非负性恰好给出 Fréchet–Hoeffding 界，且区间 **sharp**：

\[
\max(0,RA+II-1)\ \le\ z\ \le\ \min(RA,II).
\]

因此，给定 \((RA,II)\)，base-correct 联合状态被部分识别，耦合有一个自由度。

- Qwen Count：\(RA=0.17\)，\(II=1\)，故 \(z\in\{0.17\}\)。联合状态被唯一确定。Figure 2(c) 是 **localization / interpretation**，不是 joint-nonidentification 的证明。
- Gemma Spatial：\(RA=0\)，故 \(z=0\) 唯一。
- Phi Attribute：\(RA=0.849\)，\(II=0.892\)，故 \(z\in[0.741,0.849]\)，区间非退化。

---

## 3.6　引理 4：二元响应代数

\[
\Delta Y_X=\mathbf 1[\hat Y_X\neq\hat Y_B],\qquad
\Delta G_X=\mathbf 1[Y_X\neq Y_B],\qquad
\Delta C_X=\mathbf 1[C_X\neq C_B].
\]

对 binary A/B judge，逐样本恒等式

\[
\Delta C_X=\Delta Y_X\oplus\Delta G_X.
\]

无关干预 \(\Delta G_I=0\) 立即得到 \(\Delta C_I=\Delta Y_I\)。相关、gold 翻转的干预 \(\Delta G_R=1\) 得到 \(\Delta C_R=1-\Delta Y_R\)。这就是最反直觉那句的严格形式：

> when gold flips, staying invariant is exactly the correctness failure.

Qwen Attribute（\(F_R=1\)，correctness change \(=0\)）与 Qwen Count（\(F_R=0.17\)，correctness change \(=0.83\)）是同一引理的两个经验实现。Figure 3 应从本引理长出，不进入 Figure 2。引理只用标签集为二元；它不从 \(\pi_{bri}\) 恢复 \(F_R,F_I\)。

---

## 3.7　这些结果不说什么

- 不识别内部因果 grounding。
- 不声称 \(A^S\) 无用。
- 不声称 RA/II 在 Best-of-N 上优于 \(A^S\)。
- 命题 3 只关于 base-correct 2×2，不是含 \(C_B=0\) 的完整八状态。
- 定理 1 相对于指定的类 \(\mathcal J\)；八模型集合是一个类，不是所有可能 judges。

---

**本节冻结的对象。** \(A_f^S\)、\(A_f^B\)、\(RA_f\)、\(II_f\)、\(D_f\)、\(\mathcal A_f\)、\(\mathcal D_f\)、\(\mathcal F_f(a)\)、\(\pi_{bri}\)、\(\mathcal E_{f,\epsilon}\)。

**本节冻结的四个结果。** 定理 1（纤维刻画）、命题 2（重构下界）、命题 3（Fréchet sharp set）、引理 4（XOR 代数）。

**方法如何把 \(D_f\) 变成可观测量**，是第 4 节的任务。第 4 节的 edits 称为 **design-matched / structurally matched**；pixel-change 只是 diagnostic。不写 magnitude-matched edits。
