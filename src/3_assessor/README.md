# Module 3: The Semantic RAG Assessor 🧠
**Owner:** [Student 3 Name]
**Role:** AI Backend Engineer

## Objective
Your goal is to provide the system with historical "memory". Instead of hardcoding IF/ELSE statements, you will use a local Vector Database (ChromaDB) to perform a semantic similarity search, finding the closest historical asteroid impact that matches the current asteroid's energy.

## Required Deliverables

### 1. `tools.py`
Write the function `query_vector_memory(energy_joules: float) -> str`.
* **Technique:** Initialize a local `chromadb` client pointing to `data/vector_db/`. You must first write a tiny helper script to populate this database with 3-4 paragraphs of historical impacts (e.g., Tunguska, Chicxulub).
* **Logic:** Your tool will convert the `energy_joules` into a descriptive search string (e.g., "Asteroid impact with massive energy..."), query the vector database, and return the most relevant historical paragraph.
* **Grading Requirement:** Include strict Python type hinting and a docstring explaining the RAG (Retrieval-Augmented Generation) mechanism.

### 2. `agent.py`
Write the LangGraph Node function and the System Prompt for your Agent.
* **Persona:** "You are a planetary defense threat assessor. Take the kinetic energy from the `physics_results`. Use your tool to retrieve historical context. Based on that context, classify the threat as LOW, MODERATE, or HIGH. Update the state with both the context and the classification."

### 3. `test.py`
Write a Property-Based Test using Python's `unittest`.
* **To Do:** Write a script that passes a massive fake energy number into your tool and asserts that the returned string is not empty and successfully queried the database without crashing.