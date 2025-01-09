import math
from decimal import Decimal


class LatLngDistance(object):
    def __init__(self, **kwargs):
        self.lat1 = kwargs.get('lat1')
        self.lon1 = kwargs.get('lon1')
        self.lat2 = kwargs.get('lat2')
        self.lon2 = kwargs.get('lon2')

    def calculate(self):
        """
        单位是米
        """
        # r=6371.393公里
        r: float = 6371.393 * 1000
        dlat = self.deg2rad(self.lat2 - self.lat1)
        dlon = self.deg2rad(self.lon2 - self.lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(self.deg2rad(self.lat1)) * math.cos(self.deg2rad(self.lat2)) * math.sin(
            dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = r * c
        print(f"计算距离:{distance}")
        return distance

    def deg2rad(self, deg):
        return deg * (Decimal(math.pi / 180))
