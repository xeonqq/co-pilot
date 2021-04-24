import numpy as np


class TrafficLight(object):
    WORLD_WIDTH = 0.45
    WORLD_HEIGHT = 0.9
    H_W_RATIO = WORLD_HEIGHT / WORLD_WIDTH

    def __init__(self, cls, score, obj, image):
        self.cls = cls
        self.score = score
        self.obj = obj
        self.image = image

        self._update_property()

        self._driving_relevant = False

    def _update_property(self):
        self._center = np.asarray(
            [
                (self.obj.bbox[0] + self.obj.bbox[2]) / 2,
                (self.obj.bbox[1] + self.obj.bbox[3]) / 2,
            ]
        )
        self._area = self.width*self.height

    def set_driving_relevance(self, is_relevant):
        self._driving_relevant = is_relevant

    @property
    def area(self):
        return self._area

    @property
    def width(self):
        return self.obj.bbox[2] - self.obj.bbox[0]

    @property
    def height(self):
        return self.obj.bbox[3] - self.obj.bbox[1]

    @property
    def center(self):
        return self._center

    def center_pixel_distance(self, other_center):
        d = self._center - other_center
        return np.linalg.norm(d)

    def update(self, traffic_light):
        if self._driving_relevant and traffic_light.cls != self.cls:
            for cb in self._callbacks:
                cb(traffic_light.cls)
        self.cls = traffic_light.cls
        self.score = traffic_light.score
        self.obj = traffic_light.obj
        self.image = traffic_light.image
        self._update_property()

    def __repr__(self):
        return "<TrafficLight {} {}>".format(self.cls, self.obj.bbox)
