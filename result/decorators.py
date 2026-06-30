from functools import wraps
from django.shortcuts import redirect

def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'teacher'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
        
    