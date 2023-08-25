from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from mailjet_rest import Client
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from django.http import FileResponse, Http404,HttpResponseBadRequest
import razorpay
from django.conf import settings

from .models import User, Food, FoodCategory, FoodLog, Image, Weight ,UserCalories,Coaches,Premium
from .forms import FoodForm, ImageForm

def index(request):
    '''
    The default route which lists all food items
    '''
    return food_list_view(request)


def register(request):
    currency = 'INR'
    amount = 1100000
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        active = request.POST['active']############
        age = request.POST['age']##############
        weight = request.POST['weight']########
        premium = request.POST['premium']
        print(premium)
        p = int(weight)*2.4#########
        f = int(weight)*0.7#########
        if active==0:#####
            c = int(((2000 - (p*4 + f*9))/4)*(0.7))########
        if active==1:#####
            c = int(((2000 - (p*4 + f*9))/4)*(1))########
        elif active==2:######
            c = int(((2000 - (p*4 + f*9))/4)*(1.2))#####
        elif active==3:########
            c = int(((2000 - (p*4 + f*9))/4)*(1.25))######
        else:#######
            c = int(((2000 - (p*4 + f*9))/4)*(1.5))######
        if password != confirmation:
            return render(request, 'register.html', {
                'message': 'Passwords must match.',
                'categories': FoodCategory.objects.all()
            })
        calories = 4*(p+c) + 9*f
        # Attempt to create new user
        try:
            users = User.objects.create_user(username, email, password)
                    ##weight_log = Weight(user=user, weight=weight, entry_date=entry_date)
        ##weight_log.save()
            usercal = UserCalories(username=username,calories=calories,proteins=p,carbohydrates=c,fats=f)
            try:
                userpremium = Premium(users.id,username,int(premium))
            except:
                userpremium = Premium(users.id,username,0)
            users.save()
            usercal.save()
            userpremium.save()
        except IntegrityError:
            return render(request, 'register.html', {
                'message': 'Username already taken.',
                'categories': FoodCategory.objects.all()
            })
        api_key = 'b132dbed8693f3e2f0f104718df0861b'
        api_secret = 'aef661c0059e1f0243da1eb14c9b8954'
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        data = {'Messages': [{
                        "From": {"Email": "avneeptestcase@gmail.com","Name": "Me"},
                        "To": [{"Email": str(email),"Name": "You"}],
                        "Subject": "WELCOME",
                        "TextPart": "Greetings from Dietician!",
                        "HTMLPart": "<h3>Dear "+username+", welcome to Dietician!</h3><br><h4><a href='http://127.0.0.1:8000/login'>click on the link to verify email</a></h4><br><br><i>May the force be with you!</i>"}]
                }
        result = mailjet.send.create(data=data)
        print(result.json())
        if(premium == "1"):
            razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
            razorpay_client.set_app_details({"title" : "Dietician", "version" : "v1"})
            razorpay_order = razorpay_client.order.create(dict(amount=amount,currency=currency,payment_capture='1'))
            razorpay_order_id = razorpay_order['id']
            callback_url = 'paymenthandler'
            context = {}
            context['razorpay_order_id'] = razorpay_order_id
            context['razorpay_merchant_key'] = settings.RAZOR_KEY_ID
            context['callback_url'] = callback_url
            return render(request, 'homepay.html', context=context)
            
        login(request, users)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'register.html', {
            'categories': FoodCategory.objects.all()
        })

@csrf_exempt
def paymenthandler(request):
 
    # only accept POST request.
    if request.method == "POST":
        try:
           
            # get the required parameters from post request.
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
 
            # verify the payment signature.
            result = razorpay_client.utility.verify_payment_signature(
                params_dict)
            if result is not None:
                amount = 1100000  # Rs. 11000
                try:
 
                    # capture the payemt
                    razorpay_client.payment.capture(payment_id, amount)
 
                    # render success page on successful caputre of payment
                    return redirect('succ')
                except:
 
                    # if there is an error while capturing payment.
                    return redirect('fail')
            else:
 
                # if signature verification fails.
                return redirect('fail')
        except:
 
            # if we don't find the required parameters in POST data
            return HttpResponseBadRequest()
    else:
       # if other than POST request is made.
        return HttpResponseBadRequest()

