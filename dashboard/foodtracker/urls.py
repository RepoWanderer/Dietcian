from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register', views.register, name='register'),
    path('register/paymenthandler', views.paymenthandler, name='paymenthandler'),
    path('register/successpayment', views.Success, name='succ'),
    path('register/failedpayment', views.Fail, name='fail'),
    path('profile/weight', views.weight_log_view, name='weight_log'),
    path('profile/weight/delete/<int:weight_id>', views.weight_log_delete, name='weight_log_delete'),

    path('food/list', views.food_list_view, name='food_list'),
    path('food/add', views.food_add_view, name='food_add'),
    path('food/foodlog', views.food_log_view, name='food_log'),
    path('food/coaches', views.coaches, name='coaches'),
    path('water.pdf', views.pdf_view, name='pdf_view'),
    path('food/coaches/coach_chats/<int:coach_id>',views.coach_chats,name='coach_chats'),
    path('food/coaches/coach_msg/<int:coach_id>',views.coach_message,name='msg_coach'),
    path('food/foodlog/delete/<int:food_id>', views.food_log_delete, name='food_log_delete'),
    path('food/<str:food_id>', views.food_details_view, name='food_details'),

    path('categories', views.categories_view, name='categories_view'),
    path('categories/<str:category_name>', views.category_details_view, name='category_details_view'),
]
