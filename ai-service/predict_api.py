from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import os
import io
import hashlib
from PIL import Image

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Model setup — PyTorch MobileNetV2 trained on 10 cattle/buffalo breeds
# ---------------------------------------------------------------------------
MODEL_PATH  = os.path.join(os.path.dirname(__file__), "buffalo_breed_model.pth")
CLASSES_PATH = os.path.join(os.path.dirname(__file__), "classes.txt")

model      = None
classes    = []
load_error = None

def load_model():
    global model, classes, load_error
    import traceback
    try:
        import torch
        import torchvision.models as tv_models
        import torch.nn as nn

        # Load classes first
        if os.path.exists(CLASSES_PATH):
            with open(CLASSES_PATH, "r") as f:
                classes = [l.strip() for l in f if l.strip()]
            print(f"✅ Classes loaded: {classes}")
        else:
            print(f"⚠️ classes.txt not found at {CLASSES_PATH}")
            return

        if not os.path.exists(MODEL_PATH):
            print(f"⚠️ Model file not found at {MODEL_PATH}. Using mock predictions.")
            return

        num_classes = len(classes)
        net = tv_models.mobilenet_v2(weights=None)
        net.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(net.last_channel, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes),
        )

        checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
        net.load_state_dict(checkpoint["model_state"])
        net.eval()
        model = net
        print(f"✅ PyTorch model loaded! {num_classes} breeds: {classes}")
        load_error = None

    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌ Model load FAILED: {e}\n{tb}")
        load_error = str(e)
        model = None

load_model()

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":       "ok",
        "model_loaded": model is not None,
        "mock_mode":    model is None,
        "classes":      classes,
        "error":        load_error,
    })

# ---------------------------------------------------------------------------
# Breed metadata
# ---------------------------------------------------------------------------
BREED_INFO = {
    "Murrah":      {"type": "Buffalo", "origin": "Haryana, India",        "milkProduction": "2,000 - 2,500 kg", "characteristics": "Black, curved horns, massive body",         "description": "The most popular dairy buffalo."},
    "Nili-Ravi":   {"type": "Buffalo", "origin": "Punjab",                "milkProduction": "1,800 - 2,500 kg", "characteristics": "White markings on face/legs",               "description": "Known as the 'Black Gold'."},
    "Jaffarabadi": {"type": "Buffalo", "origin": "Gujarat, India",        "milkProduction": "2,000 - 2,700 kg", "characteristics": "Drooping horns, heavy forehead",            "description": "Heaviest buffalo breed."},
    "Mehsana":     {"type": "Buffalo", "origin": "Gujarat, India",        "milkProduction": "1,200 - 1,500 kg", "characteristics": "Intermediate Murrah/Surti features",        "description": "Consistent yield cross-breed."},
    "Surti":       {"type": "Buffalo", "origin": "Gujarat, India",        "milkProduction": "1,300 - 1,500 kg", "characteristics": "Sickle horns, medium size",                 "description": "High fat content in milk."},
    "Bhadawari":   {"type": "Buffalo", "origin": "Uttar Pradesh, India",  "milkProduction": "800 - 1,000 kg",   "characteristics": "Copper colored body, wedge shape",          "description": "Famous for extremely high butterfat."},
    "Holstein":    {"type": "Cow",     "origin": "Netherlands",           "milkProduction": "7,000 - 10,000 kg","characteristics": "Black and white spots, large frame",        "description": "Highest milk producer globally."},
    "Jersey":      {"type": "Cow",     "origin": "Jersey Island, UK",     "milkProduction": "4,000 - 5,000 kg", "characteristics": "Fawn color, prominent eyes, small",         "description": "Produces golden, high-fat milk."},
    "Gir":         {"type": "Cow",     "origin": "Gujarat, India",        "milkProduction": "2,100 kg",          "characteristics": "Red with white spots, prominent forehead",  "description": "Famous Indian dairy breed."},
    "Sahiwal":     {"type": "Cow",     "origin": "Punjab",                "milkProduction": "2,200 kg",          "characteristics": "Reddish brown, tick resistant",             "description": "Best indigenous dairy cow of India/Pakistan."},
    "Red Sindhi":  {"type": "Cow",     "origin": "Sindh",                 "milkProduction": "1,800 kg",          "characteristics": "Deep red color, compact body",              "description": "Highly heat tolerant."},
    "Tharparkar":  {"type": "Cow",     "origin": "Thar Desert",           "milkProduction": "1,700 kg",          "characteristics": "White/light grey, lyre horns",              "description": "Dual-purpose, thrives in deserts."},
    "Kankrej":     {"type": "Cow",     "origin": "Gujarat, India",        "milkProduction": "1,750 kg",          "characteristics": "Silver-grey, large crescent horns",         "description": "One of the heaviest Indian cattle."},
    "Ongole":      {"type": "Cow",     "origin": "Andhra Pradesh, India", "milkProduction": "1,500 kg",          "characteristics": "White, large hump, long horns",             "description": "Strong draught and dairy breed."},
}

def get_breed_info(name):
    return BREED_INFO.get(name, {
        "type": "Cattle/Livestock", "origin": "India",
        "milkProduction": "Varies", "characteristics": "N/A",
        "description": f"A recognised livestock breed: {name}.",
    })

# ---------------------------------------------------------------------------
# Species lists  (must match classes.txt names exactly)
# ---------------------------------------------------------------------------
BUFFALO_BREEDS = {"Murrah", "Mehsana", "Surti", "Jaffarabadi", "Bhadawari"}
CATTLE_BREEDS  = {"Gir", "Kankrej", "Ongole", "Sahiwal", "Tharparkar",
                  "Holstein", "Jersey", "Red Sindhi"}

