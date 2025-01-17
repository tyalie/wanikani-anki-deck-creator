def has_user_subscription(user_info: dict) -> bool:
    """get current subscription status
        - please don't edit this and change your subscription
    """
    return user_info["data"]["subscription"]["active"]

