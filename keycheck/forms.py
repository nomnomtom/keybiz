# -*- encoding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from keycheck.models import GpgKey

class addKey(forms.ModelForm):
	class Meta:
		model = GpgKey
		fields = ('keydata',)
		unique_together = ('keydata', 'user')
		widget = {
			'keydata': forms.TextInput(attrs={'class': 'form-control'}),	
		}
