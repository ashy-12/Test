from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'Admin'
    if hasattr(user, 'profile'):
        return user.profile.role
    return 'Admin' if user.is_staff else 'Student'


def get_dashboard_url_for_user(user):
    role = get_user_role(user)
    if role == 'Teacher':
        return reverse('teacher_dashboard')
    elif role == 'Student':
        return reverse('student_dashboard')
    else:
        return reverse('student_list')


def role_required(allowed_roles):
    """
    Decorator to restrict view access to specific roles.
    allowed_roles: list of roles, e.g. ['Admin'], ['Teacher'], ['Admin', 'Teacher']
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to access this page.')
                return redirect(f"{reverse('login')}?next={request.path}")

            user_role = get_user_role(request.user)

            # Superusers always have full access
            if request.user.is_superuser or user_role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, f'Access denied: {user_role}s cannot access this page.')
            return redirect(get_dashboard_url_for_user(request.user))

        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required(['Admin'])(view_func)


def teacher_required(view_func):
    return role_required(['Admin', 'Teacher'])(view_func)


def student_required(view_func):
    return role_required(['Admin', 'Student'])(view_func)
