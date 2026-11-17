# 全双工交互中的 SideTalk：定义、指标与评测全景（2025–2026）

> 面向技术洞察报告的研究底稿 · 2026-11-16
> 证据分级：【论文】同行评审/预印本；【厂商】厂商论文或官方文档；【实测】论文报告的实验数字。

## 0. 结论先行

1. **"sidetalk" 不是一个统一的学术术语。** arXiv 摘要中精确使用 side-talk 的仅 5 篇（其中 4 篇与全双工/穿戴相关），学术界更常用 side conversation、third-party speech、speech directed at others、bystander speech、device-directed speech detection（DDSD）。
2. **定义正从"是不是对我说"升级为"该不该行动"。** 代表是 VGBench 提出的 agentic addressedness：把指代判断落到 silence / tool call / answer 三选一的动作空间。
3. **评测从单点分类准确率，转向配对行为指标。** silence preservation、BIR、PRR、switch mute rate 等，专门惩罚"听见了仍行动"和"为了不出错一直沉默"两种退化。
4. **当前系统最大的问题不是听不出 sidetalk，而是听出了仍然行动。** VGBench 中 Step-Audio 工具识别 96%/97%，但 speaker-switch 场景 mute 率仅 1%；全部裸模型最高 switch mute 仅 14%。
5. **产业界存在两套话语。** 设备厂（Meta、Amazon、Tencent）把 sidetalk 当一等公民；实时 API 平台（OpenAI/Azure、Deepgram、LiveKit）把它当作 VAD/打断处理的副作用，没有独立指标。

---

## 1. 概念边界：sidetalk 到底是什么

### 1.1 操作性定义

> **SideTalk：在全双工会话中，声学上可被设备拾取、但语用上不指向该设备/助手，因而助手不应据此发起或继续应答的语音。**

它至少包含四种可区分形态（Duplex-MPE 的 N1–N3 分类是目前最清晰的操作化）：

| 形态 | 典型例子 | 期望行为 | 学术术语 | 产业术语 |
|---|---|---|---|---|
| N1 提及但非请求 | "Aria 刚才说得对" | 沉默 | mention without request | mention / non-request |
| N2 对他人说话 | 用户转头："妈，帮我拿一下" | 沉默，保留上下文 | speech directed at others / talking to other | side conversation |
| N3 无指定受话人 | 自言自语："这个怎么弄来着" | 沉默 | self-talk / thinking aloud | self-talk |
| 第三方插入 | 旁人问路、邻桌聊天 | 拒绝，不进入任务状态 | third-party speech / bystander speech | side-talk / background speech |

### 1.2 必须排除的邻近现象

| 现象 | 为什么不是 sidetalk | 正确行为 |
|---|---|---|
| Backchannel（"嗯嗯""对"） | 不夺取话轮，是反馈 | 不打断，继续说 |
| Pause（句内停顿） | 话轮未结束 | 等待，不抢话 |
| Barge-in（"停，不是这个"） | 明确夺取话轮 | 立即停止并响应 |
| 噪声/音乐 | 非语音事件 | 降噪/忽略 |

Harness 论文（Tencent Americas + 武大）把这一点说得最清楚：**barge-in、backchannel、side-talk 可以有几乎相同的时长和重叠形态，但要求完全不同的动作；VAD 或固定静音阈值无法区分，标签必须来自"作者意图"而非重叠几何。**

### 1.3 判定四要素

1. **谁在说**（说话人身份/声纹）
2. **从哪说**（近场/远场、方向、多通道空间线索）
3. **对谁说**（语义指向、称呼、 gaze/上下文）
4. **想干什么**（是否寻求话轮：turn / continue / backchannel / barge-in / aside）

> 洞察：sidetalk 本质是**语用问题**，不是声学问题。但 2025–2026 的最强工程增益恰恰来自声学侧（多通道/空间音频），说明当前系统的语用推理还很弱。

---

## 2. 学术界：三条脉络与一套指标词典

### 2.1 脉络演进

