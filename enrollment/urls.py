from django.urls import path
from . import views

urlpatterns = [
    path('catalog/', views.subject_catalog_view, name='subject_catalog'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:subject_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('cart/confirm/', views.confirm_enrollment_view, name='confirm_enrollment'),
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    path('dashboard/tutor/', views.tutor_dashboard_view, name='tutor_dashboard'),
    path('grades/<int:subject_id>/', views.subject_grades_view, name='subject_grades'),
    path('grades/enter/<int:enrollment_id>/', views.enter_grade_view, name='enter_grade'),
]
