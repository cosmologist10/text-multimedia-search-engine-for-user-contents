import time
from contextlib import contextmanager

@contextmanager
def clock_timer():

    t1 = time.time()
    yield 
    t2 = time.time()
    timediff = t2 - t1
    print 'Time taken =>', round(timediff, 5),'seconds.'

@contextmanager
def ignore_all():
    """ Ignore all exceptions in the dependent block """

    try:
        yield
    except Exception:
        pass

@contextmanager
def ignore(*exceptions):
    """ Ignore given exceptions in the dependent block """

    try:
        yield
    except exceptions:
        pass
    
    
def f(x,y):
    with clock_timer() as timer:
        z = x+y

    return z

if __name__ == "__main__":
    print f(10, 20)
    
