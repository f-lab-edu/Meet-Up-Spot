import json
import logging
from typing import Dict, List, Optional

import redis

from app.core.config import get_app_settings
from app.services.constants import GEOHASH_PRECISION, REDIS_EXPIRE_TIME, RedisKey
from app.utils import geohash_decode, geohash_encode

settings = get_app_settings()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class RedisOperationError(Exception):
    pass


class RedisClientFactory:
    redis_pool = redis.ConnectionPool(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0
    )

    @staticmethod
    def create_redis_client() -> redis.Redis:
        return redis.StrictRedis(connection_pool=RedisClientFactory.redis_pool)


class RedisServices:
    def __init__(self, redis_client: redis.Redis):
        self._redis_client = redis_client

    @property
    def redis_client(self) -> redis.Redis:
        return self._redis_client

    def cache_address_coordinates(
        self, address: str, latitude: float, longitude: float
    ) -> bool:
        try:
            location_geohash = geohash_encode(
                latitude, longitude, precision=GEOHASH_PRECISION
            )

            return (
                self._redis_client.set(address, location_geohash, ex=REDIS_EXPIRE_TIME)
                > 0
            )  # 캐시 유효 시간은 1시간으로
        except redis.RedisError as error:
            logger.error(
                f"Error caching address coordinates in Redis: {error}", exc_info=True
            )
            raise RedisOperationError("주소 좌표를 Redis에 캐싱하는 요청을 실패했습니다.") from error

    def get_cached_address_coordinates(
        self, address: str
    ) -> Optional[Dict[str, float]]:
        try:
            location_geohash = self._redis_client.get(address)
            if location_geohash:
                latitude, longitude = geohash_decode(location_geohash.decode("utf-8"))

                return {"latitude": float(latitude), "longitude": float(longitude)}
            return None
        except redis.RedisError as error:
            logger.error(
                f"Error retrieving cached address coordinates from Redis: {error}",
                exc_info=True,
            )
            raise RedisOperationError("Redis에서 캐시된 주소 좌표를 검색하는 요청을 실패했습니다.") from error

    def add_location_to_redis(self, latitude: float, longitude: float) -> bool:
        try:
            location_geohash = geohash_encode(latitude, longitude)

            self._redis_client.geoadd(
                RedisKey.GEOLOCATIONS_KEY.value, (longitude, latitude, location_geohash)
            )
            return location_geohash
        except redis.RedisError as error:
            logger.error(f"Error adding location to Redis: {error}", exc_info=True)
            raise RedisOperationError("geolocations 캐싱하는 요청을 실패했습니다.") from error

    def find_geohashes_in_radius(
        self, latitude: float, longitude: float, radius_m: float
    ) -> Optional[List[str]]:
        try:
            geohashes = self._redis_client.geosearch(
                RedisKey.GEOLOCATIONS_KEY.value,
                longitude=longitude,
                latitude=latitude,
                radius=radius_m,
                unit="m",
            )

            return geohashes
        except redis.RedisError as error:
            logger.error(
                f"Error retrieving geohashes from Redis: {error}", exc_info=True
            )
            raise RedisOperationError("캐시된 범위내 geolocations을 요청을 실패했습니다.") from error

    def cache_nearby_places_response(
        self, latitude: float, longitude: float, results: List[Dict]
    ) -> bool:
        # NOTE:일단은 정밀도는 5를 사용
        location_geohash = geohash_encode(latitude, longitude)
        results_json = json.dumps(results)
        try:
            return (
                self._redis_client.set(
                    location_geohash, results_json, ex=REDIS_EXPIRE_TIME
                )
                > 0
            )
        except redis.RedisError as error:
            logger.error(f"Error caching API response in Redis: {error}", exc_info=True)
            raise RedisOperationError("API 응답을 Redis에 캐싱하는 요청을 실패했습니다.") from error

    def get_cached_nearby_places_responses(
        self, geohashes: List[str]
    ) -> Optional[List[Dict]]:
        try:
            results_json = self._redis_client.mget(geohashes)
            responses = []

            for item in results_json:
                if item:
                    responses.append(json.loads(item.decode("utf-8")))
                else:
                    continue

            return responses
        except redis.RedisError as error:
            logger.error(
                f"Error retrieving cached API responses for geohashes from Redis: {error}",
                exc_info=True,
            )
            raise RedisOperationError("Redis에서 캐시된 응답을 검색하는 요청을 실패했습니다.") from error


class RedisServicesFactory:
    @staticmethod
    def create_redis_services(
        redis_client: Optional[redis.Redis] = None,
    ) -> RedisServices:
        if redis_client is None:
            redis_client = RedisClientFactory.create_redis_client()
        return RedisServices(redis_client=redis_client)
