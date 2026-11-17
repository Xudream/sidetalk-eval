# 全双工交互中的 sideTalk：定义、指标与评测的学术/产业深度洞察

> 技术洞察报告  
> 证据检索截止：2026-11-16  
> 范围：全双工语音对话、语音助手、AI 眼镜/可穿戴、多人会议、设备指向语音检测  
> 方法：只纳入可追溯到一手论文、官方技术报告或厂商官方文档的材料；无法核实的“语义拒识/背景人声过滤”宣传不作为量化结论。

---

## 0. 执行摘要

1. **sideTalk 不是统一术语，也不是单一任务。** 学术界更稳妥的上位词是 **non-addressed speech（非指向助手的语音）**；`sideTalk` 更适合作为产品化别名。
2. **至少要区分六类现象：** SDO（主用户对旁人说话）、TPS（第三方插话）、self-talk（自言自语）、media/background speech（电视、外放、邻桌）、backchannel（附和声）、pause（停顿）。它们的正确动作不同，不能合成一个“sideTalk 总分”。
3. **“拒识”至少分四层：** ASR 级抑制、设备指向二分类、轮次行为级拒识、动作级 `Mute/Tool/Answer`。WER、EER、Resume 率、拒识准确率之间不可互换。
4. **学术评测正在从“分类”转向“行为与动作”。** FDB v1.5 看 `Respond/Resume`，HumDial 看二值拒识行为，VGBench 直接看是否执行工具，Duplex-MPE 看是否新发起、是否保持静默、是否让出回答窗口。
5. **SDO 是最难、也是数据最稀缺的一类。** HumDial 的 SDO 训练集为 **0 条**，dev/test 各 200 条；TPS 训练集也只有 **120 条**。这是公开数据的最大空白。
6. **“会打断”不等于“会分辨受话人”。** FDB v1.5 中 GPT-4o 在真实打断上反应最快，但在 `talking_other` 上 `Respond=0.91`、`Resume=0.02`；Gemini 在该场景 `Respond=0.00`、`Resume=0.99`。快速响应与保持发言权存在明显 trade-off。
7. **总体 accuracy 极易被多数类掩盖。** Inoue 等人的 TEIDAN 受话人识别中，GPT-4o 总体 80.9%，看似接近人类；但显式受话人样本只有 9/23 正确（约 39.1%），高分主要来自大量 `O`（无明确受话人）样本。
8. **产业界已普遍实现相关能力，但几乎不公开 SDO 指标。** Qwen-Omni-Realtime 和 Azure OpenAI Realtime 的 `semantic_vad` 主要解决“是否说完/是否误触发”，不是“说话对象是不是助手”。官方文档没有给出 SDO 拒识率、FAR/FRR 或固定工作点曲线。
9. **不要把 AA Full-Duplex 98.9 当作 sideTalk 分数。** StepAudio 3 Realtime 的 98.9 来自 Artificial Analysis 的四项子集：Pause、Turn Taking、User Interruption、Backchannel；该子集不包含 FDB v1.5 的 `talking_to_others` 和 `background_speech`。
10. **推荐用“分场景 + 固定工作点 + 时延 + 恢复播报 + 下游质量”的多维记分卡。** 单一 accuracy 既不能支撑产品决策，也不能支撑论文对比。

---

## 1. 术语与问题边界

### 1.1 本报告推荐的定义

> **sideTalk（建议学术上位词：non-addressed speech）**：在全双工语音交互中进入助手输入通道、但当前话语的意图受话者不是该助手，或未被授权指向该设备的语音事件。系统应根据当前交互状态选择：不启动响应、继续/恢复原话轮、停止播报、仅作为上下文保留，或在多用户策略下响应。

三个关键词：

- **意图受话者**：不是“谁在说话”，而是“这句话说给谁听”。
- **当前交互状态**：系统在 `idle` 时是“不开始”，在 `speaking` 时是“是否停止/恢复”，两种动作完全不同。
- **授权与设备边界**：同一说话人、同一句话，在近场/远场、已授权/未授权设备上可能应有不同动作。

### 1.2 六类子现象

| 子类 | 典型场景 | 正确动作 | 常见错误 |
|---|---|---|---|
| SDO：speech directed at others | 主用户转头对家人说“我晚点回来” | 静默/继续原话轮 | 当成新 query 回答 |
| TPS：third-party speech | 旁人插话“今天几号？” | 拒识或按策略处理 | 把旁人当主用户 |
| Self-talk | 用户自言自语“钥匙放哪了” | 静默或仅记录上下文 | 执行命令、调用工具 |
| Media/background speech | 电视、外放语音、邻桌对话 | 过滤/不作为轮次 | 把台词当请求 |
| Backchannel | “嗯”“对”“uh-huh” | 继续/恢复原话轮，不新开回答 | 停止播报、重新回答 |
| Pause | 句中犹豫、换气 | 等待语义完成 | 抢话、提前 commit |

> **重要：** backchannel 和 pause 不是“应该被丢掉的噪声”，而是话轮管理信号。把它们和 SDO/TPS 混在一个“拒识率”里，会掩盖系统真正的能力差异。

### 1.3 说话人身份 × 受话对象矩阵

| 说话人 | 受话对象 | 例子 | 典型系统动作 |
|---|---|---|---|
| 主用户 | 助手 | “帮我查天气” | Respond |
| 主用户 | 旁人 | “妈，我晚点回” | SDO：静默/Resume |
| 主用户 | 自己 | “钥匙放哪了……” | Self-talk：静默/保留上下文 |
| 第三方 | 主用户 | 旁人插话 | TPS：拒识或等待 |
| 第三方 | 助手 | 另一个合法用户对设备说话 | 取决于多用户授权策略 |
| 媒体/设备 | 无明确对象 | 电视台词、语音消息 | 过滤/不作为轮次 |
| 主用户 | 助手 | “嗯，对” | Backchannel：继续/Resume |

这张表说明：**“非目标说话人”不等于 sideTalk**，因为主用户本人也可能 sideTalk；**“第三方”也不一定该拒**，因为多用户场景中第三方可能是合法用户。

