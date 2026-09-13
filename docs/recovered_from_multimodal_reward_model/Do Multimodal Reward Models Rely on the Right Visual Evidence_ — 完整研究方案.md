# Do Multimodal Reward Models Rely on the Right Visual Evidence?

## Factor-Specific Visual Dependencies Beyond Preference Accuracy

中文暂定：

# 多模态奖励模型是否依赖了正确的视觉证据？

## 超越偏好准确率的因素级视觉依赖研究

---

# 1. 研究背景：我们到底发现了什么理论缺口？

这篇论文不是从“多模态 Reward Model 不够强”出发。

真正的问题是：

> **Reward Model 判断正确，与 Reward Model 因为正确的证据而判断正确，并不是同一个性质。**

现有 Reward Model evaluation 主要关心：

\[
\boxed{
\text{Did the reward model rank the preferred response higher?}
}
\]

例如 VL-RewardBench 主要通过 preference accuracy 评价 vision-language reward models，并发现这种 benchmark score 与 Best-of-N downstream performance 有很高相关性。

RewardBench 2 进一步系统证明，在文本 Reward Model 上，accuracy-based benchmark 与 Best-of-N、PPO 等实际 downstream use 存在较强相关，因此我们没有理由声称“preference accuracy 没意义”。

Multimodal RewardBench 2 又把这一结果扩展到 text-to-image、image editing、interleaved generation 和 multimodal reasoning，并同样发现 benchmark performance 与 downstream success 强相关。

所以现有研究已经建立了：

\[
\boxed{
\text{Preference Accuracy}
\longrightarrow
\text{Downstream Utility}
}
\]

至少在统计意义上，这是一个有价值的 predictor。

我们的论文**不挑战这个结论**。

---

# 2. 现有理论真正遗漏了什么？

这里有另一条很成熟的机器学习思想：

## Shortcut Learning

Geirhos 等人指出，一个模型可以在标准 benchmark 上得到很好的结果，却依赖一个错误的、非稳健的 shortcut decision rule；一旦环境改变，这些 shortcut 就会暴露。

另一条相关思想是：

## Right for the Right Reasons

Ross、Hughes 和 Doshi-Velez 早在 2017 年就提出：

> 模型不仅应该输出正确预测，还应该因为正确的输入特征而产生这个预测。

其工作通过约束模型 explanation 来减少错误特征依赖。

但是这两条思想主要研究：

\[
\boxed{
\text{Task Model}
}
\]

例如分类器、预测模型。

而 Reward Model 本质上是：

