from mywash_admin import api
from controllers import *

api.add_resource(
    analytics.OrderAnalytics,
    '/analytics/order/<regex("\d{4}-\d{2}-\d{2}"):from_date>/<regex("\d{4}-\d{2}-\d{2}"):to_date>',
    '/analytics/order/<regex("\d{4}-\d{2}-\d{2}"):from_date>'
)

api.add_resource(
    analytics.UserAnalytics,
    '/analytics/user/<regex("\d{4}-\d{2}-\d{2}"):from_date>/<regex("\d{4}-\d{2}-\d{2}"):to_date>',
    '/analytics/user/<regex("\d{4}-\d{2}-\d{2}"):from_date>'
)

api.add_resource(
    analytics.OperationAnalytics,
    '/analytics/operations/<regex("\d{4}-\d{2}-\d{2}"):date>',
    '/analytics/operations'
)

api.add_resource(
    analytics.CohertAnalytics,
    '/analytics/cohert/<string:argument>'
)

api.add_resource(
    reports.DummyreyReport,
    '/report/dummyrey'
)

api.add_resource(
    reports.AuditReport,
    '/report/audit/<regex("\d{4}-\d{2}-\d{2}"):date>/<string:order_type>'
)


api.add_resource(
    reports.MarketingReport,
    '/report/marketing/<string:report_type>/<regex("\d{4}-\d{2}-\d{2}"):start_date>/<regex("\d{4}-\d{2}-\d{2}"):end_date>',
    # '/report/marketing/<string:report_type>'
)
