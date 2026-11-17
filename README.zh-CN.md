<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/banner-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="./assets/banner-light.svg" />
    <img alt="Yuuki-git 个人主页横幅" src="./assets/banner-dark.svg" width="100%" />
  </picture>

  <br />

  [English](./README.md) · **简体中文** &nbsp;|&nbsp;
  [全部仓库](https://github.com/Yuuki-git?tab=repositories) ·
  [代表项目](#-代表项目) ·
  [技术栈](#-技术栈) ·
  [数据概览](#-github-数据概览)
</div>

---

### 关于我

我是 **Yuuki**，目前在 **郑州大学（ZZU）** 攻读硕士研究生学位，关注 **多模态人工智能（Multimodal AI）** 科研与 **后端 / AI 基础设施工程**。比起停留在概念层面，我更倾向于把想法落地成可复现、可验证、可观测的真实系统——既写面向生产的后端服务与 Agent 架构，也深入异构 GPU 算子与推理优化。

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>科研方向 · 多模态 AI</h4>
      <ul>
        <li><strong>研究兴趣：</strong>多模态表征学习与多模态生成模型推理加速</li>
        <li><strong>算子与编译：</strong>基于 <code>NineToothed</code>、<code>Triton/HIP</code>、<code>InfiniCore</code> 与 <code>InfiniLM</code> 进行算子融合及 AOT 编译接入</li>
        <li><strong>工程复现：</strong>海光多卡（gfx936 / gfx906）视频生成推理部署与数值 / 性能基准测试</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>工程方向 · 后端开发与 AI Infra</h4>
      <ul>
        <li><strong>后端主力栈：</strong><code>Java</code>（<code>Spring Boot 3</code>、<code>WebFlux</code>、<code>Spring AI</code>）与 <code>Python</code>（<code>FastAPI</code>、<code>LangGraph</code>）</li>
        <li><strong>AI 应用工程：</strong>混合检索 RAG（<code>BM25 + 向量 + RRF</code>）、状态化 Agent 编排与断线可恢复 SSE 流式输出</li>
        <li><strong>数据与部署：</strong><code>PostgreSQL</code>、<code>Redis</code>、<code>OpenSearch</code>、<code>Chroma</code> 及 Docker 容器化交付</li>
      </ul>
    </td>
  </tr>
</table>

---

### 代表项目

<table>
  <tr>
    <td width="50%" valign="top">
      <h4><a href="https://github.com/Yuuki-git/Smart-Knowledge-Hub">Smart-Knowledge-Hub</a></h4>
      <sub>企业级混合检索 RAG 智能代码助手</sub>
      <p>
        面向 Spring Cloud 架构文档、Java 源码与运维日志的“可检索、可溯源、可控幻觉” RAG 系统。结合 <code>OpenSearch (BM25)</code> + <code>Chroma</code> + <code>RRF</code> 融合排序、AST/PDF 解析、作用域过滤引用与 Redis 多轮会话流式输出，支持 DeepSeek / OpenAI / Ollama。
      </p>
      <code>Java 17</code> · <code>Spring Boot 3.5</code> · <code>Spring AI</code> · <code>WebFlux</code> · <code>Vue 3</code>
    </td>
    <td width="50%" valign="top">
      <h4><a href="https://github.com/Yuuki-git/EasyPlan">EasyPlan</a></h4>
      <sub>意图驱动的 AI 规划 Agent 系统</sub>
      <p>
        融合行为模型的智能规划管线（<code>意图画像 → 策略路由 → 规划器 → 运行时校验</code>）。支持三层规划拆解、人在回路（HITL）阶段推进、长期执行闭环以及刷新可恢复的 SSE 流式生成。
      </p>
      <code>Python</code> · <code>FastAPI</code> · <code>LangGraph</code> · <code>React</code> · <code>TypeScript</code> · <code>PostgreSQL</code>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h4><a href="https://github.com/Yuuki-git/minimax-h3-8gpu">minimax-h3-8gpu</a> &amp; <a href="https://github.com/Yuuki-git/songshan3">songshan3</a></h4>
      <sub>多模态视频生成推理与九齿算子优化</sub>
      <p>
        在 8 卡海光 <code>gfx936</code> 与单卡 <code>gfx906</code> 环境完成 MiniMax-H3 FL2VA 推理接入与核心算子优化（<code>二维/三维 RMSNorm</code>、<code>三维 AdaLN + 门控残差融合</code>），通过 <a href="https://github.com/Yuuki-git/ninetoothed-ss5">NineToothed</a> 编译链生成并接入 <code>InfiniCore</code> / <code>InfiniLM</code>。
      </p>
      <code>Python</code> · <code>C++</code> · <code>NineToothed</code> · <code>HIP / Triton</code> · <code>Shell</code>
    </td>
    <td width="50%" valign="top">
      <h4><a href="https://github.com/Yuuki-git/ninetoothed-ss5">ninetoothed-ss5</a> &amp; <a href="https://github.com/Yuuki-git/InfiniCore/tree/minimax-h3-8gpu-opt">InfiniCore</a> / <a href="https://github.com/Yuuki-git/InfiniLM/tree/minimax-h3-8gpu-opt">InfiniLM</a></h4>
      <sub>编译工具链与推理引擎算子接入</sub>
      <p>
        <strong>ninetoothed-ss5：</strong>面向海光 <code>gfx936</code> AOT HIP 编译与缓存目录适配的 NineToothed 0.26.0 补丁版本。<br/>
        <strong>InfiniCore / InfiniLM：</strong>在 <code>minimax-h3-8gpu-opt</code> 分支完成自定义注意力与 AdaLN 算子集成。
      </p>
      <code>Python</code> · <code>C++</code> · <code>Triton / HIP</code> · <code>InfiniTensor</code>
    </td>
  </tr>
</table>

---

### 技术栈

| 维度 | 常用技术 |
| :--- | :--- |
| **编程语言** | ![Python](https://img.shields.io/badge/Python-3572A5?style=flat-square&logo=python&logoColor=white) ![Java](https://img.shields.io/badge/Java-ED8B00?style=flat-square&logo=openjdk&logoColor=white) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white) ![C++](https://img.shields.io/badge/C%2B%2B-00599C?style=flat-square&logo=cplusplus&logoColor=white) ![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat-square&logo=postgresql&logoColor=white) |
| **后端与系统** | ![Spring Boot](https://img.shields.io/badge/Spring_Boot_3-6DB33F?style=flat-square&logo=springboot&logoColor=white) ![WebFlux](https://img.shields.io/badge/WebFlux-6DB33F?style=flat-square&logo=spring&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) |
| **多模态与 Agent** | ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white) ![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square) ![Spring AI](https://img.shields.io/badge/Spring_AI-6DB33F?style=flat-square&logo=spring&logoColor=white) ![OpenSearch](https://img.shields.io/badge/OpenSearch-005EB8?style=flat-square&logo=opensearch&logoColor=white) ![Chroma](https://img.shields.io/badge/Chroma_DB-FF6F00?style=flat-square) ![HuggingFace](https://img.shields.io/badge/Hugging_Face-FFD21E?style=flat-square&logo=huggingface&logoColor=black) |
| **前端与环境** | ![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black) ![Vue.js](https://img.shields.io/badge/Vue_3-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white) ![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black) ![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white) |

---

### GitHub 数据概览

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/stats-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="./assets/stats-light.svg" />
    <img alt="Yuuki-git GitHub 统计卡片" src="./assets/stats-dark.svg" width="100%" />
  </picture>
</div>

<div align="center">
  <sub>由 <a href="./.github/workflows/update-profile.yml">GitHub Actions</a> 每日自动更新 · 郑州大学（ZZU）</sub>
</div>
