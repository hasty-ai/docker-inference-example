import json
import logging
import os

from PIL import Image
import albumentations as A
import numpy as np
import torch
import torch.nn.functional as F
import torchvision

from ..tools.utils import mask2bbox, rle_encoding


class SESModel:
    def __init__(self, model_path):
        self.model_path = model_path
        self.transforms = A.load(os.path.join(model_path, "transforms.json"))
        with open(os.path.join(model_path, "class_mapping.json")) as data:
            mappings = json.load(data)

        self.class_mapping = {
            item["model_idx"]: item["class_name"] for item in mappings
        }
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not torch.cuda.is_available():
            logging.warning("GPU not found")
        model = torch.jit.load(os.path.join(model_path, "model.pt"))
        self.model = model.to(self.device)
        logging.info(f"Model {model_path} loaded")

    def _preprocess_length(self, n, stride=32):
        q = int(n / stride)
        n1 = stride * q
        n2 = stride * (q + 1)
        if abs(n - n1) < abs(n - n2):
            return n1
        return n2

    def predict(self, image: Image):
        width, height = image.width, image.height
        image = np.array(image)
        image = self.transforms(image=image)["image"]
        x = torch.from_numpy(image)
        x = x.to(self.device)
        with torch.no_grad():
            # Convert to channels first, convert to float datatype
            x = x.permute(2, 0, 1).unsqueeze(dim=0).float()
            new_height = self._preprocess_length(x.shape[-2])
            new_width = self._preprocess_length(x.shape[-1])
            if (x.shape[-2], x.shape[-1]) != (new_height, new_width):
                x = F.interpolate(x, size=(new_height, new_width), mode="bilinear", align_corners=False)
            y = self.model(x)
            y = torch.nn.functional.interpolate(
                y, size=(height, width), mode="bilinear", align_corners=False
            )[0]
            mask = np.argmax(y.cpu().numpy(), axis=0).astype(np.uint8)

        post_processed_class_preds = []
        class_names = []
        bboxes = []
        for class_ind in range(y.shape[0]):
            pred = (mask == class_ind + 1).astype(np.uint8)
            if 1 not in pred:
                continue
            class_names.append(self.class_mapping[class_ind])
            bbox = mask2bbox(pred)
            cropped_pred = pred[bbox[0]: bbox[1], bbox[2]: bbox[3]].copy()
            cropped_pred = rle_encoding(cropped_pred)
            post_processed_class_preds.append(cropped_pred)
            bboxes.append([bbox[2], bbox[0], bbox[3], bbox[1]])

        results = {
            "class_names": class_names,
            "boxes": bboxes,
            "rle_masks": post_processed_class_preds,
        }
        return results
