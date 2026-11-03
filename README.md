# sidetalk-eval

sideTalk（拒识 / 说话对象判定）评测集与选型工装。本仓库放**文档 + 代码 + 清单 + 结果**，音频通过打包下载（见 `DATA.md`）。

一句话结论：公开集尺子（尺子1）建成 **3,309 条 / 音频 100% 就位**；选型用最小集分两级（冒烟 120 + 判定 1,320）；首轮判定集上 qwen-plus 为**待定**（S1 77.6% `[73.4, 81.3]`、FRR 5.0% `[3.1, 8.1]`）。

## 文档

| 文件 | 内容 |
|---|---|
| `docs/sidetalk评测集-设计构建与结果.md` | **主文档**：设计（场景/指标/判分/淘汰线）、构建结果（3,309）、最小集设计（120+1,320）、首轮结果与判定 |
| `docs/候选模型与评测方法.md` | 跑道 A 文本裁判 10 个候选、跑道 B 端到端 6 个、四组实验矩阵、复现命令 |
| `docs/S4媒体人声冒烟方案.md` | S4（电视/外放/语音消息）200 条补采方案 |
| `docs/拒识sideTalk设计文档.md` | 上游设计文档（场景定义与模块边界，口径以其 §1.3 为准） |

HTML 版与 md 同名，直接打开即可。

## 代码（`tools/`）

| 脚本 | 作用 |
|---|---|
| `fetch.py` | 从 hf-mirror 下载（跟分页、只下清单、抗僵死） |
| `build_manifests.py` | 公开集 → 统一 S0–S4 清单（含 `audio_root`/`audio_ok`/`segments`） |
| `make_mini.py` | 最小集分层抽样（`--stage smoke` 120 / `--stage screen` 1320） |
| `llm_judge.py` | 被测系统适配器（openai_compat / jev / dryrun；`--text-mode`、`--prompt-version`） |
| `rule_baseline.py` | A0 基线：字符 n-gram + 逻辑回归（5 折 CV） |
| `baselines.py` | 平凡基线 all_silent / all_respond |
| `score.py` | 分场景拒识率 / FAR_w / FRR / clarify / invalid / 误执行 + Wilson CI + 工作点扫描 |
| `stats.py` | McNemar、Bootstrap AUC、最小可分辨差 |
| `package_audio.py` | 按清单打包实际用到的音频（只打引用文件） |

## 数据

- 清单在 `manifests/`（JSONL，含样本 ID、场景标签、转写、`audio_root`）
- 音频不入库，两种获取方式：
  - **Release 资产**：`eval-audio-v1`（chorus + humdial 两个包 + SHA256SUMS；WearVox 因许可不明不随仓库分发，用 fetch.py 取）
  - **重新下载**：`tools/fetch.py`（见 `DATA.md` §3）
- 三个公开集来源：`BiggestWave/ChorusDuplex-SideTalk`（CC BY 4.0）、`zlinao/WearVox`、`ASLP-lab/HumDial-FDBench`（Apache-2.0）

## 快速开始

```bash
python3 -m pip install scikit-learn numpy

# 1) 取音频（二选一）
python3 tools/fetch.py BiggestWave/ChorusDuplex-SideTalk data/chorus --jobs 6
# 或解包 DATA.md 里的 tar.gz 到 data/

# 2) 生成清单与最小集
python3 tools/build_manifests.py --dataset all --data data --out manifests
python3 tools/make_mini.py --manifests manifests --out manifests/mini_screen.jsonl --stage screen
python3 tools/make_mini.py --manifests manifests --out manifests/mini_smoke.jsonl \
        --stage smoke --min-cell 1 --from-file manifests/mini_screen.jsonl

# 3) 跑一个模型
python3 tools/llm_judge.py --manifest manifests/mini_screen.jsonl --backend openai_compat \
  --base-url https://dashscope.aliyuncs.com/compatible-mode/v1 \
  --model qwen-plus --text-mode last --prompt-version v3 \
  --out predictions/qwen-plus__screen.jsonl

# 4) 判分
python3 tools/score.py --manifest manifests/mini_screen.jsonl \
  --pred predictions/qwen-plus__screen.jsonl --only-predicted --sweep
```

## 口径提醒

1. `--text-mode last` 是产品口径（只判当前 VAD 段），`full` 只作最差情况对照，两者 S1 差约 19pt。
2. S0 少于 300 条时 FRR 不可信（冒烟集 60 条给出 21.7%，判定集 300 条给出 5.0%）。
3. 差异小于 CI 宽度一律写"不可区分"；判定集只能判"过不过 80% 门槛"，比 3pt 以内的高低要进全量。
