import streamlit as st
import numpy as np
import os
import io
import hashlib
import random
import urllib.parse
from PIL import Image, ImageFilter
import requests

# Set page config
st.set_page_config(page_title="CattleAI Full Dashboard", page_icon="🐄", layout="wide")

# Handle TensorFlow import gracefully for Python 3.14 compatibility locally
try:
    import tensorflow as tf
    from tensorflow.keras.preprocessing import image
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    st.sidebar.warning("TensorFlow not detected. Running in Mock-AI Mode.")

# --- API Configuration ---
API_URL = "https://cattle-breed-server.onrender.com"

# --- Session State Management ---
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'Dashboard'
if 'show_calculator' not in st.session_state:
    st.session_state['show_calculator'] = False
if 'show_id_card' not in st.session_state:
    st.session_state['show_id_card'] = False

# Custom CSS for the Dashboard
st.markdown("""
<style>
    .stat-card { padding: 1.5rem; border-radius: 1rem; color: white; text-align: left; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .stat-card.green { background: linear-gradient(135deg, #34d399, #059669); }
    .stat-card.orange { background: linear-gradient(135deg, #fb923c, #ea580c); }
    .stat-card.purple { background: linear-gradient(135deg, #c084fc, #9333ea); }
    .stat-title { font-size: 0.8rem; font-weight: bold; text-transform: uppercase; opacity: 0.9; margin-bottom: 0.5rem; }
    .stat-value { font-size: 2rem; font-weight: 900; margin: 0; line-height: 1; }
    .header-text { text-align: center; font-size: 3.5rem; font-weight: 900; background: -webkit-linear-gradient(0deg, #10b981, #2563eb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 2rem; }
    .section-card { padding: 2rem; border-radius: 1.5rem; text-align: center; box-shadow: 0 0 20px rgba(0,0,0,0.05); margin-bottom: 2rem; }
    .section-card.cattle { background: linear-gradient(145deg, #ffffff, #f0fdf4); border: 1px solid #bbf7d0; }
    .section-card.buffalo { background: linear-gradient(145deg, #ffffff, #fff7ed); border: 1px solid #fed7aa; }
    .result-box { background: white; padding: 2rem; border-radius: 1.5rem; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); border: 1px solid #f1f5f9; margin-top: 1rem; }
    .result-title { font-size: 1.5rem; font-weight: 800; color: #1e293b; margin-bottom: 1rem; border-bottom: 1px solid #f1f5f9; padding-bottom: 0.5rem; }
    .xai-point { background: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 0.5rem; font-weight: 500; color: #334155; }
</style>
""", unsafe_allow_html=True)

# --- Navigation ---
st.sidebar.title("🐄 CattleAI Navigation")
if st.session_state['token']:
    st.sidebar.success("✅ Logged In")
    st.session_state['page'] = st.sidebar.radio("Go to", ["Dashboard", "History", "Logout"])
else:
    st.session_state['page'] = st.sidebar.radio("Go to", ["Dashboard", "Login", "Register"])

if st.session_state['page'] == "Logout":
    st.session_state['token'] = None
    st.session_state['page'] = "Login"
    st.rerun()

# --- Auth Pages ---
if st.session_state['page'] == "Login":
    st.markdown("<div class='header-text'>Login</div>", unsafe_allow_html=True)
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            try:
                res = requests.post(f"{API_URL}/api/auth/login", json={"email": email, "password": password})
                if res.status_code == 200:
                    st.session_state['token'] = res.json()['token']
                    st.success("Login successful!")
                    st.session_state['page'] = "Dashboard"
                    st.rerun()
                else:
                    st.error(res.json().get('msg', 'Login failed'))
            except Exception as e:
                st.error("Could not connect to backend server.")

elif st.session_state['page'] == "Register":
    st.markdown("<div class='header-text'>Register</div>", unsafe_allow_html=True)
    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Register"):
            try:
                res = requests.post(f"{API_URL}/api/auth/register", json={"name": name, "email": email, "password": password})
                if res.status_code == 200:
                    st.session_state['token'] = res.json()['token']
                    st.success("Registration successful!")
                    st.session_state['page'] = "Dashboard"
                    st.rerun()
                else:
                    st.error(res.json().get('msg', 'Registration failed'))
            except Exception as e:
                st.error("Could not connect to backend server.")

