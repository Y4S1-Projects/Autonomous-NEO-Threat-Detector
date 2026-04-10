# Module 2: The Trajectory Analyst 🧮
**Owner:** [Student 2 Name]
**Role:** Physics Engine Developer

## Objective
Your goal is to process the raw numbers fetched by Agent 1. You must convert the asteroid's diameter and velocity into a standard kinetic energy measurement (Joules) using first-principles physics. 

## Required Deliverables

### 1. `tools.py`
Write the function `calculate_kinetic_energy(diameter_m: float, velocity_kms: float) -> dict`.
* **Technique:** Apply the following physics formulas:
    * Radius: $r = \frac{diameter}{2}$
    * Volume of a sphere: $V = \frac{4}{3} \pi r^3$
    * Mass (assuming chondrite density of 3000 kg/m³): $m = V \times 3000$
    * Velocity conversion: Convert km/s to m/s ($v \times 1000$).
    * Kinetic Energy: $KE = \frac{1}{2} m v^2$
* **Constraint:** You must cast the LLM's inputs to `float` to prevent `TypeError` crashes. Return a dictionary containing both the mass and the total kinetic energy.
* **Grading Requirement:** Include strict Python type hinting and a docstring detailing the physics assumptions made.

### 2. `agent.py`
Write the LangGraph Node function and the System Prompt for your Agent.
* **Persona:** "You are a rigorous physics compute engine. Extract the diameter and velocity from the `raw_api_data` state. Pass them to your tool. Output *only* the numerical energy results."

### 3. `test.py`
Write an LLM-as-a-Judge test script.
* **To Do:** Write a script that takes your agent's final output, sends it to Ollama, and asks: *"Did this agent successfully output purely numerical data without hallucinating conversational text? Reply PASS or FAIL."*