| 阶段 | 时间 | 核心问题 | 代表 |
|---|---|---|---|
| ① 指代检测（DDSD） | 2018– | 这句话是不是对设备说的？ | Amazon DDSD；wake-word 误触发抑制 |
| ② 全双工重叠处理 | 2025–2026 | 重叠时该响应/等待/停止？ | Full-Duplex-Bench v1→v1.5、Talking Turns、HumDial |
| ③ 选择性参与 | 2026– | 多说话人中，助手何时该说/该沉默/该停？ | WearVox、VGBench、Duplex-MPE、MSI-Bench、DuplexLedger |

### 2.2 代表工作对照

| 工作（时间/机构） | 场景与数据 | sidetalk 的定义方式 | 指标 | 关键结果【实测】 |
|---|---|---|---|---|
| **Full-Duplex-Bench v1.5**（ICASSP 2026，NTU） | 在用户–助手对话中注入 4 类重叠：Interruption / Backchannel / **Talking to Other** / **Background Speech** | Talking to Other = 用户转向他人；Background = 远场第三方谈话 | 分类型行为判定 + 交互时序 + 自适应语音特征 | 论文引用：重叠占对话轮次 40%+ |
| **HumDial Challenge**（ICASSP 2026） | Rejection 类含 4 子场景：实时 backchannel、pause、**Third-party Speech**、**Speech Directed at Others** | 非目标语音应被拒绝；只有 Resume 算对 | 二值 rejection accuracy（+ 延迟） | Third-party 测试 600 条；Speech Directed at Others 测试 200 条 |
| **WearVox**（Meta，2025-12） | 3,842 段第一视角多通道眼镜录音；Side-Talk Rejection 任务 1,082 条（582 sidetalk + 500 有效请求） | 非设备指向语音（佩戴者/对话伙伴/旁观者均可发起），输出 [Mute] | Side-talk rejection accuracy | Gemini 2.5 Flash 88.2%；多通道训练 85.4→**93.9%** |
| **VGBench**（HKUST+腾讯 LIGHTSPEED，2026-09） | 1,018 条：395 side-talk、223 self-talk、400 speaker-switch 配对 | **agentic addressedness**：同一句话在不同声源/场景下应触发不同动作 | Side-talk correct、Self-talk mute、Switch mute + 正控制 | 裸模型 side-talk 32.4–41.0%；最高 switch mute 14%；SFT 后 91.3% |
| **Duplex-MPE**（北大等，2026-09） | 2,000 场景 × 显式/隐式 = 4,000 场；3–4 人 + 助手连续音频 | N1 提及/N2 对他人/N3 自言自语均须沉默；N4 测试"人类自行解决后是否停" | Fresh-onset、Answer acc、**Silence preservation**、Answering-window yield | MiniCPM-o 4.5 silence 0.924；Voila 0.835；Moshi 0.273；Freeze-Omni **0.0002** |
| **MSI-Bench**（Amazon，2026-09） | 1,152 条中英多说话人场景 | 未被指代时的"抢答"与"被打断后能否说完" | **BIR**（旁观者干扰鲁棒性）↑、**PRR**（过早响应率）↓ | Gemini 3.1 Pro BIR 78.0 / PRR 19.8；GPT Realtime 2.1 xhigh BIR 73.7 / PRR 9.4 |
| **DuplexLedger**（2026-10） | 双语受控会话 + 事务记忆账本 | 对他人说话 = 受控干扰项，不得响应、不得写入任务状态 | 记忆正确率 + distractor rejection | 51.4% 事件为 Ignore 类 |
| **MMW**（Meta，ASRU 2025） | 智能眼镜多麦 + Whisper | side speech = 附近他人语音/重叠谈话，属**干扰**而非对话行为 | 帧级抑制 + WER | 噪声下 WER 相对降 4.95% |
| **Multi-Channel Differential ASR**（Meta+OSU，Interspeech 2026） | 眼镜佩戴者语音识别 | side-talk 作为 ASR 干扰源 | 轻量 side-talk 检测 + WER | 相对 WER 降 up to 18.0% |

