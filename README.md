Cogito x Infor – AI-Powered Test Automation Agents (Spring 2025)

https://github.com/user-attachments/assets/129f85b6-8a73-432b-b68b-2cc75d0b368a

<div align="center">


</div>



⸻


<details> 
<summary><b>📋 Table of contents </b></summary>


	•	Description
	•	Key Features
	•	Architecture
	•	Getting Started
	•	Prerequisites
	•	Configuration
	•	Usage
	•	Testing
	•	Team
	•	License

</details>



⸻

Description

This project was built in collaboration with Infor, the world’s third-largest ERP provider, to solve a real-world bottleneck:
💡 The company spends tens of thousands of hours every year on manual software testing. Testers read PDFs with step-by-step instructions and then manually click through the ERP system’s UI.

We created an AI-driven solution that automates both test creation and test execution by combining:
	•	Browser-Use (agent framework)
	•	GPT-4o (multimodal reasoning on screenshots & HTML)
	•	Playwright (E2E test automation)
	•	Next.js (intuitive frontend)

👉 The result: Deterministic Playwright test scripts automatically generated from an AI agent’s navigation, with full traceability through screenshots. This makes tests fast, repeatable, and scalable – without writing a single line of code.

⸻

Key Features
	•	⚡ Massive time savings – reduces thousands of hours of manual testing every year.
	•	🖱️ No-code test generation – users create end-to-end tests without programming knowledge.
	•	🤖 AI-powered navigation – GPT-4o agents explore web UIs using screenshots and HTML.
	•	📜 Deterministic Playwright scripts – reproducible and reliable automation output.
	•	🎨 User-friendly frontend – request tests, view screenshots of each action, and export working scripts.

⸻

Architecture

flowchart LR
    subgraph User
    A[Test Request] --> B[Next.js Frontend]
    end
    
    subgraph Backend
    B --> C[Browser-Use Agent (GPT-4o)]
    C --> D[Web Application under Test]
    C --> E[Generate Playwright Scripts]
    end

    E --> F[Next.js Frontend]
    F --> G[User Downloads Ready-to-Run Tests]


⸻

Getting Started

Prerequisites
	•	Python 3.9+
	•	Node.js (for Next.js frontend)
	•	Git
	•	Playwright

Make sure Git is installed.

⸻

Configuration
	1.	Create and activate a virtual environment:

Mac/Linux:

python -m venv venv
source venv/bin/activate

Windows:

python -m venv venv
venv\Scripts\activate

	2.	Install dependencies:

pip install -r requirements.txt
pip install browser-use
playwright install

	3.	Create a .env file in the root directory:

OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""
DEEPSEEK_API_KEY=""
ANONYMIZED_TELEMETRY=true
BROWSER_USE_LOGGING_LEVEL=info


⸻

Usage

Run the project from the root directory:

python3 main.py


⸻

Testing

To run the test suite:

pytest


⸻

Team

This project was developed by the Cogito x Infor Spring 2025 team.

<table align="center">
    <tr>
        <!-- Example format for team members -->
        <td align="center">
            <a href="https://github.com/NAME_OF_MEMBER">
              <img src="https://github.com/NAME_OF_MEMBER.png?size=100" width="100px;" alt="NAME OF MEMBER"/><br />
              <sub><b>NAME OF MEMBER</b></sub>
            </a>
        </td>
    </tr>
</table>



⸻

License

Distributed under the MIT License. See LICENSE for more information.

⸻

✨ With this project, we’ve taken manual, repetitive testing and transformed it into an AI-driven, no-code workflow – saving time, scaling efficiency, and enabling faster innovation.

⸻

Would you like me to also make a shorter, more business-facing README summary (like a pitch for non-technical visitors on GitHub) in addition to this detailed developer README?
