import logging
from collections import defaultdict, namedtuple
from typing import List

from app import crud
from app.models.place import Place
from app.schemas.google_maps_api import DistanceInfo
from app.schemas.place import PlaceUpdate
from app.services.constants import AGGREGATED_ATTR

DestinationSummary = namedtuple("DestinationSummary", ("destination_id, total_value"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoutesMatrix:
    def __init__(self, distance_matrix: List[DistanceInfo]):
        self.distance_matrix = distance_matrix

    def update_candidate_addresses(self, db, candidates: List[Place]):
        """
        Update the address of the candidate.

        :param db: Database session
        :param distance_matrix: The distance matrix results.
        :param candidates: The list of candidates to update.
        """
        candidates_dict = {candidate.place_id: candidate for candidate in candidates}
        for matrix in self.distance_matrix:
            candidate = candidates_dict.get(matrix.destination_id)
            if candidate and matrix.destination != candidate.address:
                logger.info(
                    f"Updating address: {matrix.destination} != {candidate.address}"
                )
                updated_data = PlaceUpdate(
                    place_id=candidate.place_id, address=matrix.destination
                )
                crud.place.update(db, db_obj=candidate, obj_in=updated_data)

    @property
    def group_by_destination(self) -> dict:
        destination_groups = defaultdict(list)
        for matrix in self.distance_matrix:
            destination_groups[matrix.destination_id].append(matrix)
        return destination_groups

    def sort_destinations_by_aggregated_attr(
        self, attribute: AGGREGATED_ATTR, count: int
    ) -> List[DestinationSummary]:
        grouped_matrix = self.group_by_destination
        results = sorted(
            (
                DestinationSummary(
                    destination,
                    sum(getattr(info, attribute.value) for info in info_list),
                )
                for destination, info_list in grouped_matrix.items()
            ),
            key=lambda x: x.total_value,
        )[:count]

        return results
