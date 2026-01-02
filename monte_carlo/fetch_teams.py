import requests
import pandas as pd
import json

# --------------------------
# --- TEMEL AYARLAR ---
# --------------------------
# Lütfen kendi API KEY'inizi buraya yapıştırın:
API_KEY = "6f6931e85d8241c6be0022ed866e8dc2" 
COMPETITION_CODE = 'CL' # Şampiyonlar Ligi kodu

def get_all_team_names():
    """API'den mevcut puan durumundaki tüm takım adlarını çeker."""
    url = f"https://api.football-data.org/v4/competitions/{COMPETITION_CODE}/standings"
    headers = {'X-Auth-Token': API_KEY}
    
    unique_teams = set()
    
    print(f"🔗 API: {url} adresinden puan durumu çekiliyor...")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        data = response.json()
        
        if 'standings' in data and len(data['standings']) > 0:
            
            # Lig formatında genellikle tek bir tablo olur
            table = data['standings'][0]['table'] 
            for row in table:
                team_name = row['team']['name']
                unique_teams.add(team_name)
            
            print("--------------------------------------------------")
            print(f"✅ Başarıyla çekilen takım sayısı: {len(unique_teams)}")
            print("--------------------------------------------------")
            print("💡 Kopyalayıp POWER_MAP'e yapıştırabileceğiniz liste:")
            
            # Kopyalaması kolay olsun diye Python sözlük formatında çıktı veriyoruz
            team_dict = {name: 80 for name in sorted(list(unique_teams))}
            
            # JSON/Sözlük olarak temiz çıktı
            print(json.dumps(team_dict, indent=4, ensure_ascii=False))
            
            print("--------------------------------------------------")
            
        else:
            print("⚠️ API'den puan tablosu verisi alınamadı (standings boş).")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API Hatası: Veri çekilemedi. API Anahtarınızı veya internet bağlantınızı kontrol edin. Hata: {e}")

if __name__ == '__main__':
    get_all_team_names()