### 2.3 指标词典（按决策链分层）

**A. 决策层（说还是不说）**
- Rejection accuracy / Mute accuracy：负样本被正确沉默的比例
- **PRR（Premature Response Rate）**：尚未被指代就抢答的比例（越低越好）
- FAR / FRR / EER：把 sidetalk 当二分类时的误接受/误拒绝
- Switch mute rate：同词换声源后正确静音的比例（VGBench 核心）

**B. 行为层（沉默得是否自然、恢复得是否干净）**
- **Silence preservation**：应沉默窗口内"无语音或仅短确认不夺话轮"的比例
- **BIR（Bystander Interference Robustness）**：被打断后仍能把原答案说完且通过 rubric 的比例
- Resume correctness：sidetalk 结束后正确回到原任务
- Stop latency / First response latency / Resume latency

**C. 任务层（有没有把 sidetalk 污染进任务）**
- Answer accuracy、Tool-call accuracy
- WER（ASR 视角）
- Memory contamination rate（DuplexLedger 式事务校验）

**D. 校准层（防刷分）**
- Addressing sensitivity：显式 vs 隐式指代的响应率差（Duplex-MPE 中 Gemini 3.1 Pro 达 **64.3pp**）
- Over-silence rate / always-mute baseline
- 配对反事实一致性（同词不同源、同场景不同指代）

### 2.4 评测方法学

| 方法 | 做法 | 优点 | 风险 |
|---|---|---|---|
| 受控重叠注入 | 在模型说话时插入脚本化 sidetalk（FDB v1.5） | 可控、可复现、可测时序 | 生态效度低 |
| 脚本 + 真人录制 | LLM 写脚本，演员录制（HumDial） | 自然度较高 | 成本高、难扩展 |
| 真实第一视角多通道 | 眼镜实采，标注说话人/距离/方位（WearVox） | 最接近产品 | 不可控、隐私敏感 |
| 配对反事实 | 同词换声源/距离/指代（VGBench、Duplex-MPE、Same Words Different Actions） | 能分离"识别"与"行动" | 构造复杂 |
| 多说话人连续场景 | 3–4 人共享对话，助手是参与者之一（Duplex-MPE、MSI-Bench） | 接近真实多方交互 | 评分依赖语义 judge |
| 事务记忆探针 | sidetalk 作为 distractor，检查是否写入状态（DuplexLedger） | 抓到"隐性污染" | 任务特定 |

### 2.5 学术界洞察

1. **"沉默"已经被承认为一等输出。** Duplex-MPE 把 silence preservation 单独计分，而不是把它塞进 accuracy。
2. **单指标会被刷分。** 只要允许 always-mute，rejection accuracy 就能接近满分；因此 2026 年的新基准普遍采用配对指标 + 正控制。
3. **失败模式高度一致：行动惯性。** 模型能识别工具/请求，却不愿放弃行动；这是策略层问题，不是感知层问题。
4. **过度沉默是另一种退化。** TwS 把 self-talk mute 拉到 85.7%，但 side-talk 只剩 23.0%——它学会了闭嘴，没学会分辨。
5. **隐式指代仍是空白。** 显式点名时系统尚可；一旦靠上下文推断"这句话其实是对我说的"，性能断崖。

---

## 3. 产业界：四条路线，四套 KPI

产业界不使用统一术语，按产品形态分成四条路线：

### 3.1 路线一：智能眼镜/穿戴（Meta 主导）

**定义**：side speech / side-talk = 附近他人语音或重叠谈话，是对佩戴者语音识别的干扰；产品上要求"非设备指向语音不触发助手"。

**做法与指标**：
- MMW（ASRU 2025）：多麦原始波形融合 + 帧级 diarization + 多尺度 GRPO；指标是 **WER**（噪声下 -4.95%）
- Multi-Channel Differential ASR（Interspeech 2026）：beamformer + 麦克风选择 + 轻量 side-talk 检测；**相对 WER -18.0%**
- WearVox（2026）：把 Side-Talk Rejection 做成独立任务，输出 [Mute]；**rejection accuracy** 85.4–88.2%，多通道 93.9%

