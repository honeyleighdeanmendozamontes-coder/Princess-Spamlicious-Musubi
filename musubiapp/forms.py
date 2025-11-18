from django import forms
from .models import Product, Order, Customer, InventoryLog
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'stock', 'available', 'image', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter password'
        }),
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Confirm password'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Choose a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Last name'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['phone', 'address', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Delivery address', 
                'rows': 3
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'delivery_method', 'special_instructions']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InventoryUpdateForm(forms.ModelForm):
    action = forms.ChoiceField(
        choices=[
            ('add', 'Add Stock'),
            ('remove', 'Remove Stock'),
            ('update', 'Update Stock'),
            ('waste', 'Waste/Expired'),
        ], 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity_change = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    
    class Meta:
        model = InventoryLog
        fields = ['action', 'quantity_change', 'notes']