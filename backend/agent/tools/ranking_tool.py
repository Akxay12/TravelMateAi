from models.schemas import AttractionItem

class RankingTool:
    """Wrapper tool for ranking/sorting attractions by distance."""
    
    def run(self, attractions: list[AttractionItem]) -> list[AttractionItem]:
        """
        Ranks attractions by distance.
        Reuses the existing sorting implementation from attractions_service.
        """
        return sorted(attractions, key=lambda a: a.distance_km)
