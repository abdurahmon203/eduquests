from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="Name",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your name',
            'id': 'contact_name'
        })
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'you@example.com',
            'id': 'contact_email'
        })
    )
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Tell us how we can help...',
            'id': 'contact_message',
            'rows': 5
        })
    )
