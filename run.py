import logging

import quakewatch as qw

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

if "127.0.0.1" in qw.BASE:          # practice copy of the API on this laptop
    import mock_usgs
    mock_usgs.start()

print(qw.run_pipeline())