def login_view(request):
    if request.method == 'POST':

        # Attempt to sign user in
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'login.html', {
                'message': 'Invalid username and/or password.',
                'categories': FoodCategory.objects.all()
            })
    else:
        return render(request, 'login.html',  {
            'categories': FoodCategory.objects.all()
        })


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def food_list_view(request):
    '''
    It renders a page that displays all food items
    Food items are paginated: 4 per page
    '''
    foods = Food.objects.all()

    for food in foods:
        food.image = food.get_images.first()

    # Show 4 food items per page
    page = request.GET.get('page', 1)
    paginator = Paginator(foods, 16)
    try:
        pages = paginator.page(page)
    except PageNotAnInteger:
        pages = paginator.page(1)
    except EmptyPage:
        pages = paginator.page(paginator.num_pages)

    return render(request, 'index.html', {
        'categories': FoodCategory.objects.all(),
        'foods': foods,
        'pages': pages,
        'title': 'Food List'
    })
@login_required
def coaches(request):
    cs = Coaches.objects.all()
    for c in cs:
        c.image = c.get_images.first()
        
    page = request.GET.get('page', 1)
    paginator = Paginator(cs, 4)
    try:
        pages = paginator.page(page)
    except PageNotAnInteger:
        pages = paginator.page(1)
    except EmptyPage:
        pages = paginator.page(paginator.num_pages)
    return render(request,'coaches.html',{
        'pages':pages,
        'title':'Coaches'
    })
def food_details_view(request, food_id):
    '''
    It renders a page that displays the details of a selected food item
    '''
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    food = Food.objects.get(id=food_id)

    return render(request, 'food.html', {
        'categories': FoodCategory.objects.all(),
        'food': food,
        'images': food.get_images.all(),
    })
@login_required
def food_add_view(request):
    '''
    It allows the user to add a new food item
    '''
    ImageFormSet = forms.modelformset_factory(Image, form=ImageForm, extra=2)

    if request.method == 'POST':
        food_form = FoodForm(request.POST, request.FILES)
        image_form = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())

        if food_form.is_valid() and image_form.is_valid():
            new_food = food_form.save(commit=False)
            new_food.save()

            for food_form in image_form.cleaned_data:
                if food_form:
                    image = food_form['image']

                    new_image = Image(food=new_food, image=image)
                    new_image.save()

            return render(request, 'food_add.html', {
                'categories': FoodCategory.objects.all(),
                'food_form': FoodForm(),
                'image_form': ImageFormSet(queryset=Image.objects.none()),
                'success': True
            })
        
        else:
            return render(request, 'food_add.html', {
                'categories': FoodCategory.objects.all(),
                'food_form': FoodForm(),
                'image_form': ImageFormSet(queryset=Image.objects.none()),
            })

    else:
        return render(request, 'food_add.html', {
            'categories': FoodCategory.objects.all(),
            'food_form': FoodForm(),
            'image_form': ImageFormSet(queryset=Image.objects.none()),
        })
    

@login_required
def food_log_view(request):
    '''
    It allows the user to select food items and 
    add them to their food log
    '''
    if request.method == 'POST':
        foods = Food.objects.all()

        # get the food item selected by the user
        food = request.POST['food_consumed']
        food_consumed = Food.objects.get(food_name=food)

        # get the currently logged in user
        user = request.user
        # add selected food to the food log
        food_log = FoodLog(user=user, food_consumed=food_consumed)
        food_log.save()

    else: # GET method
        foods = Food.objects.all()
        
    # get the food log of the logged in user
    user_food_log = FoodLog.objects.filter(user=request.user)
    user_food_calories = UserCalories.objects.filter(username=request.user).get()######
    p = UserCalories.objects.values('proteins').filter(username=request.user).get()['proteins']######
    c = UserCalories.objects.values('carbohydrates').filter(username=request.user).get()['carbohydrates']######
    f = UserCalories.objects.values('fats').filter(username=request.user).get()['fats']######
    return render(request, 'food_log.html', {
        'categories': FoodCategory.objects.all(),
        'foods': foods,
        'user_food_log': user_food_log,
        'user_food_calories' : user_food_calories,######
        'P' : p,
        'F' : f,
        'C' : c
    })

@login_required
def food_log_delete(request, food_id):
    '''
    It allows the user to delete food items from their food log
    '''
    # get the food log of the logged in user
    food_consumed = FoodLog.objects.filter(id=food_id)

    if request.method == 'POST':
        food_consumed.delete()
        return redirect('food_log')
    
    return render(request, 'food_log_delete.html', {
        'categories': FoodCategory.objects.all()
    })


