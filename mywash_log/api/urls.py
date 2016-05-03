from mywash_log import api
from controllers import log

api.add_resource(
    log.Logger,
    "/log"
)
