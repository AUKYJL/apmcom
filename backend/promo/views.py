from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .serializers import (
    LoginSerializer,
    ProductSerializer,
    ReceiptCreateSerializer,
    ReceiptSerializer,
    RegisterSerializer,
    build_profile,
)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfView(APIView):
    """Выдаёт CSRF-cookie. Фронтенд вызывает его один раз при загрузке."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'ok': True})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(build_profile(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['email'].lower(),
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'non_field_errors': ['Неверный e-mail или пароль']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(build_profile(user))


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(build_profile(request.user))


class ProductListView(generics.ListAPIView):
    """Акционная продукция для раздела на главной."""

    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = None

    def get_queryset(self):
        return Product.objects.filter(is_active=True)


class ReceiptListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return self.request.user.receipts.prefetch_related('photos')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReceiptCreateSerializer
        return ReceiptSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = serializer.save()
        data = ReceiptSerializer(receipt, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)
