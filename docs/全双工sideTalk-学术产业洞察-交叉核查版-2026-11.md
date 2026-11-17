# 全双工交互中的 Side Talk：定义、指标与评测 —— 学术界与产业界技术洞察报告

> 调研与撰写：技术洞察（AutoClaw agent）｜ 2026-11-16 ｜ 方法：6 路并行深度调研（≥78 次独立检索）+ 关键来源逐字核查 ｜ 信度分级见第 11 节
> 读者提示：本报告所有关键结论均标注来源编号 [S#]，来源清单见第 10 节；「未核实」条目明确降级，不作结论引用。

---

## 00 摘要：十条核心结论

1. **side talk 不是新问题，而是 25 年前就有名字的老问题的新马甲。** 2001 年 Oppermann 等人在 EUROSPEECH 提出 "Off-Talk"（与 on-talk 二分），指"说话人对第三方或自己的、非指向计算机系统的语音"[S10][S11]；2024-2026 全双工浪潮中，它以 side talk / side conversation / talking to others / off-talk / side-talk rejection 等近义词重新出现，但**至今没有统一定义**。
2. **学术界 2025-2026 年已把 side talk 做成可评测对象**，代表性锚点有四个：Full-Duplex-Bench v1.5 的 "talking to others" 场景 [S1]、Duplex-MPE 的 N1/N2/N3 沉默标签与 silence preservation 指标 [S3]、ECHO 的 off-talk 条件与 pair accuracy [S4]、DuplexLedger 的 dedicated side-talk stage [S5]。
3. **同一个词横跨两个问题域，引用文献必须先问"主体是谁"**：可穿戴/ASR 社区的 side talk 主体是**旁观者**（声学层拒绝任务，如智能眼镜的 side-talk rejection [S8][S9]）；全双工对话社区的 side talk 主体常是**正在与系统对话的用户本人**（对话策略层：不接话、不让权、不打断主线）[S1][S3]。
4. **学术界指标已收敛出一个"三件套"**：行为分类（Respond / Resume / Uncertain / Unknown，LLM-as-judge）＋ 沉默保持类指标（silence preservation / side-talk rejection）＋ 时延对（stop latency / response latency）；辅以韵律适应（UTMOSv2、pitch/intensity）与人类基线（轮换间隔约 200ms）[S1][S3]。
5. **产业界（无论国际国内）几乎不用 "side talk" 一词**：国际口径是 background speech / device-directed speech (DDSD) / interruption sensitivity [S12][S13][S34-39]；国内口径是抗干扰、无关对话、抢话、误打断、误回复、动态判停（字节 Seeduplex 官方词表）[S28]；对字节/火山/达摩院 6 个官方页面全文正则检索，`sidetalk|side talk|旁白|侧说话` **0 命中** [S28][S29][S30][S14]。
6. **国内产业已形成一套自有的、指标化的中文术语体系**：Seeduplex（2026-04）宣称复杂场景误回复率与误打断率相对半双工减半、抢话比例 -40%、判停延迟 -250ms、打断响应延迟 -300ms、判停 MOS +8%、对话流畅度 MOS +12%、A/B 通话满意度绝对值 +8.34% —— 全部为**相对自家上一代的相对值或未公开协议的评测值**，跨厂商不可比 [S28]。
7. **机制上收敛为两条技术路线**：声学层拒绝（去噪、VAD、DDSD 检测器级联、车载多音区锁定）与语义层选择参与（状态机、Full Duplex Predictor、语义打断、VAP 轮次预测）；端到端原生全双工模型正把判定内化进主模型 [S14-S23][S28][S31][S32]。
8. **所有官方文档都承认"拦截强度 vs 响应速度"的权衡**：Vapi 承认防背景打断会 "slightly delay the detection of speech onset" [S35]；阿里云百炼承认开启语义判停与拒识"可能导致对话延迟增加" [S32]；学术侧 v1.5 总结为 repair-first（300ms 内让权但易误触发）vs continuity-first（保流畅但多秒 double-talk）[S1]。
9. **评测成熟度存在明显代差**：学术已有场景化、自动化、可复现的基准族（FDB v1→v1.5→v2/v3、Duplex-MPE、ECHO、FD-Bench、HumDial、WearVox），且出现方法学自省（指标选择改变排名、over-yielding 偏置、半双工模型"协议不可评"）；产业公开指标只有硬件唤醒层的 FAR/FRR（成熟）与大厂相对值宣称（不可比），国际平台层完全黑箱，国内第三方评测（CAICT/SuperCLUE）未检索到全双工旁白专项 [S1-S6][S13][S28][S41][S49]。
10. **"会沉默"≠"听懂了不该接"**：Duplex-MPE 的显式/隐式称呼对照显示，文本大模型对名字线索敏感（响应率差 64.3 个百分点），而五个语音模型全部不显著（最小 p=0.2365）——语音系统旁白拒绝得好，可能只是"普遍不响应"的副产品；评 side talk 必须同时看应答正确率 [S3]。

---

## 01 概念界定：什么是 side talk

### 1.1 工作定义

**全双工（full-duplex）语音交互**：系统在说话的同时持续聆听，双方的语音流可以重叠，无需轮流占用信道 [S7][S28]。

**Side talk（旁白/旁语/侧说话）**：在全双工交互中，**声学上进入系统拾音范围、但语用上不指向系统的人声**——典型三类：(a) 正在对话的用户转头对第三人说话；(b) 旁观者之间的对话；(c) 用户自言自语/思考出声（thinking aloud）。系统理想行为：不响应、不让出话轮、不遗忘主线任务，事后能平滑接回。

学术操作化定义（逐字）：

| 文献/基准 | 术语 | 原文定义（verbatim） |
|---|---|---|
| Full-Duplex-Bench v1.5（v1 HTML）[S1] | side conversation | "side conversations, where the user briefly addresses someone else while the model is speaking" |
| Full-Duplex-Bench v1.5（最新版摘要）[S1] | talking to others | 四场景之一："user interruption, user backchannel, talking to others, and background speech" |
| DuplexLedger [S5] | side-talk stage | "Speech directed to another person is played through a dedicated side-talk stage and is marked as not addressed to the assistant." |
| Duplex-MPE [S3] | N2/N3 标签 | "N2: the turn is addressed to someone or something other than Aria... N3: speech without a designated addressee, including self-talk and thinking aloud. N1, N2 and N3 require silence." |
| ECHO [S4] | off-talk | "It additionally includes off-talk examples for diagnosing unnecessary yielding."（目标动作 Keep——系统不应让出话轮） |
| 数据合成 Harness [S26] | speech addressed to a third party | "must distinguish ... an interruption that requests a turn from a brief acknowledgment or speech addressed to a third party" |

### 1.2 术语演化时间线

| 时间 | 术语 | 出处 | 语义重心 |
|---|---|---|---|
| 1972/1981 | side sequence / byplay、ratified participant vs overhearer | Jefferson；Goffman《Forms of Talk》 | 会话分析源头：参与框架与从属序列（思想先祖，非工程术语）[S11a] |
| 2001 | **Off-Talk**（与 on-talk 二分） | Oppermann et al., EUROSPEECH 2001 "Off-Talk – A Problem for Human-Machine-Interaction" | HCI/语音界面：说话人对第三方或自己、非指向计算机的语音 [S10][S11] |
| 2008-2019 | off-talk 检测、SmartWeb 语料 | Batliner/Hacker/Schiel 等 | 智能语音助手时代的检测任务 [S11] |
| 2010s-2020s | **device-directed speech detection (DDSD)** | Amazon Science、Apple、IEEE | 智能音箱：这句话是说给设备的还是背景语音；FAR/FRR 评测 [S12][S13] |
| 2010s-2020s | **addressee detection / recognition** | Microsoft、ACM 2026、多方对话社区 | 多方对话：这一轮的预期接收者是谁（含 gaze 多模态）[S12a] |
| 2025-07 | **side-talk rejection**（可穿戴） | MMW（智能眼镜多麦克 Whisper）；WearVox 五任务之一 | 主体=旁观者；麦克风阵列+ASR 层的拒绝/抑制 [S8][S9] |
| 2025-07 | **side conversation → talking to others** | Full-Duplex-Bench v1.5 | 全双工基准场景（v1→新版改名）[S1] |
| 2026 | **side-talk stage / off-talk / Sidetalk 类目** | DuplexLedger；ECHO；CoDeTT | 全双工协议与诊断基准中的标准事件 [S4][S5][S50] |

### 1.3 概念边界（最容易写错的部分）

| 概念 | 与 side talk 的区别 | 一句话判据 |
|---|---|---|
| barge-in / interruption（插话/打断） | 争夺话轮，指向当前说话方 | v1.5："speaks over others, violating their turn to speak"；ECHO 目标动作 Yield [S1][S4] |
| backchannel（反馈语/附和） | 不夺权，但指向当前说话方 | v1.5："signal attention but do not claim the floor"；ECHO 目标动作 Keep [S1][S4] |
| ambient/background speech（环境/背景语音） | 共享声学通道但非对话参与方（电视、广播、远处旁人） | v1.5："shares the acoustic channel but is not directed at the system" [S1] |
| side talk（旁白） | **对话参与方**（用户或在场者）说出、但指向第三方/自己 | v1.5："the user briefly addresses someone else" [S1] |
| false trigger / 误触发 | side talk 拒绝失败的下游后果（把旁白当指令响应） | 唤醒词时代为误唤醒；全双工时代为误回复 [S13][S28] |
| sidetone（侧音） | 耳机/电话里用户**自己**声音的回放，与 side talk 无关 | 电信术语，仅词形相近 [S39] |
| Google Duplex | 外呼任务型 agent，非全双工旁白问题 | 概念辨析必备 [S39a] |

**两处高频误用**：① 把 "off-talk rate" 当"旁白发生率"——ECHO 里它是模型在 off-talk 条件上的错误率（低=好）[S4]；② 把可穿戴 side-talk rejection 与全双工 side talk 混为一谈——前者是 ASR 前端的声学拒绝，后者是对话策略的语义选择参与 [S3][S8]。

---

## 02 学术界洞察（一）：定义操作化与机制流派

### 2.1 定义操作化的四个基准锚点

- **Full-Duplex-Bench v1.5 [S1]**：把重叠语音拆成四类可控事件——user interruption / user backchannel / talking to others / background speech（v1 HTML 旧名：side conversation / ambient speech），每个 trial 用 4 要素参数化（上文查询、重叠时机、重叠内容、说话人身份/声学通道），以重叠结束时刻切分 pre/post-overlap 行为窗。
- **Duplex-MPE [S3]**：把"何时开口/沉默/停止"变成标签问题——T（对助手的直接请求）、N1（提及但未请求）、N2（对他人/他物）、N3（无指定受话人，含自言自语）、N4（应答后须停）；N1/N2/N3 均要求沉默。
- **ECHO [S4]**：成对改写设计——同一重叠转写、两种前置上下文，一个要求 Yield、一个要求 Keep；另含 off-talk 样本诊断"不必要的让权"；指标 pair accuracy 对成对成员同时判对才给分，杜绝"固定动作策略"刷分。
- **DuplexLedger [S5]**：把 side-talk 事件嵌入持久记忆协议——旁白语音经专用 stage 注入并标注"非指向助手"，观测窗 1.2 秒，考察"该忽略的没忽略"是否污染记忆。

### 2.2 机制五大流派（side talk 在哪里被处理）

| 流派 | 代表 | 机制 | side talk 的处理位置 | 局限 |
|---|---|---|---|---|
| ① 双流并行隐式学习 | Moshi [S15]、OmniFlatten [S17]、LSLM | 用户声道+自身声道同时建模、时间块交错 | **无显式判定**——旁人语音原样进入用户流，靠训练数据分布隐式学"何时响应" | v1.5 实测：Moshi 在 talking_other 场景 Unknown 高达 0.59 [S1] |
| ② 显式状态机 | neural FSM [S20]、SALMONN-omni（user/echo/assistant 三流 80ms 交错+动态状态控制 token）[S16]、Freeze-Omni（状态切换）[S18]、VITA-1.5（双阈值 VAD 守卫）[S19] | listening/thinking/speaking 状态转移 | 状态转移规则+背景声守卫（工程级） | 阈值硬编码，易误杀 backchannel、状态边界引入延迟 |
| ③ 全双工预测模块（学术化中间态） | MinMo Full Duplex Predictor [S14]（用 LLM 语义决策"继续说/停/轮次"，4000 小时真人长对话训练） | 预测式轮次控制 | 面向轮次而非受话人；全文 0 处 side-talk 术语 | 仍需与 ASR/受话人判定协同 |
| ④ VAP 轮次预测 | VAP（Ekstedt & Skantze）[S21]、三方 VAP（Interspeech 2025）、MuVAP（多模态+人脸轨迹）[S21] | 自监督预测双方未来语音活动，流式输出 Shift/Hold | 天然容纳多方重叠；多模态版最接近"谁在说、是否轮到我" | 只做活动预测，无语言内容生成，需与 LLM 级联 |
| ⑤ DDSD/addressee 检测器级联 | Amazon 系 DDSD 论文群 [S22]、多模态 DDSD（LLM）[S22] | VAD 后接二分类器："这句话是否指向设备" | **显式处理**：非指向则静默 | 级联延迟与错误传播；多为唤醒词触发后的 follow-up 场景 |

**2026 年的新动向**：side-talk 场景进入训练数据合成——Harness（LLM 编剧→意图标注→双通道合成）[S26] 与 DuplexDrama（6,400 段双语/800 小时）[S25] 把旁白编码为可编程"意图事件"；Lychee-FD（ACL 2026）报告了 incidental side-talk 的处理难度 [S27]。另须注意：2026 年有论文直言"目前多数端到端语音 LLM 仍以半双工方式运行，如 Kimi-Audio、Step-Audio 2、MiMo-Audio、GLM-4-Voice"——半双工是开源界的事实常态 [S24]。

---

## 03 学术界洞察（二）：指标与基准

### 3.1 指标三件套（可直接引用的"金指标"）

1. **行为分类**：post-overlap 语音 → ASR 词级时间戳（parakeet-tdt-0.6b-v2）→ LLM（GPT-4o）归入 Respond / Resume / Uncertain / Unknown / silence 五类 [S1]。
2. **沉默保持类**：Duplex-MPE `silence preservation`——"Fraction of N1, N2 and N3 windows with no speech or only a brief acknowledgement that does not take the floor"；WearVox `side-talk rejection`；HumDial `complete rejection`（双通道真人对话，四子场景）[S3][S9]。
3. **时延对**：`stop latency`（重叠语音起点→模型停止说话）；`response latency`（重叠语音结束→模型下一次开口）；人类基线约 200ms（Levinson & Torreira，经 v1.5 引用）[S1]。
辅助：韵律适应（pitch/intensity/speaking rate/UTMOSv2 MOS，配对 t 检验 p<0.05）[S1]；FTO（Floor Transfer Offset，话权转移间隔，可负=重叠）[S51]；VAP 的 Shift/Hold 预测 [S21]；显式/隐式称呼 paired difference（McNemar 检验）[S3]。

### 3.2 Full-Duplex-Bench v1.5：场景×指标×结果（已全文核实）

| 场景 | 构造要点 | 关键结果（五个 SOTA 模型） |
|---|---|---|
| user_intr（用户打断） | 200 样本 | 两种策略分化：repair-first vs continuity-first |
| user_backch（反馈语） | 99 样本 | 部分模型误把反馈语当打断 |
| **talking_other（旁白）** | 同一用户音色对第三人说话；-8dB、4kHz 高频衰减、45/120ms 混响；100 样本 | **Gemini 0.99 / Nova Sonic 0.90 以 Resume 保持不打扰；GPT-4o 0.91 Respond（旁白误接话）；Freeze-Omni 0.58；Moshi Unknown 0.59** |
| bkg_speech（背景人声） | 不同音色、-15dB、3kHz 低通、回声；100 样本 | Sonic Resume 0.98 最稳；GPT-4o Respond 0.93（把背景声当用户意图）；Gemini Respond 0.70 |
| 时延（talking_other，stop\|response，秒） | — | GPT-4o 0.18\|1.16；Moshi 0.87\|2.38；Freeze 1.39\|1.32；Gemini 1.69\|1.78；Sonic 1.77\|2.04 |
| 总体结论 | — | 重叠后重入延迟 1.16-2.76s，比人类约 200ms 慢 5-6 倍；出现 repair-first（≤300ms 让权但易误触发）与 continuity-first（保流畅但多秒 double-talk）两派 |

### 3.3 Duplex-MPE：多人共享对话中的选择性参与（已全文核实）

- 规模：2,000 场景 ×3-4 名说话人+1 助手，显式/隐式称呼成对 → 4,000 段评测对话，共 110.93h（Claude Opus 5 写脚本 + Qwen3-TTS 合成，事件级 gold 边界）。
- 四计分指标：fresh-onset response rate（新起音应答率）/ conditional answer accuracy（条件应答正确率）/ **silence preservation（沉默保持率）** / answering-window yield（该停时停）。
- 关键结果：**显式称呼下 silence preservation：MiniCPM-o 0.9242 > Voila 0.8351 > FLM-Audio 0.3957 > Moshi 0.2734 > Freeze-Omni 0.0002（20,360 个该沉默窗口只保住 5 个）**；MiniCPM-o 对非对准请求仍误响应 4.6%（216/4,704）。
- 方法学警示：response presence 与 fresh-onset 排名的 Spearman 相关仅 −0.4303——**指标选择会改变模型排名**；文本参考（Gemini 3.1 Pro）对显式/隐式称呼差 64.3pp，五个语音模型全部不显著（最小 p=0.2365）——"会沉默"可能只是"普遍不响应"。

### 3.4 其他基准与数据资产

| 基准/资产 | 定位 | side talk 相关 | 状态 |
|---|---|---|---|
| Full-Duplex-Bench v1 [S2] | 四行为（pause/backchannel/turn-taking/interruption）自动化评测 | 前代框架 | 摘要核实；逐场景指标（Takeover Rate 等）二手未核 |
| FD-Bench（Interspeech 2025）[S6] | LLM+TTS+ASR 全双工评测流水线 | 打断/延迟/鲁棒性 | 快照级，指标名未核 |
| ECHO [S4] | 中文成对轮次诊断 | off-talk 条件+pair accuracy；四系统中三个 over-yielding（backchannel 正确保持 <13%） | 已核实 |
| DuplexLedger [S5] | 双语事务记忆（1,094 会话） | side-talk stage（1.2s 观测窗）+"该忽略未忽略"进记忆 | 已核实 |
| WearVox [S9] | AI 眼镜自中心多通道语料（3,842 段） | 五任务之一=side-talk rejection | 转引核实 |
| HumDial [S3 转引] | 双通道真人对话 | complete rejection 四子场景 | 转引，未核原文 |
| 数据合成 Harness [S26] / DuplexDrama [S25] | 全双工训练数据 | 旁白=可编程意图事件 | 摘要核实 |
| FDB v2/v3、"Take the Floor" [S53] | 多轮/流式/工具调用扩展 | 扩展线 | 快照级 |

### 3.5 方法学争论（写报告时可作"批判视角"）

1. 术语不统一、指标名不收敛，跨基准数值**不可直接比较**（v1.5 的 Resume 0.99 与 Duplex-MPE 的 silence preservation 0.9242 分母完全不同）。
2. 单一聚合指标掩盖行为——Duplex-MPE 用 Spearman −0.4303 实证"指标选择改排名"。
3. 合成数据 vs 真实录音之争（可控性 vs 真实感；HumDial/WearVox 是对合成路线的补位）。
4. 半双工模型"不可评"还是"不公平"？Duplex-MPE 明确拒绝评半双工（协议不兼容），意味着无法回答"半双工+VAD 方案在旁白场景差多少"这一工程界常见问题。
5. LLM-as-judge 依赖人工抽检兜底（Duplex-MPE 报 99/100、98/100 一致率；v1.5 未见同等描述）。
6. "拒绝得好"存在歧义：可能是有意的受话人推断，也可能是普遍迟钝（见摘要第 10 条）。
7. 会话分析源头（Jefferson/Goffman）是思想先祖而非术语出处——2025-2026 全双工文献正文并未回溯引用它们，直接当"出处"引用属过度还原。

---

## 04 产业界洞察（一）：国际

### 4.1 术语与机制

**结论：国际产业界官方文档不使用 "side talk"**。最接近的官方概念：Amazon 的 device-directed speech、平台层的 background speech / background noise、OpenAI 的 turn detection / interruption handling。

国际语音 Agent 技术栈已收敛为**四级流水线**，side talk 被拆解到不同层处理：

| 层 | 职能 | 代表实现 |
|---|---|---|
| ① 前端降噪/回声消除 | 把背景人声/设备外放从拾音里消掉 | ElevenLabs WebRTC [S39]、Vapi 双去噪器 [S35]、LiveKit voice isolation、Amazon implicit AEC [S13] |
| ② VAD/语音起点 | 防背景声误触发 | 各平台 VAD 阈值、`min_interruption_duration` 类参数 |
| ③ 端点/轮次判定 | 判断"话说完了没/值不值得响应" | OpenAI `server_vad`/`semantic_vad`（eagerness）[S34]、Pipecat Smart Turn [S37]、Hume 韵律 end-of-turn [S38] |
| ④ 打断执行策略 | 让权/暂停/预生成 | cancel-and-regenerate、pause-and-resume（LiveKit：嘈杂线路多为"假打断"）[S37]、preemptive generation（提前算，代价是浪费） |

### 4.2 指标：硬件层成熟，平台层黑箱

- **成熟的一层（硬件唤醒）**：Amazon Science 论文实锤 DDSD 评测口径——"We use false reject rate (FRR) and false accept rate (FAR) as our metrics and report FRR at two fixed FAR values (non-playback and playback)"（区分设备自外放与不放声两种条件）[S13]；智能音箱误唤醒有学术量化研究 [S13a]。
- **黑箱的一层（模型/平台）**：OpenAI/Google/AWS/ElevenLabs/Vapi/Retell/LiveKit/Pipecat/Hume 的公开文档**均未公布**误打断率、误触发率数值或基准集；只有定性故障树（Retell："agent 抢话 → endpointing 太短"）[S36] 与第三方小样本测量博客。**任何"行业误打断率 X%"的数据都应视为不可信。**

### 4.3 三组已核实的工程张力

1. **防误打断 vs 响应速度**：Vapi 官方承认防背景打断阈值"even if it slightly delays the detection of speech onset" [S35]。
2. **预生成 vs 浪费算力**：LiveKit preemptive generation "doesn't always reduce latency" [S37]。
3. **降噪过度 vs 保真**：Retell 社区投诉降噪连真实第二说话人/环境音一起消掉（2026-02 社区帖，二手）[S36]。

---

## 05 产业界洞察（二）：国内

### 5.1 代际时间线（"全双工"的定义权叙事）

| 时间 | 事件 | 关键词 |
|---|---|---|
| 2019-07 | 百度小度发布"全双工免唤醒"（小度助手 5.0），官方宣传"在与他人对话的同时互不干扰地实现人机交互"，并首创"**拒绝反应**"（对无关话语不响应）[S33] | 智能音箱时代，规则+信号处理 |
| 2025-01-20 | 字节发布豆包实时语音大模型（端到端、可随时打断；当时未称全双工，后被官方追认为"上一代半双工"）[S28] | 端到端 |
| 2025-01 | 达摩院 MinMo 论文：Full Duplex Predictor（LLM 语义决策继续/停止/轮次，4000h 真人对话训练）；延迟口径 STT~100ms、全双工理论 600ms/实践 800ms、user turn-taking 250ms、assistant turn-taking ~660ms；评测用正类 F1 + offset distance K [S14] | 学术化定义 |
| 2026-03-30 | 阿里 Qwen3.5-Omni：官方宣布"语义打断"——自动识别 turn-taking 意图，"避免附和和无意义背景音打断"，API 原生支持 [S31] | 语义打断 |
| **2026-04-09** | **字节发布 Seeduplex（原生全双工语音大模型，豆包 App 全量上线）**：精准抗干扰（持续倾听+忽略背景噪音和无关对话）+ 动态判停（语音语义联合判断用户意图）；明确处理"被其他人打断、插入其他对话…听懂哪些话是针对自己发出的指令，哪些只是他人之间的闲聊" [S28] | 原生全双工 |
| 2026-06-18 | 豆包实时语音模型 3.0 API（Seeduplex 全双工版，火山引擎 Realtime 事件协议，"边听边说边办事"）[S30] | API 化 |
| 2026-08-05 | 字节 SeedRealtime 音视频全双工大模型："能分辨旁人闲聊与背景噪声，不因干扰误触发"；音视频对话节奏问题较级联模型减少一半 [S29] | 全模态 |

### 5.2 Seeduplex 官方指标（相对半双工上一代；2026-04-09 官方博客逐字核实 [S28]）

| 指标 | 数值 | 口径 |
|---|---|---|
| 误回复率 / 误打断率 | 减少一半（-50%） | 复杂声学干扰场景，相对半双工模型 |
| 抢话比例 | 相对下降 40% | 复杂场景 |
| 判停延迟 | 降低约 250ms | 相对半双工 |
| 打断响应延迟 | 进一步缩短约 300ms | 响应准确率更高的前提下 |
| 判停 MOS | +8% | 相对半双工 |
| 对话流畅度 MOS | +12% | 相对半双工 |
| 通话满意度（A/B） | 绝对值 +8.34% | 大规模 A/B；"抢话/响应慢/误打断"提及下降 |
| 人人对话对比 | 判停 +8%；打断响应略好于人人对话均值；**整体流畅度"仍有不小差距"**（官方自承） | 真人对话基准 |

**读数纪律**：以上全部是"相对自家上一代"或未公开评测协议的数值；样本量、人群、量表未公开——跨厂商引用必须注明口径。

### 5.3 国内术语矩阵（谁用哪个词）

| 术语 | 使用者 | 备注 |
|---|---|---|
| 全双工/半双工、边听边说 | 字节（代际叙事）、全体 | 字节把"可打断的端到端"追认为半双工 |
| 抗干扰、动态判停/判停 | 字节/火山（三大优势之二） | 指标化最充分 |
| 抢话、误打断、误回复、抢断 | 字节官方 + 社区 | 成对指标词族 |
| 语义打断 | 阿里 Qwen3.5-Omni（自称"独家"）[S31] | turn-taking 意图识别 |
| 附和 | 字节（未来方向）、阿里 | = backchannel 的中文化 |
| 拒绝反应 | 百度小度（2019，独有）[S33] | 国内最早的"抗旁白干扰"产品化表述 |
| 旁白 / 侧说话 / sidetalk | **国内产业官方文本 0 命中**（6 个官方页面全量正则）[S28][S29][S30][S14] | 引用需自行映射 |

### 5.4 机制叙事收敛

字节（"语音语义联合建模替代外部 VAD 机械切音"）、阿里（"语义打断/turn-taking 意图识别"）、达摩院（"Full Duplex Predictor 用 LLM 语义决策"）——三家机制话术高度同构，且**没有任何一家在别人家的公开测试集上跑过**；区分度目前只能靠官方宣称与产品体验 [S28][S31][S14]。

---

## 06 产业界洞察（三）：硬件场景与评测实践

### 6.1 场景×指标对照

| 场景 | side talk 的产品化形态 | 公开指标 | 成熟度 |
|---|---|---|---|
| 智能音箱（唤醒态） | 唤醒词门控天然挡住旁白 | 误唤醒率（TAF-WG7-AS0043 标准定义："听到与唤醒词相近的音…被误触发"）、唤醒率、响应时间 [S41] | 成熟 |
| 智能音箱（全双工免唤醒态） | 小度 2019"与他人对话互不干扰"+"拒绝反应" [S33] | 仅功能声明，无数值 | 早期 |
| 车载座舱 | **多音区锁定/音区隔离**——把"副驾/后排说话不算指令"从唤醒词门控升级为空间维度的访问控制：理想四音区锁定（2021 OTA，可"关闭副驾驶音区"）[S42]、小鹏双音区锁定（2020，动机原文即"其他乘客说话干扰"）[S43]、蔚来 NOMI 免唤醒下"正确响应副驾指令、辨别四人同时交叠指令"（2024 官方）[S44]、鸿蒙座舱四音区定位 [S45]；亿欧报告：双音区锁定 20s-120s 时间窗 [S48] | 全部为功能声明；无"旁白拦截率"数值 | 最产品化 |
| AI 眼镜 | Rokid Glasses 2 多人说话区分（听障字幕向）；雷鸟 V3 连续对话/可打断双模式 [S46]；**"用户与旁人交谈时 AI 不抢答"的官方表述未见** | — | 萌芽 |
| 机器人 | 唤醒词+超时门控（宇树 G1 二开文档"15 秒没声音退出"）；讯飞"智能语音背包"（麦克风阵列+全双工套件）[S47] | — | 门控式，非语义拦截 |

### 6.2 评测体系现状

- **TAF 团体标准**只覆盖唤醒态"误唤醒率"——side talk 发生在免唤醒/全双工态，**现行标准没有对应条目** [S41]。
- **中国信通院（CAICT）**：本次检索范围内未见语音全双工/抗干扰专项（检索空结论，存在漏检可能）[S49a]。
- **SuperCLUE 实时语音基准（2024-12）**：4 维度 15 项能力，是否含全双工/打断专项未核实；知乎评测综述当时把"全双工对话评测"列为**未来展望** [S49]。
- **商业测试公司已先行**：Roark/Evalgent 把"背景对话导致 derail""mm-hm 类附和误停（false stop）""抢话"列为全双工必测失效面（2026-09，二手）[S54]。
- **在线指标**：可确认的官方口径只有阿里云百炼——把"语义判停与拒识"做成产品开关，目标是"避免误打断、误唤醒"，并承认"开启后可能导致对话延迟增加" [S32]；社区工程口径有"打断成功率、误打断率、抢话率、长停顿"等指标名（开源笔记，二手）。

**结论：产品走到了标准与评测前面。** 全双工把 side talk 问题放大而非解决——半双工+唤醒词天然挡住旁白；全双工免唤醒后系统"一直在听"，忽略旁白从"外围工程"变成"核心能力"，而公开评测体系尚未跟上。

---

## 07 学术界 vs 产业界：对照总表

| 维度 | 学术界 | 产业界（国际） | 产业界（国内） |
|---|---|---|---|
| 术语 | off-talk / side conversation / talking to others / side-talk stage / side-talk rejection | background speech / device-directed speech (DDSD) / interruption sensitivity | 抗干扰 / 无关对话 / 抢话 / 误打断 / 误回复 / 动态判停 / 拒绝反应；**不用 sidetalk** |
| 定义方式 | 基准协议内的操作性定义（场景构造+标签体系） | 产品文档级（配置参数与功能边界） | 发布会叙事+代际对立（半双工 vs 全双工） |
| 主体假设 | 两种并存：旁观者（可穿戴）与对话用户本人（全双工对话） | 主要是对话用户+环境人声 | 主对话用户+旁人闲聊/车内其他音区 |
| 核心指标 | 行为五分类、silence preservation、stop/response latency、pair accuracy、UTMOSv2、F1+offset K（MinMo） | 硬件层 FAR/FRR（成熟）；平台层无数值（黑箱） | 相对上一代相对值：误回复率/误打断率 -50%、抢话 -40%、判停 -250ms、打断 -300ms、MOS +8%/+12%、满意度 +8.34% |
| 评测方法 | 场景化基准（TTS 合成可控事件+LLM-as-judge+人工抽检）、真人对话基准（MinMo/Seeduplex 人人对比） | 文档化配置+定性故障树+第三方小样本 | 大规模 A/B+人工 MOS+宣称对比 |
| 可复现性 | 高（开源基准+代码：FDB、Duplex-MPE 等） | 低（闭源 API，参数名可查数值不可查） | 低（协议未公开） |
| 最大缺口 | 真实多人重叠数据；跨基准不可比；半双工不可评 | 误打断率/误触发率无公开基准 | 无第三方专项；宣称指标口径不透明 |

---

## 08 关键数字速查（全部经核查）

| 数字 | 含义 | 来源 | 信度 |
|---|---|---|---|
| ~200ms | 人类对话轮换间隔（人类基线） | v1.5 引 Levinson & Torreira [S1] | 高 |
| 1.16-2.76s | v1.5 实测系统重叠后重入延迟（最 responsive 慢 5-6 倍） | [S1] | 高 |
| 0.99 / 0.90 | talking_other 场景 Gemini / Nova Sonic 的 Resume 占比（旁白保持不打扰最优） | [S1] | 高 |
| 0.91 | GPT-4o 在 talking_other 的 Respond 占比（旁白误接话最重的 SOTA 之一） | [S1] | 高 |
| 0.9242 | Duplex-MPE 显式称呼下 MiniCPM-o silence preservation（最高） | [S3] | 高 |
| 5 / 20,360 | Freeze-Omni 在该沉默窗口保住沉默的个数 | [S3] | 高 |
| 64.3pp vs 不显著 | 文本模型对名字线索敏感 vs 五个语音模型全部不显著（最小 p=0.2365） | [S3] | 高 |
| <13% | ECHO：三个系统 backchannel 场景正确保持话轮的比例（over-yielding） | [S4] | 高 |
| -50% / -40% | Seeduplex 误回复率+误打断率 / 抢话比例（相对半双工） | [S28] | 高（相对值） |
| -250ms / -300ms | Seeduplex 判停延迟 / 打断响应延迟 | [S28] | 高（相对值） |
| +8% / +12% | Seeduplex 判停 MOS / 流畅度 MOS | [S28] | 高（相对值） |
| +8.34% | Seeduplex A/B 通话满意度绝对值 | [S28] | 高 |
| 600ms/800ms | MinMo 全双工理论/实践端到端延迟 | [S14] | 高 |
| 1.2s | DuplexLedger side-talk 观测窗 | [S5] | 高 |
| 100 样本 | FDB v1.5 talking_other / bkg_speech 场景规模 | [S1] | 高 |

---

## 09 对你技术洞察报告的写作建议

1. **先给术语映射表，再引用任何数字**——把 off-talk / side conversation / talking to others / side-talk rejection / 抗干扰 / 抢话 / 拒绝反应 对齐到一张表（可直接用本报告 1.2/1.3/5.3 节）。
2. **标注基准与版本**——FDB v1.5 场景名在 v1（side conversation/ambient speech）与新版（talking to others/background speech）间有演化，引用注明版本。
3. **不跨基准比数字**——v1.5 与 Duplex-MPE 分母/量纲不同；Duplex-MPE 已实证指标选择改变排名。
4. **分两条线叙述机制**——"声学层拒绝（旁观者）"与"语义层选择参与（对话主体）"是两个问题域，合并叙述会让读者混淆 MMW 与 FDB 的关系。
5. **产业数字全部注明口径**——国内宣称均为相对自家上一代；"行业误打断率 X%"类说法一律不可引用。
6. **"会沉默≠听懂了不该接"**——引用 silence preservation 时配 answer accuracy 一起读，否则会把迟钝误读成分寸感。
7. **把"评测缺口"作为洞察点**——学术基准族 vs 产业黑箱/宣称、标准（TAF 只覆盖唤醒态）与第三方评测（CAICT 无专项）的代差，是这份洞察里最有报告价值的发现之一。
8. **人类基线作前瞻锚**——200ms vs 1-3s 的差距 + Seeduplex 官方自承"与人人对话仍有不小差距"，可作为"离自然交互还有多远"的收尾论据。

---

## 10 来源清单（编号 = 正文 [S#]）

**一手学术来源（已逐字/摘要核实）**
- [S1] Full-Duplex-Bench v1.5: Evaluating Overlap Handling for Full-Duplex Speech Models. arXiv 2507.23159（v1 2025-07-30；最新版摘要 2026-04）. https://arxiv.org/abs/2507.23159 ｜ 项目页 https://full-duplex-bench.github.io/ ｜ GitHub DanielLin94144/Full-Duplex-Bench
- [S2] Full-Duplex-Bench: ... Turn-taking Capabilities. arXiv 2503.04721. https://arxiv.org/abs/2503.04721
- [S3] Duplex-MPE: Benchmarking Multi-Party Interaction in Full-Duplex Dialogue. arXiv 2609.31948. https://arxiv.org/abs/2609.31948
- [S4] ECHO: A Matched-Contrast Benchmark for Context-Sensitive Turn-Taking in Full-Duplex Dialogue. arXiv 2609.17360. https://arxiv.org/abs/2609.17360
- [S5] DuplexLedger: Benchmarking Transactional Memory in Full-Duplex Speech Agents. arXiv 2610.27581. https://arxiv.org/abs/2610.27581
- [S6] FD-Bench（Peng et al.）. Interspeech 2025 / arXiv 2507.19040. https://www.isca-archive.org/interspeech_2025/peng25b_interspeech.html
- [S7] From Turn-Taking to Synchronous Dialogue: A Survey of Full-Duplex Spoken Language Models. arXiv 2509.14515. https://arxiv.org/abs/2509.14515（评测框架四维已核实；"side-talk robustness" 表行仅见检索 snippet，未核实）
- [S8] MMW: Side Talk Rejection Multi-Microphone Whisper on Smart Glasses. arXiv 2507.05609. https://arxiv.org/abs/2507.05609
- [S9] WearVox: An Egocentric Multichannel Voice Assistant Benchmark for Wearables. arXiv 2601.02391（+ Duplex-MPE 转引）. https://arxiv.org/html/2601.02391v1
- [S10] Oppermann et al. Off-Talk – A Problem for Human-Machine-Interaction. EUROSPEECH 2001（经 SmartWeb 语料论文 ACL L08-1046 与 OpenReview 文献综述交叉核实）
- [S11] Batliner et al. To Talk or not to Talk with a Computer: On-Talk vs. Off-Talk. https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.93.4828&rep=rep1&type=pdf ｜ Haider et al.（Edinburgh/TCD off-talk 检测）
- [S12] Apple ML Research：Adaptive Knowledge Distillation for Device-Directed Speech Detection. https://machinelearning.apple.com/research/adaptive-knowledge ｜ IEEE 10446421（Modality Drop-Out for Multimodal Device Directed Speech Recognition, 2024）
- [S12a] Addressee detection：Tsai 等（Microsoft）；An LLM Benchmark for Addressee Recognition in Multi-party Conversation. arXiv 2501.16643；ACM 10.1145/3776574.3831238
- [S13] Implicit Acoustic Echo Cancellation for Keyword Spotting and Device-Directed Speech Detection. Amazon Science. https://cdn.amazon.science/e5/c8/47db462c4815b13397f0d7fcd186/implicit-acoustic-echo-cancellation-for-keyword-spotting-and-device-directed-speech-detection.pdf ｜ [S13a] Exploring Accidental Triggers of Smart Speakers（2021）
- [S14] MinMo: A Multimodal Large Language Model for Seamless Voice Interaction. arXiv 2501.06282（全文抓取）. https://arxiv.org/abs/2501.06282
- [S15] Moshi: a speech-text foundation model, full-duplex spoken dialogue framework. arXiv 2410.00037. https://arxiv.org/abs/2410.00037
- [S16] SALMONN-omni. arXiv 2411.18138 / 2505.17060（NeurIPS 2025；三流 80ms 交错经 SALMONN-duo arXiv 2609.34247 转述核实）
- [S17] OmniFlatten. arXiv 2410.17799（ACL 2025）. https://arxiv.org/abs/2410.17799
- [S18] Freeze-Omni. arXiv 2411.00774（ICML 2025）. https://arxiv.org/abs/2411.00774
- [S19] VITA-1.5. arXiv 2501.01957
- [S20] A Full-duplex Speech Dialogue Scheme Based On Large Language Models（neural FSM）. arXiv 2405.19487（NeurIPS 2024）
- [S21] Voice Activity Projection. arXiv 2205.09812 ｜ MuVAP. arXiv 2606.16731 ｜ 三方 VAP（Interspeech 2025 elmers25）
- [S22] DDSD 论文群：arXiv 2110.04656 / 2403.14438 / 2411.00023 / 2409.09284
- [S23] Semantic VAD（帧级标点预测）. arXiv 2305.12450
- [S24] "多数端到端语音 LLM 仍半双工"引文. arXiv 2604.19221
- [S25] DuplexDrama. arXiv 2609.12872 ｜ [S26] A Harness for Synthesizing Diverse Naturalistic Full-duplex Conversations. arXiv 2609.28806 ｜ [S27] Lychee-FD. ACL 2026, 2026.acl-long.419（标题存在双版本，side-talk 细节经 ECHO 转引）

**一手产业来源**
- [S28] 字节 Seed《Seed 全双工语音大模型发布：懂倾听、抗干扰，走向更自然的交互》. 2026-04-09. https://seed.bytedance.com/zh/blog/introducing-seed-full-duplex-speech-llm-attentive-listening-robust-interference-suppression-enabling-more-natural-interaction ｜ 产品页 https://seed.bytedance.com/zh/seeduplex
- [S29] 字节 Seed《SeedRealtime 音视频全双工大模型发布》. 2026-08-05. https://seed.bytedance.com/zh/blog/seedrealtime-audio-visual-full-duplex-llm-released-toward-omni-modal-natural-interaction
- [S30] 火山引擎 豆包实时语音模型 3.0（Seeduplex）文档. https://www.volcengine.com/product/realtime-voice-model 及 docs 站 duplex 版本文档
- [S31] Qwen 官方（知乎专栏）：Qwen3.5-Omni 语义打断发布说明. 2026-03-30. https://zhuanlan.zhihu.com/p/2022053482077726160
- [S32] 阿里云百炼文档：多模态应用配置（打断方式/语义判停与拒识）. https://help.aliyun.com/zh/model-studio/multimodal-app-configuration
- [S33] 百度小度"全双工免唤醒"（Baidu Create 2019；官方活动页 dueros.baidu.com + 百科条目 + 媒体转述）
- [S34] OpenAI Realtime API turn detection（server_vad/semantic_vad；经 LiveKit docs 与 Azure 文档转述核实）
- [S35] Vapi docs：Speech Configuration / Background Speech Denoising. https://docs.vapi.ai/customization/speech-configuration
- [S36] Retell AI docs：Handle Background Noise / 打断故障树. https://docs.retellai.com/build/handle-background-noise
- [S37] LiveKit：Turn detection and interruption handling（docs + blog）. https://livekit.com/blog/turn-detection-and-interruption-handling ｜ Pipecat Smart Turn. https://docs.pipecat.ai
- [S38] Hume EVI：end-of-turn detection（官方博客/文档）
- [S39] ElevenLabs：Conversation Flow / WebRTC（官方文档+博客）｜ [S39a] Google Duplex（2018 官方博客，概念辨析用）
- [S41] TAF-WG7-AS0043-V1.0.0《智能产品语音识别测评方法 第二部分：智能音箱》（误唤醒定义，标准文本）
- [S42] 理想 OTA 2.2 四音区锁定（2021-09，媒体转述官方）｜ [S43] 小鹏双音区锁定（2020-11 车东西）｜ [S44] 蔚来 NOMI（nio.cn 官方 2024-09/2025-12）｜ [S45] 鸿蒙座舱四音区（华为社区）｜ [S48] 亿欧《2022 中国汽车智能化功能模块系列研究-语音交互篇》
- [S46] Rokid Glasses 2（2026-10 发布转述）；雷鸟 V3 评测（2025-02）
- [S47] 讯飞 AIUI 硬件白皮书 / 智能语音背包文档. https://aiui-doc.xf-yun.com
- [S49] SuperCLUE 实时语音交互中文基准（2024-12 转载）｜ [S49a] 中国信通院专题报告列表（检索空结论）
- [S50] CoDeTT: A Context-Aware Decision Benchmark for Turn-taking. arXiv 2603.25434（Sidetalk 类目，snippet 级）
- [S51] Sørensen et al. FTO（ISAAR 2019 / PMC 2021）
- [S53] Full-Duplex-Bench-v2（arXiv 2510.07838）、arXiv 2609.19596、arXiv 2611.14774（快照级）
- [S54] Roark AI / Evalgent：full-duplex voice agent 测试失效面（2026-09，二手）

**核查状态说明**：标注"已核实"= 主会话或 worker 直接打开原文页面抓取；"摘要/快照级"= 仅 arXiv 摘要或搜索快照；"转引"= 经另一已核实文献引用；"二手"= 媒体/社区转述官方信息。"未核实"条目（Meta Rani、Parakeet duplex、Voila turn-taking token、GLM-Realtime 全双工原文、小米超级小爱全双工、FDB v1 逐场景指标、CAICT 专项等）未写入正文结论。

---

## 11 调研方法与信度分级

- **方法**：6 个并行深度调研（学术定义溯源 / 学术模型机制 / 学术指标基准 / 国际产业 / 国内产业 / 场景与评测实践），合计 ≥78 次独立检索；主会话对 7 个最关键来源（FDB v1.5、FDB v1、Duplex-MPE、ECHO、DuplexLedger、Survey、Seeduplex 博客）直接打开原文逐字核查；对 6 个国内官方页面做全文正则术语检索。
- **信度分级**：高 = ≥2 独立来源一致或主会话直接抓取原文；中 = 单一权威源/官方 snippet；低 = 二手转述；未核实 = 明确降级不引用。
- **已知局限**：① 部分页面因抓取服务故障降级为搜索摘要级证据（已逐条标注）；② WearVox/HumDial/CoDeTT/FD-Bench 细节为转引或快照级；③ 会话分析源头文献（Jefferson 1972 / Goffman 1981）未逐字核对原文，按公认出处引用为"思想先祖"；④ 厂商宣称指标均为相对口径，无公开绝对值可比。

---

*报告完 · 供技术洞察报告写作使用的证据版素材，所有结论可溯源*
