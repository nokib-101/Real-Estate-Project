from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth import get_user_model
from contacts.models import Contact 


User = get_user_model()


def register(request):
    if request.method == "POST":
        # Get form values 
        first_name = request.POST['first_name']  
        last_name = request.POST['last_name'] 
        username = request.POST['username'] 
        email = request.POST['email'] 
        password = request.POST['password']  
        password2 = request.POST['password2'] 
        # check password match 
        if password == password2:
            #check username 
            if User.objects.filter(username=username).exists():
                messages.error(request, 'That username is taken ')
                return redirect('register')
            else:
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'That email is being used ')
                    return redirect('register')
                else:
                    user = User.objects.create_user(username=username, password=password, email=email, first_name = first_name, last_name = last_name)        
                    # login after registration 
                    user.save()
                    messages.success(request, 'You are now register and can log in')
                    return redirect('login')                
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('register')
    else:
        return render(request, 'accounts/register.html')

def login(request):
    if request.method == "POST":
        # Login User 
        username = request.POST['username']
        password = request.POST['password'] 

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
        

        
    else:
        return render(request, 'accounts/login.html')


def logout(request):
    if request.method == "POST":
        auth.logout(request)
        messages.success(request, 'Logout successful ')    
        return redirect('index')

def dashboard(request):
    user_contacts = Contact.objects.order_by('-contact_date').filter(user_id=request.user.id)
    context = {
        'contacts': user_contacts
    }
    return render(request, 'accounts/dashboard.html',context)



