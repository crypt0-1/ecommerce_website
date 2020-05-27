from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404
from .models import Item, OrderItem, Order, BillingAddress
from django.shortcuts import redirect
from django.utils import timezone
from .forms import CheckoutForm
from django.views.generic import ListView, DetailView, View
# Create your views here.

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token
stripe.Charge.create(
    amount=2000,
    currency="usd",
    source="tok_amex",
    description="My First Test Charge (created for API docs)",
)


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home-page.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(request, "you dont have any order")
            return redirect("/")


class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form': form
        }
        return render(self.request, "checkout-page.html", context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # same_shipping_address = form.cleaned_data.get(
                #     'same_shipping_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                BillingAddress = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip,
                )
                billing_address.save()
                orderbilling_address = billing_address
                order.save()
                # todo:add redirect patyment option
                return redirect('core:checkout')
            messages.warning(self.request, "Failed checkout")
            return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.error(request, "you dont have any order")
            return redirect("core:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        return render(self.request, "payment.html")

    def post(self, *args, **kwargs):
        order = Order.object.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        stripe.Charge.create(
            amount=order.get_total() * 100,
            currency="usd",
            source=token,
            description="My First Test Charge (created for API docs)",
        )
        order.ordered = True


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(

        item=item,
        user=request.user,
        ordered=False,


    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "this item quantity was updated")
            return redirect("core:order-summary")
        else:

            order.items.add(order_item)
            messages.info(request, "this item was added to your cart")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "this item was added to your cart")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # checks order  item is in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(

                item=item,
                user=request.user,
                ordered=False,
            )[0]
            order.items.remove(order_item)
            messages.info(request, "this item was removed from your cart")
            return redirect("core:order-summary")

        else:
            # add a message saying user doesnt have a order
            messages.info(request, "this item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        # add a message saying user doesnt have a order
        messages.info(request, "no activate order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # checks order  item is in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(

                item=item,
                user=request.user,
                ordered=False,
            )[0]
            if order_item.quantity > 1:

                order_item.quantity -= 1
                order_item.save()
            else:

                order.items.remove(order_item)

            messages.info(request, "this item quantity was updated")
            return redirect("core:order-summary")
        else:
            # add a message saying user doesnt have a order
            messages.info(request, "this item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        # add a message saying user doesnt have a order
        messages.info(request, "no activate order")
        return redirect("core:product", slug=slug)