\[
\boxed{
\text{Evaluator of another model's output}.
}
\]

所以一个非常重要的问题一直没有被充分回答：

> **如果一个 Reward Model 本身正在使用错误的视觉证据进行判断，会发生什么？**

---

# 3. Multimodal Reward Model 已经出现这种迹象

最近研究已经说明这个问题不是假想的。

ICML 2025 的工作发现，Multimodal Reward Models 会依赖 text-only unimodal spurious correlations，从而降低 OOD generalization，并专门提出 shortcut-aware training 缓解这种问题。

VL-RewardBench 发现 VL reward models 的主要瓶颈很多时候首先来自基础视觉感知，而不是高级 reasoning。

2026 年的 Perception-Judge 更进一步指出，multimodal judges 可能已经正确感知图片，却仍然因为 response text 很合理而锚定在文本上，从而给视觉错误回答更高评价；他们称之为 Perceptual Judgment Bias。

CoNLL 2026 的研究也发现，Multimodal Reward Models 在数量、空间关系、方向等 physical-world constraints 上可能给出看似合理的 reward score，但其 reasoning 对关键视觉因素并不可靠。

SIVA-RL 则从被训练的 multimodal reasoning model 角度说明：

\[
\text{answer-level correctness}
\]

并不能保证：

\[
\text{correct visual grounding},
\]

并提出同时考虑 sensitivity 和 invariance。

---

# 4. 因此我们的理论缺口是什么？

现有研究分别证明了三件事：

\[
\text{A. Benchmark accuracy 与 downstream utility 有关系}
\]

\[
\text{B. Multimodal systems 会产生 visual shortcuts}
\]

\[
\text{C. Visual intervention 可以揭示 sensitivity / invariance}
\]

但是目前缺少把三件事真正连接起来的检验：

\[
\boxed{
\textbf{
Does a reward model's dependence on the right visual evidence provide information about its downstream usefulness beyond ordinary preference accuracy?
}
}
\]

也就是说：

> **模型为什么给出这个 Reward，是否本身就是 Reward Model quality 的一个独立维度？**

---

# 5. 我们是在挑战、修正还是发展什么理论？

严格来说，我不会在论文里声称：

> “我们推翻了某个理论。”

因为现有文献并没有一个正式理论声称：

\[
Preference\ Accuracy
\]

就是 Reward Model quality 的充分统计量。

我们真正做的是：

## 发展现有 Reward Model evaluation paradigm

现有主要关注：

\[
\boxed{
Outcome\ Validity
}
\]

也就是：

> Reward judgment 最后对不对？

我们增加一个新的评价层：

\[
\boxed{
Evidence\text{-}Dependence\ Validity
}
\]

即：

> Reward judgment 是否随着真正决定判断的视觉证据改变，并对与判断无关的视觉变化保持稳定？

因此我们的理论框架可以写成：

\[
\boxed{
\text{Reliable Reward}
=
\text{Correct Outcome}
+
\text{Correct Evidence Dependence}
}
\]

然后实验检验第二项是否在第一项之外具有实际价值。

所以这篇论文不是：

> **Preference accuracy is wrong.**

而是：

> **Preference accuracy may be informative but incomplete.**

这也是我们和 RewardBench 2 / Multimodal RewardBench 2 最重要的关系：

\[
\boxed{
\text{Complement, not contradict.}
}
\]

---

# 6. 论文母问题

最终冻结：

> **Do Multimodal Reward Models Rely on the Right Visual Evidence?**

我们研究的 carrier 是：

\[
\boxed{
\textbf{Multimodal Reasoning Reward / Judge}
}
\]

即：

\[
r_m(I,q,y)
\]

其中：

- \(I\)：图片；
- \(q\)：问题；
- \(y\)：候选回答；
- \(r_m\)：Reward Model / multimodal judge。

主论文不声称直接解决 image/video generation reward。

Image Editing 只作为 secondary external validation。

---

# 7. Research Questions

## RQ1 — Visual Dependency

> **Do similarly accurate multimodal reward models rely on different visual evidence?**

对于模型 \(m\) 和视觉因素 \(f\)，定义：

\[
A_{mf}
\]

为普通 static preference accuracy。

而：

\[
D_{mf}
\]

表示模型的视觉 dependency profile。

核心检验：

\[
\boxed{
A_{mf}\approx A_{m'f}
}
\]

时，是否仍可能：

\[
\boxed{
D_{mf}\gg D_{m'f}.
}
\]

如果成立，说明：

> 两个 benchmark accuracy 相似的 Reward Models，可能完全不是通过同一种视觉依据作判断。

---

## RQ2 — Incremental Downstream Validity

这是整篇论文最重要的问题。

> **Does factor-specific visual dependency explain downstream reward utility beyond static preference accuracy?**

定义：

\[
U_{mf}
\]

为模型 \(m\) 在视觉 factor \(f\) 上的 Best-of-N selection utility。

比较：

\[
\boxed{
U\sim A
}
\]

与：

\[
\boxed{
U\sim A+D.
}
\]

如果后者稳定优于前者，那么说明：

> visual dependency 中存在普通 preference accuracy 尚未捕获的 downstream-relevant information。

---

## RQ3 — Specificity

仅仅：

\[
D\rightarrow U
\]

还不够。

因为 dependency score 可能只是另一个“总体模型能力”指标。

因此我们进一步检验：

\[
\boxed{
D_{m,f}\rightarrow U_{m,f}
>
D_{m,f'}\rightarrow U_{m,f},
\quad f'\neq f.
}
\]

例如：

\[
D_{\text{count}}
\]

应该主要解释：

\[
U_{\text{count}},
\]

而不是 equally explain：

\[
U_{\text{spatial}}.
\]

如果得到这种近似 diagonal structure，就说明：

> 我们测到的确实是 factor-specific visual dependency。

---

## Optional RQ4 — Intervention-Aware Training

只有 RQ1–RQ3 成立以后才做。

> **Can intervention-aware training improve visual dependency and downstream reward utility without materially sacrificing static preference accuracy?**

它不是论文成立的必要条件。

---

# 8. 四个 Primary Visual Factors

第一篇只研究：

\[
\boxed{
Count
}
\]

\[
\boxed{
Attribute
}
\]

\[
\boxed{
Spatial
}
\]

\[
\boxed{
Presence
}
\]

暂时不把 OCR 纳入 primary analysis。

因为 OCR error 会混入：

\[
\text{text recognition failure}
\]

和：

\[
\text{evidence-dependence failure}.
\]

OCR 可以作为 appendix robustness。

---

# 9. 核心方法：Controlled Visual Intervention

固定：

\[
q,\ y_A,\ y_B.
\]

定义 Reward Margin：

\[
m_m(I)
=
r_m(I,q,y_A)
-
r_m(I,q,y_B).
\]

---

## 9.1 Relevant Intervention

只改变真正决定答案的视觉因素。

例如：

原图：

> 3 个 red cubes。

问题：

> How many red cubes are there?

回答：

\[
A=3,\quad B=4.
\]

原图：

\[
m(I)>0.
\]

把：

\[
3\rightarrow4
\]

得到：

\[
I_{\text{rel}}.
\]

那么正确行为应该是：

\[
\boxed{
m(I_{\text{rel}})<0.
}
\]

也就是 preference flip。

---

## 9.2 Irrelevant Intervention

改变同样量级、但不影响当前问题答案的视觉因素。

例如 Count：

Relevant：

\[
+1\ target\ red\ cube.
\]

Irrelevant：

\[
+1\ non\text{-}target\ blue\ sphere.
\]

两者都是：

\[
+1\ object.
\]

但只有前者应该影响回答。

因此：

\[
\boxed{
m(I_{\text{irr}})>0.
}
\]

也就是 preference stay。

---

# 10. Intervention Magnitude Matching

这是方法里非常重要的一部分。

我们不能比较：

> 增加整个 object

和：

> 改背景一小块颜色。

否则模型可能只是对视觉 perturbation 大小敏感。

因此：

| Factor | Relevant intervention | Matched irrelevant intervention |
|---|---|---|
| Count | +1 target object | +1 distractor object |
| Attribute | target red→blue | distractor red→blue |
| Spatial | move target until relation flips | move distractor similar distance |
| Presence | remove queried object | remove matched non-target object |

每个 intervention triplet 同时保存：

\[
\text{scene-graph edit distance}
\]

以及必要时：

\[
pixel\ difference,\ LPIPS,\ object\ area,\ displacement.
\]

这些量不定义 semantic relevance，只用于验证：

\[
\Delta_{\mathrm{rel}}
\approx
\Delta_{\mathrm{irr}}.
\]

---

# 11. Primary Metrics

不能只用一个指标。

## Joint Preference Flip Consistency

\[
PFC
=
P(
\text{base correct}
\land
\text{relevant intervention correct}
).
\]

## Joint Preference Stay Consistency

\[
PSC
=
P(
\text{base correct}
\land
\text{irrelevant intervention correct}
).
\]

这两个衡量实际 reliability。

同时报告：

## Conditional PFC

\[
PFC_{\mathrm{cond}}
=
P(
\text{relevant correct}
\mid
\text{base correct}
).
\]

## Conditional PSC

\[
PSC_{\mathrm{cond}}
=
P(
\text{irrelevant correct}
\mid
\text{base correct}
).
\]

它们回答：

> 在模型本来已经判断正确的情况下，它面对 intervention 是否仍表现出正确 dependency？

Joint 和 Conditional 必须同时保留。

---

# 12. 数据集来源

这里必须严格区分：

\[
D_{\text{static}},
D_{\text{audit}},
D_{\text{downstream}}.
\]

原则：

\[
\boxed{
D_{\text{static}}
\neq
D_{\text{audit}}
\neq
D_{\text{downstream}}.
}
\]

至少 image/question 完全 disjoint；能够使用不同数据源时优先不同数据源。

---

# 13. Dataset A — Controlled Audit

## CLEVR

**用途：Primary Intervention Audit。**

CLEVR 官方包含：

- 70,000 train images；
- 15,000 validation images；
- 15,000 test images；
- train/val scene graphs；
- object locations；
- attributes；
- relationships；
- functional programs；
- 官方 Blender generation code。

因此我们可以知道：

> 场景中到底有哪些 objects、它们有什么属性、彼此是什么关系。

而且可以重新生成图片。

官方来源：

[CLEVR 官方数据与生成代码](https://cs.stanford.edu/people/jcjohns/clevr/?utm_source=chatgpt.com)

### 我们不是直接使用 CLEVR benchmark

而是基于官方 generator 创建新的：

\[
\boxed{
RewardLens\text{-}CLEVR
}
\]

每个样本：

\[
(I,\ I_{\text{rel}},\ I_{\text{irr}})
\]

以及：

```text
question
candidate_A
candidate_B
factor
base_scene_graph
relevant_edit
irrelevant_edit
expected_base_label
expected_relevant_label
expected_irrelevant_label
edit_magnitude_metadata
```

正式实验目标：

\[
1,000\text{–}2,000\ triplets/factor.
\]

四类总计约：

\[
4,000\text{–}8,000\ triplets.
\]

Pilot 先做：

\[
300\text{–}500/factor.
\]

---

# 14. Dataset B — Static Preference Baseline

Static accuracy 不能直接使用 audit 的 base samples。

我们需要一个独立普通 preference set。

主分析建议建立：

## GQA-Static

GQA 是 real-world visual reasoning 数据集，包含约：

- 113K images；
- 22M+ questions；
- dense scene graphs；
- object attributes；
- relations；
- question functional programs。

这使我们可以把问题映射到 Count / Attribute / Spatial / Presence。

官方数据：

[GQA 官方下载页](https://cs.stanford.edu/people/dorarad/gqa/download.html?utm_source=chatgpt.com)

我们从 GQA 创建一个：

\[
D_{\text{static}}
\]

例如：

\[
1,000/factor
\]

约 4,000 个普通 pairwise preference items。

每个：

\[
(I,q,y^+,y^-).
\]

这里没有 intervention structure。

目标只是测：

\[
A_{mf}.
\]

---

# 15. Dataset C — Downstream Reward Utility

同样使用真实图片，但与 Static 完全 image-disjoint。

构建：

## GQA-Best-of-N

GQA 原始论文有 113,018 张图片、22,669,678 个问题，并且官方 split 保证同一图片的所有问题位于同一 split，因此非常适合做 image-disjoint evaluation。

我们重新按 image ID 冻结：

\[
D_{\text{static}}
\]

和：

\[
D_{\text{downstream}}.
\]

每个 downstream question 构造：

\[
C(x)
=
\{y_1,\ldots,y_8\}.
\]

---

# 16. Hybrid Candidate Pool

不能全部来自自由 sampling。

每个 pool 包含：

### Gold

至少 1 个 verified correct answer。

### Structured hard negatives

例如：

Count：

\[
gold\pm1.
\]

Attribute：

替换 target attribute。

Spatial：

invert relation：

\[
left\leftrightarrow right.
\]

Presence：

\[
present\leftrightarrow absent.
\]

### Natural distractors

再由一个固定开源 VLM 生成若干自然但错误的回答。

这样得到：

\[
\boxed{
controlled\ difficulty
+
naturalistic\ language.
}
\]

所有 Reward Models 使用完全相同 candidate pools。

---

# 17. Candidate-Pool Shortcut Audit

这是必要的 negative control。

至少检测：

- correct answer length；
- punctuation；
- verbosity；
- lexical frequency；
- candidate position。

并运行：

\[
\boxed{
Text\text{-}Only\ Judge
}
\]

作为 shortcut baseline。

如果模型不看图片就可以高概率选择正确答案，那么这个 candidate pool 不合格。

---

# 18. Dataset D — Counting External Validation

## TallyQA

TallyQA 专门研究 visual counting。

公开数据包含约：

- 287K questions；
- 165K images；
- 19K 人工收集的 complex counting questions。

图片来自 COCO 和 Visual Genome。

来源：

[TallyQA 官方数据仓库](https://github.com/manoja328/TallyQA_dataset?utm_source=chatgpt.com)

用途不是训练主结论。

而是验证：

\[
D_{\text{count}}
\]

是否也能解释一个完全不同 counting dataset 上的 reward selection quality。

---

# 19. Dataset E — Natural Paired Validation

## VQA v2 Complementary Pairs

VQA v2 官方发布：

- 200,394 training complementary pairs；
- 95,144 validation complementary pairs。

它专门通过相似图片 + 相同/相关 question 构造答案变化，减少 language prior。

来源：

[VQA v2 官方下载页](https://visualqa.org/download.html?utm_source=chatgpt.com)

用途：

> Natural-image flip validation。

不是 controlled causal intervention。

---

## MMVP

MMVP 有 300 张测试图片；MMVP-VLM 又将视觉困难划成 9 类 pattern，包括 Orientation、Presence、Camera Perspective 等。

来源：

[MMVP 官方仓库](https://github.com/tsb0601/MMVP?utm_source=chatgpt.com)

用途：

> fine-grained external stress test。

---

# 20. Dataset F — Image Editing External Case Study

只作为 secondary validation。

## EditReward-Bench / EditReward-Data

ICLR 2026 的 EditReward 构建了超过 200K 人工 preference pairs，覆盖七个 editing models 和十二个数据来源；其目标正是评价 instruction-guided image editing reward quality。

用途只做：

\[
2\text{–}4\ compatible\ judges
\]

的小规模 case study：

> requested edit 是否完成；

以及：

> irrelevant content 是否被不必要改变。

但它**不进入主 regression**。

也不声称 reasoning-side dependency 必然预测 editing-side behavior。

它只是验证：

> 相同的 evidence-dependence evaluation principle 是否在另一个 multimodal reward domain 中仍然揭示差异。

---

# 21. Model Universe

目标不是堆很多同一家族 checkpoint。

正式目标：

\[
\boxed{
8\text{–}12\ models
}
\]

并覆盖至少：

\[
\boxed{
4\text{–}5\ genuinely\ distinct\ families/paradigms.
}
\]

候选包括：

- general MLLM-as-a-judge；
- generative multimodal reward models；
- specialized multimodal critics；
- preference-trained reward models。

例如 Qwen、Gemma 系列和公开 specialized judges/reward models。

但最终名单必须经过：

## Model Compatibility Audit

所有模型必须稳定支持：

\[
image+question+candidate
\]

或：

\[
image+question+A/B.
\]

同 family 的不同 size 可以使用，但 statistical analysis 中必须 cluster。

---

# 22. 实验设计

## E0 — Feasibility Audit

在正式主实验前先运行。

检查：

1. 四个 factor 至少三个能稳定生成 matched interventions；
2. 至少 8 个 compatible models；
3. PFC/PSC 不出现严重 floor / ceiling；
4. GQA candidate pools 有实际 ranking difficulty。

任何一项失败：

> 修改 carrier / dataset pipeline。

不重新推翻研究问题。

---

# 23. E1 — Controlled Dependency Audit

对每个：

\[
model\times factor
\]

测：

\[
A,\ PFC,\ PSC,\ PFC_{cond},\ PSC_{cond}.
\]

核心寻找：

## Accuracy-Matched Pairs

例如：

\[
A_1=74.2
\]

\[
A_2=74.5
\]

但：

\[
PFC_1=82
\]

\[
PFC_2=55.
\]

如果大量出现：

\[
\boxed{
Same\ Accuracy,\ Different\ Dependency
}
\]

RQ1 成立。

---

# 24. E2 — Dependency Fingerprint

构建：

\[
Model\times Factor.
\]

例如：

| Model | Count | Attribute | Spatial | Presence |
|---|---:|---:|---:|---:|
| M1 | strong | strong | weak | medium |
| M2 | weak | strong | strong | strong |
| M3 | strong | weak | weak | strong |

我们希望说明：

> Reward Model 不是简单地“看图 / 不看图”。

而是存在：

\[
\boxed{
factor\text{-}specific\ visual\ dependency\ profiles.
}
\]

---

# 25. E3 — Best-of-N Downstream Utility

对于每个：

\[
(I,q)
\]

Reward Model 从：

\[
N=8
\]

候选中选择：

\[
y_m^*
=
\arg\max_y r_m(I,q,y).
\]

Primary：

\[
N=8.
\]

Robustness：

\[
N=2,\ 4.
\]

得到：

\[
U_{mf}.
\]

---

# 26. E4 — Incremental Validity

Baseline：

\[
\mathcal M_0:
U_{mf}
\sim
A_{mf}.
\]

Proposed：

\[
\mathcal M_1:
U_{mf}
\sim
A_{mf}
+
PFC_{mf}
+
PSC_{mf}.
\]

Conditional metrics 用于 robustness/decomposition。

主比较：

\[
\boxed{
\Delta Predictive\ Validity
=
Perf(\mathcal M_1)-Perf(\mathcal M_0).
}
\]

不能只看 p-value。

同时报告：

- leave-one-model-family-out；
- family-level cluster bootstrap；
- accuracy-matched model pairs；
- held-out prediction error。

---

# 27. E5 — Factor-Specific Negative Control

这是我认为全文最有科学价值的实验之一。

建立：

\[
Audit\ Factor
\times
Downstream\ Factor.
\]

我们希望观察：

\[
\boxed{
Diagonal>Off\text{-}Diagonal.
}
\]

即：

\[
D_{\text{count}}
\]

主要解释：

\[
U_{\text{count}},
\]

而不是同样解释 Spatial。

如果成立，可以排除：

> dependency metric 只是另一个 general intelligence score。

---

# 28. Optional E6 — Intervention-Aware Training

如果前面结果成立、有时间才运行。

使用一个 4B open MLLM。

比较：

\[
STD
\]

和：

\[
INT.
\]

INT 加入 matched relevant / irrelevant intervention supervision。

保持：

- token budget；
- steps；
- optimizer；
- LR；
- LoRA capacity；

尽量一致。

测试：

\[
A
\]

\[
D
\]

\[
U.
\]

如果：

\[
D\uparrow
\]

同时：

\[
U\uparrow
\]

而：

\[
A\approx constant,
\]

会提供更强的 causal evidence。

但它不是论文生死线。

---

# 29. Statistical Strategy

这篇论文不能因为有十万 image instances 就假装有十万个独立 Reward Models。

真正独立 variation 主要来自：

\[
Model\times Factor.
\]

因此 primary analysis 使用：

- hierarchical logistic model；
- model/family random effects；
- family-level cluster bootstrap；
- leave-one-family-out prediction。

不能靠巨大 instance count 得到虚假的极小 p-value。

Accuracy-matched pairs 和 factor-specific matrix 必须与 regression 一起出现。

---

# 30. 我们希望得到什么结论？

以下是 hypotheses，不是预先写好的结果。

## H1

\[
\boxed{
Similar\ static\ accuracy
\text{ can coexist with }
different\ visual\ dependencies.
}
\]

---

## H2

\[
\boxed{
Static\ preference\ accuracy
\text{ is informative but incomplete.}
}
\]

---

## H3 — 核心

\[
\boxed{
Factor\text{-}specific\ dependency
\text{ adds downstream information beyond static accuracy.}
}
\]

---

## H4 — strongest version

\[
\boxed{
D_f\rightarrow U_f
>
D_{f'}\rightarrow U_f.
}
\]

这会说明：

> dependency audit 真正测到了具体视觉因素，而不是模型总体强弱。

---

# 31. 理论价值：对 AI 理论的发展是什么？

我认为有四层。

## 第一层：扩展 Shortcut Learning

传统 shortcut learning 研究：

> task model 是否通过错误 feature 得到正确输出。

我们的工作把问题扩展到：

> **Evaluator 本身是否通过错误 feature 给出了正确 reward。**

这很重要，因为现代 AI 系统越来越依赖：

\[
Model
\rightarrow
Judge
\rightarrow
Optimization.
\]

如果 Judge 本身依赖 shortcut：

\[
\boxed{
\text{shortcut evaluator}
\rightarrow
\text{shortcut optimization target}.
}
\]

这比一个普通 task model 犯错的影响可能更大。

---

## 第二层：扩展 Right-for-the-Right-Reasons

过去：

\[
Prediction
\]

应该来自正确 evidence。

我们提出：

\[
\boxed{
Reward\ Judgment
}
\]

同样应该来自正确 evidence。

因此：

\[
\boxed{
Right\ Reward
\neq
Right\ Ranking\ Only.
}
\]

而应该进一步要求：

\[
\boxed{
Right\ Ranking
+
Right\ Evidence\ Dependence.
}
\]

---

## 第三层：发展 Reward Model Evaluation Theory

今天 Reward Model evaluation 的中心量仍然是：

\[
Preference\ Accuracy.
\]

我们的贡献不是替代它。

而是提出第二个正交维度：

\[
\boxed{
Evidence\text{-}Dependence\ Validity.
}
\]

这相当于把 Reward Model quality 从：

\[
\text{Outcome correctness}
\]

扩展成：

\[
\boxed{
\text{Outcome correctness}
+
\text{Evidence dependence}.
}
\]

如果 RQ2 成立，这不是哲学上的“解释更漂亮”，而是：

> 第二个维度确实包含 downstream-relevant information。

这才使它成为 AI science contribution。

---

## 第四层：连接 Interpretability 与 Utility

大量 interpretability 工作的问题是：

> explanation 是否漂亮，并不一定影响实际性能。

而我们的实验直接问：

\[
\boxed{
\text{Does evidence dependence matter for actual reward use?}
}
\]

所以我们不把“正确视觉依赖”只作为 explanation property。

而是测试它是否与：

\[
Best\text{-}of\text{-}N
\]

实际选择性能连接。

这可以把：

\[
\text{interpretability / grounding}
\]

和：

\[
\text{decision utility}
\]

真正连接起来。

---

# 32. 实践价值

## 价值一：Reward Model 选型

企业现在可能有两个 judge：

```text
Judge A: 81.2%
Judge B: 81.5%
```

传统 benchmark 基本认为两者一样。

RewardLens 可以进一步告诉工程师：

```text
             Count  Attribute Spatial Presence
Judge A       91       84       51      88
Judge B       62       87       83      79
```

那么：

- counting-heavy application 选 A；
- spatial-heavy application 选 B。

这比一个总 accuracy 更能指导部署。

---

## 价值二：Best-of-N / Inference-Time Scaling

Reward Models 被广泛用于：

\[
Generate\ N
\rightarrow
Reward
\rightarrow
Select\ Best.
\]

如果 judge 对目标 factor 使用了错误 visual shortcut：

> 增加 N 甚至可能让系统更容易找到一个“骗过 Reward Model”的答案。

所以 dependency audit 可以用于判断：

> **这个 judge 是否适合被用来做 inference-time optimization。**

---

## 价值三：Synthetic Data Filtering

Reward Model 经常被用于：

\[
大量 synthetic data
\rightarrow
Reward filter
\rightarrow
高质量训练集.
\]

如果 Reward Model 的 count / spatial dependency 很差，它会系统性保留某一类错误数据。

EditReward 已经证明，可靠 reward model 可以通过筛选 synthetic edit data 改善下游模型训练。

因此我们的 audit 可以成为 reward data pipeline 上线前的：

\[
\boxed{
QA\ layer.
}
\]

---

## 价值四：避免 Reward Hacking

如果未来模型被直接优化：

\[
\max r_\theta,
\]

那么 reward 中的视觉 shortcut 最终可能成为 generator / policy 可以利用的漏洞。

因此发现：

> reward 到底依赖哪个 factor，

本质上是在做：

\[
\boxed{
Reward\ Surface\ Audit.
}
\]

这对 RL、RLAIF、synthetic-data self-training 都有意义。

---

## 价值五：Image / Video Generation 的后续扩展

这篇论文 primary carrier 是 multimodal reasoning judge。

但方法原则可以进一步扩展到：

### Image Editing

\[
\text{requested change}
\rightarrow
sensitive
\]

\[
\text{non-requested content}
\rightarrow
invariant.
\]

### Video

未来可以扩展为：

\[
\boxed{
Right\ Spatiotemporal\ Dependencies.
}
\]

例如：

- action；
- motion direction；
- temporal order；
- object permanence；
- identity consistency；
- physical interactions。

这些不是本论文要完成的 claim，但形成了一条非常自然的研究路线。

---

# 33. 论文真正希望增加的知识

如果只能用三句话概括：

> **第一，Multimodal Reward Model 的正确 judgment 与正确 visual evidence dependence 是两个不同性质。**

> **第二，普通 preference accuracy 可以掩盖 factor-specific dependency differences。**

> **第三，也是最关键的：如果这种 dependency difference 在控制 static accuracy 后仍然能够特异性预测相应 downstream reward utility，那么 Reward Model evaluation 就应该从“结果是否正确”扩展到“判断是否建立在正确证据上”。**

最终最希望能够支持的知识命题是：

\[
\boxed{
\textbf{
A reliable multimodal reward model should not only prefer the right answer; its preference should depend on the visual evidence that actually makes that answer right.
}
}
\]

而如果 downstream experiment 成立，则进一步：

\[
\boxed{
\textbf{
Evidence dependence is not merely interpretability—it is part of reward-model validity.
}
}
\]

这就是我认为这篇论文真正有理论价值的地方。