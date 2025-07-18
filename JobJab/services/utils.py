SUBSCRIPTION_SERVICE_LIMITS = {
    'Starter': 3,
    'Growth': 10,
    'Elite': 9999
}

def get_service_limit_for_plan(plan):
    return SUBSCRIPTION_SERVICE_LIMITS.get(plan, 0)