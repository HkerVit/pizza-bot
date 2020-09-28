from geopy import distance
from textwrap import dedent


def get_min_distance(lon, lat, pizzerias):
    user_distances = []
    for pizzeria in pizzerias:
        pizzeria_coordinate = (float(pizzeria['lat']), float(pizzeria['lon']))
        user_distances.append({
            'name': pizzeria['alias'],
            'address': pizzeria['address'],
            'distance': distance.distance(pizzeria_coordinate, (lat, lon)).km
        })
    
    closest_pizzeria = min(user_distances, key=get_user_distance)
    reply_text = create_distance_reply(closest_pizzeria)
    
    return reply_text

def get_user_distance(user_distances):
    return user_distances['distance']


def create_distance_reply(pizzeria):
    address = pizzeria['address']
    if pizzeria['distance'] <= 0.5:
        distance = int(pizzeria['distance'] * 1000)
        return dedent(f'''
        Может заберёте пиццу из нашей пиццерии неподалеку? 
        Она всего в {distance} метров от Вас! Вот ее адрес: {address}. 
        Но можем доставить и бесплатно! Нам не сложно)''')

    elif pizzeria['distance'] <= 5:
        return dedent('''
        Похоже придется ехать до Вас на самокате. 
        Доставка будет стоить 100 руб. 
        Доставляем или самовывоз?''')

    elif pizzeria['distance'] <= 20:
        return dedent(f'''
        Вы довольно далеко от нас. Ближайшая к вам пиццерия
        находится по адресу: {address}. Доставка будет стоить 300 руб.
        Но Вы можете забрать пиццу самостоятельно)
        ''')
    else:
        distance = int(pizzeria['distance'])
        return dedent(f'''
        К сожалению Вы находитесь далеко от нас,
        Ближайшая пиццерия аж в {distance} км от Вас!
        ''')


if __name__ == "__main__":
    pass