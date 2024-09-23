from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from .models import TextFile, Credit

def check_credits_and_ownership(textfile_id_param, credits_required):
    """
    A decorator to check if a user has enough credits and if they own the TextFile.

    :param textfile_id_param: The name of the parameter in the view's kwargs that holds the TextFile ID.
    :param credits_required: The amount of credits required to access the view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Extract the textfile_id from kwargs
            textfile_id = kwargs.get(textfile_id_param)
            textfile = get_object_or_404(TextFile, id=textfile_id)

            # Check if the logged-in user is the owner of the TextFile
            if textfile.user != request.user:
                raise PermissionDenied("You do not have permission to access this file.")

            # Check if the user has an associated Credit object
            try:
                user_credit = request.user.credit
            except Credit.DoesNotExist:
                return redirect(reverse('accounts:embedded_pricing_page'))  # Redirect to pricing if no credit exists

            # Reset credits if necessary (monthly reset)
            user_credit.reset_credits(monthly_credits=10)  # Example monthly credit limit

            # Check if the user has enough credits
            if not user_credit.deduct_credits(credits_required):
                return redirect(reverse('accounts:embedded_pricing_page'))  # Redirect to pricing if not enough credits

            # If checks pass, call the original view
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
