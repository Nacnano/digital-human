import json
import os
from datetime import datetime

import hydra
from dotenv import load_dotenv
from hydra.utils import instantiate
from loguru import logger
from omegaconf import DictConfig

from module.llm import LLM
from module.stt import STT
from module.tts import TTS
from utils import build_prompt

load_dotenv()

log_dir = f"logs/log_{datetime.now():%Y-%m-%d_%H-%M-%S}"
os.makedirs(log_dir, exist_ok=True)
log_filename = f"{log_dir}/log.log"

logger.add(log_filename, level="DEBUG")


@hydra.main(config_path="config", config_name="main", version_base=None)
def main(cfg: DictConfig):
    logger.info("Baseline assessment")

    stt_service: STT = instantiate(cfg.stt)
    tts_service: TTS = instantiate(cfg.tts)
    llm_service: LLM = instantiate(cfg.llm)

    logger.debug("System Prompt:")
    logger.debug(llm_service.system_prompt)

    with open(cfg.pose_file_path, "r") as f:
        pose_data = json.load(f)

    stt_text = stt_service.transcribe(cfg.audio_file_path)

    prompt = build_prompt(stt_text, pose_data)

    logger.debug("Prompt:")
    logger.debug(prompt)

    llm_text = llm_service.generate_text(prompt)

    logger.debug("LLM Text:")
    logger.debug(llm_text)

    audio = tts_service.generate(llm_text)
    with open(os.path.join(log_dir, "response.mp3"), "wb") as f:
        f.write(b"".join(audio))


if __name__ == "__main__":
    main()
