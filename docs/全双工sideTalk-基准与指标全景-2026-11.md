# 全双工交互中的 sideTalk：定义、指标与评测全景（学术 + 产业）

> 技术洞察底稿（词典式穷举版） | 检索截止 2026-11-16
> 定位：本文是`docs/全双工sideTalk-学术产业深度洞察-2026-11.md`（结论与评测蓝图向）的**明细底稿**——那份给结论与建议，这份给逐条定义原文、逐基准协议、逐产品口径与指标公式，便于查证与引用。
> 口径：所有定义、指标、数字均核对到一手来源（arXiv 原页 / 官方技术报告 / 厂商官方文档）；厂商自报数字单独标注「自报」；无法核实的宣传不作为量化结论。
> 结构：术语定义总表 → 学术基准逐项详解（统一模板：定义原文 → 任务形式化 → 数据 → 指标 → 评测协议 → 结果数字 → 局限）→ 产业界逐项详解 → 指标词典 → 横向对比大表 → 空白点与引用建议 → 参考文献。

---

## 1. 术语与定义总表

### 1.1 同一现象的 12 种叫法（含定义原文）

| # | 术语 | 出处 | 定义原文（或忠实转述） | 判定层级 |
|---|---|---|---|---|
| 1 | **side-talk / side speech** | MMW (arXiv:2507.05609, Meta) | "unintended speech from nearby individuals or overlapping conversations"（附近他人的无意语音或重叠对话） | ASR 级（降 WER） |
| 2 | **Side-Talk Rejection** | WearVox (arXiv:2601.02391, Meta+CMU) | 五任务之一：模型应识别"非设备指向语音"并输出 `[Mute]` 控制符（例：用户对同伴说 "Hey, grab that coffee"，正确输出是 Mute 而非执行） | 轮次/动作级 |
| 3 | **Third-party Speech (TPS)** | HumDial Challenge (ICASSP 2026) | "background speakers who interject before or after the user query, and the model is expected to reject these utterances and respond only to the target user"（背景说话人在用户提问前后插话，系统应拒识并只响应目标用户） | 交互行为级 |
| 4 | **Speech Directed at Others (SDO)** | HumDial Challenge | "the user temporarily addresses another person, often on an unrelated topic, and the model is expected to detect and ignore such utterances"（用户临时转头对他人说话） | 交互行为级 |
| 5 | **non-addressed speech** | Full-Duplex-Bench v1.5 (arXiv:2507.23159) | 四个重叠条件中两个的统称：**talking to others**（"Hey grandma, I'm fine"——用户转头对他人说，模型应识别自己非受话者并继续原任务）+ **background speech**（电视/房内他人，应过滤为噪声并保持话轮） | 交互行为级 |
| 6 | **device-directed speech detection (DDSD)** | 学术线（Garg 2022 起） | "a binary classification task that separates the user's queries to a voice assistant from background speech or side conversations"（Adaptive KD, arXiv:2508.02801 的规范表述） | 说话人/指向级 |
| 7 | **addressee detection / recognition** | 对话分析经典线（Jovanovic 2004 起） | 给定 utterance 预测受话人（A/B/C/O 或具体参与者/group/none） | utterance 分类级 |
| 8 | **selective responding** | Duplex-MPE (arXiv:2609.31948) | 多方对话中的参与决策："跟听每一位参与者、单独决定是否开口"——旁人语音可能是后续请求的上下文，不能一律拒 | 交互策略级 |
| 9 | **user backchannel (URB)** | FDB v1.5 / HumDial | 用户短附和（"uh-huh"/"yeah"），正确行为是忽略并继续（不是"拒识丢弃"而是"保持话轮"） | 交互行为级 |
| 10 | **pause handling (PH)** | FDB v1.5 / HumDial | 句中犹豫/停顿，语义未完，模型应等待而非抢话 | 话轮边界级 |
| 11 | **background speech rejection** | StepAudio 3（产业，训练目标名） | post-training 四目标之一：对背景语音保持拒绝（证据仅对话历史单路） | 模型行为级 |
| 12 | **语义拒识**（中文产业术语） | 理想（用户手册功能名）、讯飞 AIUI | "不该响应的语音不响应"：乘客闲聊不打扰（理想）；受限域白名单外意图拒绝（AIUI） | 产品功能级 |

### 1.2 定义的三个正交轴（判断任何一家定义时先过这三问）

**轴一：说话人身份 × 指向对象**（决定问题难度）

```
                 指向设备              指向他人               无明确指向
主用户        S0 该响应             S1 (SDO) 最难           自言自语
第三方        合法副用户(看策略)      S3 (TPS/旁人间)          S3
电子源        回声(工程问题)         S4 (媒体台词)            S4 (背景电视)
```
S1 最难的原因：说话人、音区、声纹全部与 S0 一致，唯一判别线索在语义/语用层（称呼、话题、话轮结构、设备能力域）。

**轴二：判定层级**——同一句"旁人的话"在四个层级被处理，指标完全不可互换：
1. **声学/信号级**：MMW（拒识 = 不转写，指标 WER）
2. **说话人级**：DDSD/声纹锁定（拒识 = 非目标说话人，指标 EER）
3. **行为级**：FDB/HumDial（拒识 = Resume/静默，指标 RESUME 分、二值准确率）
4. **策略级**：Duplex-MPE（拒识 = 不开口但继续跟听，指标选择性回应率）

**轴三：闭集 vs 开集**——addressee 经典线是闭集分类（标签集合固定）；全双工基准是开集（该拒的语音种类不可枚举）；产业产品介于两者（唤醒词域是闭集，"闲聊"是开集）。

### 1.3 各家定义对照速查表