### 1.4 与相邻概念的边界

| 概念 | 回答的问题 | 输出 | 为什么不能替代 sideTalk |
|---|---|---|---|
| VAD | 当前有没有语音？ | 有/无 | 不知道说话对象，也不知道是否说完 |
| semantic VAD / turn detection | 用户是否说完？ | 轮次结束/继续 | 主要防止抢话，不判断 SDO/授权 |
| barge-in | 用户是否在打断助手？ | 停止/让出话轮 | 打断通常是“对助手说”的合法语音 |
| DDSD | 是否对设备说？ | 二分类门控 | 接近，但常只分设备/背景，不细到 SDO/TPS/self-talk |
| addressee recognition | 这句话说给谁？ | A/B/C/group/none | 多为离线、非因果、非动作级评测 |
| ASR side-speech suppression | 能否只转写目标说话人？ | 文本/WER | 降 WER 不等于“正确地不说话” |
| sideTalk policy | 当前该不该响应/停止/恢复？ | 行为/动作 | 这是本报告真正关心的端到端问题 |

### 1.5 五层评测栈

1. **信号层**：VAD、回声消除、波束成形、多麦克风空间线索。
2. **门控层**：device-directed / non-device-directed，输出 FAR、FRR、EER、FA/hour。
3. **行为层**：Respond / Resume / Stop / Silence，输出行为比例和时延。
4. **动作层**：Mute / Tool / Answer，输出动作准确率、误执行率、工具选择率。
5. **体验层**：恢复播报、上下文保持、答案正确率、长期记忆、用户打断后的修复能力。

---

## 2. 学术界：定义、数据与评测

### 2.1 Full-Duplex-Bench v1.5：把 sideTalk 放进重叠语音行为框架

