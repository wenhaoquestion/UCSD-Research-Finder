"""A stable lock inode prevents concurrent writers of one collection queue."""
import fcntl


def task_lease(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open('a+')
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        stream.close()
        raise RuntimeError('Another active process owns ' + str(path)) from None
    return stream
