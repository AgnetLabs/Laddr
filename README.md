# 🚀 Laddr<p align="center">

  <a href="https://github.com/crewAIInc/crewAI">

**A transparent, Docker-native, observable, distributed agent framework.**    <img src="docs/images/crewai_logo.png" width="600px" alt="Open source Multi-AI Agent orchestration framework">

  </a>

Build scalable multi-agent systems with local-first defaults and complete control over every aspect of your agents.</p>

<p align="center" style="display: flex; justify-content: center; gap: 20px; align-items: center;">

---  <a href="https://trendshift.io/repositories/11239" target="_blank">

    <img src="https://trendshift.io/api/badge/repositories/11239" alt="crewAIInc%2FcrewAI | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/>

## ✨ Why Laddr?  </a>

</p>

Laddr is built on three core principles:

<p align="center">

1. **🔍 Transparency** - No hidden abstractions. Every communication is visible via message queues.  <a href="https://crewai.com">Homepage</a>

2. **🐳 Container-Native** - Each agent runs in its own Docker container. Scale horizontally with ease.  ·

3. **📊 Observable** - Built-in OpenTelemetry tracing, Prometheus metrics, and structured logging.  <a href="https://docs.crewai.com">Docs</a>

  ·

### Local-First Philosophy  <a href="https://app.crewai.com">Start Cloud Trial</a>

  ·

- **LLM**: Ollama (local) by default, supports OpenAI, Anthropic, Gemini, Groq, llama.cpp  <a href="https://blog.crewai.com">Blog</a>

- **Database**: SQLite (local) by default, supports PostgreSQL, MySQL  ·

- **Storage**: Filesystem (local) by default, supports MinIO, S3  <a href="https://community.crewai.com">Forum</a>

- **Queue**: Redis Streams (can run locally), supports Kafka, RabbitMQ</p>



---<p align="center">

  <a href="https://github.com/crewAIInc/crewAI">

## 🎯 Quick Start    <img src="https://img.shields.io/github/stars/crewAIInc/crewAI" alt="GitHub Repo stars">

  </a>

### Prerequisites  <a href="https://github.com/crewAIInc/crewAI/network/members">

    <img src="https://img.shields.io/github/forks/crewAIInc/crewAI" alt="GitHub forks">

- Python 3.10+  </a>

- Docker & Docker Compose  <a href="https://github.com/crewAIInc/crewAI/issues">

- (Optional) Ollama for local LLM    <img src="https://img.shields.io/github/issues/crewAIInc/crewAI" alt="GitHub issues">

  </a>

### Installation  <a href="https://github.com/crewAIInc/crewAI/pulls">

    <img src="https://img.shields.io/github/issues-pr/crewAIInc/crewAI" alt="GitHub pull requests">

```bash  </a>

# Clone the repository  <a href="https://opensource.org/licenses/MIT">

git clone https://github.com/laddr/laddr.git    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">

cd laddr  </a>

</p>

# Install Laddr

cd lib/laddr<p align="center">

pip install -e .  <a href="https://pypi.org/project/crewai/">

    <img src="https://img.shields.io/pypi/v/crewai" alt="PyPI version">

# Or with all integrations  </a>

pip install -e ".[all]"  <a href="https://pypi.org/project/crewai/">

```    <img src="https://img.shields.io/pypi/dm/crewai" alt="PyPI downloads">

  </a>

### Create Your First Project  <a href="https://twitter.com/crewAIInc">

    <img src="https://img.shields.io/twitter/follow/crewAIInc?style=social" alt="Twitter Follow">

```bash  </a>

# Initialize a new project</p>

laddr init my_project

cd my_project### Fast and Flexible Multi-Agent Automation Framework



# Add agents> CrewAI is a lean, lightning-fast Python framework built entirely from scratch—completely **independent of LangChain or other agent frameworks**.

laddr add agent researcher> It empowers developers with both high-level simplicity and precise low-level control, ideal for creating autonomous AI agents tailored to any scenario.

laddr add agent writer

- **CrewAI Crews**: Optimize for autonomy and collaborative intelligence.

# Edit agent configs in agents/ directory- **CrewAI Flows**: Enable granular, event-driven control, single LLM calls for precise task orchestration and supports Crews natively

# Edit pipeline in pipelines/

With over 100,000 developers certified through our community courses at [learn.crewai.com](https://learn.crewai.com), CrewAI is rapidly becoming the

# Start development environmentstandard for enterprise-ready AI automation.

laddr run dev

# CrewAI AMP Suite

# View dashboard

open http://localhost:5173CrewAI AMP Suite is a comprehensive bundle tailored for organizations that require secure, scalable, and easy-to-manage agent-driven automation.

```

