# -*- encoding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from keycheck.models import GpgKey

class addKey(forms.ModelForm):
	'''
	Form for adding a gpg key.

	The form requires the user to enter the ascii armored version of their gpg
	key. 
	'''
	class Meta:
		model = GpgKey
		fields = ('keydata',)
		widget = {
			'keydata': forms.TextInput(attrs={'class': 'form-control'}),	
		}
