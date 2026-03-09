# ZeroAgent: Project Specification

## Overview
本项目旨在构建一个极简、高效且完全私有化的 AI 原生开发基础设施（AI-Native IDE Infrastructure）。系统将从单个文件的注释补全起步，逐步演进为跨越多个代码仓库的自动化代码生成、测试除错（Debugging）以及依赖管理的全局智能中枢（Orchestrator）。

---

## Phase 1: Custom SLM Fine-Tuning
**目标**：利用个人代码数据与开源高质量数据集，微调（Fine-tune）一个能够精准理解个人编码风格的小型语言模型（SLM）。

* **Workflow**:
    1.  收集并清洗个人的高质量代码片段，构建指令集（Instruction Dataset）。
    2.  利用云端免费 GPU 算力进行模型训练。
    3.  将训练完成的模型权重导出为量化格式，并部署至本地终端。
* **Tech Stack**:
    * **Compute**: Kaggle Notebooks (提供免费的 T4/P100 GPU 算力)。
    * **Framework**: Unsloth (极度轻量且高效的微调框架，完美替代传统的 Hugging Face `transformers`，显著降低 VRAM 占用)。
    * **Base Model**: DeepSeek-R1-1.5B (或同级别带有思维链能力的蒸馏模型)。
    * **Deployment**: Ollama + GGUF (本地轻量级推理引擎)。

## Phase 2: Instant Docstring Assistant
**目标**：实现跨语言的即时注释补全。当开发者保存文件时，系统自动识别变更区块并补全符合规范的 Docstring。

* **Workflow**:
    1.  启动后台守护进程（Daemon），持续监听工作区（Workspace）的文件 `Save` 事件。
    2.  一旦触发，提取发生变动的代码区块（支持 HTML, SCSS, CSS, JS, Python）。
    3.  将代码片段发送至本地部署的 SLM。
    4.  接收模型返回的 Docstring，并无缝回写至源文件。
* **Tech Stack**:
    * **File Monitor**: `watchdog` (Python 库，用于监听文件系统级事件)。
    * **Syntax Parser**: Tree-sitter (现代化的抽象语法树 AST 解析器，支持多语言且性能极高，淘汰老旧的正则表达式匹配)。

## Phase 2.5: AI-Driven Code Generation
**目标**：引入大模型 API，根据自然语言提示（Prompt）生成符合个人架构风格的代码模块。

* **Workflow**:
    1.  解析代码中特定的触发注释（Trigger Comments，例如 `// @Agent: Generate Auth Logic`）。
    2.  提取当前文件的上下文（Context）作为代码风格参考。
    3.  构造 Prompt 并路由（Route）至云端大语言模型（LLM）。
    4.  将返回的代码流（Code Stream）插入至源文件指定位置。
* **Tech Stack**:
    * **API Gateway**: LiteLLM (极简的统一接口库。仅需几行代码即可无缝切换 OpenAI, Anthropic, DeepSeek 等不同 LLM 厂商的 API，无需编写冗长的请求适配器)。

## Phase 3: Auto-Debug Loop
**目标**：建立具备弹性的自动化纠错循环。遇到代码执行报错时，优先使用本地 SLM 进行快速修复；若连续失败，则向上层 LLM 寻求解决方案。

* **Workflow**:
    1.  在测试环境（Test Environment）中运行代码。若发生 `Exception` 或测试未通过，捕获 `Traceback` 信息。
    2.  **Tier 1 (Local SLM)**: 将报错信息与源码发送给本地 1.5B 模型。模型输出修改补丁（Patch），脚本自动应用并重试。此过程最多循环 3 次。
    3.  **Tier 2 (Cloud LLM)**: 若本地模型 3 次尝试均告失败，触发降级策略（Fallback Mechanism）。打包所有的试错历史与上下文，调用云端 LLM API 进行终极修复。
* **Tech Stack**:
    * **Process Execution**: Python `subprocess` (静默执行 `pytest` 等测试命令并捕获 `stdout/stderr`)。
    * **Patching**: 借鉴 Aider 的 Diff 格式解析逻辑，实现文件的精准行级替换，避免模型重写整个文件。

## Phase 4: Single-Repo Context Management
**目标**：为单个仓库引入向量检索（RAG），使 Agent 在除错或生成代码时，能够跨文件理解依赖关系（例如修改 `agent.py` 时，能感知到 `tools.py` 中的接口变更）。

* **Workflow**:
    1.  首次初始化时，解析仓库内所有文件，按函数/类（Function/Class）进行语义切片（Chunking）。
    2.  生成文本向量（Embeddings）并存入本地数据库。
    3.  当进入 Phase 3 的除错循环时，先通过报错信息在数据库中进行相似度检索（Similarity Search），将最相关的本地代码片段作为 Context 注入到 Prompt 中。
* **Tech Stack**:
    * **Vector Database**: LanceDB (无服务器、纯本地嵌入式的轻量级向量数据库。查询速度极快，完美替代过于笨重的 Milvus 或 Elasticsearch)。
    * **Embedding Model**: BGE-Micro 或对应级别的本地极小词向量模型。

## Phase 5: Multi-Repo Dependency Tracking
**目标**：突破单点仓库限制，构建跨项目的依赖拓扑图（Dependency Graph）。当底层基建仓库更新时，上层业务仓库能自动感知并作出响应。

* **Workflow**:
    1.  执行全局扫描（Global Scan），提取所有受管仓库（Repositories）间的 `import` 引用或 API 调用关系。
    2.  在内存中维护一个映射表（Mapping Table）。
    3.  当检测到某个被依赖的核心函数发生签名（Signature）变更时，系统自动锁定所有受影响的外部仓库文件。
* **Tech Stack**:
    * **Data Structure**: 纯 JSON 结合 Python Native `dict` (对于几十个仓库、数千个文件的个人项目规模，内存字典的查询时间复杂度为 O(1)，完全不需要引入 Neo4j 等重量级图数据库)。

## Phase 6: Global Orchestrator
**目标**：整合上述所有模块，构建一个高并发、低延迟的中央调度脚本，作为整个 AI 基础设施的大脑。

* **Workflow**:
    1.  启动 `orchestrator.py` 作为主入口，挂载所有的系统监听器。
    2.  统一管理客户端连接（例如通过 `clients/__init__.py` 封装对外部 LLM API 和本地 Ollama 的网络请求）。
    3.  定义标准的事件驱动链路（Event-driven Pipeline）：如 "底层库修改 -> 触发 Phase 5 依赖分析 -> 锁定关联仓库 -> 激活 Phase 4 提取上下文 -> 进入 Phase 3 执行静默测试与修复"。
* **Tech Stack**:
    * **Concurrency**: Python `asyncio` (利用异步 I/O 确保主控中枢在等待 LLM 响应或扫描大量文件时，不会阻塞整个系统的运行，保持极致的轻量化)。