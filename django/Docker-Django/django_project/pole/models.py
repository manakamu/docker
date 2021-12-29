from accounts.models import CustomUser
from django.db import models

# Create your models here.
class Notification(models.Model):
    """通知モデル"""

    mail_address = models.CharField(
        verbose_name='ユーザー', primary_key=True,
        db_column = 'mail_address', max_length=128,)
    notification = models.BooleanField(verbose_name='メール通知',
        default=False, db_column = 'notification')
    favorite_girls = models.CharField(verbose_name='推しメン', max_length=128,
        null=True, db_column = 'favorite_girls')
    update_date = models.DateTimeField(verbose_name='更新日時',
        auto_now=True, db_column = 'update_date')

    class Meta:
        db_table = 'T_mail'
        managed = False

class Log(models.Model):
    date = models.DateTimeField(verbose_name='日時')
    log = models.IntegerField(verbose_name='ログ')

    class Meta:
        db_table = 'T_log'
        managed = False

class Girls(models.Model):
    girl_id = models.IntegerField(verbose_name='ID', db_column = 'girlId', primary_key=True)
    name = models.TextField(verbose_name='名前')
    last_update = models.DateTimeField(verbose_name='最終更新日', db_column = 'lastUpdate')

    class Meta:
        db_table = 'T_girl'
        managed = False

class Schedule(models.Model):
    blog_id = models.IntegerField(verbose_name='ブログID', db_column = 'blogId')
    girl_id = models.IntegerField(verbose_name='女の子ID', db_column = 'girlId')

    class Meta:
        db_table = 'T_girlsList'
        managed = False

class Blog(models.Model):
    blog_id = models.IntegerField(verbose_name='ブログID', db_column = 'blogId', primary_key=True)
    date = models.DateTimeField(verbose_name='日時')

    class Meta:
        db_table = 'T_blog'
        managed = False

class GirlsList(models.Model):
    girls_list_id = models.IntegerField(verbose_name='GirlsListId', db_column = 'girlsListId', primary_key=True)
    blog_id = models.IntegerField(verbose_name='ブログID', db_column = 'blogId')
    #blog_id = models.ForeignKey('Blog', db_column = 'blogId', on_delete=models.CASCADE)
    girl_id = models.IntegerField(verbose_name='女の子ID', db_column = 'girlId')

    class Meta:
        db_table = 'T_girlsList'
        managed = False

class Photo(models.Model):
    image_id = models.IntegerField(verbose_name='imageId', db_column = 'imageId', primary_key=True)
    file_path = models.CharField(verbose_name='ファイルパス', db_column = 'filePath', max_length=256)
    blog_id = models.ManyToManyField(Blog, related_name="photo_blog_id")
    date = models.ManyToManyField(Blog, related_name="photo_date")

    class Meta:
        db_table = 'T_image'
        managed = False
