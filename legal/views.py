from django.shortcuts import render

def terms_view(request):
    return render(request, 'legal/terms.html')
