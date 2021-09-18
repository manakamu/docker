import datetime
import jpholiday
from django import template

register = template.Library() # Djangoのテンプレートタグライブラリ

# カスタムフィルタとして登録する

@register.filter
def get_dict_value(dictionary, key):
    return dictionary.get(key)

@register.filter
def append_string(dest, src):
    return dest + src

@register.filter
def get_day_class(date):
    day_class = ''
    # dateは年/月/日形式の文字列
    #d = datetime.strptime(date,'%Y/%m/%d')
    # strptimeを使用すると、is_holidayが正しく動作しないためのワークアラウンド
    # datetime.date(2020,7,23,0,0)になるのが原因？
    sp = date.split('/')
    day = datetime.date(int(sp[0]), int(sp[1]), int(sp[2]))
    if day.weekday() == 5:
        # 土曜日
        day_class = 'text-primary'
    elif day.weekday() == 6 or jpholiday.is_holiday(day):
        # 日曜 or 祝日
        day_class = 'text-danger'
    return day_class

@register.filter
def get_monthly_max(monthly_list):
    max_count = 0
    for date, count in monthly_list:
        max_count = max(max_count, count)

    return max_count
