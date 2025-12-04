from django import forms

class ContactForm(forms.Form):
    #subject = forms.CharField(max_lenght=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)
