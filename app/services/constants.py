from enum import Enum


class PLACETYPE(str, Enum):
    AMUSEMENT_PARK = "amusement_park"
    AQUARIUM = "aquarium"
    ART_GALLERY = "art_gallery"
    BAKERY = "bakery"
    BAR = "bar"
    BOOK_STORE = "book_store"
    BUS_STATION = "bus_station"
    CAFE = "cafe"
    CITY_HALL = "city_hall"
    CONVENIENCE_STORE = "convenience_store"
    DEPARTMENT_STORE = "department_store"
    LIBRARY = "library"
    LOCAL_GOVERNMENT_OFFICE = "local_government_office"
    MOVIE_THEATER = "movie_theater"
    MUSEUM = "museum"
    NIGHT_CLUB = "night_club"
    PARK = "park"
    PARKING = "parking"
    RESTAURANT = "restaurant"
    SHOE_STORE = "shoe_store"
    SHOPPING_MALL = "shopping_mall"
    STADIUM = "stadium"
    STORAGE = "storage"
    STORE = "store"
    SUBWAY_STATION = "subway_station"
    SUPERMARKET = "supermarket"
    TOURIST_ATTRACTION = "tourist_attraction"
    TRAIN_STATION = "train_station"
    TRANSIT_STATION = "transit_station"


GOOGLE_MAPS_URL = {
    "geocode_address": "https://maps.googleapis.com/maps/api/geocode/json",
    "reverse_geocode": "https://maps.googleapis.com/maps/api/geocode/json",
    "auto_complete_place": "https://maps.googleapis.com/maps/api/place/autocomplete/json",
    "search_nearby_places": "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
    "get_place_detail": "https://maps.googleapis.com/maps/api/place/details/json",
    "calculate_distance_matrix": "https://maps.googleapis.com/maps/api/distancematrix/json",
}


class StatusDetail(str, Enum):
    OK = "OK"
    ZERO_RESULTS = "결과를 찾을 수 없습니다."
    OVER_DAILY_LIMIT = "API 키가 누락되었거나 잘못되었습니다."
    OVER_QUERY_LIMIT = "할당량이 초과되었습니다."
    REQUEST_DENIED = "요청이 거부되었습니다."
    INVALID_REQUEST = "입력값이 누락되었습니다."
    UNKNOWN_ERROR = "서버 내부 오류가 발생했습니다."


class MapsFunction(str, Enum):
    GEOCODE_ADDRESS = "geocode_address"
    REVERSE_GEOCODE = "reverse_geocode"
    AUTO_COMPLETE_PLACE = "auto_complete_place"
    SEARCH_NEARBY_PLACES = "search_nearby_places"
    GET_PLACE_DETAIL = "get_place_detail"
    CALCULATE_DISTANCE_MATRIX = "calculate_distance_matrix"


class TravelMode(str, Enum):
    DRIVING = "driving"
    WALKING = "walking"
    BICYCLING = "bicycling"
    TRANSIT = "transit"


class TrafficModel(str, Enum):
    BEST_GUESS = "best_guess"
    PESSIMISTIC = "pessimistic"
    OPTIMISTIC = "optimistic"


class TransitMode(str, Enum):
    BUS = "bus"
    SUBWAY = "subway"
    TRAIN = "train"
    TRAM = "tram"
    RAIL = "rail"


class TransitRoutingPreference(str, Enum):
    LESS_WALKING = "less_walking"
    FEWER_TRANSFERS = "fewer_transfers"


class Radius(Enum):
    FIRST_RADIUS = 10000
    SECOND_RADIUS = 25000
    THIRD_RADIUS = 50000


class RankBy(Enum):
    PROMINENCE = "prominence"
    DISTANCE = "distance"


class AGGREGATED_ATTR(str, Enum):
    DISTANCE = "distance_value"
    DURATION = "duration_value"