> 产业洞察：眼镜厂的 sidetalk 首先是**声学/前端问题**（多麦、波束、声源分离），因为功耗和延迟不允许跑重型语用模型；"该不该回答"被降级为"这段语音要不要送进 ASR"。

### 3.2 路线二：语音助手/多说话人（Amazon）

**定义**：device-directed speech detection（DDSD）——区分"对设备说的"与"背景语音"，用于拒绝误唤醒、支持免唤醒追问。

**演进**：
- 2018：二分类器（DDSD），指标是误唤醒/误接受
- 2026：MSI-Bench 把问题升级为多说话人协作任务，指标变成 **BIR（被打断后能否说完）** 与 **PRR（是否抢答）**

> 产业洞察：Amazon 的指标已经从"分类准确率"转向"任务是否被 sidetalk 破坏"，这与学术界的 BIR/PRR 合流。

### 3.3 路线三：实时语音 API / 平台（OpenAI/Azure、Google、Deepgram、LiveKit）

**定义**：**没有 sidetalk 概念**。它们把问题拆成 turn detection、VAD、endpointing、interruption handling。

**证据**：
- Azure/OpenAI Realtime：turn_detection = none / server_vad / semantic_vad；semantic_vad "less likely to interrupt the user"
- Deepgram：endpointing 基于 VAD 检测"足够长的停顿"
- LiveKit：adaptive interruption handling "distinguish true interruptions from conversational backchanneling"；提供 false interruptions 配置
- Google Gemini Live：服务端自管 turn-taking（LiveKit 文档说明其不支持客户端接管）

**指标**：false interruption rate、打断响应延迟、P50/P95 端到端延迟、误唤醒率。

> 产业洞察：平台型厂商的 KPI 是**延迟与打断体验**，不是 sidetalk 拒答率。sidetalk 在这条路线里是"噪声"的一种，靠 VAD/降噪/语义 VAD 间接处理。这导致一个盲区：**没有人为"该沉默却回答了"负责。**

### 3.4 路线四：基准/挑战赛（Tencent、AISpeech）

