import json
import requests
from datetime import datetime
import time

def fetch_stablecoin_data():
    print("Fetching stablecoin data from DefiLlama...")
    
    # Fetch current stablecoins
    print("1. Fetching current stablecoins list...")
    stable_res = requests.get('https://stablecoins.llama.fi/stablecoins?includePrices=true')
    stable_data = stable_res.json()
    
    # Sort by circulating and get top 10
    sorted_stables = sorted(
        [s for s in stable_data['peggedAssets'] if s.get('circulating', {}).get('peggedUSD', 0) > 0],
        key=lambda x: x.get('circulating', {}).get('peggedUSD', 0),
        reverse=True
    )
    
    top10 = sorted_stables[:10]
    top10_symbols = [s['symbol'] for s in top10]
    top10_ids = [s['id'] for s in top10]
    
    print(f"   Top 10: {top10_symbols}")
    
    # Calculate others total
    others_total = sum(
        s.get('circulating', {}).get('peggedUSD', 0) 
        for s in sorted_stables[10:]
    )
    
    # Prepare pie data
    pie_data = [
        {
            'name': s['symbol'],
            'value': s.get('circulating', {}).get('peggedUSD', 0),
            'fullName': s['name']
        }
        for s in top10
    ]
    pie_data.append({
        'name': '기타',
        'value': others_total,
        'fullName': '기타 스테이블코인'
    })
    
    # Fetch historical data for each stablecoin
    print("2. Fetching historical data for each stablecoin...")
    historical_by_coin = {}
    
    for i, (coin_id, symbol) in enumerate(zip(top10_ids, top10_symbols)):
        print(f"   Fetching {symbol} ({i+1}/10)...")
        try:
            res = requests.get(f'https://stablecoins.llama.fi/stablecoin/{coin_id}')
            data = res.json()
            tokens = data.get('tokens', [])
            historical_by_coin[symbol] = {
                item['date']: item.get('circulating', {}).get('peggedUSD', 0)
                for item in tokens
            }
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"   Error fetching {symbol}: {e}")
            historical_by_coin[symbol] = {}
    
    # Fetch total historical data
    print("3. Fetching total historical data...")
    total_hist_res = requests.get('https://stablecoins.llama.fi/stablecoincharts/all')
    total_hist_data = total_hist_res.json()
    
    # Process and combine data
    print("4. Processing data...")
    date_map = {}
    
    # Get all unique dates from total history
    for item in total_hist_data:
        date = item['date']
        total = item.get('totalCirculating', {}).get('peggedUSD', 0)
        if total > 0:
            date_map[date] = {
                'date': date,
                'total': total
            }
    
    # Add individual stablecoin data
    for symbol, history in historical_by_coin.items():
        for date, value in history.items():
            if date in date_map:
                date_map[date][symbol] = value
    
    # Calculate "기타" for each date
    for date, data in date_map.items():
        top10_sum = sum(data.get(sym, 0) for sym in top10_symbols)
        data['기타'] = max(0, data['total'] - top10_sum)
    
    # Group by month
    monthly_map = {}
    for date, data in date_map.items():
        date_obj = datetime.fromtimestamp(date)
        month_key = date_obj.strftime('%Y-%m')
        month_label = date_obj.strftime('%b %Y')
        
        # Keep the latest entry for each month
        if month_key not in monthly_map or date > monthly_map[month_key]['date']:
            monthly_map[month_key] = {
                **data,
                'monthLabel': month_label
            }
    
    # Sort by date
    historical_data = sorted(monthly_map.values(), key=lambda x: x['date'])
    
    # Create final output
    output = {
        'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M UTC'),
        'topStablecoins': top10_symbols,
        'pieData': pie_data,
        'historicalData': historical_data
    }
    
    # Save to file
    print("5. Saving to data.json...")
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("Done!")
    print(f"   Total stablecoins in pie: {len(pie_data)}")
    print(f"   Historical data points: {len(historical_data)}")
    
    return output

if __name__ == '__main__':
    fetch_stablecoin_data()
