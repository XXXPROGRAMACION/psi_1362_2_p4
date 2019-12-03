from django import forms
from django.contrib.auth.models import User
from datamodel.models import Move

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        if self.cleaned_data['password'] != self.cleaned_data['password2']:
            self._errors['password2'] = ['Password and Repeat password are not the same|La clave y su repetición no coinciden']
            del self.cleaned_data['password2']
        if len(self.cleaned_data['password']) < 6:
            self._errors['password'] = ['Can\'t be too common, too short and must have at least 6 characters,']
        return super(SignupForm, self).clean()

    class Meta:
        model = User
        fields = ('username', 'password')
        

class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'password')


class MoveForm(forms.ModelForm):
    origin = forms.IntegerField(initial=0, min_value=0, max_value=63)
    target = forms.IntegerField(initial=0, min_value=0, max_value=63)

    class Meta:
        model = Move
        fields = ('origin', 'target')
