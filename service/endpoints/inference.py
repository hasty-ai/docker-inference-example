from flask import Blueprint, request, g

from .. import api

inference_api = Blueprint('inference_api', __name__)


@inference_api.route('/v1/object_detection', methods=['POST'])
def get_object_detection_prediction():
    confidence_thresh = request.json.get('confidence_threshold', 0.5)
    attr_thresh = request.json.get('attributer_threshold', 0.5)
    request_id = request.json.get("request_id")
    if request_id:
        g.request_id = request_id
    image = request.json.get('image', {})
    image_b64, image_url = None, None
    if 'b64' in image:
        image_b64 = image.get("b64")
    if 'url' in image:
        image_url = image.get("url")
    if not image_b64 and not image_url:
        raise ValueError("Image url or base64 should be provided")
    model = request.json.get('model', None)
    cls_model_name = request.json.get('cls_model_name', None)
    attr_model_name = request.json.get('attr_model_name', None)
    predictions = api.inference.get_object_detection_prediction(
        model,
        image_b64=image_b64,
        image_url=image_url,
        confidence_thresh=confidence_thresh,
        attr_thresh=attr_thresh,
        cls_model_name=cls_model_name,
        attr_model_name=attr_model_name,
    )
    results = {"predictions": predictions}
    if request_id:
        results["request_id"] = request_id
    return api.base.get_json_response(results)


@inference_api.route("/v1/image_tagger", methods=["POST"])
def get_image_tagger_prediction():
    confidence_thresh = request.json.get("confidence_threshold", 0.5)
    request_id = request.json.get("request_id")
    if request_id:
        g.request_id = request_id
    image = request.json.get("image", {})
    image_b64, image_url = None, None
    if "b64" in image:
        image_b64 = image.get("b64")
    if "url" in image:
        image_url = image.get("url")
    if not image_b64 and not image_url:
        raise ValueError("Image url or base64 should be provided")
    model = request.json.get("model", None)
    predictions = api.inference.get_image_tagger_prediction(
        model,
        image_b64=image_b64,
        image_url=image_url,
        confidence_thresh=confidence_thresh,
    )
    results = {"predictions": predictions}
    if request_id:
        results["request_id"] = request_id
    return api.base.get_json_response(results)


@inference_api.route("/v1/semantic_segmentor", methods=["POST"])
def get_semantic_segmentor_prediction():
    request_id = request.json.get("request_id")
    if request_id:
        g.request_id = request_id
    image = request.json.get("image", {})
    image_b64, image_url = None, None
    if "b64" in image:
        image_b64 = image.get("b64")
    if "url" in image:
        image_url = image.get("url")
    if not image_b64 and not image_url:
        raise ValueError("Image url or base64 should be provided")
    model = request.json.get("model", None)
    predictions = api.inference.get_semantic_segmentor_prediction(
        model,
        image_b64=image_b64,
        image_url=image_url,
    )
    results = {"predictions": predictions}
    if request_id:
        results["request_id"] = request_id
    return api.base.get_json_response(results)
