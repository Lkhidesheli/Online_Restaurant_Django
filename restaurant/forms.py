from django import forms

class FilterForm(forms.Form):
    categoryId = forms.ChoiceField(label='კატეგორია', required=False)
    spiciness = forms.ChoiceField(label='სიცხარე', required=False, choices=[('', 'ყველა დონე')] + [(str(i), f'{i} / 4') for i in range(5)])
    nuts = forms.ChoiceField(label='ნიგვზიანი', required=False, choices=[('', 'ყველა'), ('true', 'კი'), ('false', 'არა')])
    vegeterian = forms.ChoiceField(label='ვეგეტარიანული', required=False, choices=[('', 'ყველა'), ('true', 'კი'), ('false', 'არა')])

    def __init__(self, *args, categories=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoryId'].choices = [('', 'ყველა კატეგორია')] + [(str(c['id']), c['name']) for c in categories]

class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99, error_messages={'required':'მიუთითე რაოდენობა.','invalid':'რაოდენობა უნდა იყოს მთელი რიცხვი.','min_value':'მინიმალური რაოდენობაა 1.','max_value':'მაქსიმალური რაოდენობაა 99.'})
