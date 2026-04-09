from src.extraction.llm_job_parser import parse_job_ad_with_llm

job_text = """
Frontend Engineer Intern

We are looking for a Frontend Engineer Intern to join our team.
You will work with React, TypeScript, and modern web technologies.
Experience with APIs and UI development is a plus.
"""

result = parse_job_ad_with_llm(job_text)

print(result)
print()
print(result.to_dict())