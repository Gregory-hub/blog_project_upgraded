from django import forms


class AddForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'type': 'title', 'id': 'title', 'placeholder': 'Title', 'autocomplete': 'off'}), max_length=70)
    text = forms.CharField(widget=forms.Textarea(attrs={'id': 'art', 'class': 'textareacl', 'placeholder': 'Text', 'autocomplete': 'off'}))
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'id': 'avatarfile'}))


class WriterImageForm(forms.Form):
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'id': 'af', 'name': 'avatarfile'}))


class WriterBioForm(forms.Form):
    bio = forms.CharField(widget=forms.Textarea(attrs={'id': 'itext', 'class': 'textareacl', 'name': 'info', 'placeholder': 'Information about you'}), required=False, max_length=1000)
    age = forms.IntegerField(widget=forms.TextInput(attrs={'id': "iage", 'placeholder': "Your age"}), required=False)


class SignUpForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'username', 'autocomplete': 'off'}), max_length=30)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password', 'autocomplete': 'off'}), max_length=50)


class LogInForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Your username', 'autocomplete': 'off'}), max_length=50)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Your password', 'autocomplete': 'off'}), max_length=50)


class EditForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'type': 'title', 'id': 'title', 'placeholder': 'Title', 'autocomplete': 'off'}), max_length=70)
    text = forms.CharField(widget=forms.Textarea(attrs={'id': 'art', 'class': 'textareacl', 'placeholder': 'Text', 'autocomplete': 'off'}))
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'id': 'avatarfile', 'name': 'avatarfile'}), required=False)


class CommentForm(forms.Form):
    text = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'class': 'comment__texting', 'type': 'text', 'placeholder': 'Comment'}))
