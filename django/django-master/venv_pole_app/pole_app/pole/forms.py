from django import forms
from django.core.mail import EmailMessage

from .models import Notification, Girls, Schedule, Photo

class InquiryForm(forms.Form):
    name = forms.CharField(label='お名前', max_length=30)
    email = forms.EmailField(label='メールアドレス')
    title = forms.CharField(label='タイトル', max_length=30)
    message = forms.CharField(label='メッセージ', widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs['class'] = 'form-control col-9'
        self.fields['name'].widget.attrs['placeholder'] = 'お名前をここに入力してください。'

        self.fields['email'].widget.attrs['class'] = 'form-control col-11'
        self.fields['email'].widget.attrs['placeholder'] = 'メールアドレスをここに入力してください。'

        self.fields['title'].widget.attrs['class'] = 'form-control col-11'
        self.fields['title'].widget.attrs['placeholder'] = 'タイトルをここに入力してください。'

        self.fields['message'].widget.attrs['class'] = 'form-control col-12'
        self.fields['message'].widget.attrs['placeholder'] = 'メッセージをここに入力してください。'

    def send_email(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        title = self.cleaned_data['title']
        message = self.cleaned_data['message']

        subject = 'お問い合わせ {}'.format(title)
        message = '送信者名: {0}\nメールアドレス: {1}\nメッセージ:\n{2}'.format(name, email, message)
        from_email = 'admin@example.com'
        to_list = [
            'test@example.com'
        ]
        cc_list = [
            email
        ]

        message = EmailMessage(subject=subject, body=message, from_email=from_email, to=to_list, cc=cc_list)
        message.send()

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ('notification', 'favorite_girls')

    # チェックOFFを許可するため、required=False
    notification = forms.BooleanField(label='メール通知', required=False)

    favorite_girls = forms.MultipleChoiceField(
        label='女の子',
        required=False,
        disabled=False,
        widget=forms.SelectMultiple(attrs={
            'id': 'girl',}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['favorite_girls'].widget.attrs['class'] = 'selectpicker'
        self.fields['favorite_girls'].widget.attrs['data-actions-box'] = 'true'

        if Girls.objects.db_manager("poleBlogDB").exists():
            girls_list = Girls.objects.db_manager("poleBlogDB").all().order_by('-last_update')
            girls_choice = []
            for girl in girls_list:
                girls_choice.append((girl.girl_id, girl.name))
            self.fields["favorite_girls"].choices = girls_choice

class ScheduleForm(forms.Form):
    class Meta:
        model = Schedule
        fields = ('girl_id',)
    
    girl_id = forms.ChoiceField(
        label='女の子',
        required=False,
        disabled=False,
        widget=forms.Select(attrs={
            'id': 'girl_id',}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['girl_id'].widget.attrs['class'] = 'selectpicker'
        self.fields['girl_id'].widget.attrs['data-actions-box'] = 'true'
        self.fields['girl_id'].widget.attrs['data-live-search'] = 'true'

        if Girls.objects.db_manager("poleBlogDB").exists():
            girls_list = Girls.objects.db_manager("poleBlogDB").all().order_by('-last_update')
            girls_choice = []
            for girl in girls_list:
                girls_choice.append((girl.girl_id, girl.name))
            self.fields["girl_id"].choices = girls_choice

class PhotoForm(forms.Form):
    class Meta:
        model = Photo
        fields = ('date',)
    
    date = forms.ChoiceField(
        label='年',
        required=False,
        disabled=False,
        widget=forms.Select(attrs={
            'id': 'date',}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget.attrs['class'] = 'selectpicker'
        self.fields['date'].widget.attrs['data-actions-box'] = 'true'

        if Photo.objects.db_manager("poleBlogDB").exists():
            sql = "select T_blog.blogId, T_image.filePath, T_image.imageId, \
                    strftime('%Y', date) as Year \
                    from T_blog, T_image where T_image.blogId = T_blog.blogId \
                    group by Year order by Year desc"
                    
            entries = Photo.objects.db_manager("poleBlogDB").raw(sql)
            year_choice = []
            for entry in entries:
                year_choice.append((entry.Year, entry.Year))
                self.fields["date"].choices = year_choice