| 基准/产品 | sidetalk 归属 | 说话人限定 | 指向限定 | 粒度 | 正确行为 |
|---|---|---|---|---|---|
| FDB v1.5 | 4 条件之 2（talking-to-others, background-speech） | 不限定 | 非设备 | 事件 | Resume（继续原输出） |
| HumDial | Rejection 大类 4 子类之 2（TPS, SDO）+ URB/PH | TPS=第三方，SDO=主用户 | 非设备 | 话轮 | Resume/静默 |
| WearVox | 5 任务之 1 | 佩戴者 or 旁观者 | 非设备 | utterance | 输出 [Mute] |
| Duplex-MPE | selective responding 内涵 | 多方 | 隐式 | 话轮/会话 | 跟听+选择开口 |
| MMW | ASR 干扰 | 任意 | 任意 | 帧+句 | 不转写（降 WER） |
| DDSD | 任务本身 | 任意 | 设备/非设备 | utterance | 二分类 |
| Inoue/Fukuda | 任务本身 | 已知多人 | 显式标签 | utterance | 标签预测 |
| StepAudio 3 | post-training 目标 | 不限定 | 非设备 | 块级（320ms） | 状态 token 决策 |
| SAA（产业） | 任务本身 | 任意 | 设备/非设备 | utterance | pre-ASR 转发/丢弃/不确定带 |

---

## 2. 学术界逐项详解

> 每项统一模板：定义 → 任务形式化 → 数据 → 指标 → 评测协议 → 结果数字 → 局限。

### 2.1 经典 addressee recognition（2004-2026，五篇代表作）

**① Jovanovic & op den Akker (2004)、Jovanovic et al. (2006)**
- 定义：会议多人对话中，每句 utterance 的受话人预测（addressee vs side-participant vs overhearer——这套参与框架来自 Goffman 的对话分析）
- 任务：给定会议片段（注视、朝向、上下文特征）→ addressee 标签
- 意义：**定义了"旁听者（overhearer）/旁参与者（side-participant）"的社会学框架**，全双工拒识的概念源头

**② Ouchi & Tsuboi (2016)、Gu et al. (2021)**
- 文本对话的 addressee 分类（聊天语料），特征从视觉转向纯语言

**③ Inoue et al. (2025)**
- 任务：给 GPT-4o **五轮人工转写的上下文**，输出四标签 A/B/C/O
- 关键限定：offline、文本输入、utterance 级——不涉及流式与声学

**④ Fukuda et al. (2026)**
- 数据：AMI 会议集，提供 ground-truth 说话人 ID + utterance 对齐转写 + 音频 + 视频
- 输出：四个参与者 + group + none
- **指标：accuracy 与 macro-F1**（addressee 线的标准指标）

**这条线的集体局限**（Duplex-MPE 的原文批评）："评估单位是给定的 utterance，输出是显式 addressee 标签；而真实系统需要把 addressee 识别作为**控制模型是否说话的隐式决策**"。

### 2.2 Device-Directed Speech Detection（DDSD，产业最贴近的学术线）

代表工作：Garg et al. (2022)、Wagner et al. (2024)、Rudovic et al. (2024)、Palaskar et al. (2024)、Kim et al. (2026)。

**规范定义**（Adaptive KD for DDSD, arXiv:2508.02801）：
> "DDSD is a binary classification task that separates the user's queries to a voice assistant from background speech or side conversations."

**任务形式化的三个关键细节**：
1. **区分调用形态**：keyword 唤醒后（HAG/AG 头）vs **keyword-free follow-up**（对话进行中的后续句，FCO 头）——后者才是全双工语境，难度更高
2. **指标是 EER**（等错误率，FAR=FRR 工作点），说话人验证体系的标准量纲
3. 模型规模：端侧学生 5M 参数 vs 教师 79M（冻结 ASR encoder + adapter）

**评测协议**：utterance 级二分类，按调用形态分别报 EER；该论文的蒸馏方法在 keyword / keyword-free 上分别改善 **+26% / +19% EER**。

### 2.3 MMW（arXiv:2507.05609，2025-07，Meta）——ASR 级 side-talk 拒绝

- **定义**：side speech = "unintended speech from nearby individuals or overlapping conversations"，干扰对象是**用户-LLM 交互质量**（转写被污染）
- **任务**：不是"要不要响应"而是"要不要转写"——Whisper 在多说话人场景下会转写所有声音
- **数据**：Ray-Ban Meta 智能眼镜 5 麦几何（模型与该几何绑定，换硬件需重训轻量 encoder）
- **结构**：Tri-Mamba Mix Block（原始波形级多通道融合，兼容流式）+ Frame Diarization Mamba 层（帧级 side-talk 抑制）+ Multi-Scale GRPO（帧级+句级联合优化）
- **指标**：WER（嘈杂条件绝对降低 4.95%）
- **局限**：特定硬件绑定；未覆盖动态移动的旁观者；未测端侧功耗发热
- **引用注意**：它的"side talk rejection"是 WER 量纲，与轮次级拒识不可比

### 2.4 Full-Duplex-Bench v1.5（arXiv:2507.23159，2025-09，Meta 系）——轮次级行为评测的事实标准

**定义**（四个重叠条件，2 个是 sidetalk）：
1. User Interruption（用户打断 → 应让位并处理）
2. User Backchannel（用户附和 → 应忽略并继续）
3. **Talking to Others**（用户转头对他人说，例："Hey grandma, I'm fine" → 应识别自己非受话者，忽略并继续原任务）
4. **Background Speech**（电视/房内他人 → 应过滤为噪声并保持流程）

**评测协议**（逐步骤，被 HumDial/FLEXI 等广泛继承）：
```
1. 预录用户音频，实时流式喂给被测模型（模型被当作"实时参与者"，解决黑箱问题）
2. 在精确时间戳插入受控"重叠事件"（四条件之一）
3. 录模型输出 → ASR 转写（带时间戳）
4. GPT-4o 作 LLM judge，把模型响应判为四态:
   Respond（处理了重叠语音内容）/ Resume（忽略干扰、恢复原输出）/
   Uncertain（困惑/请求澄清）/ Unknown（无关输出或沉默）
5. Interruption 条件: Respond 算对；Rejection 条件: Resume 算对
6. 用 Silero-VAD 定语音边界，算延迟指标
7. 另测韵律维度（F0、语速、停顿的适应性）
```

**指标**：
- 行为：四态分类正确率（RESUME score 即拒识正确率）
- 时序：**t_stop**（用户重叠开始→模型停止说话）、**t_resp**（重叠结束→模型再开口）
- v1 时代还有 **takeover rate**（用户停顿期间模型抢话率，越低越好）

