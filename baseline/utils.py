import json
from typing import Dict, List


def build_prompt(transcript: str, pose_data: List[Dict[str, str]]) -> str:
    json_data_str = "\n".join([json.dumps(data, indent=2) for data in pose_data])
    return f"""
## Transcript
{transcript}

## Pose Data
{json_data_str}
"""
