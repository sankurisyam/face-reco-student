import cv2
import numpy as np
import os

try:
    import face_recognition  # optional, used if available
except Exception:
    face_recognition = None

# Optional MobileNetV2 classifier (PyTorch)
try:
    import torch
    import torchvision
    from torchvision import transforms
    _TORCH_AVAILABLE = True
except Exception:
    _TORCH_AVAILABLE = False


def _compute_brightness(gray: np.ndarray) -> float:
    return float(np.mean(gray))


def _compute_edge_density(gray: np.ndarray) -> float:
    edges = cv2.Canny(gray, 50, 150)
    return float(np.sum(edges > 0) / edges.size)


def _compute_color_variation(bgr: np.ndarray) -> float:
    return float(np.std(bgr))


def _compute_white_ratio(gray: np.ndarray) -> float:
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return float(np.sum(thresh == 255) / thresh.size)


def _compute_motion(prev_bgr: np.ndarray | None, curr_bgr: np.ndarray) -> float:
    if prev_bgr is None:
        return 0.0
    prev_gray = cv2.cvtColor(prev_bgr, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_bgr, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (5, 5), 0)
    curr_gray = cv2.GaussianBlur(curr_gray, (5, 5), 0)
    # Ensure same size before difference; if mismatch, resize previous to current
    if prev_gray.shape != curr_gray.shape:
        try:
            prev_gray = cv2.resize(prev_gray, (curr_gray.shape[1], curr_gray.shape[0]), interpolation=cv2.INTER_LINEAR)
        except Exception:
            # On any failure, return a higher motion value to avoid false "static" classification
            return 10.0
    diff = cv2.absdiff(prev_gray, curr_gray)
    return float(np.mean(diff))


def _detect_face_on_region(bgr: np.ndarray) -> bool:
    if face_recognition is None:
        return False
    if bgr.size == 0:
        return False
    try:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb, model="hog", number_of_times_to_upsample=0)
        return len(faces) > 0
    except Exception:
        return False


def analyze_phone_region(phone_bgr: np.ndarray, prev_phone_bgr: np.ndarray | None = None) -> dict:
    """
    Lightweight, heuristic-based analysis of a detected phone crop.

    Returns dict with:
      - brightness, edge_density, color_std, white_ratio, motion
      - screen_like: bool (screen characteristics present)
      - face_on_screen: bool (optional, only if face_recognition available)
      - is_photo: bool (likely static image shown on phone)
    """
    if phone_bgr is None or phone_bgr.size == 0:
        return {
            "brightness": 0.0,
            "edge_density": 0.0,
            "color_std": 0.0,
            "white_ratio": 0.0,
            "motion": 0.0,
            "screen_like": False,
            "face_on_screen": False,
            "is_photo": False,
        }

    gray = cv2.cvtColor(phone_bgr, cv2.COLOR_BGR2GRAY)

    brightness = _compute_brightness(gray)
    edge_density = _compute_edge_density(gray)
    color_std = _compute_color_variation(phone_bgr)
    white_ratio = _compute_white_ratio(gray)
    motion = _compute_motion(prev_phone_bgr, phone_bgr)

    # Heuristics for "screen-like" region
    has_bright_screen = brightness > 80.0
    has_defined_edges = edge_density > 0.08
    has_color_variation = color_std > 18.0
    has_screen_lighting = 0.15 < white_ratio < 0.85

    screen_like = sum([has_bright_screen, has_defined_edges, has_color_variation, has_screen_lighting]) >= 2

    face_on_screen = _detect_face_on_region(phone_bgr)

    # Static photo if low motion and screen-like
    is_static = motion < 6.0
    is_photo = screen_like and (is_static or face_on_screen)

    return {
        "brightness": brightness,
        "edge_density": edge_density,
        "color_std": color_std,
        "white_ratio": white_ratio,
        "motion": motion,
        "screen_like": bool(screen_like),
        "face_on_screen": bool(face_on_screen),
        "is_photo": bool(is_photo),
    }


# ===== Optional MobileNetV2 loader and inference (stub) =====
def load_mobilenetv2_classifier(weights_path: str | None = None):
    """
    Load a MobileNetV2 binary classifier (live vs photo) if PyTorch is available.
    Returns (model, transform) or (None, None) if unavailable.
    """
    if not _TORCH_AVAILABLE:
        return None, None
    try:
        model = torchvision.models.mobilenet_v2(pretrained=False)
        # Replace classifier for 2 classes
        model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, 2)
        if weights_path and os.path.exists(weights_path):
            state = torch.load(weights_path, map_location="cpu")
            model.load_state_dict(state)
        model.eval()
        tfm = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224)),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        return model, tfm
    except Exception:
        return None, None


def classify_phone_screen_mobilenet(model, transform, phone_bgr: np.ndarray) -> float:
    """
    Return probability that the phone screen shows a static photo (float 0..1).
    If model is None, returns 0.0.
    """
    if model is None or transform is None or phone_bgr is None or phone_bgr.size == 0:
        return 0.0
    try:
        rgb = cv2.cvtColor(phone_bgr, cv2.COLOR_BGR2RGB)
        tensor = transform(rgb).unsqueeze(0)
        with torch.no_grad():
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            # Assume class index 1 corresponds to "photo"
            return float(probs[1])
    except Exception:
        return 0.0