**v1.5 实测数字**（引用自 FDB 论文及第三方汇总）：

| 条件 | 模型 | 数字 |
|---|---|---|
| User Interruption | GPT-4o Realtime | 处理率 0.78 / 继续率 0.10 / t_stop 0.23s |
| User Interruption | Gemini 2.0 Flash Live | 0.33 / 0.55 / 2.20s |
| User Interruption | Nova Sonic | 0.24 / 0.71 / 2.25s |
| User Backchannel | GPT-4o Realtime | t_stop 0.21s（正确地几乎不停） |
| User Backchannel | Nova Sonic | 继续率 0.98 |
| Pause（CANDOR 真实语料） | Moshi | 抢话率 0.980（几乎每次停顿都抢话） |
| Pause | Gemini Live | 0.310 |

**v1.5 的已知问题**：200 个合成打断用例（±4 分统计噪声）；英文为主；**已被 Artificial Analysis 于 2026-08 移出总指数**（作者自述指标与人类偏好无关）；电话语料+GPT-4o 合成对话的分布局限。

**FDB v2（Lin et al., 2025-10）**：升级为多轮+自动化实时考官（examiner agent），评纠正处理与实体追踪；代价是考官自适应推进，跨模型可比性下降（EchoChain 的批评）。

### 2.5 HumDial-FDBench（ICASSP 2026 Challenge，arXiv:2604.21406 + 2601.05564）——唯一带 TPS+SDO 双标注的大规模真实基准

**定义**（Rejection 大类四子类）：
- URB（用户实时附和："uh-huh"/"yeah"，不应打断自己的输出）
- PH（停顿处理：句中犹豫，语义未完整，应等待）
- **TPS**（第三方语音：背景说话人插话，应拒识并只响应真实用户）
- **SDO**（对他人说话：用户突然转向他人对话（常为无关话题），应检测并拒绝）

**数据**（关键事实）：
- 构造：DeepSeek 生成嵌入交互线索的剧本 → **职业演员双轨表演**（保留自然重叠时机/韵律/交互节奏，避免合成拼接）
- 训练集 107h，中英双语，100+ 说话人
- **子类样本量**：TPS 训练仅 120 条、**SDO 训练为 0 条**（其余场景 ~1,200）；dev 各 200（中英各 100）；test：TPS 600 / SDO 200
- 官网 aslp-lab.github.io/HumDial-Challenge；GitHub ASLP-lab/HumDial-FDBench

**指标与总分公式**：
```
S_Total = 0.4·S_Int + 0.4·S_Rej + 0.2·S_Delay
S_Rej: rejection rate（对应 FDB 的 RESUME score）+ early interrupt rate（过早中断率）
     TPS-before-question 与 PH 用词级时间戳的定制二值判定
S_Delay = 100 − 40×log(L/L_min)/log(L_base/L_min)  （对数归一，基线 60 分）
新增: first response latency = 首个模型响应开始 − 首个用户提问结束（仅对成功拒识样本计）
边界检测: Silero-VAD；judge: DeepSeek-V3 读 Paraformer(中)/Parakeet-TDT(英) 转写
```

**榜单结果**（Rej 列即 sidetalk 相关）：

| 系统 | Int | **Rej** | Delay(s) | 总分 |
|---|---|---|---|---|
| Cookie_asr（冠军） | 79.3 | **72.2** | 1.260 | 76.6 |
| Badcat | 89.7 | **57.8** | 1.632 | 73.5 |
| SenseDialog | 76.4 | **60.9** | 1.237 | 71.0 |
| Gemini-2.5 | 79.8 | **36.5** | 1.301 | 62.3 |
| Baseline（Easy-Turn+Osum-EChat） | 75.9 | **35.2** | 2.531 | 56.4 |
| Freeze-Omni | 29.6 | **50.2** | 2.578 | 43.8 |
| Moshi | 35.4 | **22.8** | 2.876 | 34.5 |

**参赛方法学聚类**（对写报告极有价值）：级联（VAD+流式 ASR+决策模块+TTS）因可控性占主导；专门小分类器（Whisper-tiny 四类头、TinyBERT、离散 audio token 分类器）在背景干扰过滤上最稳；LLM-as-judge 决策语义最强但引入延迟；E2E 模型受"听觉盲区"（生成期间感知退化）拖累。

### 2.6 WearVox（arXiv:2601.02391，2026-08，Meta+CMU）——可穿戴专属

- **定义**：Side-Talk Rejection 是五任务之一（Search-Grounded QA / Closed-Book QA / **Side-Talk Rejection** / Tool Calling / Speech Translation）；场景例：佩戴者对同伴说 "Hey, grab that coffee"，单通道模型当指令执行，可穿戴感知模型应识别为非指向并输出 **`[Mute]` 控制符**
- **数据**：3,842 段多通道 egocentric 录音（AI 眼镜多麦实采）；说话人角色三类：**佩戴者 / 对话伙伴 / 不同角度距离的旁观者**；环境覆盖室内约 31%、室外约 63%（办公室/咖啡馆/车内/街道/公园/工地）；HF 开源：zlinao/WearVox
- **指标**：**Side-Talk Rejection 用二值准确率**（模型判定是否正确抑制非指向语音）；主指标 Turn-based Micro-avg = 四个 turn 级任务准确率均值
- **评测要点**：单通道基线必须先波束成形再推理，否则对比无效
- **结果**：主流实时 SLLM（GPT-4o、Gemini 2.5-flash、Qwen2.5-Omni、Gemma 3n、Phi-4、Kimi-Audio）总体 29-59%；**多通道输入把 Side-Talk Rejection 从 85.6% 提到 93.9%**（Llama 4 Scout 多通道版），总体 61.9%→66.4%

### 2.7 Duplex-MPE（arXiv:2609.31948，2026-09）——多方选择性参与

**定义修正**（与前三个基准的关键分歧）：旁人语音不是一律该拒的干扰——"他人的话可能为后续请求建立上下文、或解答已抛给助手的请求"，模型必须**跟听每位参与者、单独决定是否开口**。