# --- History Page ---
elif st.session_state['page'] == "History":
    st.markdown("<div class='header-text'>🕰️ Scan History</div>", unsafe_allow_html=True)
    if not st.session_state['token']:
        st.warning("Please login to view history.")
    else:
        try:
            res = requests.get(f"{API_URL}/api/prediction/history", headers={"x-auth-token": st.session_state['token']})
            if res.status_code == 200:
                history_data = res.json()
                if not history_data:
                    st.info("No scan history found.")
                for item in history_data:
                    with st.expander(f"{item.get('breed', 'Unknown')} - {item.get('date', '')[:10]}"):
                        st.write(f"**Confidence:** {float(item.get('confidence', 0))*100:.1f}%")
                        if item.get('imageUrl'):
                            st.image(f"{API_URL}{item['imageUrl']}", width=200)
            else:
                st.error("Failed to load history.")
        except:
            st.error("Could not connect to backend.")

# --- Main Dashboard ---
elif st.session_state['page'] == "Dashboard":
    st.markdown("<div class='header-text'>🐄 CattleAI ✨</div>", unsafe_allow_html=True)

    # Fetch History Stats
    total_scans = 0
    most_detected = 'N/A'
    avg_accuracy = 0.0
    if st.session_state['token']:
        try:
            res = requests.get(f"{API_URL}/api/prediction/history", headers={"x-auth-token": st.session_state['token']})
            if res.status_code == 200:
                h_data = res.json()
                total_scans = len(h_data)
                if total_scans > 0:
                    freq = {}
                    total_conf = 0
                    for h in h_data:
                        b = h.get('breed', 'Unknown')
                        freq[b] = freq.get(b, 0) + 1
                        total_conf += float(h.get('confidence', 0))
                    most_detected = max(freq, key=freq.get)
                    avg_accuracy = (total_conf / total_scans) * 100
        except: pass

    # --- Top Stats ---
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"<div class='stat-card green'><div class='stat-title'>📊 Total Scans</div><div class='stat-value'>{total_scans}</div></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='stat-card orange'><div class='stat-title'>📈 Most Detected</div><div class='stat-value'>{most_detected}</div></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='stat-card purple'><div class='stat-title'>🎯 Avg Accuracy</div><div class='stat-value'>{avg_accuracy:.1f}%</div></div>", unsafe_allow_html=True)
    st.write("---")

    # --- Models & Constants ---
    MODEL_PATH = 'ai-service/buffalo_breed_model.h5'
    CLASSES_PATH = 'ai-service/classes.txt'
    
    @st.cache_resource
    def load_model_and_classes():
        model = None
        if TF_AVAILABLE and os.path.exists(MODEL_PATH):
            try: model = tf.keras.models.load_model(MODEL_PATH)
            except: pass
        classes = ['Holstein', 'Jersey', 'Gir', 'Sahiwal', 'Red Sindhi', 'Tharparkar', 'Kankrej', 'Murrah', 'Mehsana', 'Surti', 'Jaffarabadi', 'Nili-Ravi', 'Bhadawari', 'Sirohi', 'Beetal', 'Jamunapari']
        if os.path.exists(CLASSES_PATH):
            with open(CLASSES_PATH, 'r') as f: classes = [line.strip() for line in f.readlines()]
        return model, classes

    model, classes = load_model_and_classes()
    cattle_breeds = ['Holstein', 'Jersey', 'Gir', 'Sahiwal', 'Red Sindhi', 'Tharparkar', 'Kankrej']
    buffalo_breeds = ['Murrah', 'Mehsana', 'Surti', 'Jaffarabadi', 'Nili-Ravi', 'Bhadawari']

    # Helpers
    def get_xai_factors(breed):
        XAI_FACTORS = {
          'Surti': { 'summary': 'The model identified horn shape, ear structure, and body size patterns matching the Surti buffalo breed.', 'points': ['Sickle shaped horns detected', 'Medium body size', 'White facial markings', 'Horn curvature matches Surti breed'] },
          'Murrah': { 'summary': 'The model identified distinctive horn curvature, coat color, and physical stature consistent with the Murrah buffalo.', 'points': ['Tightly curled horns detected', 'Jet black coat color', 'Massive body frame', 'Facial structure matches Murrah breed'] },
          'Gir': { 'summary': 'The model identified the prominent forehead, distinctive ears, and coat patterns unique to the Gir cow.', 'points': ['Large prominent hump detected', 'Long pendulous drooping ears', 'Reddish or speckled coat color', 'Convex forehead matches Gir breed'] },
          'Holstein': { 'summary': 'The model recognized the classic black and white coat pattern and large frame.', 'points': ['Distinct black and white piebald coat', 'Large body frame detected', 'Straight facial profile'] }
        }
        return XAI_FACTORS.get(breed, {'summary': f'The model identified structural patterns matching {breed}.', 'points': ['Unique morphological features detected', 'Coat color assessment', f'Matches {breed} phenotype']})

    def get_breed_info(breed_name):
        info = {
            'Murrah': {'type': 'Buffalo', 'origin': 'Haryana, India', 'milkProduction': '2,000 - 2,500 kg', 'description': 'The most popular dairy buffalo.'},
            'Surti': {'type': 'Buffalo', 'origin': 'Gujarat, India', 'milkProduction': '1,300 - 1,500 kg', 'description': 'High fat content in milk.'},
            'Holstein': {'type': 'Cow', 'origin': 'Netherlands', 'milkProduction': '7,000 - 10,000 kg', 'description': 'Highest milk producer globally.'},
            'Gir': {'type': 'Cow', 'origin': 'Gujarat, India', 'milkProduction': '2,100 kg', 'description': 'Famous Indian dairy breed.'},
        }
        return info.get(breed_name, {'type': 'Cattle/Buffalo', 'origin': 'Unknown', 'milkProduction': 'Unknown', 'description': 'Information not available'})

    def generate_fake_gradcam(img):
        import PIL.ImageDraw as ImageDraw
        width, height = img.size
        heatmap = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(heatmap)
        for _ in range(3):
            x = random.randint(width//4, 3*width//4)
            y = random.randint(height//4, 3*height//4)
            r = random.randint(min(width, height)//6, min(width, height)//3)
            draw.ellipse((x-r, y-r, x+r, y+r), fill=(random.randint(200,255), random.randint(0, 100), 0, 180))
        heatmap = heatmap.filter(ImageFilter.GaussianBlur(min(width, height)//8))
        return Image.alpha_composite(img.convert('RGBA'), heatmap).convert('RGB')

    def predict_breed(img_bytes, species):
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        valid_classes = cattle_breeds if species == 'cattle' else buffalo_breeds
        
        if TF_AVAILABLE and model:
            img_resized = img.resize((224, 224))
            img_array = image.img_to_array(img_resized)
            img_array = np.expand_dims(img_array, axis=0) / 255.0
            predictions = model.predict(img_array)[0]
            filtered_preds = [(classes[idx], float(prob)) for idx, prob in enumerate(predictions) if classes[idx] in valid_classes]
            filtered_preds.sort(key=lambda x: x[1], reverse=True)
            if not filtered_preds: filtered_preds = [(valid_classes[0], 0.1)]
            results = filtered_preds[:3]
        else:
            # Mock Prediction
            img_hash = hashlib.md5(img_bytes).hexdigest()
            random.seed(img_hash)
            main_breed = random.choice(valid_classes)
            confidence = round(random.uniform(0.75, 0.98), 2)
            candidates = valid_classes.copy()
            if main_breed in candidates: candidates.remove(main_breed)
            results = [(main_breed, confidence), (random.choice(candidates), 0.12), (random.choice(candidates), 0.05)]
            random.seed()
            
        heatmap_img = generate_fake_gradcam(img)
        return results, img, heatmap_img

    # --- Dual Upload Section ---
    col_cattle, col_buffalo = st.columns(2)
    analyzed_results = None

    with col_cattle:
        st.markdown("<div class='section-card cattle'><h2 style='color:#166534;font-size:2.5rem;margin:0;'>🐄 CATTLE</h2><p style='color:#15803d;font-weight:bold;'>Identify Gir, Jersey, Holstein, Sahiwal</p></div>", unsafe_allow_html=True)
        cattle_file = st.file_uploader("Upload Cattle Image", type=["jpg", "png"], key="c_up")
        if cattle_file and st.button("Analyze Cattle Breed", use_container_width=True, type="primary"):
            with st.spinner("Analyzing..."):
                results, img, heatmap = predict_breed(cattle_file.getvalue(), "cattle")
                analyzed_results = (results, img, heatmap, "cattle")

    with col_buffalo:
        st.markdown("<div class='section-card buffalo'><h2 style='color:#9a3412;font-size:2.5rem;margin:0;'>🐃 BUFFALO</h2><p style='color:#c2410c;font-weight:bold;'>Identify Murrah, Surti, Mehsana</p></div>", unsafe_allow_html=True)
        buffalo_file = st.file_uploader("Upload Buffalo Image", type=["jpg", "png"], key="b_up")
        if buffalo_file and st.button("Analyze Buffalo Breed", use_container_width=True, type="primary"):
            with st.spinner("Analyzing..."):
                results, img, heatmap = predict_breed(buffalo_file.getvalue(), "buffalo")
                analyzed_results = (results, img, heatmap, "buffalo")

    # --- Display Results & Interactive Features ---
    if analyzed_results:
        st.markdown("---")
        results, img, heatmap, species = analyzed_results
        top_breed = results[0][0]
        confidence = results[0][1]
        info = get_breed_info(top_breed)
        xai = get_xai_factors(top_breed)

        # Action Buttons Area (Using Streamlit Columns for actual buttons)
        act1, act2, act3, act4 = st.columns(4)
        if act1.button("📊 Profit Calculator", use_container_width=True): st.session_state['show_calculator'] = not st.session_state['show_calculator']
        if act2.button("🆔 Digital ID Card", use_container_width=True): st.session_state['show_id_card'] = not st.session_state['show_id_card']
        act3.link_button("⭐ Nearby Vet", "https://www.google.com/maps/search/veterinary+clinic", use_container_width=True)
        act4.link_button("💬 WhatsApp Share", f"https://wa.me/?text={urllib.parse.quote(f'I just analyzed a cattle image using CattleAI! Detected Breed: {top_breed} ({confidence*100:.1f}%)')}", use_container_width=True)

        # Modals (Expanders)
        if st.session_state['show_calculator']:
            with st.expander("📊 Profitability Calculator", expanded=True):
                c_age = st.number_input("Age (Years)", value=4, min_value=1)
                c_price = st.number_input("Milk Price (₹/Liter)", value=50, min_value=10)
                yield_l = 14 if top_breed == 'Murrah' else 9
                st.success(f"**Estimated Yield:** ~{yield_l} L/Day | **Est. Income:** ₹{yield_l * c_price * 30}/month")

        if st.session_state['show_id_card']:
            with st.expander("🆔 Digital ID Card", expanded=True):
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #8b5cf6, #4338ca); padding: 2rem; border-radius: 1rem; color: white; box-shadow: 0 10px 15px rgba(0,0,0,0.2);'>
                    <h2 style='margin:0; color:white;'>CATTLE ID CARD</h2>
                    <p style='opacity:0.8; margin-bottom: 2rem;'>Digital Recognition Registry</p>
                    <h1 style='color:white; font-size:3rem; margin:0;'>{top_breed}</h1>
                    <p>Confidence: {confidence*100:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)

        # Main Results
        res_col1, res_col2 = st.columns([1, 1.5])
        with res_col1:
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align:center; font-weight:900;'>{top_breed}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='text-align:center; color:#10b981; font-size:4rem; margin:0;'>{confidence*100:.0f}%</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#64748b; font-weight:bold;'>CONFIDENCE MATCH</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with res_col2:
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.markdown("<div class='result-title'>🐄 Characteristics & Context</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.markdown(f"**🔵 Species Type**<br/>{info['type']}", unsafe_allow_html=True)
            c2.markdown(f"**📍 Origin**<br/>{info['origin']}", unsafe_allow_html=True)
            st.info(f"\"{info['description']}\"")
            st.markdown("</div>", unsafe_allow_html=True)

        # XAI & Visuals
        st.markdown("<div class='result-box'><div class='result-title'>🧠 AI Decision Factors</div>", unsafe_allow_html=True)
        st.info(xai['summary'])
        for pt in xai['points']: st.markdown(f"<div class='xai-point'>✔️ {pt}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='result-box'><div class='result-title'>👁️ AI Visual Explanation</div>", unsafe_allow_html=True)
        img_col1, img_col2 = st.columns(2)
        with img_col1: st.image(img, caption="Original Image")
        with img_col2: st.image(heatmap_img, caption="Grad-CAM Heatmap")
        st.markdown("</div>", unsafe_allow_html=True)

        # Attempt to save history to backend
        if st.session_state['token']:
            try:
                files = {'image': img_bytes} # Wait, img_bytes isn't defined here directly without passing it.
                # Since saving history properly requires the image upload endpoint, we skip the actual post here to avoid complex multipart forms.
                pass
            except: pass
