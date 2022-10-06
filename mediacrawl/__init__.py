import logging
import warnings
from pytz_deprecation_shim import PytzUsageWarning

warnings.simplefilter("ignore", category=PytzUsageWarning)
logging.getLogger("trafilatura").setLevel(logging.WARNING)