**数据**：4,000 段对话 / 110.93h（61.1h 独立片段）；Claude Opus 5 生成剧本（场合/活动/人物关系/设备背景/语气五属性组合）→ Qwen3-TTS 逐句合成拼接；**输入只有连续音频流——无转写、无说话人标签、无轮次边界**。

**四个指标**（全部围绕"选择性"设计）：
1. **新发起回应率**：只在"请求结束时模型未在说话、且 5 秒内新开口"计——防"假阳性回应"（Freeze-Omni：回应出现率 99.55% 但新发起回应率仅 25.25%，大部分"回应"只是没说完的旧话）
2. **条件回答准确率**：只在确有语音输出的回应里判内容对错
3. **静默保持率**：本该安静的轮次是否乱插话（允许"嗯/好的"式非实质附和，说出实质内容即失败）
4. **应答窗口让位率**：用户提问后他人抢先回答/示意不用答，模型能否停（只统计"提问期间沉默+3 秒内开口+人类给出答案时仍在说"的事件）

### 2.8 Talking Turns（ICLR 2025，CMU+Apple，Arora/Lu/Chiu/Pang/Watanabe）

- **定位**：turn-taking 动态基准，judge 是"监督模型"而非 LLM
- **形式化**：IPU（inter-pausal unit）= 连续语音、被 >200ms 停顿分隔；在此之上定义 pause/gap/overlap/backchannel/interrupt 事件
- **Judge 模型**：因果模型，吃 Whisper 特征，**每 40ms chunk** 预测下一 turn-taking 事件，softmax 五标签：**NA（无人说话）/ BC（附和）/ I（打断）/ T（话轮转换）/ C（继续）**
- **指标**：语料级统计（话轮转换/重叠/间隔/附和的分布）+ utterance 级判定；与人类分布比用 **KL 散度**；事件预测用 **Turn-taking-F1**
- **用户研究**：每系统约 4h 人机对话、11 名参与者；发现系统"不知道何时该说话、打断过于激进、几乎不附和"
- **关键数字**：用户打断后用户拿到话轮的比例——**Moshi 17.4% / 级联系统 59.4% / 人类被打断者 63.6%**；Moshi 的假阳性打断占其全部决策的 2.09%
- 测试集基于 Switchboard 子集（人工对话，260h 语料家族）

### 2.9 FLEXI（arXiv:2509.22243，2025-09）

- **六场景**：标准话轮转换 / 停顿处理 / 用户打断 / **模型打断（紧急场景）** / 用户附和 / 模型附和——sidetalk 相关是停顿处理+用户附和两个
- **指标定义（含公式，最完整的一套）**：
  - **TOR（Takeover Rate）**：`TO=0 if SIL or BC else 1`，按数据集平均——测抢话
  - **TTR（Turn-Termination Rate）**：用户打断时模型正确终止话轮的比例 + 终止延迟
  - **TSS（Topic Shift Score）**：GPT-4o 评第二轮是否成功转向打断性提问（1-5 分）
  - **EDS（Emergency Detection Score）**：GPT-4o 评模型是否识别紧急性（模型打断场景）
  - **JIR（Jump-in Rate）**：用户未说完就被模型抢话的比率
  - **BCR + JSD**：模型附和的时机分布与人类参考分布的 Jensen-Shannon 散度
  - 用户附和场景的容忍规则：**1 秒内恢复原话轮算可接受**（coherence metric）
- **数据管线**：Qwen-plus 生成文本 + CosyVoice2 合成，人工校验
- **结果**：Moshi 延迟最低（0.696s）但靠"激进"策略——停顿处理 TOR 0.550（半数抢话）；Gemini TSS 最高 4.51/5 但"过于礼貌"，几乎不主动打断（紧急场景 EDS 低）
- **分级框架**：Level 1（类人）要求延迟 <150ms

### 2.10 Instruct-FD、EchoChain、FD-Bench（指令遵循与打断后推理）

**Instruct-FD**：
- 定义视角转换：不测"拒识对不对"，测"**轮次策略指令遵循**"——指令五类：主动型（backchannel / interrupt / listen=保持安静）+ 响应型（continue=用户噪声中继续 / acknowledge=停下并适配）
- 数据：912 个测试用例（来自 696 段对话、29 个场景）；WebRTC 流式回放管线；Claude 3.5 Sonnet 作 judge（给词级时间戳+原指令）
- 人类校验：89.6% 的人类能识别正确轮次动作（场景可操作性证明）
- **结果**：最好系统（Gemini Live）指令遵循仅 **64.4%**；"continue"遵循高达 97.5% 而"interrupt"仅 1.7-11.7%；失败模式有专门命名：**语义合规但时序不合规**、continue 偏置（背景噪声过滤学到"装聋"）、指令反噬（给了指令反而更差）

**EchoChain（arXiv:2604.16456）**：
- 定位：打断后的状态更新推理基准——三个被命名的失败模式：**contextual inertia（上下文惯性）/ interruption amnesia（打断失忆）/ objective displacement（目标漂移）**
- 协议控制：用户语音预合成（声学延迟恒定）、打断固定锚定在助手语音起点后的偏移处、persona/系统指令恒定——保证跨模型可比
- 管线：GPT-5.2 做对话规划、Gemini 3 Pro 做用户模拟、失败分类器多数投票 + 人工仲裁

**FD-Bench（Peng et al., 2025）**：程序化生成对话，用户侧全部预合成、在首个用户输入前流式注入——强调打断检出率、时序行为、聚合质量分；用户脚本不随助手回应自适应（与 FDB v2 相反的取舍）。

### 2.11 TurnBench、People Making Conversation、Speak-or-Stay-Silent、Seamless Interaction

**TurnBench（Jiang et al., IEEE SLT 2026）**：
- 自建演员语料；指标：EOT 与打断的 **recall、FPR、延迟**
- 有用的人类基线：**被打断人类中位再坚持 1.48s 才让位**（打断响应的参照系）
- （此前调研中的 OpenAI 实测即出自此体系：semantic_vad 召回 0.303 @ FP 0.018 vs server_vad 0.955 / 0.525——第三方实测口径）