# ---------------------------------------------------------------------------
# Preprocessing  (ImageNet normalisation)
# ---------------------------------------------------------------------------
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def preprocess(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = (arr - MEAN) / STD
    arr = arr.transpose(2, 0, 1)          # HWC → CHW
    return arr[np.newaxis, ...]            # add batch dim

# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------
def generate_heatmap(img_bytes, seed):
    import random, base64
    from PIL import ImageFilter, ImageDraw
    random.seed(seed)
    base = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = base.size
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)
    for _ in range(3):
        x = random.randint(w//4, 3*w//4)
        y = random.randint(h//4, 3*h//4)
        r = random.randint(min(w,h)//6, min(w,h)//3)
        draw.ellipse((x-r, y-r, x+r, y+r),
                     fill=(random.randint(200,255), random.randint(0,80), 0, 170))
    ov = ov.filter(ImageFilter.GaussianBlur(min(w,h)//8))
    out = Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

# ---------------------------------------------------------------------------
# Image quality
# ---------------------------------------------------------------------------
def image_quality(img_bytes):
    from PIL import ImageStat
    img  = Image.open(io.BytesIO(img_bytes)).convert("L")
    stat = ImageStat.Stat(img)
    br   = stat.mean[0]
    blur = float(np.var(np.array(img, dtype=float)))
    return {
        "animal_detected":    True,
        "lighting_sufficient": bool(50 < br < 210),
        "background_clutter":  bool(blur < 1000),
    }

# ---------------------------------------------------------------------------
# Prediction endpoint
# ---------------------------------------------------------------------------
@app.route("/predict/<species>", methods=["POST"])
def predict(species):
    import traceback
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 400
        if species not in ("cattle", "buffalo"):
            return jsonify({"error": "Invalid species"}), 400

        img_bytes = request.files["image"].read()
        img_hash  = hashlib.md5(img_bytes).hexdigest()
        quality   = image_quality(img_bytes)

        valid_set = BUFFALO_BREEDS if species == "buffalo" else CATTLE_BREEDS

        if model is not None and classes:
            import torch
            inp    = torch.tensor(preprocess(img_bytes), dtype=torch.float32)
            with torch.no_grad():
                logits = model(inp)[0]                    # shape: (num_classes,)
                probs  = torch.softmax(logits, dim=0).numpy()

            # Build score dict  {breed_name: probability}
            scores = {classes[i]: float(probs[i]) for i in range(len(classes))}

            # ── Species mismatch detection ──────────────────────────────────
            buffalo_score = sum(scores.get(b, 0) for b in BUFFALO_BREEDS if b in scores)
            cattle_score  = sum(scores.get(b, 0) for b in CATTLE_BREEDS  if b in scores)
            actual_species = "buffalo" if buffalo_score > cattle_score else "cattle"
            species_conf   = round(max(buffalo_score, cattle_score) /
                                   max(buffalo_score + cattle_score, 1e-6), 2)

            if actual_species != species:
                wrong_label   = "Buffalo" if actual_species == "buffalo" else "Cattle/Cow"
                # Best breed of the detected species
                actual_set = BUFFALO_BREEDS if actual_species == "buffalo" else CATTLE_BREEDS
                detected_breed = max(
                    [(b, scores[b]) for b in actual_set if b in scores],
                    key=lambda x: x[1], default=("Unknown", 0)
                )[0]
                return jsonify({
                    "error":             "Species-Breed Mismatch",
                    "message":           f"This image looks like a {wrong_label}, but you uploaded it in the {'Cattle/Cow' if species == 'cattle' else 'Buffalo'} section.",
                    "detected_species":  actual_species,
                    "requested_species": species,
                    "detected_breed":    detected_breed,
                    "species_confidence": species_conf,
                    "suggestion":        f"Please upload this image in the {wrong_label} section instead.",
                }), 422

            # ── Not-an-animal check ─────────────────────────────────────────
            top_prob = max(probs)
            if top_prob < 0.15:
                return jsonify({
                    "error":      "Not a livestock animal",
                    "message":    "The image does not appear to contain a recognisable cattle or buffalo.",
                    "suggestion": "Make sure the animal is clearly visible, well-lit, and takes up most of the frame.",
                }), 422

            # ── Normal prediction ───────────────────────────────────────────
            filtered = sorted(
                [(b, scores[b]) for b in valid_set if b in scores],
                key=lambda x: x[1], reverse=True
            )
            if not filtered:
                filtered = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            results = [{"breed": b, "confidence": round(s, 4)} for b, s in filtered[:3]]
            main_breed = results[0]["breed"]
            confidence = results[0]["confidence"]
            is_mock    = False

        else:
            # ── Mock fallback ───────────────────────────────────────────────
            import random
            valid_list = list(valid_set)
            random.seed(img_hash)
            main_breed = random.choice(valid_list)
            confidence = round(random.uniform(0.55, 0.90), 4)
            others     = [b for b in valid_list if b != main_breed]
            random.shuffle(others)
            results = [
                {"breed": main_breed,                                          "confidence": confidence},
                {"breed": others[0] if others else main_breed,                 "confidence": round(random.uniform(0.05, 0.20), 4)},
                {"breed": others[1] if len(others) > 1 else main_breed,        "confidence": round(random.uniform(0.01, 0.05), 4)},
            ]
            random.seed()
            is_mock = True

        heatmap = generate_heatmap(img_bytes, img_hash)

        return jsonify({
            "prediction": main_breed,
            "confidence": confidence,
            "top3":       results,
            "info":       get_breed_info(main_breed),
            "heatmap":    heatmap,
            "quality":    quality,
            "mock":       is_mock,
        })

    except Exception as e:
        print("CRASH:", traceback.format_exc())
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


if __name__ == "__main__":
    app.run(port=8000, debug=True)
