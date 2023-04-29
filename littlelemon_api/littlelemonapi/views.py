from . import models
from . import serializers
from decimal import Decimal
import datetime
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.decorators import throttle_classes
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator, EmptyPage

@api_view()
def home(request):
    return Response('The home page.', status.HTTP_200_OK)

@api_view()
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def throttle_check(request):
    return Response({"message": "Throttle check message."})

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAdminUser])
def manager_admin(request):
    username = request.data['username']
    message = 'User ' + username + ' '
    if username:
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name="Manager")
        if request.method == 'POST':
            managers.user_set.add(user)
            message += 'is set as Manager role.'
        elif request.method == 'DELETE':
            managers.user_set.remove(user)
            message += 'is deleted from Manager group.'
        elif request.method == 'GET':
            serialized_item = serializers.UserSerializer(managers, many=True)
            return Response(serialized_item.data)
        return Response({"message": message})
    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAdminUser])
def group_view(request):
    if request.method == 'GET':
        serialized_item = serializers.GroupSerializer(Group.objects.all(), many=True)
        return Response(serialized_item.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def category(request):
    if request.method == 'GET':
        items = models.Category.objects.all()
        serialized_item = serializers.CategorySerializer(items, many=True)
        return Response(serialized_item.data, status.HTTP_200_OK)
    if request.method == 'POST' and request.user.groups.filter(name='Manager').exists():
        serialized_item = serializers.CategorySerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_201_CREATED)
    return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def category_single(request, id):
    item = get_object_or_404(models.Category, pk=id)
    if request.method == 'GET':
        serialized_item = serializers.CategorySerializer(item)
        return Response(serialized_item.data, status.HTTP_200_OK)
    elif request.method == 'POST':
        return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
    if not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
    if request.method == 'PUT':
        serialized_item = serializers.CategorySerializer(item, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'PATCH':
        serialized_item = serializers.CategorySerializer(item, data=request.data, partial=True)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'DELETE':
        item.delete()
        return Response(status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menuitems(request):
    if request.method == 'GET':
        items = models.MenuItem.objects.all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=2)
        page = request.query_params.get('page', default=1)
        if category_name:
            items = items.filter(category__title=category_name)
        if to_price:
            items = items.filter(price__lte=to_price)
        if search:
            items = items.filter(title__icontains=search)
        if ordering:
            ordering_fields = ordering.split(",")
            items = items.order_by(*ordering_fields)
        
        paginator = Paginator(items, per_page=perpage)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []
        serialized_item = serializers.MenuItemSerializer(items, many=True)
        return Response(serialized_item.data, status.HTTP_200_OK)
    if request.method == 'POST' and request.user.groups.filter(name='Manager').exists():
        serialized_item = serializers.MenuItemSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_201_CREATED)
    return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menuitems_single(request, id):
    item = get_object_or_404(models.MenuItem, pk=id)
    if request.method == 'GET':
        serialized_item = serializers.MenuItemSerializer(item)
        return Response(serialized_item.data, status.HTTP_200_OK)
    elif request.method == 'POST' or not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
    if request.method == 'PUT':
        serialized_item = serializers.MenuItemSerializer(item, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'PATCH':
        serialized_item = serializers.MenuItemSerializer(item, data=request.data, partial=True)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'DELETE':
        item.delete()
        return Response(status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manager_set(request):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
    
    if request.method == 'POST':
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
        else:
            return Response({"message": "Username is incorrect or does not existed."}, status.HTTP_400_BAD_REQUEST)
        managers = Group.objects.get(name="Manager")
        managers.user_set.add(user)
        message = 'User ' + username + ' ' 'is set as Manager.'
        return Response({"message": message}, status.HTTP_201_CREATED) 
    elif request.method == 'GET':
        managers = User.objects.filter(groups = Group.objects.get(name="Manager"))
        serialized_item = serializers.UserSerializer(managers, many=True)
        return Response(serialized_item.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def manager_delete(request, id):
    if request.user.groups.filter(name='Manager').exists():
        if request.method != 'DELETE':
            return Response({"message": "This only supports DELETE."}, status.HTTP_400_BAD_REQUEST) 
        user = get_object_or_404(User, id=id)
        if user.groups.filter(name='Manager').exists():
            managers = Group.objects.get(name="Manager")
            managers.user_set.remove(user)
            message = 'User ' + user.get_username + ' ' + 'is not a manager now.'
            return Response({"message": message}, status.HTTP_200_OK)
        else:
            return Response({"message": "This user is not a manager"}, status.HTTP_400_BAD_REQUEST) 
    else:
        return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def delivery_set(request):
    if not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
    
    if request.method == 'POST':
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
        else:
            return Response({"message": "Username is incorrect or not existed."}, status.HTTP_400_BAD_REQUEST)
        crews = Group.objects.get(name="Delivery crew")
        crews.user_set.add(user)
        message = 'User ' + username + ' ' 'is set as delivery crew.'
        return Response({"message": message}, status.HTTP_201_CREATED) 
    elif request.method == 'GET':
        crews = User.objects.filter(groups = Group.objects.get(name="Delivery crew"))
        serialized_item = serializers.UserSerializer(crews, many=True)
        return Response(serialized_item.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def delivery_delete(request, id):
    if request.user.groups.filter(name='Manager').exists():
        if request.method != 'DELETE':
            return Response({"message": "This only supports DELETE."}, status.HTTP_400_BAD_REQUEST) 
        user = get_object_or_404(User, id=id)
        if user.groups.filter(name='Delivery crew').exists():
            crews = Group.objects.get(name="Delivery crew")
            crews.user_set.remove(user)
            message = 'User ' + user.get_username + ' ' + 'is not a delivery crew now.'
            return Response({"message": message}, status.HTTP_200_OK)
        else:
            return Response({"message": "This user is not a delivery crew"}, status.HTTP_400_BAD_REQUEST) 
    else:
        return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
    


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def cart(request):
    if request.method == 'GET':
        try:
            cart = models.Cart.objects.get(user=request.user)
        except:
            return Response({"message": "The cart is empty."}, status.HTTP_400_BAD_REQUEST)
        serialized_item = serializers.CartSerializer(cart)
        return Response(serialized_item.data, status.HTTP_200_OK)
    if request.method == 'POST':
        if models.Cart.objects.filter(user=request.user).exists():
            return Response({"message": "The user has already a cart."}, status.HTTP_400_BAD_REQUEST)
        menuitem = request.data["menuitem"]
        quantity = request.data["quantity"]
        unit_price = models.MenuItem.objects.get(pk=menuitem).price
        price = Decimal(quantity) * unit_price
        data = {"menuitem_id": menuitem, 
                "quantity": quantity,
                "unit_price": unit_price,
                "price": price,
                "user_id": request.user.id,
        }
        serialized_item = serializers.CartSerializer(data=data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        message = 'Cart is created.'
        return Response({"message": message}, status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        cart = get_object_or_404(models.Cart, user=request.user)
        cart.delete()
        return Response(status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order(request):
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists():
            orders = models.Order.objects.all()
            to_price = request.query_params.get('to_price')
            search = request.query_params.get('search')
            ordering = request.query_params.get('ordering')
            perpage = request.query_params.get('perpage', default=2)
            page = request.query_params.get('page', default=1)
            if to_price:
                orders = orders.filter(total__lte=to_price)
            if search:
                orders = orders.filter(status__icontains=search)
            if ordering:
                ordering_fields = ordering.split(",")
                orders = orders.order_by(*ordering_fields)
            
            paginator = Paginator(orders, per_page=perpage)
            try:
                orders = paginator.page(number=page)
            except EmptyPage:
                orders = []
            serialized_order = serializers.OrderSerializer(orders, many=True)
            return Response(serialized_order.data, status.HTTP_200_OK)
        elif request.user.groups.filter(name='Delivery crew').exists():
            orders = models.Order.objects.filter(delivery_crew=request.user)
            serialized_order = serializers.OrderSerializer(orders, many=True)
            return Response(serialized_order.data, status.HTTP_200_OK)
        else:
            if models.Order.objects.filter(user=request.user).exists():
                order = models.Order.objects.filter(user=request.user)
                serialized_order = serializers.OrderSerializer(order)
                return Response(serialized_order.data, status.HTTP_200_OK)
            else:
                return Response(status.HTTP_404_NOT_FOUND)
    if request.method == 'POST':
        cart = get_object_or_404(models.Cart, user=request.user)
        
        
        orderitem_data = {
            "user_id": cart.user_id,
            "menuitem_id": cart.menuitem_id,
            "quantity": cart.quantity,
            "unit_price": cart.unit_price,
            "price": cart.price
        }
        serialized_orderitem = serializers.OrderItemSerializer(data=orderitem_data)
        serialized_orderitem.is_valid(raise_exception=True)
        serialized_orderitem.save()
        orderitem = models.OrderItem.objects.get(user=request.user, menuitem=cart.menuitem)
        order_data = {
            "user_id": cart.user_id,
            "total": cart.price,
            "orderitem_id": orderitem.id,
        }
        serialized_order = serializers.OrderSerializer(data=order_data)
        serialized_order.is_valid(raise_exception=True)
        serialized_order.save()
        
        cart.delete()
        message = 'Order is created.'
        return Response({"message": message}, status.HTTP_201_CREATED)
    return Response({"message": "Not authorized."}, status.HTTP_403_FORBIDDEN) 


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order_single(request, id):
    order = get_object_or_404(models.Order, pk=id)
    if request.method == 'GET':
        if order.user != request.user:
            return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
        serialized_order = serializers.OrderSerializer(order)
        return Response(serialized_order.data, status.HTTP_200_OK)
    if request.method == 'PUT':
        if not request.user.groups.filter(name='Manager').exists():
            return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN) 
        serialized_item = serializers.OrderSerializer(order, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
    if request.method == 'PATCH':
        if request.user.groups.filter(name='Delivery crew').exists(): 
            if order.delivery_crew != request.user:
                return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
            deliverystatus = request.data["status"]
            status_data = {"status": deliverystatus}
            serialized_item = serializers.OrderSerializer(order, data=status_data, partial=True)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
        if request.user.groups.filter(name='Manager').exists():
            serialized_item = serializers.OrderSerializer(order, data=request.data, partial=True)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
        return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN) 
    if request.method == 'DELETE':
        if not request.user.groups.filter(name='Manager').exists():
            return Response({"message": "Not Authorized."}, status.HTTP_403_FORBIDDEN)
        order.delete()
        return Response(status.HTTP_204_NO_CONTENT)