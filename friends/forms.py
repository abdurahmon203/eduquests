from django import forms


class UserSearchForm(forms.Form):
    q = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input friends-search-input",
                "placeholder": "Search by username...",
                "autocomplete": "off",
                "id": "friends-search-input",
            }
        ),
    )
