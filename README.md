# SomaOS Brain Next — SO-100 集成版 (Robonix Community Entry)

> 本仓库为 Robonix 社区收录用「闭源部署目录」: 元数据 (robonix_manifest.yaml) +
> 可运行 demo 包 (demos/) + 容器构建与运行说明 (docker/) + 本 README。
> **不含源码 / 模型权重 / 训练数据 / 协议细节 / 内部基准数据。**

---

## 平台与验证状态 (Platform & Validation Status)

| 项 | 状态 |
|---|---|
| 目标平台 (Target) | Feetech SO-100 六轴串口机械臂 |
| 验证状态 (Validation) | **仅仿真验证 (simulation only)** — 安全门控过滤与轨迹跟随执行链路已对虚拟舵机模型闭环运行 |
| 真机状态 (Real robot) | **尚未在真实 SO-100 硬件部署** — 真机集成进行中 |
| 计算环境 (仿真) | x86 桌面, Windows 11 / Ubuntu 22.04 |
| 证据形式 | ① 本仓库可运行 demo (确定性, 结果可复现) ② 闭源二进制运行时 (GitHub Release [v1.1.0-bin](https://github.com/13717930620-alt/somaos-next-motor-brain-so100/releases/tag/v1.1.0-bin), mock 后端 `/health` 自检通过) ③ 闭源容器 (demo/ service 双模式) |

---

## 可运行演示 (Runnable Demos — clone 即跑)

零依赖 (纯 Python 标准库, 3.8+), 确定性输出。安全门控规则顺序
(急停锁存 → 限位检查 → 速度钳制 → 放行) 为公开通用工程模式, 在 demo 中
**真实可读**; 核心算法闭源, 详见 [demos/README.md](demos/README.md)。

```bash
# 演示 1: 安全门控 — 30 条指令流含越限/超速/急停注入, 逐条打印裁决
python demos/safety_gate/demo_safety_gate.py

# 演示 2: 轨迹跟随 — 3 个 SO-100 航点, 速度上限插值 + 虚拟舵机跟随误差统计
python demos/traj_follow/demo_traj_follow.py --seed 3 --hz 20
```

实测输出 (节选, 确定性可复现):

```
f18  !! ESTOP ASSERTED (scripted) -- latch engaged
f20  J5 pos= +90.0 vel= 40.0 -> ESTOP_LATCH (dropped)
summary: total=30  PASS=18  CLAMPED=2  REJECTED=2  ESTOP_LATCH=8

summary: waypoints=3  steps=124  overall_RMS=1.35deg  worst_err=2.34deg
```

---

## 闭源二进制运行时 (GitHub Release — 下载即跑, 免源码)

完整运动脑运行时已编译为 V8 字节码发布 (无任何可读源码 / 权重 / 凭据):

1. 从 [Release v1.1.0-bin](https://github.com/13717930620-alt/somaos-next-motor-brain-so100/releases/tag/v1.1.0-bin)
   下载 `somaos-brain-next-bin-1.1.0.zip`
2. 解压后仅需 Node.js 18+ (零外部依赖, 纯 Node 内置模块):

```bash
node loader.js
```

默认 mock 机器人后端启动, 监听 `127.0.0.1:3002`。自检:

```bash
curl http://127.0.0.1:3002/health
# -> 200 OK (JSON 健康/模块状态)
```

Web 控制台: `http://127.0.0.1:3002/console`。对接真实 SO-100 驱动
(`SOMAOS_ROBOT_BACKEND=http`, 驱动端口 3110) 与本地 LLM/VLM 的可选配置
详见包内 RUN.md。

---

## 部署 (闭源容器)

完整系统以编译后二进制形式发布为容器镜像 (源码与权重不出维护者环境):

```bash
# demo 模式 — 自包含, 无需权重, 输出完整门控/轨迹运行
docker run --rm ghcr.io/13717930620-alt/somaos-motor-brain:latest

# service 模式 — 启动闭源运动运行时 (权重启动时从维护者受控源拉取, sha256 校验)
docker run --rm -e SOMAOS_WEIGHT_URL="..." -e SOMAOS_WEIGHT_SHA256="..." \
  -p 8766:8766 ghcr.io/13717930620-alt/somaos-motor-brain:latest --mode service
```

镜像构建保证: 构建阶段将私有源码编译为二进制扩展, 运行阶段仅含编译产物
(源码层在阶段边界丢弃); 权重永不打入镜像。详见
[docker/install.md](docker/install.md)。

---

## 项目一句话定位

**SomaOS Brain Next (SomaOS 运动执行分册)** 是一个面向实体机械臂的「**零依赖安全执行内核**」。
它将高等动物的“脑干（基本生存反射）+ 小脑（快速时序协调）”组合，在极受限的硬件资源下，
依然为 Feetech SO-100 串口机械臂提供工业级功能：三层动作过滤 + 确定性实时执行 + VLA 热插拔接口。
设计金句: **确定性运行时 + 双重安全门控 + 轻量化引擎**。

---

## 为何 SomaOS Brain Next 不只是一个舵机机械臂控制箱

| 主流执行方案的结构性痛点 | SomaOS Brain Next 的设计对策 |
|---|---|
| 依赖爆炸: 完整 ROS2/MoveIt2 依赖包数百万启停几分钟任何一个包更新都可能引入安全回归 | **零依赖可验证运行时内核** |
| 安全是靠贴: Action Shield / CBF 在决策链外部, 与执行器不同步 | **双层动作过滤确定执行安全模型**: 慢链路+快链路 同核内部共 |
| VLA 绑定: 换一个 VLA 就要跟着重做一整套安全验证 | **VLA 热插拔热接入接口**: 换模型=改一行 URL |
| 经验回放是滑窗口FIFO: 经典的失败样本被"成功样本"淹没 | **高价值经验损失优先可信经验回放** |
| 运行时状态不可追溯 执行宕机了不知道是哪一层触发的 | **全链可回溯事件主链 + 结构诊断快照** |
| 资源空耗: 跑个舵机控制也要 Orin, 算力全花在了调度上 | **1GB RAM / 4核 ARM 低资源天地板限制** |

---

## 核心技术主栈 (概念层白皮书 · 不含任何实现细节)

> 以下描述全部为「公开可说明的算法层级技术主栈」。

### 栈1 零依赖可验证运行时内核 (dependencies = {})

### 栈2 双层动作过滤确定执行安全模型

### 栈3 VLA 热插拔热接入接口

### 栈4 高价值经验损失优先可信经验回放

### 栈5 全链可回溯事件主链 + 结构诊断快照

### 栈6 1GB RAM / 4核 ARM 低资源天地板限制

---

## 对外接口

- **标准**: RCAN 指令入口 / HTTP 本地控制接口 / 可插 VLA 上游模型接入 / ESTOP 制动主线路输入 / 状态事件回传
- **部署方式**: 独立 robot entry，与 cognitive_brain 协同使用 RCAN 语义接口层对接

---

## 平台说明

- **适用硬件**: Feetech SO-100 串口机械臂 (Feetech 主编驱动全驱系列)
- **推荐算力**: 树莓派 4+ / Jetson Nano+ / Jetson Orin (低至 1GB 内存 + 4核 ARM 级即可稳定运行)
- **操作系统**: Linux (Ubuntu 22.04+ 推荐); Windows 开发可用

---

## 许可证

MulanPSL-2.0
