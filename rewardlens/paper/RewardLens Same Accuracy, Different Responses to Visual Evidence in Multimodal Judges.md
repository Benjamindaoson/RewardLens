# RewardLens: Same Accuracy, Different Responses to Visual Evidence in Multimodal Judges

**RewardLens：相同准确率下，多模态评判模型对视觉证据的不同响应**

## Abstract

Static preference accuracy can make multimodal judges appear equivalent while concealing substantial differences in how they respond to visual evidence. We investigate this blind spot with RewardLens, a controlled intervention study of eight judges across four visual factors. We match judges on independent natural-image tests and audit them on procedurally rendered scenes, keeping questions and candidate responses fixed. Relevant edits change the correct choice; irrelevant edits preserve it. Among cases each judge initially answers correctly, we measure accuracy after each edit type as Relevant Adaptation (RA) and Irrelevant Invariance (II). Phi-3.5-Vision and LLaVA-OneVision achieve identical measured static accuracy on Attribute (80.5%), yet differ by 15.1 percentage points in RA. A predeclared within-factor rule matching static accuracies within one percentage point yields seven pairs, with a median RA gap of 15.1 points. An identification analysis formalizes why the shared static score cannot uniquely determine the judges’ observed intervention profiles. Post-hoc joint-state and prediction analyses make the failures concrete: Qwen judges all 200 Count audit bases correctly, but retains its original choice after relevant edits on 166 (83%), turning correct judgments into errors. Here, consistency is the failure rather than evidence of successful judgment. RewardLens thus complements static accuracy by testing whether judges revise their choices correctly when relevant evidence changes and remain correct when irrelevant details change. Our findings show that static-score equivalence is not sufficient grounds for treating judges as behaviorally interchangeable.

## 中文摘要

静态偏好准确率会让多模态评判模型看起来不相上下，却可能掩盖它们面对视觉证据变化时的明显差异。本文提出 RewardLens，通过八个模型、四类视觉因素的受控干预实验，研究这一评估盲点。我们先在独立的自然图像测试中匹配准确率相同或接近的模型，再在程序化生成的场景中检验它们对视觉变化的响应。实验保持问题和候选回答不变：相关编辑改变正确选项，无关编辑保留正确选项。对每个模型，我们在它原本判断正确的样本上，分别统计两种编辑后的正确率，得到相关适应性（RA）与无关不变性（II）。 

在属性任务上，Phi-3.5-Vision 与 LLaVA-OneVision 的实测静态准确率均为 **80.5%**，但 RA 相差 **15.1 个百分点**。按照预先声明的规则，在同一视觉因素内匹配静态准确率相差不超过 1 个百分点的模型，共得到七组模型对，其 RA 差距的中位数为 15.1 个百分点。我们的识别分析进一步说明：这个共同的静态分数，无法唯一确定两个模型各自的实测干预表现。  

事后的联合状态与预测分析揭示了这些错误如何发生：Qwen 在 200 个计数审计样本的原图上全部判断正确，却在其中 **166 个（83%）**样本经过相关编辑后仍保留原选择，因而由对变错。此时，保持一致恰恰是失败，而不是判断可靠的证据。RewardLens 因此补充了静态准确率：检验模型能否在关键证据变化时正确改判，并在无关变化下保持正确。我们的发现表明，**静态分数相同，并不足以将两个评判模型视为在判断行为上可以相互替代。**