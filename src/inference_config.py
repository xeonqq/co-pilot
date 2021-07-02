import yaml


class InferenceConfig(object):
    def __init__(self, inference_config):
        with open(inference_config, "r") as f:
            content = yaml.load(f, Loader=yaml.FullLoader)
            self._inference_resolution = (
                content["infer_image_width"],
                content["infer_image_height"],
            )

    @property
    def inference_resolution(self):
        return self._inference_resolution
