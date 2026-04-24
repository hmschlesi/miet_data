import json
from models_ber_merkmale import MietspiegelEvaluation

# Generate the JSON Schema
schema = MietspiegelEvaluation.model_json_schema()

# Print it as a formatted string to copy-paste
print(json.dumps(schema, indent=2))