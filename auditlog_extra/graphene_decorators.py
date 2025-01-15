import logging
from functools import wraps

from auditlog.signals import accessed

logger = logging.getLogger(__name__)


def auditlog_access(cls):
    """
    Decorator to add audit logging to a Graphene DjangoObjectType's get_node method.

    Uses the `accessed` signal to log the access of the node.
    """
    old_get_node = cls.get_node

    @classmethod
    @wraps(old_get_node)
    def wrapper(cls, info, id):
        node = old_get_node(info, id)
        try:
            if node:
                sender = getattr(cls, "_meta", getattr(cls, "Meta", None)).model
                if sender:
                    accessed.send(sender=sender, instance=node, actor=info.context.user)
        except Exception as e:
            logger.exception(f"Could not write access log for node {node}: {e}")
        return node

    cls.get_node = wrapper
    return cls
