from django.shortcuts import render, redirect, reverse, HttpResponse, get_object_or_404
from django.contrib import messages
from products.models import Product

# Create your views here.


def view_bag(request):
    """Return shopping bag main page"""
    return render(request, "bag/bag.html")


def add_to_bag(request, item_id):
    """Add a quantity of item to the bag"""

    product = get_object_or_404(Product, pk=item_id)
    quantity = int(request.POST.get("quantity"))
    redirect_url = request.POST.get("redirect_url")
    size = None

    if "product_size" in request.POST:
        size = request.POST["product_size"]

    bag = request.session.get("bag", {})

    if size:
        if item_id in list(bag.keys()):
            if size in bag[item_id]["items_by_size"].keys():
                bag[item_id]["items_by_size"][size] += quantity
                messages.success(
                    request,
                    f'Updated size {size.upper()} \
                    {product.name} quantity to \
                    {bag[item_id]["items_by_size"][size]}',
                )
            else:
                bag[item_id]["items_by_size"][size] = quantity
                messages.success(
                    request,
                    f"Added {quantity} size {size.upper()} {product.name} to bag",
                )
        else:
            bag[item_id] = {"items_by_size": {size: quantity}}
            messages.success(
                request,
                f"Added {quantity} size {size.upper()} {product.name} to your bag",
            )
    else:
        if item_id in list(bag.keys()):
            bag[item_id] += quantity
            messages.success(request, f"Updated {product.name} quantity {bag[item_id]}")
        else:
            bag[item_id] = quantity
            messages.success(request, f"Added {quantity} {product.name} to your bag")

    request.session["bag"] = bag
    return redirect(redirect_url)


def adjust_bag(request, item_id):
    """Adjusts the bag quantities safely"""

    product = get_object_or_404(Product, pk=item_id)
    quantity = int(request.POST.get("quantity"))
    size = None

    if "product_size" in request.POST:
        size = request.POST["product_size"]

    bag = request.session.get("bag", {})

    if size:
        if item_id in bag:
            if quantity > 0:
                bag[item_id]["items_by_size"][size] = quantity
                messages.success(
                    request,
                    f'Updated size {size.upper()} \
                    {product.name} quantity to \
                    {bag[item_id]["items_by_size"][size]}',
                )
            else:
                if size in bag[item_id]["items_by_size"]:
                    del bag[item_id]["items_by_size"][size]
                    if not bag[item_id]["items_by_size"]:
                        bag.pop(item_id)
                        messages.success(
                            request,
                            f"Removed size {size.upper()} {product.name} from your bag",
                        )
        else:
            messages.error(request, "Item not found in your bag.")
    else:
        if item_id in bag:
            if quantity > 0:
                bag[item_id] = quantity
                messages.success(
                    request, f"Updated {product.name} quantity {bag[item_id]}"
                )
            else:
                bag.pop(item_id)
                messages.success(request, f"Removed {product.name} from your bag")
        else:
            messages.error(request, "Item not found in your bag.")

    request.session["bag"] = bag
    return redirect(reverse("view_bag"))


def remove_from_bag(request, item_id):
    """Removes items from the bag on the shopping bag page"""
    product = get_object_or_404(Product, pk=item_id)
    try:
        size = None

        if "product_size" in request.POST:
            size = request.POST["product_size"]

        bag = request.session.get("bag", {})

        if size:
            if size in bag[item_id]["items_by_size"]:
                del bag[item_id]["items_by_size"][size]
                messages.success(
                    request, f"Removed size {size.upper()} {product.name} from your bag"
                )

                if not bag[item_id]["items_by_size"]:
                    bag.pop(item_id)
        else:
            bag.pop(item_id)
            messages.success(request, f"Removed {product.name} from your bag")

        request.session["bag"] = bag
        return HttpResponse(status=200)

    except Exception as e:
        messages.error(request, f"Error removing item {e}")
        return HttpResponse(status=500)
