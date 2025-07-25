from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .forms import UserProfileForm
from checkout.models import Order


@login_required
def profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile Updated Successfully")
        else:
            messages.error(request, "Something went wrong!")
    else:
        form = UserProfileForm(instance=profile)
    orders = profile.orders.all()

    template = "profiles/profile.html"
    context = {
        "form": form,
        "orders": orders,
        "on_profile_page": True,
    }

    return render(request, template, context)


@login_required
def order_history(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    messages.info(
        request, (f"This is past order confirmation for order: {order_number}")
    )

    template = "checkout/checkout_success.html"
    context = {"order": order, "from_profile": True}

    return render(request, template, context)
