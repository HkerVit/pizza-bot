from geopy import distance
from textwrap import dedent
import json


def get_closest_pizzeria(lon, lat, pizzerias):
    for pizzeria in pizzerias:
        pizzeria_coordinate = (pizzeria['latitude'], pizzeria['longitude'])
        pizzeria_distance = distance.distance(pizzeria_coordinate, (lat, lon)).km
        pizzeria['distance'] = pizzeria_distance

    closest_pizzeria = min(pizzerias, key=get_distance)
    closest_pizzeria['customer_lon'] = lon
    closest_pizzeria['customer_lat'] = lat

    return closest_pizzeria

def get_distance(pizzerias):
    return pizzerias['distance']