import numpy as np
import pandas as pd
import requests
from flask import Flask, render_template, jsonify
import time
import random

# Flask uygulamasını başlat
app = Flask(__name__)

# --------------------------
# --- TEMEL AYARLAR ---
# --------------------------
# Lütfen API KEY'inizi buraya yapıştırın:
API_KEY = "6f6931e85d8241c6be0022ed866e8dc2" # Football-Data.org API Key
COMPETITION_CODE = 'CL' # Şampiyonlar Ligi kodu
SIMULATION_COUNT = 100000 # Hız ve hassasiyet ayarı (Yükseltildi)
TOTAL_MATCHES = 8 # Yeni formatta her takım 8 maç yapar

# Güç Haritası: Simülasyon motorunun tahmin yapması için temel girdi
# Not: Takım isimlerinin API'deki ile aynı olması kritik!
POWER_MAP = {
    "AFC Ajax": 68, 
    "AS Monaco FC": 71,
    "Arsenal FC": 87,
    "Atalanta BC": 77,
    "Athletic Club": 77,
    "Bayer 04 Leverkusen": 76,
    "Borussia Dortmund": 82,
    "Chelsea FC": 80,
    "Club Atlético de Madrid": 80,
    "Club Brugge KV": 69,
    "Eintracht Frankfurt": 73,
    "FC Barcelona": 86,
    "FC Bayern München": 87,
    "FC Internazionale Milano": 85,
    "FC København": 70,
     "FK Bodø/Glimt": 66,
    "FK Kairat": 58,
    "Galatasaray SK":73,
    "Juventus FC": 78,
    "Liverpool FC": 80,
    "Manchester City FC": 87,
    "Newcastle United FC": 77,
    "Olympique de Marseille": 78,
    "PAE Olympiakos SFP": 71,
    "PSV": 75,
    "Paphos FC": 65,
    "Paris Saint-Germain FC": 88,
    "Qarabağ Ağdam FK": 75,
    "Real Madrid CF": 85,
    "Royale Union Saint-Gilloise": 73,
    "SK Slavia Praha": 61,
    "SSC Napoli": 78,
    "Sport Lisboa e Benfica": 72,
    "Sporting Clube de Portugal": 74,
    "Tottenham Hotspur FC": 79,
    "Villarreal CF": 67
}

# --------------------------
# --- API VERİ ÇEKME FONKSİYONLARI ---
# --------------------------