- **Tencent LIGHTSPEED**：VGBench（agentic addressedness）+ Harness（turn/continue/backchannel/barge-in/**aside** 的事件语法）
- **AISpeech（Hui Bu 等）**：ICASSP 2026 HumDial Challenge，把 Rejection 做成正式赛道

> 产业洞察：这两家在做"学术指标的工程化"，把 sidetalk 从研究概念变成可提交、可排名的任务。这是 2026 年最重要的产业–学术接口。

### 3.5 产业指标 vs 学术指标

| 维度 | 产业界 | 学术界 |
|---|---|---|
| 主指标 | 误唤醒/小时、false interruption rate、P95 延迟、A/B 胜率、投诉率 | rejection acc、PRR、BIR、silence preservation |
| 数据 | 真机采集、灰度流量、红队脚本 | 受控录制、合成、配对反事实 |
| 判定 | 人工听测 + 业务指标 | 自动 judge + 人工抽检 |
| 优化目标 | 用户体验/成本 | 能力刻画/可复现 |
| 盲区 | 缺"误响应成本"建模；跨设备不可比 | 生态效度弱；judge 可靠性参差 |

---

## 4. 产业 vs 学术：定义与评测矩阵

| 路线 | 代表 | sidetalk 定义 | 核心指标 | 评测载体 | 强项 | 短板 |
|---|---|---|---|---|---|---|
| 穿戴/眼镜 | Meta | 非设备指向语音（干扰） | rejection acc、WER | 真机多通道 | 最接近产品 | 缺语用/多轮 |
| 语音助手 | Amazon | 非 device-directed | DDSD acc、BIR、PRR | 多说话人任务 | 任务级 | 公开数据少 |
| 实时 API | OpenAI/Azure、LiveKit、Deepgram | 无独立定义（VAD/打断） | false interruption、延迟 | 线上流量 | 真实规模 | 无 sidetalk 验收 |
| 基准/赛事 | Tencent、AISpeech | addressedness / rejection | switch mute、rejection acc | 脚本+合成 | 可复现、可排名 | 生态效度 |
| 学术综合基准 | Duplex-MPE、MSI-Bench、WearVox | 多说话人选择性参与 | silence preservation、BIR、PRR | 连续多方音频 | 维度全 | 评分成本高 |

---

## 5. 八条洞察结论（可直接写进报告）

1. **术语碎片化本身就是成本。** 同一现象在四类团队里有四个名字、四套 KPI；跨团队对齐的第一步不是模型，而是术语表。
2. **sidetalk 的定义正在"动作化"。** 从"是否对设备说"（分类）到"是否该执行动作"（策略），VGBench 的 agentic addressedness 是标志。
3. **沉默是一等输出，但不能单独优化。** Duplex-MPE 证明 silence preservation 与回答能力正交；Freeze-Omni 0.0002 vs MiniCPM-o 0.924 就是极端例证。
4. **主要失败模式是"行动惯性"，不是"听不见"。** 工具识别 96% 却不 silence（Step-Audio switch mute 1%），说明缺的是抑制机制而非感知能力。
5. **过度沉默是真实退化路径。** TwS 的 self-talk 85.7% / side-talk 23.0% 说明"学会闭嘴"与"学会分辨"是两种能力；评测必须成对报告。
6. **隐式指代是下一道分水岭。** 显式点名时差距不大；隐式指代下 Gemini 3.1 Pro 的显隐响应率差达 64.3pp，语音系统甚至无显著差异——语用推理基本缺席。
7. **空间音频是当前最确定的工程杠杆。** Meta 多通道把 rejection 从 85.6% 提到 93.9%，ASR 相对 WER 降 18%；短期 ROI 高于堆语用模型。
8. **产业界缺一个"误响应成本"指标。** 误响应（在 sidetalk 上回答）与漏响应（该答不答）代价不对称，但现有指标多为等权；建议引入 cost-weighted score，并按场景（驾驶/会议/眼镜）分别标定。

---

## 6. 给报告的落地建议：一套可复用的 sidetalk 评测协议

**负样本（4 类）**：N1 提及非请求、N2 对他人说话、N3 自言自语、远场旁观者插入。
**正样本（3 类）**：显式直接请求、隐式指代请求、sidetalk 结束后的恢复请求。

**六个核心指标**：
1. PRR ↓（过早响应率）
2. Rejection / Mute accuracy ↑
3. Silence preservation ↑（允许短确认、不夺话轮）
4. BIR ↑（被打断后原答案仍通过）
5. Resume latency ↓（sidetalk 结束到恢复）
6. Answer / Tool accuracy ↑（正样本不被沉默误伤）

**报告维度**：显式/隐式 × 近场/远场 × 安静/噪声 × 单说话人/多说话人。

**防刷分三件套**：always-mute baseline、配对反事实（同词不同源）、cost-weighted 汇总。

---

## 7. 主要参考（精选）

- Full-Duplex-Bench v1.5 — arXiv:2507.23159（ICASSP 2026）
- Full-Duplex-Bench — arXiv:2503.04721（ASRU 2025）
- Full-Duplex-Bench v2 — arXiv:2510.07838
- HumDial Challenge — arXiv:2601.05564；综合研究 arXiv:2604.21406（ICASSP 2026）
- WearVox（Meta）— arXiv:2601.02391
- VGBench（HKUST + Tencent LIGHTSPEED）— arXiv:2609.32536
- Duplex-MPE（北大等）— arXiv:2609.31948
- MSI-Bench（Amazon）— arXiv:2609.24812
- DuplexLedger — arXiv:2610.27581
- A Harness for Synthesizing Diverse Naturalistic Full-Duplex Conversations（Tencent Americas + 武大）— arXiv:2609.28806
- MMW（Meta）— arXiv:2507.05609（ASRU 2025）
- Multi-Channel Differential ASR（Meta + OSU）— arXiv:2509.14430（Interspeech 2026）
- Device-directed Utterance Detection（Amazon）— Amazon Science, 2018
- LiveKit Turns / Adaptive interruption 文档；Azure OpenAI Realtime 文档（semantic_vad）；Deepgram Endpointing 文档

> 备注：2026 年部分工作为预印本，未经同行评审；产业侧公开指标有限，本文对未公开内部指标不做推断。

---

## 8. 与本地 `sidetalk-eval` 项目的口径对齐（补充）

> 本节基于 `~/repos/projects/sidetalk-eval`（2026-11-03）的实际设计与首轮结果，用于把上文的全景落到本项目口径。

### 8.1 场景映射

| 学术口径 | 产业口径 | 本项目场景 | 说明 |
|---|---|---|---|
| SDO / speech directed at others | side conversation | **S1** 主用户→旁人 | 核心场景，与 S0 文本同形 |
| TPS / third-party speech | side-talk / background speech | **S2** 旁人→主用户；**S3** 旁人↔旁人 | 以声纹/DoA 为主判据 |
| —（无对应） | media / electronic voice | **S4** 媒体/电子人声 | 本项目独有，家庭音箱高频 |
| device-directed request | device-directed speech | **S0** 真指令/答句 | 对照场景，测拒识代价 |
| self-talk | self-talk | 单列（不进 S1–S4） | VGBench/Duplex-MPE 同样单列 |
| URB / PH | backchannel / pause | 语义 VAD 模块 | 属“时机问题”，不属归属问题 |

### 8.2 指标映射

| 学术指标 | 本项目指标 | 备注 |
|---|---|---|
| Rejection accuracy | 分场景拒识率（S1–S4） | 逐场景考核，不做单一总分 |
| FAR / PRR | 误响应率 FAR（加权） | 按真实流量权重聚合 |
| — | **误执行 = 0（一票否决）** | 比学术指标更严，产品级约束 |
| FRR | 漏响应率 FRR（S0） | 承诺 ≤3%，内部目标 ≤2% |
| — | clarify 率 ≤2% | 低置信度轻确认，学术基准少见 |
| silence / response latency | 静默决策延迟 ≤500ms | partial ASR + L1/L2 窗内闭合 |
| BIR | 暂缺 | 建议补：sidetalk 打断后原答案恢复正确率 |
| addressing sensitivity | 暂缺 | 建议补：S1 显式 vs 隐式指代子集 |

### 8.3 三条被自家数据验证的洞察

1. **过度沉默的 trade-off 真实存在。** qwen-plus 提示词 v1→v3：S1 从 57.5% 升到 75.8%（+18.3pt），FRR 从 6.7% 涨到 21.7%。这与学术界 TwS 的“self-talk 85.7% / side-talk 23.0%”是同一退化模式——模型学会闭嘴，没学会分辨。
2. **单指标刷分有实证。** A0（TF-IDF+LR）S1 95.6%、S2 100%，但 FRR 61.7%——把真指令大量吞掉。说明只看拒识率会选出不可用系统；必须 FRR + 误执行 + clarify 共同约束。
3. **文本同形是硬天花板。** HumDial 子集 S2 仅 32%：没有说话人标记时，“旁人问他”和“他问助手”在文本上同形。这与 WearVox 多通道 85.4→93.9% 相互印证：S1/S2 的下一步不是换更大的文本模型，而是声纹/DoA/双声道。

### 8.4 对前文结论的两处修订

- 前文把 self-talk 列为 sidetalk 形态之一；按本项目口径应**单列**（VGBench、Duplex-MPE 也单列），产品模块不纳入 v1 支持清单。
- 前文说“产业界无 sidetalk 验收标准”，更准确的说法是：**平台型实时 API 无独立标准；设备厂有内部标准**——本项目（S0–S4 + 拒识率/FAR/FRR/误执行/clarify/延迟）就是一个典型的产品级标准样本。