**论文**：Guan-Ting Lin 等，*Full-Duplex-Bench v1.5: Evaluating Overlap Handling for Full-Duplex Speech Models*，[arXiv:2507.23159](https://arxiv.org/abs/2507.23159)

**任务定义**：用实时音频流测试全双工模型在四类重叠语音下的行为：

- `user_interruption`：200 条
- `user_backchannel`：99 条
- `talking_to_others`：100 条
- `background_speech`：100 条

后两类最接近 sideTalk。论文对 `talking_to_others` 的表述是“用户对另一个人说话，模型应识别自己不是受话者并优雅地继续”；对 `background_speech` 的表述是“远处第三方语音，不是对模型说的”。

**行为标签**：`Respond / Resume / Uncertain / Unknown`，由 GPT-4o 基于 ASR 文本判定。`Respond` 是回应当前重叠语音，`Resume` 是忽略重叠并继续原话轮，`Uncertain` 是不确定，`Unknown` 是无法归类。

**指标**：

- Stop latency：重叠语音起点到模型停止说话的时间。
- Response latency：重叠语音结束到模型下一次开始说话的时间。
- 预期行为：真实打断应 `Respond` 且低 stop/response latency；backchannel、talking to others、background speech 应 `Resume`，且 stop latency 可以较高、response latency 尽量低。
- 另有 WPM、pitch、intensity、UTMOSv2 等韵律/质量指标。

**关键结果**（Table 2）：

| 场景 | 系统 | Respond | Resume | 解读 |
|---|---|---:|---:|---|
| user_interruption | GPT-4o | 0.78 | 0.10 | 真实打断反应强 |
| talking_other | GPT-4o | 0.91 | 0.02 | 把旁人语音当新意图 |
| talking_other | Gemini | 0.00 | 0.99 | 保持发言权强，但可能偏保守 |
| bkg_speech | GPT-4o | 0.93 | 0.04 | 背景语音几乎总被当成请求 |
| bkg_speech | Sonic | 0.01 | 0.98 | 过滤背景语音强 |

**洞察**：

- 这套基准第一次把“是否响应”和“何时响应”放在同一个框架里，但**没有单独的 sideTalk rejection rate**；需要从 `Respond/Resume` 分布中二次推导。
- `Resume` 不是“沉默”，而是“继续此前的话轮”。这使它可以同时衡量“没有误开新回答”和“没有丢掉原任务”。
- 真实打断与 sideTalk 拒识是竞争目标：越倾向于快速响应，越容易把 SDO/TPS 当成请求；越倾向于保持发言权，越容易在真实打断上反应迟钝。

### 2.2 HumDial Challenge / HumDial-FDBench：目前最完整的拒识分类体系

**论文**：Zhixian Zhao 等，*The ICASSP 2026 HumDial Challenge: Benchmarking Human-like Spoken Dialogue Systems in the LLM Era*，[arXiv:2601.05564](https://arxiv.org/abs/2601.05564)；以及 *Full-Duplex Interaction in Spoken Dialogue Systems: A Comprehensive Study from the ICASSP 2026 HumDial Challenge*，[arXiv:2604.21406](https://arxiv.org/abs/2604.21406)

**数据**：真实双通道、中英双语、超过 100 小时；专业演员按脚本录制，保留自然重叠、停顿、附和和转向。

**两大任务、八个子场景**：

- Interruption：Follow-up Question、Negation/Dissatisfaction、Repetition Request、Topic Switch、Silence/Stop。
- Rejection：User Real-time Backchannels（URB）、Pause Handling（PH）、Third-party Speech（TPS）、Speech Directed at Others（SDO）。

**样本量**（Table 1）：

| 子场景 | Train | Dev | Test |
|---|---:|---:|---:|
| 五个 Interruption 子类 | 每类 1,507 / 1,211 / 1,213 / 1,213 / 1,212 | 各 200 | 各 600 |
| URB | 1,211 | 200 | 600 |
| PH | 1,211 | 200 | 600 |
| TPS | **120** | 200 | 600 |
| SDO | **0** | 200 | 200 |

> **这是本报告最重要的数据结论之一：** 最接近“主用户对旁人说话”的 SDO，公开训练集为 0；TPS 训练集只有 120 条。学术界的评测集可以测 SDO，但训练监督几乎空白。

**判分**：

- Interruption：只有 `Respond` 正确。
- Rejection：backchannel、用户问题之后的 TPS、SDO 以 `Resume` 为正确；PH 和“用户问题之前的 TPS”用词级时间戳判断是否过早响应。
- ASR：中文 Paraformer、英文 Parakeet-TDT；行为分类用 DeepSeek-V3。
- 时延：stop latency、response latency、first response latency（首个用户问题结束到首个模型响应开始）。
- 总分：`0.4 × Interruption + 0.4 × Rejection + 0.2 × Delay`，其中 Delay 做对数归一化。

**榜单结果**（Table 2）：

| 系统 | Interruption | Rejection | Delay(s) | Final |
|---|---:|---:|---:|---:|
| Cookie asr | 79.3 | 72.2 | 1.260 | 76.6 |
| Gemini-2.5 | 79.8 | 36.5 | 1.301 | 62.3 |

**洞察**：

- **Rejection 明显难于 Interruption。** Gemini 的 Interruption 79.8，但 Rejection 只有 36.5；Cookie 也呈现同样趋势。
- 这套榜单把 URB、PH、TPS、SDO 合成了一个 Rejection 分，**没有单独公布 SDO/TPS 子项**。因此不能把 Rejection 分数直接当作 sideTalk 分数。
- SDO 训练集为 0 意味着现有系统在 SDO 上更可能依赖零样本语义/语用推理，而不是监督学习。

### 2.3 WearVox：AI 眼镜场景的“单轮动作 + 二值拒识”

**论文**：Zhaojiang Lin 等，*WearVox: An Egocentric Multichannel Voice Assistant Benchmark for Wearables*，[arXiv:2601.02391](https://arxiv.org/abs/2601.02391)

**数据**：3,842 条第一视角、多通道 AI 眼镜录音；五个任务：Search-Grounded QA、Closed-Book QA、Side-Talk Rejection、Tool Calling、Speech Translation。

**Side-Talk Rejection 任务**：

- 共 1,082 条 = 582 条 side talk + 500 条 valid query（后者与 tool-calling 任务复用）。
- 输入是 `Text In + Speech In`，输出是 `[Mute]` 或答案/工具调用。
- 指标是**二值准确率**：模型是否正确抑制非设备指向语音。

**关键结果**（Table 2；必须按列读，不能把 QA 分数误当 side-talk）：

| 模型 | Side-Talk Rejection |
|---|---:|
| Gemma 3n | 59.9 |
| Kimi-Audio | 47.0 |
| Qwen2.5-Omni | 60.4 |
| GPT-4o Audio | 66.0 |
| GPT-5 w/ Whisper | 73.8 |
| Gemini 2.5 Flash | 88.2 |
| Gemini 2.5 Flash Thinking | 91.4 |

**时延**（Side-Talk Rejection TTFT）：

- Gemini 2.5 Flash：1,306.62 ms
- Gemini 2.5 Flash Thinking：2,176.97 ms
- GPT-4o Audio：1,341.04 ms

**多通道增益**：

- Table 4：Side-Talk Rejection 85.4% → 93.9%。
- 论文引言写作 85.6% → 93.9%，与 Table 4 有 0.2pt 口径差异；引用时建议注明“正文引言/表格存在 0.2pt 差异，以 Table 4 为准”。

**洞察**：

- 这是最接近“产品动作”的公开评测之一：不是问“模型知不知道这是 side talk”，而是问“它会不会执行/回答”。
- 但它是**单轮、文本输出、非流式行为**评测；不测停止播报、恢复话轮、连续多轮上下文。
- 91.4% 的高分伴随 2,176.97 ms TTFT；对于实时语音助手，这个时延可能不可接受。**sideTalk 准确率必须和时延一起报。**

### 2.4 VGBench：动作级 addressedness 与“同词反向”反事实

**论文**：Yanjie Zhang 等，*Do Audio LLMs Listen Before They Act? Diagnosing Acoustic-Context Gating in Voice Agents*，[arXiv:2609.32536](https://arxiv.org/abs/2609.32536)

**数据**：1,018 条，三个家族：

- Side-talk：395 条
- Self-talk：223 条
- Speaker-switch：400 对

**任务形式**：统一动作空间 `Mute / Tool / Answer`。`Mute` 返回 `[Mute]`，`Tool` 输出结构化工具调用，`Answer` 输出自然语言。

**关键设计**：speaker-switch 对保持触发词和上下文不变，只改变“来源/近场条件”，使正确动作从 `Tool` 翻转为 `Mute`。这把“识别工具”与“是否允许执行”分开了。

**指标**：

- Side-talk correct：是否只对助手指向的 utterance 执行动作。
- Self-talk mute rate。
- Switch mute rate：来源/场景切换后是否正确静音。
- Target-tool selection：同说话人/纯文本正控中选择目标工具的比例。

**关键结果**（Table 1）：

| 系统 | Side-talk correct | Self-talk mute | Switch mute | 目标工具（同说话人/纯文本） |
|---|---:|---:|---:|---:|
| Qwen3-Omni | 39.0 | 57.0 | 1 | 77 / 81 |
| Kimi-Audio-7B | 38.2 | 30.5 | 14 | 53 / 44 |
| Step-Audio-R1.1 | 41.0 | 22.4 | 1 | 96 / 97 |
| Gemini-3.8-flash | 32.4 | 68.6 | 7 | 80 / 71 |

**最重要的发现**：

- 最强 raw switch mute rate 仅 **14%**；最强 training-free 方法仅 **6%**。
- Step-Audio-R1.1 的目标工具识别达到 96%/97%，但 switched command 只 mute 1%。**工具识别能力不等于声学上下文门控能力。**
- VoxGate SFT 将 switch mute 提升到 **91.3%**，同时保持同说话人/纯文本正控的目标工具选择；exploratory GRPO 将 side-talk accuracy 从 68.4% 提到 70.9%，self-talk mute 从 52.0% 提到 60.0%。

**局限**：

- side-talk judge 使用固定 LLM judge，论文未报告与人工标注的一致率。
- 工具识别只检查工具名，不检查参数。
- 合成/受控成分较高，不能替代真实远场多人对话。

### 2.5 Duplex-MPE：多人对话中的“选择性参与”，而非简单拒识

**论文**：Chengqian Ma 等，*Duplex-MPE: Benchmarking Multi-Party Interaction in Full-Duplex Dialogue*，[arXiv:2609.31948](https://arxiv.org/abs/2609.31948)

**数据**：2,000 个多人连续对话场景，3–4 个真人 + assistant Aria；每个场景有 explicit/implicit addressing 两个版本，共 4,000 条音轨；61.10 小时唯一语音，含复用和间隙共 110.93 小时。

**标签体系**：

- `T`：直接请求 Aria，且尚未解决。
- `N1`：提到 Aria，但不是请求。
- `N2`：对其他人或其他设备说。
- `N3`：无明确对象，包括 self-talk。
- `N4`：人类回答或取消 Aria 的请求。

**四个指标**（Table 2）：

1. **Fresh-onset response rate**：T 请求结束时模型未在说话，并在 5 秒内新发起语音的比例。
2. **Conditional answer accuracy**：只在模型确实有语音输出的 T 请求中判断答案正确性。
3. **Silence preservation**：N1/N2/N3 窗口中没有语音或只有不夺取话轮的短暂附和的比例。
4. **Answering-window yield**：N4 问题期间模型沉默、问题后 3 秒内首次说话、且在 N4R 开始时仍在说话的事件中，能否在 N4R 起点 +2 秒及之后保持沉默。

**核心结果与洞察**：

- 不合成总分是论文的刻意设计：四个指标的分母不同，不能互相补偿。
- Freeze-Omni 的 response presence 高达 0.9955，但 fresh-onset response rate 只有 0.2525；说明“看起来一直在说话”不等于“在该回应时新发起回应”。
- MiniCPM-o 4.5 的 response presence 0.9545、fresh-onset 0.9500，差距只有 0.0045，说明它更能在请求结束时真正接管话轮。
- 五种语音系统的 explicit/implicit 响应率差异只有 -1.75 到 +0.60 个百分点，统计上不显著；这提示当前系统可能并没有真正利用“是否点名 Aria”的语用线索。
- MiniCPM-o 在 4,704 个“对其他人/设备说”的请求中，仍有 216 个（4.6%）未能保持静默。

**理论贡献**：

> 非指向语音不一定是噪声。它可能为后续请求提供上下文，甚至直接回答用户已经抛给助手的问题。因此正确的策略不是“全部删除”，而是“保留上下文、单独决定是否开口”。

### 2.6 受话人识别（addressee recognition）：离线分类线的价值与陷阱

#### Inoue 等：TEIDAN 三人日语对话

**论文**：Koji Inoue 等，*An LLM Benchmark for Addressee Recognition in Multi-modal Multi-party Dialogue*，[arXiv:2501.16643](https://arxiv.org/abs/2501.16643)

- 5 个 session、387 个 turn；只有 75/387（约 20%）显式指定受话人。
- 标签 A/B/C/O；O 表示没有特定个人被指定。
- GPT-4o 总体 accuracy 80.9%，但论文给出的 chance level 约 80.6%。
- 显式受话人（A/B/C）只有 9 正确、14 错误；O 类 304 正确、60 错误。
- 结论：总体 accuracy 主要被 O 类主导，模型在真正需要区分 A/B/C 时表现很差。

#### Fukuda 等：AMI 四人英语会议

**论文**：Ryo Fukuda 等，*Evaluating Large Language Models Abilities for Addressee, Turn-change, and Next Speaker Prediction in Meetings*，[arXiv:2606.17542](https://arxiv.org/abs/2606.17542)

- 指标：accuracy + macro-F1。
- 人类：Addressee Acc 66.6 / macro-F1 67.5。
- Qwen3-14B：51.5 / 52.0。
- Gemini 2.5 Pro：61.4 / 57.4。
- AMI 原始 addressee 标注的 Krippendorff α 约 0.45–0.56；本实验参与者间一致性为 0.67。
- 结论：多模态 LLM 仍低于人类；上下文和 gaze 很重要。

#### Mori 等：把受话人从离散标签改成连续 addressivity

**论文**：Taiga Mori 等，*On the Structure of Address in Multi-Party Dialogue: From Discrete Labels to Continuous Levels*，[arXiv:2607.15648](https://arxiv.org/abs/2607.15648)

- 3,078 个 turn，三位标注者，Fleiss κ=0.52。
- 将 addressee 建模为 listener-wise 连续 addressivity，而不是单一离散标签。
- 连续表示对 next speaker、gaze、backchannel 的预测拟合更好。
- 结论：真实对话中的“受话”经常是程度问题，二分类会丢失歧义。

**对 sideTalk 的启示**：

- 受话人识别是 sideTalk 的“语义内核”，但离线分类结果不能直接推导出流式动作。
- 只看总体 accuracy 会被多数类严重误导；必须报 per-class recall、macro-F1、混淆矩阵和多数类基线。
- 真实产品需要的是因果、低时延、可校准的“当前是否对助手说”，而不是看完整个对话再分类。

### 2.7 DDSD / FTM：工业门控线的指标传统

**DDSD** 把问题定义为二分类：用户对语音助手的 query vs 背景语音/旁谈。

- Adaptive KD，[arXiv:2508.02801](https://arxiv.org/abs/2508.02801)：2.7K 小时内部数据；指标 EER、DET；keyword/follow-up 的 EER 相对改善 26%/19%。
- Follow-up DDSD，[arXiv:2411.00023](https://arxiv.org/abs/2411.00023)：联合建模上一轮 query 与 ASR n-best；在固定 10% false reject 时，false alarm 降低 20–40%。

**价值**：

- EER、DET、固定 FRR 下的 FAR 是产业可部署的指标语言。
- 这类工作证明“上下文”和“ASR 不确定性”对门控很重要。

**局限**：

- 多数 DDSD 只分“设备指向/非设备指向”，不细分 SDO、TPS、self-talk、media。
- 不是轮次行为评测，不能回答“应该停止还是恢复播报”。

### 2.8 MMW：ASR 级 side-speech suppression

**论文**：Yang Liu 等，*MMW: Side Talk Rejection Multi-Microphone Whisper on Smart Glasses*，[arXiv:2507.05609](https://arxiv.org/abs/2507.05609)

- 定义：附近他人的无意语音或重叠对话。
- 方法：多麦克风 raw-waveform 融合 + frame diarization + GRPO。
- 指标：WER，不是拒识率，也不是是否终止响应。
- 主表：MMW WER 3.71%；MMW + Llama 4 WER 4.53%。
- 摘要另称 noisy condition 下 WER 降低 4.95%；这与正文主表的绝对 WER 是不同口径，引用时必须写清“相对改善/绝对 WER”，不能混成“sideTalk 准确率提升 4.95 个百分点”。

**洞察**：ASR 级抑制解决的是“不要转写旁人”，但产品还可能需要“不要执行旁人”“不要打断主用户”“保留旁人语音作为上下文”。三者不是同一个目标。

### 2.9 学术基准横向对比

| 基准/工作 | 核心对象 | 数据/规模 | 评测单位 | 主指标 | 最值得借鉴 | 主要局限 |
|---|---|---|---|---|---|---|
| FDB v1.5 | 重叠语音行为 | 200/99/100/100 | 轮次行为 | Respond/Resume + stop/response latency | 行为与时机联合 | 无独立 sideTalk 分数 |
| HumDial | 拒识 + 打断 | >100h，中英 | 子场景行为 | Rejection accuracy + latency | SDO/TPS/URB/PH 分类最完整 | SDO train=0；子项未单列 |
| WearVox | AI 眼镜动作 | 3,842 条；Side-Talk 1,082 | 单轮动作 | 二值准确率 + TTFT | 真实第一视角多通道 | 非流式、非多轮 |
| VGBench | 动作级 addressedness | 1,018 条 | 单轮动作 | Mute/Tool/Answer | 同词反事实、防 always-mute | LLM judge 未报一致性 |
| Duplex-MPE | 多人选择性参与 | 2,000 场景/4,000 音轨 | 多轮连续音频 | 四项独立指标 | 非指向语音可作上下文 | 无总分、系统覆盖少 |
| Addressee recognition | 受话人分类 | TEIDAN/AMI 等 | utterance | Acc/macro-F1 | 语用与多模态线索 | 离线、类别不平衡 |
| DDSD/FTM | 设备指向门控 | 2.7K 小时等 | 帧/段 | EER/DET/FAR@FRR | 固定工作点、可部署 | 不细分 SDO/TPS |
| MMW | ASR 侧语音抑制 | 5k 小时训练/22h 评测 | 帧/词 | WER | 多麦克风空间线索 | 不是交互级拒识 |

---

## 3. 产业界：能力已落地，指标仍不透明

### 3.1 Qwen-Omni-Realtime：`semantic_vad` 是轮次检测，不是 SDO 检测

**官方文档**：[Alibaba Cloud Model Studio Realtime](https://www.alibabacloud.com/help/en/model-studio/realtime) / [阿里云百炼 Realtime](https://help.aliyun.com/zh/model-studio/realtime)

官方表述：

- 支持 full-duplex 音视频交互。
- 支持 `semantic_vad`，可过滤附和声、背景音等无意义声音，减少语音轮次误触发。
- 另有 `semantic_vad_ec`，更易检测用户说话并打断模型回复。

**判断**：

- 这是目前公开文档中最接近 sideTalk 的产品能力之一，但官方没有给出 SDO/TPS 分类准确率、FAR/FRR、固定工作点或时延分布。
- `semantic_vad` 的核心问题是“这一轮是否说完/是否值得触发”，不是“这句话是不是对助手说的”。它可以吸收一部分 sideTalk，但不能替代受话人判断。

### 3.2 Azure OpenAI Realtime：`semantic_vad` 的官方定义

**官方文档**：[Azure AI Foundry Realtime Audio](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio)

- `turn_detection` 可取 `none`、`server_vad`、`semantic_vad`。
- `semantic_vad` 根据用户说出的词判断其是否完成话语，降低 speech-to-speech 中打断用户的概率。
- 可设置 `create_response=false`，让 VAD 只检测结束、不自动生成响应。

**判断**：

- 这是 turn detection 的语义化，不是 addressee recognition。
- 官方没有 sideTalk 指标；`create_response=false` 只是把“何时响应”交给应用层，不等于应用层已经能正确判断 SDO。

### 3.3 StepAudio 3 Realtime：有 background speech rejection 训练目标，但 98.9 不是 sideTalk

**技术报告**：[arXiv:2609.14005](https://arxiv.org/abs/2609.14005)

- 后训练显式覆盖 turn taking、user backchannel、interruption、background speech rejection。
- 系统使用对话历史判断 incoming speech 是否指向助手，决定纳入当前交换还是视为无关背景。
- 报告自报 Artificial Analysis Full-Duplex Overall **98.9**：Pause 98.9、Turn Taking 100、User Interruption 99、Backchannel 98。

**关键雷区**：

- AA 的 Full-Duplex conversational dynamics 子集只包含 Pause Handling、Turn Taking、User Interruption、Backchannel。
- 它**不包含** FDB v1.5 的 `talking_to_others` 和 `background_speech`。
- 因此 98.9 不能作为 sideTalk/SDO 指标，也不能证明系统能区分“主用户对旁人说”和“对助手说”。

### 3.4 Attention Labs SAS：pre-ASR、fail-closed 的设备指向路由

**论文**：David Joohun Kim 等，*Selective Attention System (SAS): Device-Addressed Speech Detection for Real-Time On-Device Voice AI*，[arXiv:2604.08412](https://arxiv.org/abs/2604.08412)，作者单位为 Attention Labs。

**定义**：在 ASR 之前做三分类路由：

- `0`：静音/无语音
- `1`：对人说
- `2`：对设备说

只有 `y=2` 且置信度 `c≥τ` 才 forward 到下游；否则 abstain（fail-closed）。这是一个非常明确的“宁可漏放，不可误放”的产业策略。

**内部评测**（60 小时 held-out 多说话人英文数据）：

| 配置 | Precision | Recall | F1 |
|---|---:|---:|---:|
| Audio-only | 0.89 | 0.83 | 0.86 |
| Audio+Video | 0.97 | 0.93 | 0.95 |

其他数字：

- 去掉 temporal context：audio+video F1 0.95 → 0.57 ± 0.03。
- 时延：audio-only <55 ms（median 38 ms，p95 51 ms）；A+V <150 ms（median 105 ms，p95 142 ms）。
- 运行内存 <20 MB，ARM Cortex-A72 级别。
- baseline false-trigger rate 2.1%；TV-active 场景 7.8%；τ=0.82 时 TV-FTR 3.4%，但 recall 掉约 6 个百分点。

**判断**：

- 这是最接近“产品级 sideTalk 门控”的公开材料：有明确路由、阈值、fail-closed、时延和资源约束。
- 但它是厂商内部评测，数据不公开，不能当作独立可复现的 benchmark。
- 它的三分类仍把“对人说”作为一个大类，没有细分 SDO/TPS/self-talk/media；电视场景的误触发说明 media speech 是独立难点。

### 3.5 智能眼镜/可穿戴研究：多麦克风是 sideTalk 的关键变量

WearVox 和 MMW 都来自 AI 眼镜场景，共同结论是：

- 单通道音频很难区分“主用户对旁人说”与“主用户对设备说”，因为声纹和音区可能完全一样。
- 多麦克风/空间线索能显著提升 sideTalk 拒识和 ASR 抑制。
- WearVox 的多通道实验把 side-talk rejection 从 85.4% 提到 93.9%（Table 4）；MMW 则把 WER 降到 3.71%/4.53% 量级。

这说明：**sideTalk 不是纯语义问题，近场设备还必须利用空间、波束、距离、回声等声学证据。**

### 3.6 产业界公开证据矩阵

| 主体/产品 | 公开能力 | 公开指标 | 是否有 SDO 指标 | 证据等级 |
|---|---|---|---|---|
| Qwen-Omni-Realtime | full-duplex、semantic_vad、过滤附和/背景音 | 无 sideTalk 数值 | 未公开 | 官方文档 |
| Azure OpenAI Realtime | semantic_vad/server_vad、turn detection | 无 sideTalk 数值 | 未公开 | 官方文档 |
| StepAudio 3 Realtime | background speech rejection、AA 98.9 | AA 四项分数 | 否（AA 子集不含 talking_others/bkg_speech） | 厂商技术报告/自报 |
| Attention Labs SAS | pre-ASR 三分类、fail-closed | F1/时延/TV-FTR | 部分（“对人说”大类） | 厂商预印本/内部评测 |
| WearVox（产业场景研究） | AI 眼镜 side-talk rejection | 91.4% 最高、TTFT 2.18s | 部分（未细分 SDO/TPS） | 论文/公开数据 |
| MMW（产业场景研究） | 多麦克风 side speech suppression | WER 3.71%/4.53% | 否（ASR 级） | 论文/公开数据 |

> 本次检索未取得理想“语义拒识”、讯飞 AIUI“语义拒识”、小度“拒绝反应”、豆包 Seeduplex SDO 指标的一手可引用定义/公开评测，因此不纳入量化横向对比。它们可以作为“市场存在类似命名”的背景，但不能写成已验证事实。

---

## 4. 指标体系：推荐的计算口径

### 4.1 门控层指标

设：

- `TP`：应响应且响应
- `FN`：应响应但静默（false reject）
- `FP`：应静默但响应（false accept）
- `TN`：应静默且静默

则：

```text
Rejection accuracy = TN / (TN + FP)
False Accept Rate (FAR) = FP / (FP + TN)
False Reject Rate (FRR) = FN / (FN + TP)
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 = 2 * Precision * Recall / (Precision + Recall)
```

工业场景还应报告：

```text
FA/hour = 误接收次数 / 交互小时数
```

以及固定工作点：

- `FAR @ FRR=1%/2%/5%`
- `FRR @ FA/hour=0.5/1/2`
- `EER`：FAR=FRR 的点
- `DET`：全工作点曲线

**只报 EER 不够。** 产品部署一定落在某个阈值上，必须报固定工作点的 precision/recall/FAR/FRR。

### 4.2 行为层指标

对每个应静默事件：

- `Silence preservation`：没有语音，或只有不夺取话轮的短暂附和。
- `Resume rate`：模型继续此前话轮，而不是开新回答。
- `Respond rate`：模型把该事件当成新请求。
- `Stop latency`：重叠语音起点到模型停止说话。
- `Response latency`：重叠语音结束到模型下一次开始说话。
- `First response latency`：首个用户问题结束到首个模型响应开始。

对每个应响应事件：

- `Fresh-onset response rate`：请求结束时模型未说话，并在规定窗口内新发起语音。
- `Conditional answer accuracy`：只在模型确实响应时判断答案正确性。

**必须区分系统状态：**

- `idle` 时，拒识动作是“不开始”。
- `speaking` 时，拒识动作是“继续/恢复原话轮”，不是简单静默。

### 4.3 动作层指标

适用于工具型语音助手：

- `Mute accuracy`：该静音时是否静音。
- `Tool selection accuracy`：该调用工具时是否选对工具。
- `Wrong execution rate`：不该执行却执行的比例，通常比“多问一句”代价更高。
- `Switch mute rate`：同词反事实下，来源/距离变化后是否正确从 `Tool` 翻转为 `Mute`。
- `Answer accuracy`：该回答时内容是否正确。

**必须同时报正控和负控**，否则 `always-mute` 会在“拒识率”上作弊。

### 4.4 ASR 层指标

- WER/CER：只说明转写质量。
- Target-speaker WER：只说明目标说话人识别/抑制。
- 不能把 WER 降低直接解释为“正确拒识”，因为模型可能只是把旁人词删掉，却仍然执行了错误动作。

### 4.5 体验与上下文指标

- 恢复播报成功率：被打断/旁谈后能否接回原任务。
- 上下文保持：SDO/TPS 之后是否记得此前任务。
- 长期记忆：多轮后是否仍能引用先前约束。
- 误拒绝代价：用户需要重复几遍。
- 误接收代价：误执行工具、误下单、误发消息。
- P50/P90/P99 首音时延、stop latency、恢复时延。

### 4.6 统计报告规范

- 报样本量和 95% Wilson 置信区间。
- 类别不平衡时，报 per-class recall、macro-F1、混淆矩阵。
- 必须包含 `always-respond`、`always-mute`、`VAD-only`、`semantic VAD` 基线。
- LLM judge 必须报与人工标注的一致率；没有一致率时，结论降级。
- 多系统比较用配对 bootstrap 或 McNemar，不要只比小数点。

样本量对 90% 附近准确率的 95% CI 半宽（近似）：

| n | 约 ±CI |
|---:|---:|
| 200 | ±4.2 pt |
| 395 | ±3.0 pt |
| 582 | ±2.4 pt |
| 986 | ±1.9 pt |
| 2,000 | ±1.3 pt |

> 因此，200 条测试集上 88% 与 91% 的差异很可能不显著；报告里必须给 CI，不要把噪声写成洞察。

---

## 5. 评测设计蓝图（建议直接用于技术报告/内部基准）

### 5.1 场景矩阵

至少覆盖以下正交维度：

| 维度 | 取值 |
|---|---|
| 说话人 | 主用户、第三方、多人、媒体/设备 |
| 受话对象 | 助手、旁人、群体、自己、无明确对象 |
| 距离/通道 | 近场、远场、离轴、电视外放、耳机 |
| 系统状态 | idle、speaking、刚刚停止、恢复中 |
| 语义 | 请求、陈述、疑问、命令、附和、停顿 |
| 语言 | 中文、英文、中英混说 |
| 设备 | 单麦、多麦、AI 眼镜、车载、音箱 |

### 5.2 推荐测试集组成

1. **SDO 核心集**：主用户对旁人说话，声纹/音区与对助手说话一致；至少 500–1,000 条。
2. **TPS 集**：旁人插话在用户问题前/后；至少 500 条。
3. **Self-talk 集**：命令式自言自语、非命令式自言自语；至少 300 条。
4. **Media 集**：电视、短视频、语音消息、播客；至少 300 条。
5. **Backchannel/Pause 集**：附和、犹豫、换气；至少 500 条。
6. **Speaker-switch 反事实集**：同词、同上下文，仅改来源/距离/授权；至少 300 对。
7. **正控集**：真实用户请求，确保模型不是 always-mute；至少 500 条。

### 5.3 协议要点

- 实时流式回放，不能用离线整段音频。
- 固定系统状态：idle 与 speaking 分开测。
- 固定工作点：例如 `FRR≤2%` 或 `FA/hour≤1`。
- 统一 VAD/端点器，避免不同 harness 改变分母。
- 记录模型实际音频，不用 token 时间戳代替首音。
- 对同一场景做 explicit/implicit 两个版本，测语用线索。
- 对 SDO/TPS 保留“后续是否成为上下文”的标注，测“保留但不响应”。

### 5.4 推荐记分卡

| 维度 | 指标 | 目标 |
|---|---|---|
| SDO 拒识 | silence preservation / resume rate | 越高越好，同时看 FRR |
| TPS 拒识 | rejection accuracy | 分子场景报 |
| Self-talk | mute rate | 防误执行 |
| Media | false accept rate | 电视/外放单独报 |
| Backchannel | resume rate | 不新开回答 |
| Pause | premature response rate | 不抢话 |
| Speaker-switch | switch mute rate + target-tool | 防 always-mute |
| 真实打断 | respond rate + stop latency | 不能因拒识变迟钝 |
| 时延 | P50/P90 first audio、stop、resume | 产品门槛 |
| 质量 | conditional answer accuracy | 只在响应时判 |
| 上下文 | 3 轮后任务成功率 | 非指向语音可作上下文 |
| 统计 | CI、配对检验、baseline | 必须报 |

---

## 6. 关键缺口与研究机会

### 6.1 SDO 数据缺口

HumDial 的 SDO 训练集为 0；TPS 训练集只有 120 条。相比之下，URB/PH 各有 1,211 条训练样本。这意味着：

- 公开模型很可能没有见过足够的“主用户对旁人说话”监督。
- 现有高分可能来自语义先验、说话人变化或场景偏置，而不是真正的受话人推理。
- 研究机会：SDO 数据合成 + 真人录制 + 同词反事实 + 多通道远场。

### 6.2 非指向语音作为上下文

Duplex-MPE 的核心洞察是：旁人的话可能是后续请求的上下文，不能一律删除。研究机会：

- “保留但不响应”的上下文缓存。
- 旁谈中的实体、约束、答案如何进入后续回答。
- 长期记忆中的“谁说的、说给谁、是否可信”。

### 6.3 流式因果决策

多数 addressee 研究是离线分类；全双工需要因果、低时延、可校准的在线决策。研究机会：

- 部分语音下的 early addressee prediction。
- 决策后仍可修正的 anytime 模型。
- 置信度校准与 fail-closed 策略。

### 6.4 多人、多设备、授权边界

真实场景不只有“主用户 vs 助手”，还有：

- 多个合法用户。
- 多个设备同时在线。
- 电视/音箱/手机互相听见。
- 近场/远场和授权设备不同。

研究机会：设备身份、用户身份、空间关系、会话授权的联合建模。

### 6.5 中文与中英混说

HumDial 提供中英双语，但 SDO/TPS 子类样本仍少；多数其他基准以英文为主。研究机会：

- 中文称呼、语气词、间接请求、礼貌策略对 SDO 的影响。
- 中英混说中的受话人线索。
- 中文电视/短视频/外放语音的媒体 sideTalk。

---

## 7. 对技术洞察报告的写作建议

### 7.1 术语策略

建议在报告开头写：

> 本文使用 `sideTalk` 作为产品化统称，学术上位词为 `non-addressed speech`。它包含 SDO、TPS、self-talk、media/background speech、backchannel、pause 等子类；不同子类的正确动作和指标不同，不能合并为单一准确率。

### 7.2 引用时的“四必须”

1. **必须写单位**：轮次、动作、帧、词、小时。
2. **必须写工作点**：阈值、FRR、FA/hour。
3. **必须写系统状态**：idle 还是 speaking。
4. **必须写数据性质**：真实/合成、单通道/多通道、中文/英文、样本量。

### 7.3 不要写的四句话

- “某模型 sideTalk 准确率 98.9%”——除非该基准真的测了 SDO/TPS。
- “semantic VAD 就是 sideTalk 检测”——它主要是轮次结束检测。
- “WER 降低 4.95% 等于拒识提升 4.95 个百分点”——量纲不同。
- “总体 accuracy 80.9% 接近人类”——必须看 per-class 和多数类基线。

### 7.4 一句话结论

> 产业界已经能“做出来”，学术界已经能“分出来”，但还没有一个公开基准能同时做到：真实多人、流式因果、SDO/TPS 细分、固定工作点、时延/恢复、上下文保留和可复现评测。谁先补齐这套评测，谁就掌握 sideTalk 的定义权。

---

## 8. 参考来源与证据等级

### 8.1 学术论文/技术报告

| 编号 | 来源 | 链接 | 证据等级 |
|---|---|---|---|
| A1 | Full-Duplex-Bench v1.5 | https://arxiv.org/abs/2507.23159 | 论文/预印本 |
| A2 | HumDial Challenge | https://arxiv.org/abs/2601.05564 | 论文/预印本 |
| A3 | HumDial Full-Duplex Study | https://arxiv.org/abs/2604.21406 | 论文/预印本 |
| A4 | WearVox | https://arxiv.org/abs/2601.02391 | 论文/预印本 |
| A5 | VGBench | https://arxiv.org/abs/2609.32536 | 论文/预印本 |
| A6 | Duplex-MPE | https://arxiv.org/abs/2609.31948 | 论文/预印本 |
| A7 | TEIDAN Addressee Recognition | https://arxiv.org/abs/2501.16643 | 论文/预印本 |
| A8 | AMI Addressee/Turn-change | https://arxiv.org/abs/2606.17542 | 论文/预印本 |
| A9 | Continuous Addressivity | https://arxiv.org/abs/2607.15648 | 论文/预印本 |
| A10 | Adaptive KD for DDSD | https://arxiv.org/abs/2508.02801 | 论文/预印本 |
| A11 | Follow-up DDSD | https://arxiv.org/abs/2411.00023 | 论文/预印本 |
| A12 | MMW Side Talk Rejection | https://arxiv.org/abs/2507.05609 | 论文/预印本 |
| A13 | Attention Labs SAS | https://arxiv.org/abs/2604.08412 | 厂商预印本/内部评测 |
| A14 | StepAudio 3 Realtime | https://arxiv.org/abs/2609.14005 | 厂商技术报告/自报 |

### 8.2 官方产品文档

| 编号 | 来源 | 链接 | 证据等级 |
|---|---|---|---|
| B1 | Alibaba Cloud Qwen-Omni-Realtime | https://www.alibabacloud.com/help/en/model-studio/realtime | 官方文档 |
| B2 | 阿里云百炼 Realtime | https://help.aliyun.com/zh/model-studio/realtime | 官方文档 |
| B3 | Azure OpenAI Realtime Audio | https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio | 官方文档 |
| B4 | Artificial Analysis Speech-to-Speech Methodology | https://artificialanalysis.ai/methodology/speech-to-speech | 第三方评测方法 |

### 8.3 数据集/代码入口

- Full-Duplex-Bench：https://github.com/DanielLin94144/Full-Duplex-Bench
- HumDial-FDBench：https://github.com/ASLP-lab/HumDial-FDBench
- WearVox：https://huggingface.co/datasets/zlinao/WearVox

---

## 附录 A：指标速查表

| 指标 | 定义 | 适用层 | 常见误用 |
|---|---|---|---|
| Rejection accuracy | TN/(TN+FP) | 行为/门控 | 与总体 accuracy 混用 |
| FAR | FP/(FP+TN) | 门控 | 不写工作点 |
| FRR | FN/(FN+TP) | 门控 | 不写固定 FAR |
| EER | FAR=FRR 的点 | 门控 | 只报 EER 不报曲线 |
| FA/hour | 误接收/小时 | 门控 | 忽略交互时长 |
| Respond rate | 把重叠当请求的比例 | 行为 | 与正确率混用 |
| Resume rate | 继续原话轮的比例 | 行为 | 把“沉默”当 Resume |
| Silence preservation | 应静默时保持安静的比例 | 行为 | 允许附和的口径未说明 |
| Stop latency | 重叠起点→停止说话 | 时延 | 不写音频/VAD 口径 |
| Response latency | 重叠结束→下次开口 | 时延 | 与 first response 混用 |
| First response latency | 用户问题结束→首次响应 | 时延 | 不看拒绝场景 |
| Fresh-onset response | 请求结束时未说话且 5s 内新发起 | 行为 | 与 response presence 混用 |
| Conditional answer accuracy | 只在实际响应时判对错 | 质量 | 把沉默算错/算对 |
| Answering-window yield | 人类回答时能否让出窗口 | 行为 | 不看分母 |
| Switch mute rate | 同词反事实下正确静音 | 动作 | 不报正控 |
| WER | 词错误率 | ASR | 当拒识率用 |

## 附录 B：常见失败模式

1. **False accept**：把 SDO/TPS/media 当请求，误执行工具。
2. **False reject**：把合法用户请求当旁谈，用户需要重复。
3. **Late stop**：真实打断后停不下来。
4. **Premature resume**：用户还没说完就抢话。
5. **Always-mute**：为了拒识率牺牲所有正控。
6. **Context discard**：把后来有用的旁谈信息删掉。
7. **Cross-turn amnesia**：多轮后忘记谁说了什么。
8. **Speaker-switch confusion**：同词换来源后仍执行。
9. **Format mismatch**：模型会做对动作，但输出不符合解析器。
10. **Judge bias**：LLM judge 把“礼貌沉默”判成“无响应”。
