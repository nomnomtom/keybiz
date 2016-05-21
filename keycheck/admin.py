from django.contrib import admin
from keycheck.models import GpgKey, Mail

@admin.register(GpgKey)
class GpgKeyAdmin(admin.ModelAdmin):
	fields = ['keydata', 'keyhash']

@admin.register(Mail)
class MailAdmin(admin.ModelAdmin):
	fields = ['user', 'address', 'gpgkey']

