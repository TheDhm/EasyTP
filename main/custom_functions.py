from threading import Thread


def autotask(func):
    def decor(*args, **kwargs):
        t = Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return decor

