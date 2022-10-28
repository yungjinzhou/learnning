from functools import wraps


def task_time_consuming(task_type):
    def func_wrapper(func):
        @wraps(func)
        def inner_wrapper(self, *args, **kwargs):
            ret = func(self, *args, **kwargs)
            return ret
        return inner_wrapper
    return func_wrapper
