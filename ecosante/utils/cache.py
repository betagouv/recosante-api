from contextlib import contextmanager
import time
from ecosante.extensions import cache

@contextmanager
def cache_lock(lock_id, oid):
    LOCK_EXPIRE = 60 * 60
    timeout_at = time.monotonic() + LOCK_EXPIRE - 180
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            cache.delete(lock_id)

def cache_unlock(lock_id):
    cache.delete(lock_id)