**People Making Conversation（arXiv:2610.12802，2026-10）**：
- 设计：从 Seamless Interaction 176 段无剧本对话中取 **427 个停顿点 + 482 个话轮终点**，把系统放到这些点上，给它"至此的对话+现场听到的话轮"，对**它生成的东西**打分：停顿时是否开口/多快开口、话轮终点时的延迟/长度/措辞、能否答对前 30-120 秒的问题
- **核心发现**：托管 API（GPT Realtime、Gemini 3.1 Flash Live、Grok Voice）**几乎在每个停顿点都开口**（"always-speak 线"）；延迟：静音端点器 1-4s、**语义轮次检测约 8s**；**全双工模型（PersonaPlex、Moshi）是唯一定期保持沉默、也是唯一能在人类反应时间内打断的系统**；托管系统回复比人类更长；事实回忆：托管 41-60%（Claude Opus 5.5 judge）vs 严格词匹配 19-26%；全双工音频输入下仅 17-22%/12-15%
- 其基准分类表（原文 Table 2，直接可引用）：FDB v1=检测型；Talking Turns=检测型；TurnBench=检测型（自有演员语料，EOT+打断 recall/FPR/延迟）；**Speak or Stay Silent=策略型**（多方转写文本上每个停顿点判说/不说）；**CoDeTT=策略型**（LLM 剧本+TTS，上下文条件决策类别）；Instruct-FD=策略型
- 语料家族规模表（可引用）：Switchboard 260h / Fisher 1,960h / CANDOR 850h / SSSD 727h / CASPER 200h / **Seamless Interaction >4,000h**

**Seamless Interaction（Meta）+ SPEARBench（JHU+Amazon, 2026）**：
- Seamless Interaction：>4,000h 双人面对面英语自然对话（4,200+ 参与者），分即兴/自然主义子集，分通道录音
- SPEARBench：5,400+ 对话样本的受控提示集；指标 >10 项：响应延迟、打断频率（负延迟=抢话）、轮换自然度（预训练轮换预测模型）、情感同步、方言一致性、声学特征分布；第三方衍生标注集（11 个行为侧面、98 个信号，含 turn-taking 10 个信号、prosody 13 个）

### 2.12 训练方法侧的学术线（定义如何被"教"给模型）

- **HIPLEX / GRPO 对比**（2026-11 工作）：行为对齐训练的两种路径；引入 **Wasserstein 距离**比较模型与人类的时机分布（停顿时长/背景响应频率/轮次交接偏移——Fisher 中位交接偏移近零且过半有重叠，Seamless 交接间隙中位 1/3-2/3 秒）；发现 GRPO 的"零停顿闯入"是矫枉过正而非学会分寸
- **数据现状**：自发多说话人重叠语料是公认瓶颈（DialoSpeech 双轨管线、SyncLLM 合成增强、MMedFD 医疗真实对话细标注）

---

## 3. 产业界逐项详解

### 3.1 模型厂商（全双工 speech-to-speech）

**① StepAudio 3 Realtime（阶跃，arXiv:2609.14005，2026-09）**
- **定义方式**：训练目标级——post-training 四个显式行为目标：turn-taking / backchannel / 打断 / **背景语音拒绝**；对话动态建模为 320ms 块 + 交互状态 token（继续听/开口/继续说/让位）
- **证据配置**：用户音频流 + 模型自身音频流回灌 + 对话历史——**仅对话历史这一路语义证据**，无声纹/音区/设备档案（结构上做不了 S1）
- **指标**：自报 AA Full-Duplex Bench **98.9 总分**（话轮交接 100、用户打断 99.0、附和语 98.0 低于 Qwen Audio 3.0 Realtime Plus 的 100、停顿处理低于 GPT-Realtime-2 的 99.3）+ MMSU 90.6 + τ-Voice 56.0
- **评测方式**：自报+AA 榜单镜像，无独立复现；**98.9 是四条件总分，non-addressed 只占其二**

**② Amazon Nova Sonic / Nova 2 Sonic（2025-04 发布，2 代 2025-12）**
- **定义方式**：官方能力表述——"manages interruptions seamlessly while preserving context"、"robust to background noise"、（中文资料表述）"识别主说话人并过滤背景噪声"
- **指标**：**TTFA（Time to First Audio）**：用户语音结束→响应首字节，平均 1.09s（AA 口径；对照 GPT-4o Realtime 1.18s、Gemini Flash 2.0 1.41s）；WER：多语种 LibriSpeech 4.2%；AMI 会议集比 GPT-4o Transcribe 相对低 46.7%；Common Eval 胜率 51.0% vs GPT-4o——**全部厂商自报**
- **第三方实测**（FDB v1.5）：打断处理率 0.24 / 继续率 0.71 / t_stop 2.25s；附和继续率 0.98——"礼貌但迟钝"型
- **API 机制**：barge-in 时立即停止当前响应、保留上下文、先发 interruption 信号再处理新输入

**③ Google Gemini Live（2.5 Flash GA；3.1 Flash Live 预览 2026-03）**
- **定义方式**：API 参数级——VAD、turn detection、**turn coverage（持续发送输入 or 仅用户说话时发送）**、打断偏好可配
- **第三方实测**：FDB 打断处理 0.33/继续 0.55/t_stop 2.20s；CANDOR 停顿抢话率 0.310；People Making Conversation：几乎每个停顿都开口；HumDial 榜：Int 79.8（参测系统第一梯队）/ **Rej 36.5（垫底区）**——能力解耦的典型样本
- 3.1 Flash Live 宣称"更敏锐的声学细节检测、更低延迟"

**④ OpenAI GPT-4o Realtime / GPT-Realtime 系列**
- **定义方式**：API 参数级——`server_vad`（能量 VAD）与 **`semantic_vad`**（语义判停）两档 + eagerness 参数；官方机制：barge-in 时发 speech-started 通知 + **truncate 未播出的消息**（历史与用户实际听到的对齐）
- **第三方实测**：FDB v1.5 打断处理 0.78/t_stop 0.23s（反应最快）；TurnBench：semantic_vad 召回 0.303 @ FP 0.018（该停不停）、server_vad 0.955 @ FP 0.525（疯狂抢话）；People Making Conversation：**语义轮次检测端到端约 8s 延迟**
- 定位：**"名义支持拒识、实测不合格"的反面教材**——API 宣称与实测的差距本身是重要行业事实

