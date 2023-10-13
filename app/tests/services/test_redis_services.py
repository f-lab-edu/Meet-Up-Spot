from unittest import TestCase
from unittest.mock import Mock

from app.services.constants import RedisKey
from app.services.redis_services import RedisOperationError, RedisServicesFactory


class RedisServicesTest(TestCase):
    def setUp(self):
        self.redis_service = RedisServicesFactory.create_redis_services()
        self.redis_client = self.redis_service.redis_client
        self.mock_redis_client = Mock()
        self.mock_redis_service = RedisServicesFactory.create_redis_services(
            self.mock_redis_client
        )
        self.redis_client.flushdb()

    def test_add_location_to_redis(self):
        assert len(self.redis_client.keys("*")) == 0
        result = self.redis_service.add_location_to_redis(37.0, 127.0)
        self.assertIsNotNone(result)
        assert len(self.redis_client.keys("*")) == 1
        assert (
            self.redis_client.keys("*")[0].decode("utf-8")
            == RedisKey.GEOLOCATIONS_KEY.value
        )

    def test_add_location_to_redis_failure(self):
        self.mock_redis_client.geoadd.side_effect = RedisOperationError("Some error")

        with self.assertRaises(RedisOperationError):
            self.redis_service.add_location_to_redis(123.0, 456.0)

    def test_find_geohashes_in_radius(self):
        self.redis_service.add_location_to_redis(37.0, 127.0)
        assert len(self.redis_client.keys("*")) == 1
        result = self.redis_service.find_geohashes_in_radius(37.0, 127.0, 100)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) == 1)

    def test_find_geohashes_in_radius_failure(self):
        self.mock_redis_client.geosearch.side_effect = RedisOperationError("Some error")

        with self.assertRaises(RedisOperationError):
            self.mock_redis_service.find_geohashes_in_radius(123.0, 456.0, 100)

    def test_cache_nearby_places_response(self):
        self.redis_service.add_location_to_redis(37.0, 127.0)
        assert len(self.redis_client.keys("*")) == 1
        result = self.redis_service.cache_nearby_places_response(37.0, 127.0, [])
        assert len(self.redis_client.keys("*")) == 2
        self.assertTrue(result)

    def test_cache_nearby_places_response_failure(self):
        self.mock_redis_client.set.side_effect = RedisOperationError("Some error")

        with self.assertRaises(RedisOperationError):
            self.mock_redis_service.cache_nearby_places_response(123.0, 456.0, [])

    def test_get_cached_nearby_places_responses(self):
        self.redis_service.add_location_to_redis(37.0, 127.0)
        assert len(self.redis_client.keys("*")) == 1

        self.redis_service.cache_nearby_places_response(37.0, 127.0, [{"a": "b"}])
        assert len(self.redis_client.keys("*")) == 2
        geohashes = self.redis_service.find_geohashes_in_radius(37.0, 127.0, 100)

        result = self.redis_service.get_cached_nearby_places_responses(geohashes)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)

    def test_get_cached_nearby_places_responses_failure(self):
        self.mock_redis_client.mget.side_effect = RedisOperationError("Some error")

        with self.assertRaises(RedisOperationError):
            self.mock_redis_service.get_cached_nearby_places_responses(["123"])

    def tearDown(self):
        self.redis_client.flushdb()
