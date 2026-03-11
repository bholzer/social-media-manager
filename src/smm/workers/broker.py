import dramatiq
from dramatiq.brokers.redis import RedisBroker

from smm.config import settings

redis_broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(redis_broker)
