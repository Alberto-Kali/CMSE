import requests

class TravelService:
    def __init__(self, token=None):
        """
        Инициализация сервиса путешествий.
        
        :param token: Ваш партнерский токен (если есть).
        """
        self.token = token

    def get_hotel_price(self, location, check_in, check_out, currency='rub', adults=2, limit=10):
        """
        Получает информацию о ценах на проживание в отелях в указанном городе.

        :param location: Имя локации (город).
        :param check_in: Дата заселения (в формате YYYY-MM-DD).
        :param check_out: Дата выселения (в формате YYYY-MM-DD).
        :param currency: Валюта ответа (по умолчанию 'rub').
        :param adults: Количество гостей (по умолчанию 2).
        :param limit: Количество отелей (по умолчанию 10).
        :return: Ответ от API с информацией о ценах на отели.
        """
        url = "https://engine.hotellook.com/api/v2/cache.json"
        
        # Параметры запроса
        params = {
            'location': location,
            'checkIn': check_in,
            'checkOut': check_out,
            'currency': currency,
            'adults': adults,
            'limit': limit
        }
        
        if self.token:
            params['token'] = self.token

        # Выполнение запроса
        response = requests.get(url, params=params)
        # Проверка на успешный ответ
        if response.status_code == 200:
            hotels = response.json()
            if hotels:
                average_price = sum(hotel['priceAvg'] for hotel in hotels) / len(hotels)
                return average_price
            else:
                return "Нет доступных отелей."
        else:
            return f"Ошибка при запросе: {response.status_code} - {response.text}"

    def get_transport_price(self, from_station, to_station, check_out, api_key):
        """
        Получает стоимость перемещения из одного города в другой.
        
        :param from_station: Станция отправления.
        :param to_station: Станция назначения.
        :param date: Дата поездки.
        :param api_key: API ключ для доступа к сервису.
        :return: Стоимость перемещения или сообщение о том, что сервисы ещё не настроены.
        """
        return "Сервисы ещё не настроены"


# API РАЗНЫХ ИСТОЧНИКОВ ДАННЫХ О МАРШРУТАХ