def get_live_data():
    """API'den canlı puan durumunu çeker."""
    url = f"https://api.football-data.org/v4/competitions/{COMPETITION_CODE}/standings"
    headers = {'X-Auth-Token': API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        data = response.json()
        
        standings = []
        if 'standings' in data and len(data['standings']) > 0:
            # API'den gelen veride takımlar GroupStage yerine League olarak listelenir.
            table = data['standings'][0]['table'] 
            for row in table:
                team_name = row['team']['name']
                # Eğer haritada yoksa, varsayılan güç haritada en düşük değeri değil, 
                # ortalama bir değer olarak 78 alınıyor.
                power = POWER_MAP.get(team_name, 78) 
                
                standings.append({
                    'Takım': team_name,
                    'Puan': row['points'],
                    'Oynanan': row['playedGames'],
                    'Averaj': row['goalDifference'],
                    'Güç': power
                })
        return pd.DataFrame(standings)
    except requests.exceptions.RequestException as e:
        print(f"❌ Puan Tablosu API Hatası: {e}")
        return pd.DataFrame()

def get_remaining_fixtures(api_key, competition_code):
    """API'den oynanmamış (SCHEDULED) maçları çeker."""
    url = f"https://api.football-data.org/v4/competitions/{competition_code}/matches?status=SCHEDULED"
    headers = {'X-Auth-Token': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        data = response.json()
        
        fixtures = []
        if data.get('matches'):
            for match in data['matches']:
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                
                # API'den gelen takım adlarını kontrol et, güç haritasında yoksa atla
                if home_team in POWER_MAP and away_team in POWER_MAP:
                    fixtures.append({
                        'Ev Sahibi': home_team,
                        'Deplasman': away_team,
                        'Tarih': match['utcDate'] 
                    })
        return fixtures
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Fikstür API Hatası: {e}")
        return []

# --------------------------
# --- SİMÜLASYON MOTORU ---
# --------------------------

def predict_match_score(power_h, power_a):
    """
    İki takımın gücüne göre skor tahmini üretir. (Daha dengeli Poisson & Olasılık)
    power_h = Ev Sahibi, power_a = Deplasman
    """
    diff = power_h - power_a
    # Sigmoid fonksiyonu ile Ev Sahibi Galibiyet olasılığı hesaplanır
    # Daha yumuşak geçiş için bölen 20'ye çıkarıldı.
    win_prob_h = 1 / (1 + np.exp(-diff / 20))
    
    # Ortalama beraberlik payını düşürmek için galibiyet/mağlubiyet aralığı daraltıldı (0.15 -> 0.10)
    rand = np.random.random()
    
    # Ortalama Gol Beklentisi (Lambda Değerleri)
    # Ev sahibi avantajı + Güç farkının küçük bir etkisi eklendi.
    lambda_h_base = 1.6 # Ev sahibi ortalama golü
    lambda_a_base = 1.1 # Deplasman ortalama golü
    
    # Güç farkının etkisini Poisson lambda değerlerine yansıtma (max 0.4 etki)
    effect = np.clip(diff / 50, -0.4, 0.4) 
    lambda_h = lambda_h_base + effect
    lambda_a = lambda_a_base - effect
    
    # KAZANMA DURUMLARI (Daha az agresif)
    if rand < win_prob_h - 0.10: # Ev Sahibi Galibiyet
        score_h = np.random.poisson(lambda_h * 1.1) # Kazanana hafif bonus
        score_a = np.random.poisson(lambda_a * 0.9) # Kaybedene hafif düşüş
        
        # Garanti Galibiyet için (skorlar aynı gelirse)
        if score_h <= score_a: score_h = score_a + 1
        
        return 3, 0, (score_h - score_a)
        
    elif rand > win_prob_h + 0.10: # Deplasman Galibiyeti
        # Ev sahibi ve deplasman lambdaları yer değiştirir (simülasyonun Ev Sahibi bakış açısından)
        score_h = np.random.poisson(lambda_h * 0.9)
        score_a = np.random.poisson(lambda_a * 1.1)
        
        if score_a <= score_h: score_a = score_h + 1
        
        return 0, 3, (score_h - score_a)
        
    else: # Beraberlik (Denge lambda değerleri kullanılır)
        # 0-0, 1-1 gibi düşük skorlu beraberlik olasılığını artırmak için
        lambda_draw = (lambda_h + lambda_a) / 2 * 0.9 
        score = np.random.poisson(lambda_draw)
        return 1, 1, 0

def run_simulation():
    """Ana simülasyon motoru."""
    
    # 1. Canlı Puan Durumunu Çek
    df = get_live_data()
    if df.empty:
        return {"error": "Puan Tablosu Verisi çekilemedi. API key ve kodu kontrol edin."}
    
    # 2. Kalan Fikstürü Çek
    fixtures = get_remaining_fixtures(API_KEY, COMPETITION_CODE)
    
    if not fixtures:
        print("❌ API'den kalan fikstür çekilemedi. Statik fikstür yedek koduna geçiliyor.")
        # Fikstür çekilemezse, statik, daha güvenli yedek fonksiyona geç
        return run_static_fixture_simulation(df)
    
    # Simülasyon sonuçlarını tutacak yapı
    results = {team: {'top8': 0, 'top24': 0, 'eliminated': 0, 'total_points': 0} for team in df['Takım']}
    power_map = df.set_index('Takım')['Güç'].to_dict()

    print(f"✅ Gerçek Fikstür Çekildi. Kalan Maç Sayısı: {len(fixtures)}. Simülasyon Başlatılıyor...")

    # 3. Simülasyonu Gerçek Fikstüre Göre Çalıştır
    for _ in range(SIMULATION_COUNT):
        # Her simülasyon başlangıcında puan tablosunu sıfırla (mevcut puandan başla)
        sim_df = df.copy()
        sim_df['Puan'] = sim_df['Puan'].astype(int) 
        sim_df['Averaj'] = sim_df['Averaj'].astype(int)
        
        # Dictionary'ye çeviriyoruz - daha hızlı ve tip güvenli
        puan_dict = sim_df.set_index('Takım')['Puan'].to_dict()
        averaj_dict = sim_df.set_index('Takım')['Averaj'].to_dict()
        
        for match in fixtures:
            home = match['Ev Sahibi']
            away = match['Deplasman']
            
            power_h = power_map.get(home)
            power_a = power_map.get(away)
            
            if power_h is None or power_a is None:
                continue 
            
            # Maçı simüle et
            points_h, points_a, av_diff = predict_match_score(power_h, power_a)
            
            # Dictionary üzerinden güncelle
            puan_dict[home] = puan_dict[home] + points_h
            averaj_dict[home] = averaj_dict[home] + av_diff
            
            puan_dict[away] = puan_dict[away] + points_a
            averaj_dict[away] = averaj_dict[away] - av_diff
        
        # Dictionary'leri tekrar DataFrame'e çevir
        sim_df['Puan'] = sim_df['Takım'].map(puan_dict)
        sim_df['Averaj'] = sim_df['Takım'].map(averaj_dict)
        
        # Sıralama: Puan -> Averaj
        sim_df = sim_df.sort_values(by=['Puan', 'Averaj'], ascending=[False, False]).reset_index(drop=True)
        
        # İstatistikleri Kaydet
        for real_rank, row in enumerate(sim_df.itertuples(), start=1):
            team = row.Takım
            if team in results:
                results[team]['total_points'] += int(row.Puan)
                
                if real_rank <= 8:
                    results[team]['top8'] += 1
                    results[team]['top24'] += 1
                elif real_rank <= 24:
                    results[team]['top24'] += 1
                else:
                    results[team]['eliminated'] += 1

    # 4. Sonuçları Formatla
    final_data = []
    current_df_indexed = df.set_index('Takım') 
    
    for team, stats in results.items():
        if team not in current_df_indexed.index: continue 

        avg_points = stats['total_points'] / SIMULATION_COUNT
        current_data = current_df_indexed.loc[team] 

        final_data.append({
            'team': team,
            'avg_points': round(avg_points, 1),
            'top8_prob': round((stats['top8'] / SIMULATION_COUNT) * 100, 1),
            'top24_prob': round((stats['top24'] / SIMULATION_COUNT) * 100, 1),
            'elim_prob': round((stats['eliminated'] / SIMULATION_COUNT) * 100, 1),
            'current_points': int(current_data['Puan']),
            'matches_played': int(current_data['Oynanan'])
        })
    
    final_data.sort(key=lambda x: x['top8_prob'], reverse=True)
    return final_data

# --------------------------
# --- YEDEK SİMÜLASYON FONKSİYONU (STATİK FİKSTÜR) ---
# --------------------------

def run_static_fixture_simulation(df):
    """Fikstür API'den veri gelmezse yedek olarak çalışır. 
    Gerçek CL formatına uygun statik bir rakip kümesi simüle eder."""
    
    SIMULATION_COUNT_STATIC = 2000 # Simülasyon sayısı düşürüldü
    teams = df['Takım'].tolist()
    results = {team: {'top8': 0, 'top24': 0, 'eliminated': 0, 'total_points': 0} for team in teams}
    power_map = df.set_index('Takım')['Güç'].to_dict()
    
    print("⚠️ STATİK YEDEK SİMÜLASYON BAŞLATILDI: Sonuçlar gerçek fikstüre dayanmayacaktır.")

    for _ in range(SIMULATION_COUNT_STATIC):
        sim_df = df.copy()
        sim_df['Sim_Puan'] = sim_df['Puan'].astype(int)
        sim_df['Sim_Av'] = sim_df['Averaj'].astype(int)
        
        # Dictionary'ye çeviriyoruz
        puan_dict = sim_df.set_index('Takım')['Sim_Puan'].to_dict()
        averaj_dict = sim_df.set_index('Takım')['Sim_Av'].to_dict()
        oynanan_dict = sim_df.set_index('Takım')['Oynanan'].to_dict()
        
        # Oynanmamış tüm maçlar için bir fikstür oluştur
        temp_fixtures = []
        for home_team in teams:
            matches_played = int(oynanan_dict[home_team])
            remaining = TOTAL_MATCHES - matches_played
            
            if remaining > 0:
                # Olası rakipler: Kendi takımı hariç tüm takımlar
                opponents = [t for t in teams if t != home_team]
                
                # Kalan maç sayısı kadar rastgele rakip seç (statik yaklaşıma göre)
                # Yeni CL formatında rastgele rakiplerle karşılaşılır, bu nedenle bu yaklaşım hala bir tahmindir.
                static_opponents = random.sample(opponents, min(remaining, len(opponents))) 
                
                for opp in static_opponents:
                    temp_fixtures.append({'Ev Sahibi': home_team, 'Deplasman': opp})
        
        # Simülasyonu çalıştır (Oluşturulan statik fikstürün yarısı kadar maç, 
        # çünkü her maç iki takımın da puanını etkilemeli)
        for match in temp_fixtures:
            home = match['Ev Sahibi']
            away = match['Deplasman']
            
            # Eğer takımlardan biri zaten simüle edilmişse atla (iki kere oynanmasın diye)
            if home not in puan_dict or away not in puan_dict: 
                continue
                
            power_h = power_map.get(home)
            power_a = power_map.get(away)
            
            # Maçı simüle et
            points_h, points_a, av_diff = predict_match_score(power_h, power_a)
            
            # Dictionary üzerinden güncelle
            puan_dict[home] = puan_dict[home] + points_h
            averaj_dict[home] = averaj_dict[home] + av_diff
            
            puan_dict[away] = puan_dict[away] + points_a
            averaj_dict[away] = averaj_dict[away] - av_diff
        
        # Dictionary'leri tekrar DataFrame'e çevir
        sim_df['Sim_Puan'] = sim_df['Takım'].map(puan_dict)
        sim_df['Sim_Av'] = sim_df['Takım'].map(averaj_dict)
        sim_df = sim_df.sort_values(by=['Sim_Puan', 'Sim_Av'], ascending=[False, False]).reset_index(drop=True)
        
        for real_rank, row in enumerate(sim_df.itertuples(), start=1):
            team = row.Takım
            results[team]['total_points'] += int(row.Sim_Puan)
            
            if real_rank <= 8:
                results[team]['top8'] += 1
                results[team]['top24'] += 1
            elif real_rank <= 24:
                results[team]['top24'] += 1
            else:
                results[team]['eliminated'] += 1

    # Sonuçları Formatla
    final_data = []
    current_df_indexed = df.set_index('Takım')
    
    for team, stats in results.items():
        if team not in current_df_indexed.index: continue 

        avg_points = stats['total_points'] / SIMULATION_COUNT_STATIC
        current_data = current_df_indexed.loc[team] 

        final_data.append({
            'team': team,
            'avg_points': round(avg_points, 1),
            'top8_prob': round((stats['top8'] / SIMULATION_COUNT_STATIC) * 100, 1),
            'top24_prob': round((stats['top24'] / SIMULATION_COUNT_STATIC) * 100, 1),
            'elim_prob': round((stats['eliminated'] / SIMULATION_COUNT_STATIC) * 100, 1),
            'current_points': int(current_data['Puan']),
            'matches_played': int(current_data['Oynanan'])
        })
    
    final_data.sort(key=lambda x: x['top8_prob'], reverse=True)
    return final_data

# --------------------------
# --- FLASK ROTLARI ---
# --------------------------

@app.route('/')
def home():
    # Bu kısmı çalıştırmak için 'index.html' adında bir şablon dosyanız olmalı.
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    start_time = time.time()
    data = run_simulation()
    end_time = time.time()
    print(f"Simülasyon Süresi: {end_time - start_time:.2f} saniye")
    return jsonify(data)

if __name__ == '__main__':
    print("Sunucu Başlatılıyor: http://127.0.0.1:5000")
    # debug=True'yu production ortamında kapatmayı unutmayın.
    app.run(debug=True, use_reloader=False)