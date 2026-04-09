from src.generation.generator import AssignmentGenerator

prompt = """
Create a realistic take-home assignment for a frontend engineering intern role.
The assignment should focus on React, TypeScript, and UI implementation.
Include title, task description, deliverables, evaluation criteria, and time estimate.
"""

generator = AssignmentGenerator()
result = generator.generate(prompt=prompt)

print("MODEL:", result.model)
print()
print(result.content)