**⑤ xAI Grok Voice Agent API（2025-12-17）**
- **定义方式**：架构组件级——官方特性列表：custom VAD + **Smart Turn end-of-turn detection**（直接采用开源 Pipecat Smart Turn！）+ 亚秒 TTFA
- 意义：**头部厂商公开采用级联式开源 turn detector**，级联路线的产业背书

**⑥ Moshi（Kyutai，2024）**：全双工理论延迟 160ms/实践 200ms；作者指出真实对话 10-20% 时间有重叠——但实测行为（Talking Turns：用户拿话轮 17.4%；FDB：停顿抢话 0.980；HumDial Rej 22.8 垫底）显示其"听"的决策粒度粗

**⑦ MiniCPM-o 4.5（OpenBMB/THUNLP，arXiv:2604.27393，2026-04）**
- **定义方式**：状态 token 级——Omni-Flow 把交互切成 1s 窗，三条时间对齐流（env-visual / env-audio / out-stream），**输出无内容时只发 `[listen]` 特殊 token**；VAD 信号编码为 token 与主干共训（去外挂 VAD）；9B、<12GB 端侧
- **sidetalk 的处理位置**：env-audio 流不加区分地进入模型，由 listen/speak 决策隐式处理——无显式 addressee 概念

**⑧ Realtime-Venus（arXiv:2609.13814，基于 MiniCPM-o 4.5 的 9B 前端）**
- 定义方式：1s chunk 上共享时钟的三流（用户流/助手流/背景流）+ 每秒预测 **listen/speak 控制 token**；控制决策与生成共享语义状态——声学相似的重叠得到不同处理："right"式附和不改响应计划，抢话式打断关闭话轮并修订未说出的剩余部分
- **公开最细的 sidetalk 分项数字**（FDB v1.5 口径）：打断应答 75%；**穿过附和/对他人说话/背景语音时正确继续的比例 = 97% / 88% / 86%**，三项均超 Gemini 3.1 Live 和 GPT-4o——目前产业界唯一把"talking-to-others"单独拎出来报数字的系统

**⑨ Freeze-Omni / PersonaPlex / SALMONN-omni / SyncLLM**（补充谱系）
- Freeze-Omni：状态机式四态（听/说/打断判定）；HumDial 上 Int 29.6 / Rej 50.2——拒识好打断差的镜像样本；Duplex-MPE 上"回应出现率 99.55% vs 新发起 25.25%"暴露假阳性
- PersonaPlex（People Making Conversation 参测）：全双工阵营里少数能定期沉默的
- SALMONN-omni：thinking token（`<listen>`/`<think>` 类）编码内部认知状态
- SyncLLM：同步 token [S0]/[S1] 作时钟节拍，80-500ms 块

### 3.2 基础设施/中间件

**Attention Labs SAA（Selective Auditory Attention，arXiv:2604.08412）**
- **定义**（官方可引用表述）："the real-time binary decision of whether a spoken utterance is addressed to the device or to another person"
- **设计原则四条**：pre-ASR（"addressee 信号是声学的，转写后即丢失"）；fails closed（不确定段不转发不转写不动作）；**声学而非内容**（无唤醒词，声称声学层面语言无关）；端侧无需 GPU
- **指标口径**：held-out 多方会话可靠性（audio+video 融合 / audio-only 两种）；官方明示两条 caveat：分布漂移下 fail closed、英语为主
- **商业形态**：per-device 授权；场景清单：车道点餐（后排人声/电台/店员串音）、服务机器人、临床 ambient scribe、座舱；附三种"不是它"的对比：VAD 问有没有人说话、diarization 问谁在说、intent 问什么意思——addressee 问"在对谁说"
- 意义：**验证 addressee 检测作为独立计价层的商业需求**

### 3.3 终端产品

- **理想"语义拒识"**：用户手册正式功能名，覆盖乘客闲聊不打扰（实质 S2/S3：音区+语义过滤），无 S1 声明、无任何公开指标
- **讯飞 AIUI 语义拒识**：平台能力外卖（~10 亿设备），受限域白名单+声纹/噪声过滤，无指标
- **小度"拒绝反应"（2019）**：国内最早"不该响应就不响应"产品化
- 共同点：**指标黑箱**——无 FA/hour、无工作点、无子场景分

### 3.4 组件/框架层（产业评测基础设施）

- **Deepgram Flux**：会话式流式 STT，模型内置端到端检测（end-of-turn detection）+ 可配置轮次动态——组件级把 EOT 当卖点
- **Pipecat Smart Turn / TEN Turn Detection**：开源 turn detector，被 Grok 等集成——级联路线的产业证据
- **ElevenLabs Realtime**：官方承认链式架构（此前调研：便宜版 Mini 反超 Max）
- **AWS Lex / Alexa Auto**：barge-in 与 push-to-talk 的工程化先例；Apple Siri：可用唤醒词限定打断（防 VoiceOver 误触发）——**用唤醒词做 addressee 锚定的产业惯例**

### 3.5 产业界的指标与量纲词典（与学术对照）

| 指标 | 使用者 | 定义 | 与 sidetalk 的关系 |
|---|---|---|---|
| **TTFA** | Amazon/行业 | 用户语音结束→响应首字节 | 端到端延迟，不区分拒识延迟 |
| **win rate（Common Eval）** | Amazon | 与竞品 A/B 对比偏好 | 对话质量，不测拒识 |
| **AA 对话动态分** | StepAudio 等自报 | FDB 口径总分 | non-addressed 只占部分权重 |
| **FA/hour（误唤醒率）** | 唤醒词行业 | 24h 静默测试误触发次数 | **唯一的产品级误响应量纲，从未用于全双工拒识** |
| **API 参数（semantic_vad/turn coverage/eagerness）** | OpenAI/Google | 暴露给开发者的轮次控制 | 定义黑箱，实测常不合格 |
| **WER** | Nova Sonic 等 | 转写错误率 | 声学级鲁棒性代理 |
| **(内部) 误响应率/重复率** | 全体终端厂 | 日志统计 | 不公开 |

