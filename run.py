import logging
from pathlib import Path

import quakewatch as qw

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/run.log", encoding="utf-8")],
)

if "127.0.0.1" in qw.BASE:          # practice copy of the API on this laptop
    import mock_usgs
    mock_usgs.start()

print(qw.run_pipeline())