You can try one part of the suite the [Crew Control Plane for free](https://app.crewai.com)

---

## Crew Control Plane Key Features:

## 📊 Architecture

- **Tracing & Observability**: Monitor and track your AI agents and workflows in real-time, including metrics, logs, and traces.

```- **Unified Control Plane**: A centralized platform for managing, monitoring, and scaling your AI agents and workflows.

┌─────────────┐     ┌─────────────┐     ┌─────────────┐- **Seamless Integrations**: Easily connect with existing enterprise systems, data sources, and cloud infrastructure.

│  Controller │────▶│Redis Streams│────▶│   Workers   │- **Advanced Security**: Built-in robust security and compliance measures ensuring safe deployment and management.

│  (Submits)  │     │  (Queue)    │     │ (Per Agent) │- **Actionable Insights**: Real-time analytics and reporting to optimize performance and decision-making.

└─────────────┘     └─────────────┘     └─────────────┘- **24/7 Support**: Dedicated enterprise support to ensure uninterrupted operation and quick resolution of issues.

                                               │- **On-premise and Cloud Deployment Options**: Deploy CrewAI AMP on-premise or in the cloud, depending on your security and compliance requirements.

                                               ▼

                    ┌──────────────────────────────────┐CrewAI AMP is designed for enterprises seeking a powerful, reliable solution to transform complex business processes into efficient,

                    │      Observability Stack         │intelligent automations.

                    │  • OpenTelemetry (Traces)        │

                    │  • Prometheus (Metrics)          │## Table of contents

                    │  • Structured Logs               │

                    └──────────────────────────────────┘- [Why CrewAI?](#why-crewai)

```- [Getting Started](#getting-started)

- [Key Features](#key-features)

---- [Understanding Flows and Crews](#understanding-flows-and-crews)

- [CrewAI vs LangGraph](#how-crewai-compares)

## 🎨 Features- [Examples](#examples)

  - [Quick Tutorial](#quick-tutorial)

### ✅ Multi-LLM Support  - [Write Job Descriptions](#write-job-descriptions)

  - [Trip Planner](#trip-planner)

```yaml  - [Stock Analysis](#stock-analysis)

# agents/researcher.yml  - [Using Crews and Flows Together](#using-crews-and-flows-together)

name: researcher- [Connecting Your Crew to a Model](#connecting-your-crew-to-a-model)

role: Research Specialist- [How CrewAI Compares](#how-crewai-compares)

llm_provider: ollama      # Local default- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)

llm_model: llama2- [Contribution](#contribution)

- [Telemetry](#telemetry)

# Or use cloud providers- [License](#license)

llm_provider: openai

llm_model: gpt-4## Why CrewAI?

llm_api_key: ${OPENAI_API_KEY}

```<div align="center" style="margin-bottom: 30px;">

  <img src="docs/images/asset.png" alt="CrewAI Logo" width="100%">

Supported providers:</div>

- **Ollama** (local, default)

- **llama.cpp** (local)CrewAI unlocks the true potential of multi-agent automation, delivering the best-in-class combination of speed, flexibility, and control with either Crews of AI Agents or Flows of Events:

- **OpenAI** (gpt-4, gpt-4-turbo, gpt-3.5-turbo)

- **Anthropic** (claude-3-opus, claude-3-sonnet)- **Standalone Framework**: Built from scratch, independent of LangChain or any other agent framework.

- **Google Gemini** (gemini-pro, gemini-ultra)- **High Performance**: Optimized for speed and minimal resource usage, enabling faster execution.

- **Groq** (fast inference)- **Flexible Low Level Customization**: Complete freedom to customize at both high and low levels - from overall workflows and system architecture to granular agent behaviors, internal prompts, and execution logic.

- **Ideal for Every Use Case**: Proven effective for both simple tasks and highly complex, real-world, enterprise-grade scenarios.

### ✅ Scalable Workers- **Robust Community**: Backed by a rapidly growing community of over **100,000 certified** developers offering comprehensive support and resources.



```bashCrewAI empowers developers and enterprises to confidently build intelligent automations, bridging the gap between simplicity, flexibility, and performance.

# Scale any agent to N instances

laddr scale researcher 5## Getting Started



# Or with docker composeSetup and run your first CrewAI agents by following this tutorial.

docker compose up --scale researcher_worker=5 -d

[![CrewAI Getting Started Tutorial](https://img.youtube.com/vi/-kSOTtYzgEw/hqdefault.jpg)](https://www.youtube.com/watch?v=-kSOTtYzgEw "CrewAI Getting Started Tutorial")

# Check status

laddr ps###

``` Learning Resources



### ✅ Complete ObservabilityLearn CrewAI through our comprehensive courses:



- **Traces**: Every task execution traced in Jaeger- [Multi AI Agent Systems with CrewAI](https://www.deeplearning.ai/short-courses/multi-ai-agent-systems-with-crewai/) - Master the fundamentals of multi-agent systems

- **Metrics**: Queue depth, latency, tokens, errors in Prometheus- [Practical Multi AI Agents and Advanced Use Cases](https://www.deeplearning.ai/short-courses/practical-multi-ai-agents-and-advanced-use-cases-with-crewai/) - Deep dive into advanced implementations

- **Logs**: Structured JSON logs per agent

- **Dashboard**: Real-time agent status and system health### Understanding Flows and Crews



### ✅ Flexible ConfigurationCrewAI offers two powerful, complementary approaches that work seamlessly together to build sophisticated AI applications:



Every component is configurable:1. **Crews**: Teams of AI agents with true autonomy and agency, working together to accomplish complex tasks through role-based collaboration. Crews enable:



```yaml   - Natural, autonomous decision-making between agents

# laddr.yml   - Dynamic task delegation and collaboration

name: my_project   - Specialized roles with defined goals and expertise

   - Flexible problem-solving approaches

llm:2. **Flows**: Production-ready, event-driven workflows that deliver precise control over complex automations. Flows provide:

  provider: ollama

  model: llama2   - Fine-grained control over execution paths for real-world scenarios

  temperature: 0.7   - Secure, consistent state management between tasks

   - Clean integration of AI agents with production Python code

database:   - Conditional branching for complex business logic

  provider: sqlite

  database: ./data/laddr.dbThe true power of CrewAI emerges when combining Crews and Flows. This synergy allows you to:



storage:- Build complex, production-grade applications

  provider: filesystem- Balance autonomy with precise control

  base_path: ./data/storage- Handle sophisticated real-world scenarios

- Maintain clean, maintainable code structure

queue:

  provider: redis### Getting Started with Installation

  url: redis://localhost:6379

```To get started with CrewAI, follow these simple steps:



---### 1. Installation



## 📚 DocumentationEnsure you have Python >=3.10 <3.14 installed on your system. CrewAI uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.



### Core ConceptsFirst, install CrewAI:



- **Agents**: Autonomous workers with specific roles and goals```shell

- **Tasks**: Units of work with dependencies and contextpip install crewai

- **Pipeline**: Workflow definition connecting tasks```

- **Message Bus**: Redis Streams for reliable communication

- **Workers**: Containerized agent executorsIf you want to install the 'crewai' package along with its optional features that include additional tools for agents, you can do so by using the following command:



### Configuration Files```shell

pip install 'crewai[tools]'

- `laddr.yml` - Project configuration```

- `agents/*.yml` - Individual agent configs

- `pipelines/*.yml` - Workflow definitionsThe command above installs the basic package and also adds extra components which require more dependencies to function.

- `docker-compose.yml` - Container orchestration

### Troubleshooting Dependencies

### CLI Commands

If you encounter issues during installation or usage, here are some common solutions:

```bash

laddr init <name>           # Create new project#### Common Issues

laddr add agent <name>      # Add new agent

laddr add tool <name>       # Add new tool1. **ModuleNotFoundError: No module named 'tiktoken'**

laddr run dev               # Start dev environment

laddr scale <agent> <N>     # Scale agent workers   - Install tiktoken explicitly: `pip install 'crewai[embeddings]'`

laddr ps                    # Show service status   - If using embedchain or other tools: `pip install 'crewai[tools]'`

laddr logs <agent>          # View agent logs2. **Failed building wheel for tiktoken**

laddr stop                  # Stop all services

laddr run job <pipeline>    # Submit job   - Ensure Rust compiler is installed (see installation steps above)

```   - For Windows: Verify Visual C++ Build Tools are installed

   - Try upgrading pip: `pip install --upgrade pip`

---   - If issues persist, use a pre-built wheel: `pip install tiktoken --prefer-binary`



## 🔧 Development### 2. Setting Up Your Crew with the YAML Configuration



### Project StructureTo create a new CrewAI project, run the following CLI (Command Line Interface) command:



``````shell

my_project/crewai create crew <project_name>

├── laddr.yml           # Project config```

├── agents/               # Agent definitions

│   ├── researcher.ymlThis command creates a new project folder with the following structure:

│   └── writer.yml

├── pipelines/            # Workflow definitions```

│   └── research.ymlmy_project/

├── tools/                # Custom tools├── .gitignore

├── docker-compose.yml    # Container orchestration├── pyproject.toml

└── data/                 # Local storage├── README.md

```├── .env

└── src/

### Adding Custom Tools    └── my_project/

        ├── __init__.py

```bash        ├── main.py

laddr add tool web_search        ├── crew.py

```        ├── tools/

        │   ├── custom_tool.py

Edit `tools/web_search.py`:        │   └── __init__.py

        └── config/

```python            ├── agents.yaml

from laddr.tools import Tool            └── tasks.yaml

```

class WebSearchTool(Tool):

    name = "web_search"You can now start developing your crew by editing the files in the `src/my_project` folder. The `main.py` file is the entry point of the project, the `crew.py` file is where you define your crew, the `agents.yaml` file is where you define your agents, and the `tasks.yaml` file is where you define your tasks.

    description = "Search the web for information"

    #### To customize your project, you can:

    def execute(self, query: str) -> dict:

        # Implementation- Modify `src/my_project/config/agents.yaml` to define your agents.

        return {"results": [...]}- Modify `src/my_project/config/tasks.yaml` to define your tasks.

```- Modify `src/my_project/crew.py` to add your own logic, tools, and specific arguments.

- Modify `src/my_project/main.py` to add custom inputs for your agents and tasks.

---- Add your environment variables into the `.env` file.



## 🚀 Production Deployment#### Example of a simple crew with a sequential process:



### Scaling StrategyInstantiate your crew:



1. **Horizontal Scaling**: Add more worker containers per agent```shell

2. **Load Balancing**: Redis consumer groups distribute load automaticallycrewai create crew latest-ai-development

3. **Resource Limits**: Configure CPU/memory limits in docker-compose.yml```

4. **Auto-scaling**: Use Kubernetes HPA or Docker Swarm for dynamic scaling

Modify the files as needed to fit your use case:

### Monitoring

**agents.yaml**

- **Jaeger**: http://localhost:16686 - Distributed tracing

- **Prometheus**: http://localhost:9090 - Metrics collection```yaml

- **Dashboard**: http://localhost:5173 - Real-time monitoring# src/my_project/config/agents.yaml

- **Grafana**: (Optional) Add for advanced dashboardsresearcher:

  role: >

---    {topic} Senior Data Researcher

  goal: >

## 🤝 Contributing    Uncover cutting-edge developments in {topic}

  backstory: >

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).    You're a seasoned researcher with a knack for uncovering the latest

    developments in {topic}. Known for your ability to find the most relevant

---    information and present it in a clear and concise manner.



## 📄 Licensereporting_analyst:

  role: >

MIT License - see [LICENSE](LICENSE) file for details.    {topic} Reporting Analyst

  goal: >

---    Create detailed reports based on {topic} data analysis and research findings

  backstory: >

## 🌟 Star History    You're a meticulous analyst with a keen eye for detail. You're known for

    your ability to turn complex data into clear and concise reports, making

Support the project by giving it a ⭐!    it easy for others to understand and act on the information you provide.

```

---

**tasks.yaml**

## 💬 Community

```yaml

- **GitHub Issues**: Bug reports and feature requests# src/my_project/config/tasks.yaml

- **GitHub Discussions**: Questions and community supportresearch_task:

- **Twitter**: [@Laddr](https://twitter.com/laddr) (coming soon)  description: >

    Conduct a thorough research about {topic}

---    Make sure you find any interesting and relevant information given

    the current year is 2025.

**Built with transparency. Shipped with observability. Ready for scale.** 🚀  expected_output: >

    A list with 10 bullet points of the most relevant information about {topic}
  agent: researcher

reporting_task:
  description: >
    Review the context you got and expand each topic into a full section for a report.
    Make sure the report is detailed and contains any and all relevant information.
  expected_output: >
    A fully fledge reports with the mains topics, each with a full section of information.
    Formatted as markdown without '```'
  agent: reporting_analyst
  output_file: report.md
```

**crew.py**

```python
# src/my_project/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class LatestAiDevelopmentCrew():
	"""LatestAiDevelopment crew"""
	agents: List[BaseAgent]
	tasks: List[Task]

	@agent
	def researcher(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher'],
			verbose=True,
			tools=[SerperDevTool()]
		)

	@agent
	def reporting_analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['reporting_analyst'],
			verbose=True
		)

	@task
	def research_task(self) -> Task:
		return Task(
			config=self.tasks_config['research_task'],
		)

	@task
	def reporting_task(self) -> Task:
		return Task(
			config=self.tasks_config['reporting_task'],
			output_file='report.md'
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the LatestAiDevelopment crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)
```

**main.py**

```python
#!/usr/bin/env python
# src/my_project/main.py
import sys
from latest_ai_development.crew import LatestAiDevelopmentCrew

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'AI Agents'
    }
    LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
```

### 3. Running Your fleet

Before running your crew, make sure you have the following keys set as environment variables in your `.env` file:

- An [OpenAI API key](https://platform.openai.com/account/api-keys) (or other LLM API key): `OPENAI_API_KEY=sk-...`
- A [Serper.dev](https://serper.dev/) API key: `SERPER_API_KEY=YOUR_KEY_HERE`

Lock the dependencies and install them by using the CLI command but first, navigate to your project directory:

```shell
cd my_project
crewai install (Optional)
```

To run your crew, execute the following command in the root of your project:

```bash
crewai run
```

or

```bash
python src/my_project/main.py
```

If an error happens due to the usage of poetry, please run the following command to update your crewai package:

```bash
crewai update
```

You should see the output in the console and the `report.md` file should be created in the root of your project with the full final report.

In addition to the sequential process, you can use the hierarchical process, which automatically assigns a manager to the defined crew to properly coordinate the planning and execution of tasks through delegation and validation of results. [See more about the processes here](https://docs.crewai.com/core-concepts/Processes/).

## Key Features

CrewAI stands apart as a lean, standalone, high-performance multi-AI Agent framework delivering simplicity, flexibility, and precise control—free from the complexity and limitations found in other agent frameworks.

- **Standalone & Lean**: Completely independent from other frameworks like LangChain, offering faster execution and lighter resource demands.
- **Flexible & Precise**: Easily orchestrate autonomous agents through intuitive [Crews](https://docs.crewai.com/concepts/crews) or precise [Flows](https://docs.crewai.com/concepts/flows), achieving perfect balance for your needs.
- **Seamless Integration**: Effortlessly combine Crews (autonomy) and Flows (precision) to create complex, real-world automations.
- **Deep Customization**: Tailor every aspect—from high-level workflows down to low-level internal prompts and agent behaviors.
- **Reliable Performance**: Consistent results across simple tasks and complex, enterprise-level automations.
- **Thriving Community**: Backed by robust documentation and over 100,000 certified developers, providing exceptional support and guidance.

Choose CrewAI to easily build powerful, adaptable, and production-ready AI automations.

## Examples

You can test different real life examples of AI crews in the [CrewAI-examples repo](https://github.com/crewAIInc/crewAI-examples?tab=readme-ov-file):

- [Landing Page Generator](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/landing_page_generator)
- [Having Human input on the execution](https://docs.crewai.com/how-to/Human-Input-on-Execution)
- [Trip Planner](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/trip_planner)
- [Stock Analysis](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/stock_analysis)

### Quick Tutorial

[![CrewAI Tutorial](https://img.youtube.com/vi/tnejrr-0a94/maxresdefault.jpg)](https://www.youtube.com/watch?v=tnejrr-0a94 "CrewAI Tutorial")

### Write Job Descriptions

[Check out code for this example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/job-posting) or watch a video below:

[![Jobs postings](https://img.youtube.com/vi/u98wEMz-9to/maxresdefault.jpg)](https://www.youtube.com/watch?v=u98wEMz-9to "Jobs postings")

### Trip Planner

[Check out code for this example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/trip_planner) or watch a video below:

[![Trip Planner](https://img.youtube.com/vi/xis7rWp-hjs/maxresdefault.jpg)](https://www.youtube.com/watch?v=xis7rWp-hjs "Trip Planner")

### Stock Analysis

[Check out code for this example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/stock_analysis) or watch a video below:

[![Stock Analysis](https://img.youtube.com/vi/e0Uj4yWdaAg/maxresdefault.jpg)](https://www.youtube.com/watch?v=e0Uj4yWdaAg "Stock Analysis")

### Using Crews and Flows Together

CrewAI's power truly shines when combining Crews with Flows to create sophisticated automation pipelines.
CrewAI flows support logical operators like `or_` and `and_` to combine multiple conditions. This can be used with `@start`, `@listen`, or `@router` decorators to create complex triggering conditions.

- `or_`: Triggers when any of the specified conditions are met.
- `and_`Triggers when all of the specified conditions are met.

Here's how you can orchestrate multiple Crews within a Flow:

```python
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai import Crew, Agent, Task, Process
from pydantic import BaseModel

# Define structured state for precise control
class MarketState(BaseModel):
    sentiment: str = "neutral"
    confidence: float = 0.0
    recommendations: list = []

class AdvancedAnalysisFlow(Flow[MarketState]):
    @start()
    def fetch_market_data(self):
        # Demonstrate low-level control with structured state
        self.state.sentiment = "analyzing"
        return {"sector": "tech", "timeframe": "1W"}  # These parameters match the task description template

    @listen(fetch_market_data)
    def analyze_with_crew(self, market_data):
        # Show crew agency through specialized roles
        analyst = Agent(
            role="Senior Market Analyst",
            goal="Conduct deep market analysis with expert insight",
            backstory="You're a veteran analyst known for identifying subtle market patterns"
        )
        researcher = Agent(
            role="Data Researcher",
            goal="Gather and validate supporting market data",
            backstory="You excel at finding and correlating multiple data sources"
        )

        analysis_task = Task(
            description="Analyze {sector} sector data for the past {timeframe}",
            expected_output="Detailed market analysis with confidence score",
            agent=analyst
        )
        research_task = Task(
            description="Find supporting data to validate the analysis",
            expected_output="Corroborating evidence and potential contradictions",
            agent=researcher
        )

        # Demonstrate crew autonomy
        analysis_crew = Crew(
            agents=[analyst, researcher],
            tasks=[analysis_task, research_task],
            process=Process.sequential,
            verbose=True
        )
        return analysis_crew.kickoff(inputs=market_data)  # Pass market_data as named inputs

    @router(analyze_with_crew)
    def determine_next_steps(self):
        # Show flow control with conditional routing
        if self.state.confidence > 0.8:
            return "high_confidence"
        elif self.state.confidence > 0.5:
            return "medium_confidence"
        return "low_confidence"

    @listen("high_confidence")
    def execute_strategy(self):
        # Demonstrate complex decision making
        strategy_crew = Crew(
            agents=[
                Agent(role="Strategy Expert",
                      goal="Develop optimal market strategy")
            ],
            tasks=[
                Task(description="Create detailed strategy based on analysis",
                     expected_output="Step-by-step action plan")
            ]
        )
        return strategy_crew.kickoff()

    @listen(or_("medium_confidence", "low_confidence"))
    def request_additional_analysis(self):
        self.state.recommendations.append("Gather more data")
        return "Additional analysis required"
```

This example demonstrates how to:

1. Use Python code for basic data operations
2. Create and execute Crews as steps in your workflow
3. Use Flow decorators to manage the sequence of operations
4. Implement conditional branching based on Crew results

## Connecting Your Crew to a Model

CrewAI supports using various LLMs through a variety of connection options. By default your agents will use the OpenAI API when querying the model. However, there are several other ways to allow your agents to connect to models. For example, you can configure your agents to use a local model via the Ollama tool.

Please refer to the [Connect CrewAI to LLMs](https://docs.crewai.com/how-to/LLM-Connections/) page for details on configuring your agents' connections to models.

## How CrewAI Compares

**CrewAI's Advantage**: CrewAI combines autonomous agent intelligence with precise workflow control through its unique Crews and Flows architecture. The framework excels at both high-level orchestration and low-level customization, enabling complex, production-grade systems with granular control.

- **LangGraph**: While LangGraph provides a foundation for building agent workflows, its approach requires significant boilerplate code and complex state management patterns. The framework's tight coupling with LangChain can limit flexibility when implementing custom agent behaviors or integrating with external systems.

*P.S. CrewAI demonstrates significant performance advantages over LangGraph, executing 5.76x faster in certain cases like this QA task example ([see comparison](https://github.com/crewAIInc/crewAI-examples/tree/main/Notebooks/CrewAI%20Flows%20%26%20Langgraph/QA%20Agent)) while achieving higher evaluation scores with faster completion times in certain coding tasks, like in this example ([detailed analysis](https://github.com/crewAIInc/crewAI-examples/blob/main/Notebooks/CrewAI%20Flows%20%26%20Langgraph/Coding%20Assistant/coding_assistant_eval.ipynb)).*

- **Autogen**: While Autogen excels at creating conversational agents capable of working together, it lacks an inherent concept of process. In Autogen, orchestrating agents' interactions requires additional programming, which can become complex and cumbersome as the scale of tasks grows.
- **ChatDev**: ChatDev introduced the idea of processes into the realm of AI agents, but its implementation is quite rigid. Customizations in ChatDev are limited and not geared towards production environments, which can hinder scalability and flexibility in real-world applications.

## Contribution

CrewAI is open-source and we welcome contributions. If you're looking to contribute, please:

- Fork the repository.
- Create a new branch for your feature.
- Add your feature or improvement.
- Send a pull request.
- We appreciate your input!

### Installing Dependencies

```bash
uv lock
uv sync
```

### Virtual Env

```bash
uv venv
```

### Pre-commit hooks

```bash
pre-commit install
```

### Running Tests

```bash
uv run pytest .
```

### Running static type checks

```bash
uvx mypy src
```

### Packaging

```bash
uv build
```

### Installing Locally

```bash
pip install dist/*.tar.gz
```

## Telemetry

CrewAI uses anonymous telemetry to collect usage data with the main purpose of helping us improve the library by focusing our efforts on the most used features, integrations and tools.

It's pivotal to understand that **NO data is collected** concerning prompts, task descriptions, agents' backstories or goals, usage of tools, API calls, responses, any data processed by the agents, or secrets and environment variables, with the exception of the conditions mentioned. When the `share_crew` feature is enabled, detailed data including task descriptions, agents' backstories or goals, and other specific attributes are collected to provide deeper insights while respecting user privacy. Users can disable telemetry by setting the environment variable OTEL_SDK_DISABLED to true.

Data collected includes:

- Version of CrewAI
  - So we can understand how many users are using the latest version
- Version of Python
  - So we can decide on what versions to better support
- General OS (e.g. number of CPUs, macOS/Windows/Linux)
  - So we know what OS we should focus on and if we could build specific OS related features
- Number of agents and tasks in a crew
  - So we make sure we are testing internally with similar use cases and educate people on the best practices
- Crew Process being used
  - Understand where we should focus our efforts
- If Agents are using memory or allowing delegation
  - Understand if we improved the features or maybe even drop them
- If Tasks are being executed in parallel or sequentially
  - Understand if we should focus more on parallel execution
- Language model being used
  - Improved support on most used languages
- Roles of agents in a crew
  - Understand high level use cases so we can build better tools, integrations and examples about it
- Tools names available
  - Understand out of the publicly available tools, which ones are being used the most so we can improve them

Users can opt-in to Further Telemetry, sharing the complete telemetry data by setting the `share_crew` attribute to `True` on their Crews. Enabling `share_crew` results in the collection of detailed crew and task execution data, including `goal`, `backstory`, `context`, and `output` of tasks. This enables a deeper insight into usage patterns while respecting the user's choice to share.

## License

CrewAI is released under the [MIT License](https://github.com/crewAIInc/crewAI/blob/main/LICENSE).

## Frequently Asked Questions (FAQ)

### General

- [What exactly is CrewAI?](#q-what-exactly-is-crewai)
- [How do I install CrewAI?](#q-how-do-i-install-crewai)
- [Does CrewAI depend on LangChain?](#q-does-crewai-depend-on-langchain)
- [Is CrewAI open-source?](#q-is-crewai-open-source)
- [Does CrewAI collect data from users?](#q-does-crewai-collect-data-from-users)

### Features and Capabilities

- [Can CrewAI handle complex use cases?](#q-can-crewai-handle-complex-use-cases)
- [Can I use CrewAI with local AI models?](#q-can-i-use-crewai-with-local-ai-models)
- [What makes Crews different from Flows?](#q-what-makes-crews-different-from-flows)
- [How is CrewAI better than LangChain?](#q-how-is-crewai-better-than-langchain)
- [Does CrewAI support fine-tuning or training custom models?](#q-does-crewai-support-fine-tuning-or-training-custom-models)

### Resources and Community

- [Where can I find real-world CrewAI examples?](#q-where-can-i-find-real-world-crewai-examples)
- [How can I contribute to CrewAI?](#q-how-can-i-contribute-to-crewai)

### Enterprise Features

- [What additional features does CrewAI AMP offer?](#q-what-additional-features-does-crewai-amp-offer)
- [Is CrewAI AMP available for cloud and on-premise deployments?](#q-is-crewai-amp-available-for-cloud-and-on-premise-deployments)
- [Can I try CrewAI AMP for free?](#q-can-i-try-crewai-amp-for-free)

### Q: What exactly is CrewAI?

A: CrewAI is a standalone, lean, and fast Python framework built specifically for orchestrating autonomous AI agents. Unlike frameworks like LangChain, CrewAI does not rely on external dependencies, making it leaner, faster, and simpler.

### Q: How do I install CrewAI?

A: Install CrewAI using pip:

```shell
pip install crewai
```

For additional tools, use:

```shell
pip install 'crewai[tools]'
```

### Q: Does CrewAI depend on LangChain?

A: No. CrewAI is built entirely from the ground up, with no dependencies on LangChain or other agent frameworks. This ensures a lean, fast, and flexible experience.

### Q: Can CrewAI handle complex use cases?

A: Yes. CrewAI excels at both simple and highly complex real-world scenarios, offering deep customization options at both high and low levels, from internal prompts to sophisticated workflow orchestration.

### Q: Can I use CrewAI with local AI models?

A: Absolutely! CrewAI supports various language models, including local ones. Tools like Ollama and LM Studio allow seamless integration. Check the [LLM Connections documentation](https://docs.crewai.com/how-to/LLM-Connections/) for more details.

### Q: What makes Crews different from Flows?

A: Crews provide autonomous agent collaboration, ideal for tasks requiring flexible decision-making and dynamic interaction. Flows offer precise, event-driven control, ideal for managing detailed execution paths and secure state management. You can seamlessly combine both for maximum effectiveness.

### Q: How is CrewAI better than LangChain?

A: CrewAI provides simpler, more intuitive APIs, faster execution speeds, more reliable and consistent results, robust documentation, and an active community—addressing common criticisms and limitations associated with LangChain.

### Q: Is CrewAI open-source?

A: Yes, CrewAI is open-source and actively encourages community contributions and collaboration.

### Q: Does CrewAI collect data from users?

A: CrewAI collects anonymous telemetry data strictly for improvement purposes. Sensitive data such as prompts, tasks, or API responses are never collected unless explicitly enabled by the user.

### Q: Where can I find real-world CrewAI examples?

A: Check out practical examples in the [CrewAI-examples repository](https://github.com/crewAIInc/crewAI-examples), covering use cases like trip planners, stock analysis, and job postings.

### Q: How can I contribute to CrewAI?

A: Contributions are warmly welcomed! Fork the repository, create your branch, implement your changes, and submit a pull request. See the Contribution section of the README for detailed guidelines.

### Q: What additional features does CrewAI AMP offer?

A: CrewAI AMP provides advanced features such as a unified control plane, real-time observability, secure integrations, advanced security, actionable insights, and dedicated 24/7 enterprise support.

### Q: Is CrewAI AMP available for cloud and on-premise deployments?

A: Yes, CrewAI AMP supports both cloud-based and on-premise deployment options, allowing enterprises to meet their specific security and compliance requirements.

### Q: Can I try CrewAI AMP for free?

A: Yes, you can explore part of the CrewAI AMP Suite by accessing the [Crew Control Plane](https://app.crewai.com) for free.

### Q: Does CrewAI support fine-tuning or training custom models?

A: Yes, CrewAI can integrate with custom-trained or fine-tuned models, allowing you to enhance your agents with domain-specific knowledge and accuracy.

### Q: Can CrewAI agents interact with external tools and APIs?

A: Absolutely! CrewAI agents can easily integrate with external tools, APIs, and databases, empowering them to leverage real-world data and resources.

### Q: Is CrewAI suitable for production environments?

A: Yes, CrewAI is explicitly designed with production-grade standards, ensuring reliability, stability, and scalability for enterprise deployments.

### Q: How scalable is CrewAI?

A: CrewAI is highly scalable, supporting simple automations and large-scale enterprise workflows involving numerous agents and complex tasks simultaneously.

### Q: Does CrewAI offer debugging and monitoring tools?

A: Yes, CrewAI AMP includes advanced debugging, tracing, and real-time observability features, simplifying the management and troubleshooting of your automations.

### Q: What programming languages does CrewAI support?

A: CrewAI is primarily Python-based but easily integrates with services and APIs written in any programming language through its flexible API integration capabilities.

### Q: Does CrewAI offer educational resources for beginners?

A: Yes, CrewAI provides extensive beginner-friendly tutorials, courses, and documentation through learn.crewai.com, supporting developers at all skill levels.

### Q: Can CrewAI automate human-in-the-loop workflows?

A: Yes, CrewAI fully supports human-in-the-loop workflows, allowing seamless collaboration between human experts and AI agents for enhanced decision-making.