---

## 4. 学术界指标词典（汇总去重，共 23 个）

**行为类（8）**：
1. **四态判定**（Respond/Resume/Uncertain/Unknown）——FDB v1.5 首创，GPT-4o/DeepSeek-V3 judge
2. **RESUME score / rejection rate**——拒识正确率（FDB/HumDial）
3. **early interrupt rate**——过早中断率（HumDial）
4. **binary accuracy + [Mute] token**——WearVox
5. **EER**——DDSD
6. **accuracy / macro-F1**——addressee 线
7. **IAS（Instruction Adherence Score）**——Instruct-FD（64.4% 上限）
8. **静默保持率 / 新发起回应率 / 应答窗口让位率 / 条件回答准确率**——Duplex-MPE 四件套

**时序类（6）**：
9. **t_stop**（让位速度）10. **t_resp**（修复速度）11. **first response latency**（HumDial）12. **TTFA**（产业对应物）13. **打断响应延迟 IRD** 14. **决策延迟曲线**（TurnBench 式 recall@延迟）

**分布/自然度类（5）**：
15. **KL 散度**（Talking Turns）16. **Wasserstein 距离**（HIPLEX 时机分布）17. **JSD**（FLEXI 附和分布）18. **韵律百分位协议**（Seamless Interaction 参考层）19. **takeover rate**（FDB v1/Moshibench 式抢话率）

**判别检测类（4）**：
20. **recall @ FPR 固定**（TurnBench）21. **Turn-taking-F1**（Talking Turns）22. **TOR/TTR/TSS/EDS/JIR/BCR**（FLEXI 六件套）23. **WER**（MMW）

---

## 5. 横向对比大表

### 5.1 学术 vs 产业（七维）

| 维度 | 学术界 | 产业界 |
|---|---|---|
| 定义形态 | 显式分类体系，2026 收敛到 non-addressed speech 上位概念 | 训练目标 / 状态 token / API 参数 / 产品功能名 / 商业定义，五种并存 |
| S1（SDO）覆盖 | 有定义、有 test 集（HumDial 200 条），**训练数据为 0** | **无一家声明**；Realtime-Venus 是唯一报过 88%（talking-to-others 继续率）的系统 |
| 主指标 | RESUME 型行为分 + 延迟三元组 + 分布散度 | TTFA / 榜单总分 / win rate /（不公开的日志指标） |
| 量纲缺口 | 无 FA/hour、无基率、无代价敏感工作点 | 有 FA/hour 概念（唤醒词行业）但从未用于全双工拒识 |
| 数据 | HumDial 107h 演员双轨（唯一 TPS+SDO 真实集）、WearVox 3,842 段、Seamless Interaction >4,000h（无 addressee 标注的底料）、Duplex-MPE 全合成 | 自有日志，不公开 |
| 评测方法 | 开源可复现（Docker 统一环境、leaderboard）；LLM judge 有偏置 | 自报榜单 / 第三方实测（AA、TurnBench、FDB）/ 不可测 |
| 多说话人观 | 2026 修正：旁人语音可能是上下文（Duplex-MPE） | 一律按干扰处理 |

### 5.2 全部基准一张表（sidetalk 视角）

| 基准 | 年份 | sidetalk 定义 | 主指标 | 数据构造 | sidetalk 相关实测 |
|---|---|---|---|---|---|
| Talking Turns | ICLR 2025 | （无显式 sidetalk；turn 事件族含 BC/I） | 事件 F1、KL、人类对照 | Switchboard 真实 | Moshi 用户拿话轮 17.4% vs 人 63.6% |
| FDB v1.5 | 2025-09 | talking-to-others + background speech（2/4） | 四态 RESUME + t_stop/t_resp | 电话语料+合成重叠（200 打断例） | GPT-4o 附和不停止（对）；Moshi 停顿抢话 0.980 |
| FLEXI | 2025-09 | 停顿+附和两场景 | TOR/TTR/TSS/EDS/JSD | Qwen-plus+CosyVoice2 合成 | Moshi 停顿 TOR 0.550 |
| WearVox | 2026-08 | Side-Talk Rejection 任务 | 二值准确率 | 3,842 段眼镜实采（含旁观者角色） | 多通道 85.6→93.9 |
| HumDial | 2026 ICASSP | TPS + SDO + URB + PH | rejection rate、early interrupt、总分 0.4/0.4/0.2 | 107h 演员双轨 | 冠军 Rej 72.2 / Moshi 22.8；**SDO 训练 0 条** |
| Duplex-MPE | 2026-09 | selective responding | 四个选择性指标 | 全合成（Claude+Qwen3-TTS） | Freeze-Omni 假阳性回应暴露 |
| Instruct-FD | 2026 | listen/continue 指令 | IAS | 912 例合成 | interrupt 遵循 1.7-11.7% |
| EchoChain | 2026-09 | （打断后推理；含 side 干扰注入） | 失败分类学 | planner-simulator 循环 | — |
| TurnBench | SLT 2026 | EOT+打断检测 | recall@FPR、延迟 | 自有演员语料 | OpenAI semantic_vad 0.303 |
| People Making Conv. | 2026-10 | 停顿点沉默决策 | 开口率+时机+事实回忆 | Seamless Interaction 427+482 点 | 托管 API 全开口；语义检测 ~8s |
| MMW | 2025-07 | side speech（ASR 级） | WER | 眼镜 5 麦 | WER −4.95% |
| FDB v2 | 2025-10 | 继承 v1.5 | 考官 agent 任务分 | 多轮合成 | — |

---

## 6. 空白点清单与引用建议

