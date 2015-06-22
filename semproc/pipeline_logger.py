import logging
from datetime import datetime


logger = logging.getLogger(__name__)
handler = logging.FileHandler(
    filename="logs/pipeline_%s.log" % datetime.now().strftime('%Y%m%d-%H%M'),
    mode="a",
    encoding="UTF-8"
)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
