import calendar
import logging
import os
import uuid
from datetime import *

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template import loader
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_protect

from accounts.models import CustomUser

from . import forms
from .forms import InquiryForm, NotificationForm, PhotoForm, ScheduleForm
from .models import Blog, Girls, GirlsList, Log, Notification, Photo, Schedule

logger = logging.getLogger(__name__)


class IndexView(generic.TemplateView):
    template_name = "index.html"

class InquiryView(generic.FormView):
    template_name = "inquiry.html"
    form_class = InquiryForm
    success_url = reverse_lazy('pole:inquiry')

    def form_valid(self, form):
        form.send_email()
        messages.success(self.request, 'メッセージを送信しました。')
        logger.info('Inquiry sent by {}'.format(form.cleaned_data['name']))
        return super().form_valid(form)

class NotificationView(LoginRequiredMixin, generic.FormView): 
    template_name = "notification.html"
    form_class = NotificationForm
    model = Notification
    success_url = reverse_lazy('pole:notification')

    def get_initial(self):
        initial = super().get_initial()
        # DBにレコードがあるか確認する（ないのに取得するとエラーになる）
        if Notification.objects.db_manager("poleBlogDB").filter(mail_address=self.request.user.email).exists():
            # DBからレコードを取得して初期値設定する
            notification = Notification.objects.db_manager("poleBlogDB").get(mail_address=self.request.user.email)
            initial["notification"] = notification.notification
            # listが文字列としてDBに保存されるため、数値のリストに変換する
            girls_ids = notification.favorite_girls.strip('[]')
            if len(girls_ids) > 0:
                girl_id_list = girls_ids.split(',')
                girl_id_list = [id.strip("' ") for id in girl_id_list]
                girl_id_num_list = list(map(int, girl_id_list))
                initial["favorite_girls"] = girl_id_num_list

        return initial

    def form_valid(self, form):
        notification = form.save(commit=False)
        # メールアドレスをScraperのDBに保存する
        notification.mail_address = self.request.user.email
        notification.update_date = datetime.now()
        if Notification.objects.db_manager("poleBlogDB").filter(mail_address=notification.mail_address).exists():
            Notification.objects.db_manager("poleBlogDB").filter(mail_address=notification.mail_address).update(
                mail_address=notification.mail_address,
                notification=notification.notification,
                favorite_girls=notification.favorite_girls,
                update_date=notification.update_date
                )
        else:
            Notification.objects.db_manager("poleBlogDB").filter(mail_address=notification.mail_address).create(
                mail_address=notification.mail_address,
                notification=notification.notification,
                favorite_girls=notification.favorite_girls,
                update_date=notification.update_date
                )

        messages.success(self.request, '変更を適用しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "変更の適用に失敗しました。")
        return super().form_invalid(form)

class LogListView(LoginRequiredMixin, generic.ListView):
    model = Log
    template_name = 'log_list.html'
    paginate_by = 50

    def get_queryset(self):
        logs = Log.objects.db_manager("poleBlogDB").all().order_by('-date')
        return logs

class ScheduleView(LoginRequiredMixin, generic.FormView):
    template_name = 'schedule.html'
    form_class = ScheduleForm
    model = Schedule

    success_url = reverse_lazy('pole:schedule')

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        girl_id = self.request.POST.get('id', None)
        if girl_id:
            logger.debug("self.request.POST.get() = " + girl_id)
            response = HttpResponse()
            
            # 指定された女の子の出勤日を年月日のリストで返す
            # blogIdは不要だが、Djangoの制約でPKを取得する必要がある
            sql = "select T_blog.blogId, group_concat(T_blog.url) as Url, \
                    group_concat(T_blog.blogId) as BlogIdList, \
                    strftime('%Y', date) as Year, \
                    strftime('%m', date) as Month, \
                    group_concat(strftime('%d', date)) as Day \
                    from T_blog, T_girlsList where girlId = {} and \
                    T_girlsList.blogId = T_blog.blogId \
                    group by Year, Month order by Year desc, Month desc".format(girl_id)
            entries = Blog.objects.db_manager("poleBlogDB").raw(sql)
            
            week_day = [0, 0, 0, 0, 0, 0, 0]
            calender = []
            monthly = []
            for entry in entries:
                days = entry.Day.split(',')
                urls = entry.Url.split(',')
                # DBの日付は01等になっているため、1に変換して更に文字列に変換する
                # (辞書を検索する際に、'01'と'1'では不一致になってしまうため)
                dictionary = dict(zip([str(int(d)) for d in days], urls))
                month_calendar = calendar.monthcalendar(int(entry.Year), int(entry.Month))
                month_calendar_str = []
                for week in month_calendar:
                    w = []
                    # カレンダーのリストは数値のリストのため、文字列のリストに変換する
                    # (辞書は文字列のため、比較したときにヒットするように)
                    for d in week:
                        w.append(str(d))
                        if d > 0:
                            if str(d) in dictionary:
                                date = datetime.strptime('{}/{}/{}'.format(
                                    entry.Year, entry.Month, d),'%Y/%m/%d')
                                week_day[date.weekday()] += 1
                    month_calendar_str.append(w)
                calender.append([entry.Year, entry.Month, month_calendar_str, dictionary])
                # 棒グラフ（月別出勤回数）用のデータの準備
                monthly.append(['{year:02}/{month:02}'.format(
                    year=int(entry.Year) % 2000, month=int(entry.Month)), len(dictionary)])

            # 円グラフ（曜日別割合）用の割合を計算
            total = sum(week_day)
            rate = [round(d/total * 100.0, 1) for d in week_day]
            
            template = loader.get_template('schedule_response.html')
            context = {'schedule':calender, 'pichart':rate, 'barchart':monthly}
            return HttpResponse(template.render(context, request))

class DashBoardView(generic.TemplateView):
    template_name = 'dashboard.html'

class PhotoView(LoginRequiredMixin, generic.FormView):
    template_name = 'photo.html'
    form_class = PhotoForm

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        year = self.request.POST.get('date', None)
        if year:
            sql = "select T_blog.blogId, T_image.filePath, T_image.url as URL, T_image.imageId, \
                    strftime('%Y', date) as Year, \
                    strftime('%m', date) as Month, \
                    strftime('%d', date) as Day \
                    from T_blog, T_image where T_image.blogId = T_blog.blogId and Year = '{}' \
                    order by Year desc, Month desc, Day desc".format(year)
                    
            entries = Photo.objects.db_manager("poleBlogDB").raw(sql)
            photos = []
            for entry in entries:
                photos.append(os.path.basename(entry.file_path))
            
            template = loader.get_template('photo_response.html')
            context = {'photos':photos}
            print(template.render(context, request))
            return HttpResponse(template.render(context, request))
