from src.detector.model_loader import model_loader


class InferenceEngine:
    def __init__(self):
        self.model = model_loader.get_model()

    def run(self, image_path: str):

        return self.model.predict(image_path)


inference_engine = InferenceEngine()
