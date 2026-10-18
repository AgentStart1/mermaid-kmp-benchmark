# mermaid-kmp-benchmark

对 GitHub 上 Mermaid Kotlin Multiplatform 库进行可复现的 JVM 性能测量，参考 [mermaid-rust-benchmark](https://github.com/storytellerF/mermaid-rust-benchmark)。

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
python run_benchmarks.py
```

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
- 当前结果仅代表本机 JVM 热态延迟，不代表 Android、iOS、Kotlin/Native、JS 或 Wasm。不是与 Rust 参考项目在同一设备上运行的跨语言比较。
- `mermaid-native` 只添加 JVM 时钟 actual 和构建时版本常量，公共实现不修改。其余三个 Kotlin 库也通过本项目的独立 KMP JVM 构建编译；统一 Kotlin 2.3.21 和 coroutines 1.11.0 等依赖，不能直接等同于各库发布二进制的性能。

开发、CI 与测量方法见 [DEVELOPMENT.md](DEVELOPMENT.md)。