"""
import requests
import zipfile
import os
import pandas as pd

def download_and_extract_csv(url, extract_to='.'):
    # Скачиваем ZIP-архив
    response = requests.get(url)
    zip_file_path = 'routes.zip'
    
    with open(zip_file_path, 'wb') as f:
        f.write(response.content)

    # Распаковываем ZIP-архив
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    # Удаляем ZIP-файл после распаковки
    os.remove(zip_file_path)

def load_station_data(csv_file):
    # Загружаем данные из CSV в DataFrame
    df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
    return df

def get_station_code(station_name, df):
    # Ищем ID станции по названию
    station_name = station_name.lower()  # Приводим к нижнему регистру для сравнения
    for index, row in df.iterrows():
        if station_name in row['departure_station_name'].lower():
            return row['departure_station_id']
    return None

def get_train_price(departure_station, arrival_station):
    # URL для скачивания CSV файла
    csv_url = "https://support.travelpayouts.com/hc/article_attachments/360031345731/tutu_routes.csv.zip"
    
    # Скачиваем и распаковываем файл
    download_and_extract_csv(csv_url)

    # Загружаем данные о станциях
    df = load_station_data('tutu_routes.csv')

    # Получаем коды станций
    term = get_station_code(departure_station, df)
    term2 = get_station_code(arrival_station, df)

    # Проверяем, были ли найдены коды станций
    if term is None:
        print(f"Станция отправления '{departure_station}' не найдена.")
        return
    if term2 is None:
        print(f"Станция назначения '{arrival_station}' не найдена.")
        return

    # Формируем запрос к API
    url = f"https://suggest.travelpayouts.com/search?service=tutu_trains&term={term}&term2={term2}"
    
    # Отправляем запрос
    response = requests.get(url)
    
    # Обрабатываем ответ
    if response.status_code == 200:
        data = response.json()
        if data != []:
            trips = data.get('trips', [])
        else:
            print("Нет доступных поездов.")
            return
        
        # Если есть доступные поездки
        if trips:
            for trip in trips:
                print(f"Поезд: {trip['trainNumber']}")
                for category in trip['categories']:
                    print(f"Тип: {category['type']}, Цена: {category['price']} руб.")
        else:
            print("Нет доступных поездов.")
    else:
        print("Ошибка при получении данных.")

# Пример использования
get_train_price("Воронеж", "Москва")








import requests

def get_stations_list(api_key, lang='ru_RU', format='json'):
    '''
    Получает список всех доступных станций из Яндекс Расписаний.

    :param api_key: Ключ доступа к API Яндекс Расписаний.
    :param lang: Язык возвращаемой информации (по умолчанию 'ru_RU').
    :param format: Формат ответа (по умолчанию 'json').
    :return: Список всех станций с их информацией или None в случае ошибки.
    '''
    url = "https://api.rasp.yandex.net/v3.0/stations_list/"
    
    # Параметры запроса
    params = {
        'apikey': api_key,
        'lang': lang,
        'format': format
    }

    # Выполнение запроса
    response = requests.get(url, params=params)
    
    # Проверка на успешный ответ
    if response.status_code == 200:
        data = response.json()
        stations = []

        # Извлечение информации о станциях
        for country in data.get('countries', []):
            for region in country.get('regions', []):
                for settlement in region.get('settlements', []):
                    for station in settlement.get('stations', []):
                        station_info = {
                            'country': country.get('title'),
                            'region': region.get('title'),
                            'settlement': settlement.get('title'),
                            'station_title': station.get('title'),
                            'station_type': station.get('station_type'),
                            'transport_type': station.get('transport_type'),
                            'latitude': station.get('latitude'),
                            'longitude': station.get('longitude'),
                            'yandex_code': station['codes'].get('yandex_code')
                        }
                        stations.append(station_info)
        
        return stations
    else:
        print(f"Ошибка при запросе: {response.status_code} - {response.text}")
        return None

# Пример использования функции
if __name__ == "__main__":
    api_key = "YOUR_API_KEY"  # Замените на ваш ключ API
    stations = get_stations_list(api_key)

    if stations:
        for station in stations[:10]:  # Печатаем первые 10 станций для примера
            print(f"Станция: {station['station_title']}, "
                  f"Тип: {station['station_type']}, "
                  f"Тип транспорта: {station['transport_type']}, "
                  f"Широта: {station['latitude']}, "
                  f"Долгота: {station['longitude']}, "
                  f"Код Яндекса: {station['yandex_code']}, "
                  f"Населенный пункт: {station['settlement']}, "
                  f"Регион: {station['region']}, "
                  f"Страна: {station['country']}")







import requests

def get_yandex_trip_cost(from_station, to_station, date, api_key):
    '''
    Получает стоимость перемещения из одного города в другой.

    :param from_station: Код станции отправления.
    :param to_station: Код станции прибытия.
    :param date: Дата поездки (в формате YYYY-MM-DD).
    :param api_key: Ключ доступа к API Яндекс Расписаний.
    :return: Список доступных рейсов и их стоимости.
    '''
    url = "https://api.rasp.yandex.net/v3.0/search/"
    
    # Параметры запроса
    params = {
        'apikey': api_key,
        'format': 'json',
        'from': from_station,
        'to': to_station,
        'date': date,
        'lang': 'ru_RU',
        'limit': 10  # Ограничение на количество рейсов
    }

    # Выполнение запроса
    response = requests.get(url, params=params)
    # Проверка на успешный ответ
    if response.status_code == 200:
        data = response.json()
        trips = data.get('segments', [])
        
        # Извлечение информации о стоимости
        trip_costs = []
        for trip in trips:
            if 'tickets_info' in trip:
                for place in trip['tickets_info'].get('places', []):
                    price = place['price']
                    currency = place['currency']
                    trip_costs.append({
                        'trip': trip['thread']['title'],
                        'price': f"{price['whole']} {currency}",
                        'departure': trip['departure'],
                        'arrival': trip['arrival'],
                        'has_transfers': trip['has_transfers']
                    })
        
        return trip_costs
    else:
        print(f"Ошибка при запросе: {response.status_code} - {response.text}")
        return None

# Пример использования функции
if 0==0:
    api_key = "6d569e0f-df8b-4c92-8e64-4a7997e0c6ae"  # Замените на ваш ключ API
    from_station = "c146"  # Код станции отправления (например, Симферополь) в системе IATA
    to_station = "c213"  # Код станции прибытия (например, Москва) в системе IATA
    date = "2024-12-20"  # Дата поездки

    trip_costs = get_yandex_trip_cost(from_station, to_station, date, api_key)
    #print(trip_costs)
    if trip_costs:
        for trip in trip_costs:
            print(f"Рейс: {trip['trip']}, Стоимость: {trip['price']}, "
                  f"Дата отправления: {trip['departure']}, "
                  f"Дата прибытия: {trip['arrival']}, "
                  f"Пересадки: {'Да' if trip['has_transfers'] else 'Нет'}")
"""