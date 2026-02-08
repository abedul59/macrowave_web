from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .utils import update_all_data

def home(request):
    # 每次使用者訪問首頁，都會執行 update_all_data
    # 在生產環境中，建議加上簡單的快取 (Cache)，例如 10 分鐘內不重複抓
    # 但這裡為了滿足"即時"需求，直接執行
    
    context = update_all_data()
    
    # 獲取當前時間
    context['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return render(request, 'home.html', context)