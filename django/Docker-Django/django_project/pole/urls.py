from django.urls import path

from . import views


app_name = 'pole'
urlpatterns = [
    path('pole/', views.IndexView.as_view(), name="top"),
    path('schedule/', views.ScheduleView.as_view(), name="schedule"),
    path('photo/', views.PhotoView.as_view(), name="photo"),
    path('notification/', views.NotificationView.as_view(), name="notification"),
    path('inquiry/', views.InquiryView.as_view(), name="inquiry"),
    path('log/', views.LogListView.as_view(), name="log"),
    path('dashboard/', views.DashBoardView.as_view(), name="dashboard"),
]