@login_required
def weight_log_view(request):
    '''
    It allows the user to record their weight
    '''
    if request.method == 'POST':

        # get the values from the form
        weight = request.POST['weight']
        entry_date = request.POST['date']

        # get the currently logged in user
        user = request.user

        # add the data to the weight log
        weight_log = Weight(user=user, weight=weight, entry_date=entry_date)
        weight_log.save()

    # get the weight log of the logged in user
    user_weight_log = Weight.objects.filter(user=request.user)
    
    return render(request, 'user_profile.html', {
        'categories': FoodCategory.objects.all(),
        'user_weight_log': user_weight_log
    })


@login_required
def weight_log_delete(request, weight_id):
    '''
    It allows the user to delete a weight record from their weight log
    '''
    # get the weight log of the logged in user
    weight_recorded = Weight.objects.filter(id=weight_id) 

    if request.method == 'POST':
        weight_recorded.delete()
        return redirect('weight_log')
    
    return render(request, 'weight_log_delete.html', {
        'categories': FoodCategory.objects.all()
    })


def categories_view(request):
    '''
    It renders a list of all food categories
    '''
    return render(request, 'categories.html', {
        'categories': FoodCategory.objects.all()
    })


def category_details_view(request, category_name):
    '''
    Clicking on the name of any category takes the user to a page that 
    displays all of the foods in that category
    Food items are paginated: 4 per page
    '''
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    category = FoodCategory.objects.get(category_name=category_name)
    foods = Food.objects.filter(category=category)

    for food in foods:
        food.image = food.get_images.first()

    # Show 4 food items per page
    page = request.GET.get('page', 1)
    paginator = Paginator(foods, 4)
    try:
        pages = paginator.page(page)
    except PageNotAnInteger:
        pages = paginator.page(1)
    except EmptyPage:
        pages = paginator.page(paginator.num_pages)

    return render(request, 'food_category.html', {
        'categories': FoodCategory.objects.all(),
        'foods': foods,
        'foods_count': foods.count(),
        'pages': pages,
        'title': category.category_name
    })

@login_required
def coach_chats(request,coach_id):
    amount=1100000
    currency='INR'
    coach = Coaches.objects.get(id=coach_id)
    isp = Premium.objects.get(user=request.user)
    print(isp)
    print(request.user.id)
    if(isp.ispremium==0):
        isp.ispremium = 1
        isp.save()
        razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        razorpay_client.set_app_details({"title" : "Dietician", "version" : "v1"})
        razorpay_order = razorpay_client.order.create(dict(amount=amount,currency=currency,payment_capture='1'))
        razorpay_order_id = razorpay_order['id']
        callback_url = 'paymenthandler'
        context = {}
        context['razorpay_order_id'] = razorpay_order_id
        context['razorpay_merchant_key'] = settings.RAZOR_KEY_ID
        context['callback_url'] = callback_url
        return render(request,'homepay.html',context=context)
    else:
        return render(request,'coach_chats.html',{
            'name' : coach.name,
            'type' : coach.type,
            'images' : coach.get_images.all(),
            'id' : coach.id
        })
    
@login_required
def coach_message(request,coach_id):
    coach = Coaches.objects.get(id=coach_id)
    user = request.user
    st = ""
    if request.method == 'POST':
        sub = request.POST.get('subject')
        text = request.POST.get('details')
        print(sub)
        print(text)
        api_key = 'b132dbed8693f3e2f0f104718df0861b'
        api_secret = 'aef661c0059e1f0243da1eb14c9b8954'
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        data = {'Messages': [{
                        "From": {"Email": str(user.email),"Name": "Me"},
                        "To": [{"Email": "avneeptestcase@gmail.com","Name": "You"}],
                        "Subject": "From "+str(user.username)+" to "+str(coach.name),
                        "HTMLPart": "<h1>"+str(sub)+",</h1><br>"+"<h2>"+str(text)+"</h2>"}]
                }
        result = mailjet.send.create(data=data)
        print(result.json())
        st = "message to the coach has been sent"
    
    return render(request,'msg_coach.html',{
        'name' : coach.name,
        'type' : coach.type,
        'message' : st
    })

def pdf_view(request):
    try:
        return FileResponse(open('water.pdf', 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404()
def Success(request):
    return render(request,'succpay.html',{})
def Fail(request):
    return render(request,'failpay.html',{})
