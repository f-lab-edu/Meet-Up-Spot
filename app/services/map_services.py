import logging
from dataclasses import asdict
from functools import wraps
from typing import List

import googlemaps
from sqlalchemy.orm import Session

from app import crud
from app.core.config import get_app_settings
from app.models.user import User
from app.schemas.google_maps_api import (
    DistanceInfo,
    DistanceMatrixRequest,
    GeocodeResponse,
    ReverseGeocodeResponse,
)
from app.schemas.google_maps_api_log import GoogleMapsApiLogCreate
from app.schemas.location import Location, LocationBase, LocationCreate
from app.schemas.place import AutoCompletedPlace, Place, PlaceCreate
from app.services.constants import (
    GOOGLE_MAPS_URL,
    PLACETYPE,
    MapsFunction,
    Radius,
    RankBy,
    StatusDetail,
    TravelMode,
)
from app.services.redis_services import RedisServicesFactory

settings = get_app_settings()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZeroResultException(Exception):
    pass


class CustomException(Exception):
    pass


class NoAddressException(Exception):
    pass


def add_api_request_log(api_call):
    @wraps(api_call)
    def wrapper(self, db, user, *args, **kwargs):
        try:
            results = api_call(self, db, user, *args, **kwargs)
            if not results or (
                (
                    type(results) == dict
                    and results.get("status") == StatusDetail.ZERO_RESULTS.name
                )
            ):
                raise ZeroResultException(
                    {"status": 204, "detail": StatusDetail.ZERO_RESULTS.value}
                )

            if api_call.__name__ == MapsFunction.CALCULATE_DISTANCE_MATRIX:
                for result in results:
                    if result.origin is None:
                        raise NoAddressException(
                            {
                                "status": 400,
                                "detail": StatusDetail.INVALID_REQUEST.value,
                            }
                        )
                    elif result.distance_value is None or result.duration_value is None:
                        raise ZeroResultException(
                            {"status": 204, "detail": StatusDetail.ZERO_RESULTS.value}
                        )

            return results
        except Exception as error:
            crud.google_maps_api_log.create(
                db,
                obj_in=GoogleMapsApiLogCreate(
                    request_url=GOOGLE_MAPS_URL[api_call.__name__],
                    status_code=400,
                    reason=str(error),
                    payload=str(args) + "," + str(kwargs),
                    print_result=str(error),
                    user_id=user.id,
                ),
            )
            raise error

    return wrapper


class MapAdapter:
    def __init__(self, client=None, db=None):
        self.client = client
        self.db = db

    def format_destinations(self, destinations: List[str] | str):
        if isinstance(destinations, str):
            return [f"place_id:{place_id}" for place_id in [destinations]]
        elif isinstance(destinations, list):
            return [f"place_id:{place_id}" for place_id in destinations]
        else:
            raise TypeError("destinations must be a list or string")

    @add_api_request_log
    def geocode_address(self, db, user, address):
        return self.client.geocode(address)

    @add_api_request_log
    def reverse_geocode(self, db, user, latitude, longitude):
        return self.client.reverse_geocode((latitude, longitude))

    @add_api_request_log
    def search_nearby_places(
        self,
        db,
        user,
        latitude,
        longitude,
        radius=Radius.FIRST_RADIUS.value,
        language="ko",
        place_type: PLACETYPE = PLACETYPE.TRANSIT_STATION,
        rank_by: RankBy = RankBy.PROMINENCE,
    ) -> List[dict]:
        return self.client.places_nearby(
            location=(latitude, longitude),
            radius=radius if rank_by == RankBy.PROMINENCE else None,
            language=language,
            type=place_type.value,
            rank_by=rank_by.value,
        )

    @add_api_request_log
    def auto_complete_place(
        self, db, user, text: str, location: LocationBase = None, language="ko"
    ) -> List[dict]:
        res = self.client.places_autocomplete(
            text,
            language=language,
            location=f"{location.latitude}, {location.longitude}" if location else None,
            radius=Radius.AUTO_COMPLETE_RADIUS.value if location else None,
        )
        return res

    @add_api_request_log
    def get_place_detail(self, db, user, place_id: str):
        return self.client.place(place_id=place_id)

    @add_api_request_log
    def calculate_distance_matrix(
        self,
        db,
        user,
        **kwargs,
    ) -> List[DistanceInfo]:
        origins = kwargs["origins"]
        destinations = (
            kwargs["destinations"]
            if isinstance(kwargs["destinations"], list)
            else [kwargs["destinations"]]
        )
        mode: TravelMode = kwargs["mode"]
        language = kwargs["language"]
        is_place_id = kwargs["is_place_id"]

        matrix = self.client.distance_matrix(
            origins=origins,
            destinations=self.format_destinations(destinations)
            if is_place_id
            else destinations,
            mode=mode.value,
            language=language,
        )

        distances = []
        for row_idx, row in enumerate(matrix["rows"]):
            for ele_idx, element in enumerate(row["elements"]):
                if element["status"] != "OK":
                    distances.append(
                        DistanceInfo(
                            origin=matrix["origin_addresses"][row_idx],
                            destination=matrix["destination_addresses"][ele_idx],
                            destination_id=destinations[ele_idx]
                            if is_place_id
                            else None,
                            distance_text=None,
                            distance_value=None,
                            duration_text=None,
                            duration_value=None,
                        )
                    )
                    continue

                distances.append(
                    DistanceInfo(
                        origin=matrix["origin_addresses"][row_idx],
                        destination=matrix["destination_addresses"][ele_idx],
                        destination_id=destinations[ele_idx] if is_place_id else None,
                        distance_text=element["distance"]["text"],
                        distance_value=element["distance"]["value"],
                        duration_text=element["duration"]["text"],
                        duration_value=element["duration"]["value"],
                    )
                )
        return distances


