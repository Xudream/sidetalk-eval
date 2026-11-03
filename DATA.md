# 数据与打包

音频**不入库**（体积 + 许可），只保留"清单 + 打包 + 校验"三件套。

## 1. 包内容

打包规则：只打 `manifests/` 里**实际引用**的音频文件，不打包整份数据集。

| 包 | 文件数 | 压缩后 | 解压占用（约） | 覆盖 |
|---|---:|---:|---:|---|
| `chorus.tar.gz` | 93 | 339 MB | 341 MB | ChorusDuplex 93 段对话音频（1,338 条样本按时间轴切分引用） |
| `humdial.tar.gz` | 889 | 166 MB | 612 MB | HumDial 中文 test 5 个目录的 raw wav（不含 `clean_` 副本） |
| `wearvox.tar.gz` | 1,082 | 138 MB | 197 MB | WearVox non-assistant-directed 用到的 wav |
| **合计** | **2,064** | **643 MB** | **1.15 GB** | 覆盖全部 3,309 条样本 |

包内路径：`<dataset>/<相对路径>`，例如 `chorus/audio/side_talk-0001.flac`、`wearvox/wav/GH8w-....wav`、`humdial/talk_to_others/0006_0011_add.wav`。

**发行说明**：Release `eval-audio-v1` 托管三个包。Chorus 为 CC BY 4.0（须署名）、HumDial 为 Apache-2.0（须保留声明）；WearVox 的仓库许可未明确禁止二次分发，此处仅为内部评测复现留存，不对第三方再分发。

## 2. 校验和

```
bde3130e3cd246c5c29412c3571d1b256493d8f97468098be58b4e1f1f8d76e8  chorus.tar.gz
504187dc3e50c5b332c907a1b2f96a15e5e261381ca7de443937228f68c4b529  humdial.tar.gz
e36fb9aa92d3d3ecda0c8fce2a970e082c8cb07bd5ed0eddc043144a6ebc8939  wearvox.tar.gz
```

校验：

```bash
shasum -a 256 -c SHA256SUMS
```

## 3. 获取方式（三选一）

### A. 解包本地打包文件

```bash
mkdir -p data && tar -xzf chorus.tar.gz -C data && tar -xzf humdial.tar.gz -C data && tar -xzf wearvox.tar.gz -C data
```

包内路径与清单里的 `audio` 字段一一对应，解包到 `data/` 即可：

| 包 | 解包后 | 清单里 `audio` 形如 |
|---|---|---|
| chorus | `data/chorus/` | `audio/side_talk-0001.flac` |
| wearvox | `data/wearvox/` | `wav/GH8w-....wav` |
| humdial | `data/humdial/` | `talk_to_others/0006_0011_add.wav` |

> 仓库里的 `audio_root` 是**相对路径**（`data/chorus`、`data/wearvox`、`data/humdial`），解包到 `data/` 后可直接用。若你的数据放在别处，重跑 `build_manifests.py --data <你的路径>` 会自动重写。

### B. 重新下载（推荐，格式与官方一致）

```bash
python3 tools/fetch.py BiggestWave/ChorusDuplex-SideTalk data/chorus --jobs 6
python3 tools/fetch.py zlinao/WearVox data/wearvox --only-file wearvox_needed.txt --jobs 4
```

WearVox 全量 59.45 GB（3,842 wav + 3,842 双通道原始录音），评测只需要其中 1,082 个单通道 wav；`--only-file` 可只下这些。

### C. 打包（自己重建）

```bash
python3 tools/build_manifests.py --dataset all --data data --out manifests
python3 tools/package_audio.py --manifests manifests --out pack
```

## 4. 许可与使用边界

| 集 | 许可 | 义务 |
|---|---|---|
| ChorusDuplex-SideTalk | CC BY 4.0 | 保留署名；babble 变体再分发须保留 VOiCES 出处 |
| HumDial-FDBench | Apache-2.0 | 保留声明 |
| WearVox | 见仓库 | 第一视角数据，禁止用于人脸/身份推断 |

本仓库的打包文件仅供内部评测复现，不再对外分发。若需对外发布结果，请引用原始数据集仓库。
