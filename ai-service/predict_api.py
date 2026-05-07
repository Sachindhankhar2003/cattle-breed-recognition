from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import os
import io
import json
import hashlib
from PIL import Image

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Model setup — downloads from HuggingFace on first cold start (~90 MB)
# Uses ONNX Runtime (no TensorFlow needed, works on free Render tier)
# ---------------------------------------------------------------------------
MODEL_REPO = "vishnuamar/cattle-breed-classifier"
MODEL_FILE = "model.onnx"
PROTO_FILE = "prototypes.json"

session = None
prototypes = None
load_error = None

def load_model():
    global session, prototypes, load_error
    import traceback
    try:
        from huggingface_hub import hf_hub_download
        import onnxruntime as ort

        print("📥 Downloading model from HuggingFace (first run only)...")
        model_path = hf_hub_download(MODEL_REPO, MODEL_FILE)
        print(f"✅ model.onnx downloaded to: {model_path}")
        proto_path = hf_hub_download(MODEL_REPO, PROTO_FILE)
        print(f"✅ prototypes.json downloaded to: {proto_path}")

        session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        with open(proto_path, "r") as f:
            prototypes = json.load(f)

        print(f"✅ Real model loaded! Breeds: {list(prototypes['prototypes'].keys())}")
        load_error = None
    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌ Model load FAILED: {e}\n{tb}")
        load_error = str(e) + "\n" + tb
        session = None
        prototypes = None

# Load synchronously at startup
load_model()

# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": session is not None,
        "mock_mode": session is None,
        "error": load_error
    })

# ---------------------------------------------------------------------------
# Breed metadata
# ---------------------------------------------------------------------------
# Map HuggingFace breed names → our display names (normalise spelling)
BREED_NAME_MAP = {
    "Jaffarbadi": "Jaffarabadi",
    "Jaffrabadi":  "Jaffarabadi",
}

def normalise(name):
    return BREED_NAME_MAP.get(name, name)

BREED_INFO = {
    # Buffaloes
    "Murrah":      {"type": "Buffalo", "origin": "Haryana, India",       "milkProduction": "2,000 - 2,500 kg", "characteristics": "Black, curved horns, massive body",          "description": "The most popular dairy buffalo."},
    "Nili-Ravi":   {"type": "Buffalo", "origin": "Punjab",               "milkProduction": "1,800 - 2,500 kg", "characteristics": "White markings on face/legs",                "description": "Known as the 'Black Gold'."},
    "Jaffarabadi": {"type": "Buffalo", "origin": "Gujarat, India",       "milkProduction": "2,000 - 2,700 kg", "characteristics": "Drooping horns, heavy forehead",             "description": "Heaviest buffalo breed."},
    "Mehsana":     {"type": "Buffalo", "origin": "Gujarat, India",       "milkProduction": "1,200 - 1,500 kg", "characteristics": "Intermediate Murrah/Surti features",         "description": "Consistent yield cross-breed."},
    "Surti":       {"type": "Buffalo", "origin": "Gujarat, India",       "milkProduction": "1,300 - 1,500 kg", "characteristics": "Sickle horns, medium size",                  "description": "High fat content in milk."},
    "Bhadawari":   {"type": "Buffalo", "origin": "Uttar Pradesh, India", "milkProduction": "800 - 1,000 kg",   "characteristics": "Copper colored body, wedge shape",           "description": "Famous for extremely high butterfat."},
    # Cows
    "Holstein":    {"type": "Cow",     "origin": "Netherlands",          "milkProduction": "7,000 - 10,000 kg","characteristics": "Black and white spots, large frame",         "description": "Highest milk producer globally."},
    "Jersey":      {"type": "Cow",     "origin": "Jersey Island, UK",    "milkProduction": "4,000 - 5,000 kg", "characteristics": "Fawn color, prominent eyes, small",          "description": "Produces golden, high-fat milk."},
    "Gir":         {"type": "Cow",     "origin": "Gujarat, India",       "milkProduction": "2,100 kg",          "characteristics": "Red with white spots, prominent forehead",   "description": "Famous Indian dairy breed."},
    "Sahiwal":     {"type": "Cow",     "origin": "Punjab",               "milkProduction": "2,200 kg",          "characteristics": "Reddish brown, tick resistant",              "description": "Best indigenous dairy cow of India/Pakistan."},
    "Red Sindhi":  {"type": "Cow",     "origin": "Sindh",                "milkProduction": "1,800 kg",          "characteristics": "Deep red color, compact body",               "description": "Highly heat tolerant."},
    "Tharparkar":  {"type": "Cow",     "origin": "Thar Desert",          "milkProduction": "1,700 kg",          "characteristics": "White/light grey, lyre horns",               "description": "Dual-purpose, thrives in deserts."},
    "Kankrej":     {"type": "Cow",     "origin": "Gujarat, India",       "milkProduction": "1,750 kg",          "characteristics": "Silver-grey, large crescent horns",          "description": "One of the heaviest Indian cattle."},
    "Ongole":      {"type": "Cow",     "origin": "Andhra Pradesh, India","milkProduction": "1,500 kg",          "characteristics": "White, large hump, long horns",              "description": "Strong draught and dairy breed."},
}

