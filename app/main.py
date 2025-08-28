from nlp_treatment.extraction import extract_to_dict
import json

data = extract_to_dict()
print(json.dumps(data, ensure_ascii=False, indent=2))