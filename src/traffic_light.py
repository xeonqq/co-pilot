class TrafficLight(object):
    WORLD_WIDTH = 0.45
    WORLD_HEIGHT = 0.9
    H_W_RATIO = WORLD_HEIGHT / WORLD_WIDTH

    def __init__(self, cls, score, obj, image):
        self.cls = cls
        self.score = score
        self.obj = obj
        self.image = image

    def width(self):
        return self.obj.bbox[2] - self.obj.bbox[0]

    def height(self):
        return self.obj.bbox[3] - self.obj.bbox[1]

    def center(self):
        return (
            (self.obj.bbox[0] + self.obj.bbox[2]) / 2,
            (self.obj.bbox[1] + self.obj.bbox[3]) / 2,
        )