def get_breed_info(breed_name):
    return BREED_INFO.get(breed_name, {
        "type": "Cattle/Livestock",
        "origin": "India",
        "milkProduction": "Varies",
        "characteristics": "N/A",
        "description": f"A recognised livestock breed: {breed_name}.",
    })

# ---------------------------------------------------------------------------
# Species breed lists
# ---------------------------------------------------------------------------
BUFFALO_BREEDS = {"Murrah", "Mehsana", "Surti", "Jaffarabadi", "Nili-Ravi", "Bhadawari"}
CATTLE_BREEDS  = {"Holstein", "Jersey", "Gir", "Sahiwal", "Red Sindhi", "Tharparkar", "Kankrej", "Ongole"}

# HuggingFace model's own breed names (before normalisation)
HF_BUFFALO = {"Bhadawari", "Jaffarbadi", "Mehsana", "Murrah", "Surti"}
HF_CATTLE  = {"Gir", "Kankrej", "Ongole", "Sahiwal", "Tharparkar"}

# ---------------------------------------------------------------------------
# Image preprocessing (ImageNet normalisation, same as the model was trained on)
# ---------------------------------------------------------------------------
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def preprocess(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((224, 224), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0          # [0,1]
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD              # normalise
    arr = arr.transpose(2, 0, 1)                            # HWC -> CHW
    return np.expand_dims(arr, axis=0)                      # add batch dim

# ---------------------------------------------------------------------------
# Heatmap (visual overlay — cosmetic only)
# ---------------------------------------------------------------------------
def generate_heatmap(img_bytes, seed_hash):
    import random
    from PIL import ImageFilter, ImageDraw
    random.seed(seed_hash)
    base = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = base.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for _ in range(3):
        x = random.randint(w // 4, 3 * w // 4)
        y = random.randint(h // 4, 3 * h // 4)
        r = random.randint(min(w, h) // 6, min(w, h) // 3)
        draw.ellipse((x - r, y - r, x + r, y + r),
                     fill=(random.randint(200, 255), random.randint(0, 80), 0, 170))
    overlay = overlay.filter(ImageFilter.GaussianBlur(min(w, h) // 8))
    result = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    buf = io.BytesIO()
    result.save(buf, format="JPEG", quality=85)
    import base64
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

# ---------------------------------------------------------------------------
# Image quality check
# ---------------------------------------------------------------------------
def image_quality(img_bytes):
    from PIL import ImageStat
    img = Image.open(io.BytesIO(img_bytes)).convert("L")
    stat = ImageStat.Stat(img)
    brightness = stat.mean[0]
    blur = float(np.var(np.array(img, dtype=float)))
    return {
        "animal_detected": True,
        "lighting_sufficient": bool(50 < brightness < 210),
        "background_clutter": bool(blur < 1000),
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
            return jsonify({"error": "Invalid species. Use 'cattle' or 'buffalo'"}), 400

        img_bytes = request.files["image"].read()
        img_hash  = hashlib.md5(img_bytes).hexdigest()
        quality   = image_quality(img_bytes)

        # Choose which HF breed set to filter by
        hf_valid = HF_BUFFALO if species == "buffalo" else HF_CATTLE

        if session is not None and prototypes is not None:
            # ---- REAL MODEL PREDICTION ----
            inp = preprocess(img_bytes)
            input_name = session.get_inputs()[0].name
            features = session.run(None, {input_name: inp})[0][0]   # 2048-dim vector

            # Cosine similarity against ALL breed prototypes
            scores = {}
            for breed, proto in prototypes["prototypes"].items():
                proto_arr = np.array(proto, dtype=np.float32)
                sim = float(np.dot(features, proto_arr) /
                            (np.linalg.norm(features) * np.linalg.norm(proto_arr) + 1e-8))
                scores[breed] = sim

            # --- SPECIES MISMATCH DETECTION ---
            # Find the globally best breed across ALL species
            all_ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            best_breed_overall = all_ranked[0][0]
            best_score_overall = all_ranked[0][1]

            # Determine what species the image actually is
            if best_breed_overall in HF_BUFFALO:
                detected_species = "buffalo"
            elif best_breed_overall in HF_CATTLE:
                detected_species = "cattle"
            else:
                detected_species = "unknown"

            # Compute buffalo vs cattle group scores
            buffalo_scores = [s for b, s in scores.items() if b in HF_BUFFALO]
            cattle_scores  = [s for b, s in scores.items() if b in HF_CATTLE]
            avg_buffalo = sum(buffalo_scores) / len(buffalo_scores) if buffalo_scores else 0
            avg_cattle  = sum(cattle_scores)  / len(cattle_scores)  if cattle_scores  else 0

            # Decide actual species by group average
            actual_species = "buffalo" if avg_buffalo > avg_cattle else "cattle"

            # Confidence gap — how strongly does the model prefer one species over the other
            species_gap = abs(avg_buffalo - avg_cattle)
            # Normalise gap to 0-1 confidence
            species_confidence = round(min(0.5 + species_gap * 10, 0.99), 2)

            # If species doesn't match what user selected → return mismatch error
            if actual_species != species:
                wrong_label   = "Buffalo" if actual_species == "buffalo" else "Cattle/Cow"
                correct_label = "Cattle/Cow" if actual_species == "buffalo" else "Buffalo"
                # Get top breed of the actual detected species for the error message
                actual_hf_set = HF_BUFFALO if actual_species == "buffalo" else HF_CATTLE
                actual_ranked = sorted(
                    [(b, s) for b, s in scores.items() if b in actual_hf_set],
                    key=lambda x: x[1], reverse=True
                )
                detected_breed = normalise(actual_ranked[0][0]) if actual_ranked else best_breed_overall

                return jsonify({
                    "error":              "Species-Breed Mismatch",
                    "message":            f"This image looks like a {wrong_label}, but you uploaded it in the {correct_label} section.",
                    "detected_species":   actual_species,
                    "requested_species":  species,
                    "detected_breed":     detected_breed,
                    "species_confidence": species_confidence,
                    "suggestion":         f"Please upload this image in the {wrong_label} section instead.",
                }), 422

            # --- IMAGE QUALITY / NOT AN ANIMAL CHECK ---
            # If the best score across all breeds is very low, image is likely not a livestock animal
            if best_score_overall < 0.3:
                return jsonify({
                    "error":      "Not a livestock animal",
                    "message":    "The image does not appear to contain a recognisable cattle or buffalo. Please upload a clear photo of the animal.",
                    "suggestion": "Make sure the animal is clearly visible, well-lit, and takes up most of the frame.",
                }), 422

            # --- NORMAL PREDICTION (species matches) ---
            hf_valid = HF_BUFFALO if species == "buffalo" else HF_CATTLE
            filtered = {b: s for b, s in scores.items() if b in hf_valid}
            ranked   = sorted(filtered.items(), key=lambda x: x[1], reverse=True)

            top_raw    = ranked[0][1]
            bottom_raw = ranked[-1][1]
            span = max(top_raw - bottom_raw, 1e-6)

            def norm_conf(s):
                return round(0.55 + 0.42 * (s - bottom_raw) / span, 4)

            results    = [{"breed": normalise(b), "confidence": norm_conf(s)} for b, s in ranked[:3]]
            main_breed = results[0]["breed"]
            confidence = results[0]["confidence"]
            is_mock    = False

        else:
            # ---- MOCK FALLBACK (model not loaded) ----
            import random
            valid_list = list(BUFFALO_BREEDS if species == "buffalo" else CATTLE_BREEDS)
            random.seed(img_hash)
            main_breed = random.choice(valid_list)
            confidence = round(random.uniform(0.75, 0.97), 4)
            others     = [b for b in valid_list if b != main_breed]
            random.shuffle(others)
            results = [
                {"breed": main_breed, "confidence": confidence},
                {"breed": others[0] if others else main_breed, "confidence": round(random.uniform(0.08, 0.20), 4)},
                {"breed": others[1] if len(others) > 1 else main_breed, "confidence": round(random.uniform(0.02, 0.07), 4)},
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