class MapServices:
    def __init__(self, map_client):
        self._map_client = map_client
        self._map_adapter = MapAdapter(map_client)
        self.max_results = 20

    @property
    def map_adapter(self):
        return self._map_adapter

    def _extract_lat_lngs_from_results(self, results):
        return [
            (res["geometry"]["location"]["lat"], res["geometry"]["location"]["lng"])
            for res in results
        ]

    def _create_new_locations_from_result(self, results):
        return [
            LocationCreate(
                latitude=result["geometry"]["location"]["lat"],
                longitude=result["geometry"]["location"]["lng"],
                compound_code=result["plus_code"]["compound_code"],
                global_code=result["plus_code"]["global_code"],
            )
            for result in results
        ]

    def create_or_get_locations(self, db, results) -> Location:
        results_lat_lngs = self._extract_lat_lngs_from_results(results)

        existing_locations = crud.location.get_by_latlng_list(
            db, latlng_list=results_lat_lngs
        )

        existing_lat_lngs = {
            (location.latitude, location.longitude) for location in existing_locations
        }

        new_results = [
            result
            for result in results
            if (
                result["geometry"]["location"]["lat"],
                result["geometry"]["location"]["lng"],
            )
            not in existing_lat_lngs
        ]

        new_locations = self._create_new_locations_from_result(new_results)

        if new_locations:
            crud.location.bulk_insert(
                db, [location.model_dump() for location in new_locations]
            )
            lat_lngs = [(loc.latitude, loc.longitude) for loc in new_locations]
            new_locations = crud.location.get_by_latlng_list(db, latlng_list=lat_lngs)

        return existing_locations + new_locations

    def _create_new_places_from_results(self, results, location_ids_map) -> List[Place]:
        return [
            PlaceCreate(
                place_id=result["place_id"],
                name=result["name"],
                address=result["vicinity"],
                user_ratings_total=result.get("user_ratings_total", 0),
                rating=result.get("rating", 0),
                place_types=result["types"],
                location_id=location_ids_map[
                    (
                        result["geometry"]["location"]["lat"],
                        result["geometry"]["location"]["lng"],
                    )
                ],
            )
            for result in results
        ]

    def create_or_get_places(self, db, results, location_ids_map) -> List[Place]:
        results_place_ids = [result["place_id"] for result in results]
        existing_places = crud.place.get_by_place_ids(db, place_ids=results_place_ids)

        existing_place_ids = {place.place_id for place in existing_places}
        new_results = [
            result for result in results if result["place_id"] not in existing_place_ids
        ]

        new_places = self._create_new_places_from_results(new_results, location_ids_map)

        if new_places:
            crud.place.bulk_insert(db, [place.model_dump() for place in new_places])
            new_places = crud.place.get_by_place_ids(
                db, place_ids=[place.place_id for place in new_places]
            )

        return existing_places + new_places

    def process_nearby_places_results(
        self, db: Session, user: User, results: List[dict]
    ) -> List[Place]:
        locations = self.create_or_get_locations(db, results)
        location_ids_map = {(loc.latitude, loc.longitude): loc.id for loc in locations}

        places = self.create_or_get_places(db, results, location_ids_map)

        return places[: self.max_results]

    def get_lat_lng_from_address(
        self, db: Session, user: User, address: str
    ) -> GeocodeResponse:
        redis_services = RedisServicesFactory.create_redis_services()
        cached_coordinates = redis_services.get_cached_address_coordinates(address)

        if cached_coordinates:
            logger.info("Successfully cached Geocoding API response in Redis.")
            return GeocodeResponse(
                latitude=cached_coordinates["latitude"],
                longitude=cached_coordinates["longitude"],
            )

        results = self._map_adapter.geocode_address(db, user, address)

        location = results[0]["geometry"]["location"]

        redis_services.cache_address_coordinates(
            address, location["lat"], location["lng"]
        )

        return GeocodeResponse(latitude=location["lat"], longitude=location["lng"])

    def get_address_from_lat_lng(
        self, db: Session, user: User, latitude: float, longitude: float
    ) -> str:
        result = self._map_adapter.reverse_geocode(db, user, latitude, longitude)

        return ReverseGeocodeResponse(address=result[0]["formatted_address"])

    def get_geocoded_addresses(self, db, user, aaddresses):
        return [
            self.get_lat_lng_from_address(db, user, address) for address in aaddresses
        ]

    def get_nearby_places(
        self,
        db: Session,
        user: User,
        latitude: float,
        longitude: float,
        radius=Radius.FIRST_RADIUS.value,
        language="ko",
        place_type=PLACETYPE.TRANSIT_STATION,
    ) -> List[Place]:
        """
        주변 지역 검색 API 요청
        """
        redis_services = RedisServicesFactory.create_redis_services()

        response = self._map_adapter.search_nearby_places(
            db,
            user,
            latitude,
            longitude,
            radius=radius,
            place_type=place_type,
            language="ko",
        )
        results = response["results"]

        if redis_services.cache_nearby_places_response(latitude, longitude, results):
            logger.info(
                "Successfully cached search_nearby_places API response in Redis."
            )
        if redis_services.add_location_to_redis(latitude, longitude):
            logger.info("Successfully cached geolocation in Redis.")

        return self.process_nearby_places_results(db, user, results)

    def get_complete_addresses(
        self, db: Session, user: User, addresses: List[str]
    ) -> List[str]:
        complete_addresses = []
        for address in addresses:
            complete_addresses.append(
                self.get_auto_completed_place(db, user, address)[0].address
            )
        return complete_addresses

    def get_auto_completed_place(
        self, db: Session, user: User, text: str, location: LocationBase = None
    ) -> List[AutoCompletedPlace]:
        results = self._map_adapter.auto_complete_place(db, user, text, location)

        return [
            AutoCompletedPlace(
                address=prediction["description"],
                main_address=prediction["structured_formatting"]["main_text"],
                secondary_address=prediction["structured_formatting"]["secondary_text"],
                place_id=prediction["place_id"],
            )
            for prediction in results
        ]

    # TODO: 현재는 transit만 됨
    def get_distance_matrix_for_places(
        self,
        db: Session,
        user: User,
        origins: str | List[str],
        destinations: str | List[str],
        mode: TravelMode = TravelMode.TRANSIT,
        is_place_id: bool = True,
    ) -> List[DistanceInfo]:
        """
        origins: list of origins
        destination: single destination
        mode: "driving", "walking", or "transit"
        language: language in which to return results, default is "ko"
        """

        # Ensure the selected mode is valid
        if mode not in ["driving", "walking", "transit", "bicycling"]:
            raise ValueError(
                "Invalid mode selected. Choose between 'driving', 'walking', or 'transit'."
            )
        params = DistanceMatrixRequest(
            origins=origins,
            destinations=destinations,
            mode=TravelMode[mode.upper()]
            if mode.upper() in [keys for keys in TravelMode.__members__]
            else TravelMode.TRANSIT,
            language="ko",
            is_place_id=is_place_id,
        )
        distances: List[DistanceInfo] = self._map_adapter.calculate_distance_matrix(
            db, user, **asdict(params)
        )

        return distances


class MapServicesFactory:
    @staticmethod
    def create_map_services(map_client=None):
        if map_client is None:
            map_client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        return MapServices(map_client=map_client)