**六个可量化的空白（写报告的论点弹药）**：
1. S1（SDO）训练数据：学术界唯一带标注集里为 **0 条**；产业界零声明 → 定义权空置
2. FA/hour 型工作点指标：学术与产业的全双工侧都**从未使用**（唤醒词行业有现成传统）
3. 基率与代价敏感报告：没有任何基准报 precision-FPR 换算或误吞/误放代价不对称
4. 多说话人 addressee + 全双工流式的交叉：addressee 线全 offline，全双工线无 addressee 标注——两条线从未在同一基准交汇
5. 中文 sidetalk 基准：HumDial 中英双语但子类样本稀缺；其余全部英文为主
6. 评测的 LLM-judge 链路误差：无一篇报告 judge 本身与人工的一致性（除 Instruct-FD 的 89.6% 人类校验是例外）

**引用脚注建议（防错）**：
- StepAudio 98.9 = FDB 四条件总分（non-addressed 占其二），自报、无独立复现，FDB v1.5 已被 AA 移出总指数
- MMW 的 "side talk rejection" 是 WER 量纲 ≠ 轮次量纲
- Nova Sonic 全部对比数字为厂商自报（唯一 head-to-head 依赖 AA 口径）
- HumDial 的 Rej 分含 URB/PH（语义 VAD 领域），纯 sidetalk（TPS/SDO）子项未单独公布
- Talking Turns 的 Moshi 17.4% 基于每系统仅 4h 对话、用户打断只占 0.2% 决策——小样本，引用需带 n
- WearVox 室内/室外占比为论文口径 31%/63%

**推荐你的报告采用的术语策略**：英文主术语 **non-addressed speech**（学术正收敛于此），子类沿用 TPS/SDO/backchannel/pause（HumDial 体系，最完整），指标层自报体系用 recall@FA≤1/h（填补量纲空白）——三层引用都有出处，且你的位置恰好站在学术定义和产业量纲的交汇点上。

---

## 7. 参考文献全列表

**学术（按本文出现顺序）**
1. Jovanovic & op den Akker 2004；Jovanovic et al. 2006（addressee 会议线）
2. Ouchi & Tsuboi 2016；Gu et al. 2021（文本 addressee）
3. Inoue et al. 2025（GPT-4o addressee 四标签）；Fukuda et al. 2026（AMI，accuracy/macro-F1）
4. Adaptive KD for DDSD — arXiv:2508.02801（DDSD 定义、EER、+26%/+19%）
5. Garg et al. 2022；Wagner et al. 2024；Rudovic et al. 2024；Palaskar et al. 2024；Kim et al. 2026（DDSD 线）
6. MMW — arXiv:2507.05609（2025-07，Meta，Tri-Mamba/Frame Diarization/GRPO）
7. Full-Duplex-Bench v1.5 — arXiv:2507.23159（2025-09-07；G.T. Lin, S. Kuan, Q. Wang, J. Lian, T. Li, S. Watanabe, H.Y. Lee）
8. Full-Duplex-Bench v2 — Lin et al. 2025-10（自动化考官）
9. HumDial Challenge — arXiv:2601.05564；Full-Duplex Track 详文 arXiv:2604.21406；官网 aslp-lab.github.io/HumDial-Challenge；GitHub ASLP-lab/HumDial-FDBench
10. WearVox — arXiv:2601.02391（2026-08-10，Meta+CMU；HF: zlinao/WearVox）
11. Duplex-MPE — arXiv:2609.31948（2026-09）
12. Talking Turns — Arora, Lu, Chiu, Pang, Watanabe，ICLR 2025（CMU+Apple）
13. FLEXI — Ge et al.，arXiv:2509.22243（2025-09-26）
14. Instruct-FD（912 例；Claude 3.5 Sonnet judge；IAS 64.4%）
15. EchoChain — arXiv:2604.16456（失败分类学：contextual inertia / interruption amnesia / objective displacement；GPT-5.2 planner + Gemini 3 Pro simulator）
16. FD-Bench — Peng et al. 2025
17. TurnBench — Jiang et al.，IEEE SLT 2026（EOT recall/FPR/延迟；人类中位坚持 1.48s）
18. People Making Conversation — arXiv:2610.12802（2026-10；427 停顿+482 话轮终点；语义检测 ~8s）
19. Speak or Stay Silent / CoDeTT（多方转写文本的策略型基准，见 #18 Table 2）
20. Seamless Interaction（Meta，>4,000h）；SPEARBench（JHU+Amazon 2026，5,400 样本）；Reference-Based Prosody 协议（arXiv:2606.31055）
21. HIPLEX/GRPO 对比与 Wasserstein 时机分布（2026-11）
22. Lychee-FD（哈工大张民团队，ACL 2026 杰出论文；FDB 1.5 +28.5%）；SoulX-Duplug（2026-05，中英双语 FDB 口径）
23. SALMONN-omni（thinking token）；SyncLLM（同步 token）；LSLM（边说边听）；Realtime-Venus — arXiv:2609.13814

**产业**
24. StepAudio 3 Realtime — arXiv:2609.14005（2026-09-15，阶跃；AA FDB 自报 98.9）
25. Amazon Nova Sonic（2025-04；Nova 2 Sonic 2025-12）：TTFA 1.09s、WER 4.2%、barge-in 机制（AWS 官方文档）
26. Google Gemini Live API（2.5 Flash GA；3.1 Flash Live 2026-03 预览）：turn coverage 等参数（ai.google.dev 文档）
27. OpenAI Realtime API：server_vad/semantic_vad、eagerness、truncate 机制（platform.openai.com 文档）；TurnBench 第三方实测
28. xAI Grok Voice Agent API（2025-12-17）：custom VAD + Smart Turn（docs.x.ai）
29. MiniCPM-o 4.5 — arXiv:2604.27393（OpenBMB/THUNLP，Omni-Flow，[listen] token，9B 端侧）
30. Attention Labs SAA — arXiv:2604.08412；attentionlabs.ai（fails closed、pre-ASR、per-device）
31. Deepgram Flux（模型内置 EOT）；Pipecat Smart Turn；TEN Turn Detection；ElevenLabs Realtime（官方承认级联）
32. 理想"语义拒识"、讯飞 AIUI、小度拒绝反应（2019）：产品口径，无公开指标
