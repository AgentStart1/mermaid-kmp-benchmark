# mermaid-kmp-benchmark

对 GitHub 上 Mermaid Kotlin Multiplatform 库进行可复现的 JVM 性能测量，参考 [mermaid-rust-benchmark](https://github.com/storytellerF/mermaid-rust-benchmark)。

## 查看结果

[完整图表报告](report.html) 按测量阶段和图类型展示耗时、相对倍数、置信区间及 JVM 内存分配。下载或克隆仓库后，用浏览器打开 `report.html`；GitHub 文件页显示的是 HTML 源码。

当前快照：**5 个库、20 项成功测量、1 项跳过**，测量于 2026-10-18，Windows x86_64 / JDK 21，Kotlin 2.3.21 / coroutines 1.11.0。

### SVG 结果摘要

平均耗时，单位为 **µs/次，越低越快**。三组结果均包含解析、布局和 SVG 序列化；Rust KMP 还包含 JNI 调用。

| 库 | 简单流程图 | 复杂流程图 | 时序图 |
| --- | ---: | ---: | ---: |
| mermaid-native（JVM 适配） | 29.94 | 145.46 | 63.78 |
| lugf027/mermaid | 86.38 | 464.44 | 51.80 |
| mermaid-rust-kmp alpha5 | 5,521.40 | 116,906.25 | 533.36 |

CMP 场景生成和 diagram 解析结果见完整报告，它们不参与 SVG 排名。上述数值仅对应所记录的版本、输入与环境，具体误差和逐轮采样见原始数据。

| 记录 | 内容 |
| --- | --- |
| [原始采样](results/jmh.json) | JMH 每轮结果、平均值与误差 |
| [测量环境](results/environment.json) | 运行配置、版本和输入 SHA-256 |
| [前置检查](results/preflight.json) | 成功项与跳过原因 |
| [SVG 样本](results/samples/) | 三个 SVG 实现的实际输出 |
| [版本锁定](libraries.lock.json) | 上游提交和 Rust KMP 制品校验值 |

## 候选库与测量范围

| 项目 | 本项目测量内容 |
| --- | --- |
| [mermaid-rust-kmp](https://github.com/storytellerF/mermaid-rust-kmp) | 发布版 `0.0.1-alpha5`：KMP API → JNI → Rust → SVG，包含跨语言调用开销 |
| [cmp-mermaid](https://github.com/swithun-liu/cmp-mermaid) | 解析、布局、场景生成；不含 Compose 绘制 |
| [mermaid-native](https://github.com/botiverse/mermaid-native) | 解析；端到端 SVG。公共源码的 JVM 适配，并非上游支持的平台 |
| [lugf027/mermaid](https://github.com/lugf027/mermaid) | 解析；端到端 SVG |
| [huarangmeng/diagram](https://github.com/huarangmeng/diagram) | 流程图/时序图底层 lexer + parser + IR snapshot |

搜集时间为 2026-10-18，候选、排除理由见 [discovery.json](discovery.json)。另核对了独立维护的 `zusrsoft/diagram`：本轮所用 Mermaid parser 和 core 源码与原项目一致，逐文件证据见 [discovery-source-comparison.json](discovery-source-comparison.json)，共享路径只计时一次。所有参与测量的上游固定到 [libraries.lock.json](libraries.lock.json) 中的提交，四个 Kotlin 实现以源码构建；Rust KMP 使用锁定版本的 Maven Central JVM 制品并校验 SHA-256，不使用浮动版本。

## 运行

需要 JDK 21、Python 3.10+、Git 和网络连接。Gradle Wrapper 随项目提供。

```sh
git clone https://github.com/storytellerF/mermaid-kmp-benchmark.git
cd mermaid-kmp-benchmark
python run_benchmarks.py
```

Linux / macOS 首次运行前执行 `chmod +x gradlew`；Windows 可直接运行，脚本会选择 `gradlew.bat`。

正式配置：单线程，每项 2 个独立 JVM；每个 JVM 预热 5 × 1 秒，测量 8 × 1 秒。使用 JMH 1.37 AverageTime，返回值交给 JMH 消费，GC profiler 记录分配量。首次运行会下载上游和构建依赖。

快速验证：

```sh
python run_benchmarks.py --profile smoke
```

结果为 `report.html`、`results/jmh.json`、环境记录、每项 JMH 日志和 SVG 样本。smoke 结果只适合验证流程，不能作为正式排名。

## 如何解读

- 沿用 Rust 项目的简单流程图、复杂流程图、时序图三组输入，内容不改写。复杂图有 11 个节点、13 条边、2 个子图；时序图有 3 个参与者和 8 条消息。
- **只在相同阶段内比较。** SVG 包含解析、布局和序列化；scene 不含最终绘制；parse 不含布局。不同文本测量和布局算法也会影响工作量，不应据此单独判断库质量。
- 前置检查验证结构数量、SVG 包装或非空场景，并重复调用检查状态累积。失败项保留诊断、跳过计时。`diagram` 底层 parser 在复杂图 `subgraph` 处失败，这不是对整个高层 SDK 的全面兼容性结论。
- SVG 和 scene 检查不是像素级保真验证。没有统一字体、统一布局或全面语义校验；场景生成仅检查尺寸和非空元素。
- Rust KMP 没有公开的独立解析 API，仅参与 SVG 组。该项验证 XML、图形元素和预期文字，不检查内部 AST。原生库加载在预热前完成，热态计时包含每次 JNI 调用和返回字符串转换。GC profiler 的 B/op 仅覆盖 JVM 堆，不包含 Rust 原生堆，不能据此比较总内存开销。
- 当前结果仅代表本机 JVM 热态延迟，不代表 Android、iOS、Kotlin/Native、JS 或 Wasm。
- `mermaid-native` 只添加 JVM 时钟 actual 和构建时版本常量，公共实现不修改。其余三个 Kotlin 库也通过本项目的独立 KMP JVM 构建编译；统一 Kotlin 2.3.21 和 coroutines 1.11.0 等依赖，不能直接等同于各库发布二进制的性能。

开发、CI 与测量方法见 [DEVELOPMENT.md](DEVELOPMENT.md)。
