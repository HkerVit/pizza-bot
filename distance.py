from geopy import distance
from textwrap import dedent


def get_min_distance(lon, lat, pizzerias):
    user_distances = []
    for pizzeria in pizzerias:
        pizzeria_coordinate = (float(pizzeria['lat']), float(pizzeria['lon']))
        user_distances.append({
            'name': pizzeria['alias'],
            'address': pizzeria['address'],
            'lat': float(pizzeria['lat']),
            'lon': float(pizzeria['lon']),
            'client_lat': lat,
            'client_lon': lon,
            'distance': distance.distance(pizzeria_coordinate, (lat, lon)).km,
            'deliveryman': pizzeria['deliveryman']
        })
    closest_pizzeria = min(user_distances, key=get_user_distance)

    return closest_pizzeria

def get_user_distance(user_distances):
    return user_distances['distance']