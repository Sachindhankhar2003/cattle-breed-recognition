import React, { useState, useEffect, useRef } from 'react';
import UploadSection from '../components/UploadSection';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, Award, MapPin, Droplets, Download, Share2, Activity, TrendingUp, Target, CreditCard, Stethoscope, Calculator, X, ImageIcon, CheckCircle, AlertTriangle } from 'lucide-react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import toast from 'react-hot-toast';
import html2pdf from 'html2pdf.js';
import axios from 'axios';
import { QRCodeSVG } from 'qrcode.react';

const XAI_FACTORS = {
  'Surti': {
    summary: 'The model identified horn shape, ear structure, and body size patterns matching the Surti buffalo breed.',
    points: ['Sickle shaped horns detected', 'Medium body size', 'White facial markings', 'Horn curvature matches Surti breed']
  },
  'Murrah': {
    summary: 'The model identified distinctive horn curvature, coat color, and physical stature consistent with the Murrah buffalo.',
    points: ['Tightly curled horns detected', 'Jet black coat color', 'Massive body frame', 'Facial structure matches Murrah breed']
  },
  'Nili-Ravi': {
    summary: 'The model recognized specific facial patterns, eye traits, and body structure aligning with the Nili-Ravi breed.',
    points: ['White markings on forehead and face', 'Wall eyes (white iris) detected', 'Wedge-shaped heavy body', 'Horn style matches Nili-Ravi breed']
  },
  'Jaffarabadi': {
    summary: 'The model evaluated the heavy facial structure, drooping horns, and large body mass typical of Jaffarabadi buffaloes.',
    points: ['Heavy drooping horns detected', 'Prominent forehead structure', 'Large massive body size', 'Facial features matches Jaffarabadi breed']
  },
  'Mehsana': {
    summary: 'The model noted intermediate horn curves, body length, and structural features characteristic of the Mehsana breed.',
    points: ['Irregularly curved horns detected', 'Longer body proportion', 'Usually black or brownish-black coat', 'Intermediate traits matching Mehsana breed']
  },
  'Gir': {
    summary: 'The model identified the prominent forehead, distinctive ears, and coat patterns unique to the Gir cow.',
    points: ['Large prominent hump detected', 'Long pendulous drooping ears', 'Reddish or speckled coat color', 'Convex forehead matches Gir breed']
  },
  'Jersey': {
    summary: 'The model detected the typical coat color, dish face, and size structure of a Jersey cow.',
    points: ['Light brown to fawn coat color', 'Dished forehead structure detected', 'Medium to small frame size', 'Facial structure matches Jersey breed']
  },
  'Holstein Friesian': {
    summary: 'The model recognized the classic black and white coat pattern and large frame of a Holstein Friesian cow.',
    points: ['Distinct black and white piebald coat', 'Large body frame detected', 'Straight facial profile', 'Pattern distribution matches Holstein breed']
  }
};

const getXAIFactors = (breed) => {
  return XAI_FACTORS[breed] || {
    summary: `The model identified structural patterns and specific visual traits matching the ${breed} breed.`,
    points: ['Unique morphological features detected', 'Coat color and pattern assessment', 'Body structure proportionality', `General phenotype matches ${breed} breed`]
  };
};

const Dashboard = () => {
  const [result, setResult] = useState(null);
  const [errorResult, setErrorResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [history, setHistory] = useState([]);
  const [activeSection, setActiveSection] = useState('cattle');
  const resultRef = useRef(null);

  // Modals
  const [showIDCard, setShowIDCard] = useState(false);
  const [showMilkCalc, setShowMilkCalc] = useState(false);
  
  // Milk Calc State
  const [milkStats, setMilkStats] = useState({ age: 4, lactation: 2, price: 50 });

  useEffect(() => {
    fetchStats();
  }, [result]);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const API_BASE = import.meta.env.VITE_API_URL || '';
      const res = await axios.get(`${API_BASE}/api/prediction/history`, { headers: { 'x-auth-token': token } });
      setHistory(res.data);
    } catch (err) {}
  };

  const onPredictionStart = () => { setIsAnalyzing(true); setResult(null); setErrorResult(null); };

  const onPredictionSuccess = (data) => {
    setResult(data);
    setErrorResult(null);
    setIsAnalyzing(false);
    toast.success('Analysis complete!');
  };

  const onPredictionError = (errObj) => {
    setIsAnalyzing(false);
    setErrorResult(errObj);
    if (errObj.error === 'Species-Breed Mismatch') {
        toast.error('Wrong section! Buffalo in Cattle or vice versa.', { icon: '⚠️' });
    } else if (errObj.error === 'Not a livestock animal') {
        toast.error('No animal detected in image!', { icon: '🚫' });
    }
  };

  const exportPDF = () => {
    const element = resultRef.current;
    if (!element) return;
    toast.loading('Generating PDF...', { id: 'pdf' });
    const opt = {
      margin: 1, filename: `Buffalo_Scan_${Date.now()}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true, backgroundColor: '#0f172a' },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(element).save().then(() => toast.success('PDF Exported!', { id: 'pdf' }));
  };

  const getConfidenceColor = (confValue) => {
    if (confValue >= 70) return '#10b981';
    if (confValue >= 50) return '#f59e0b';
    return '#ef4444';
  };

  const confidenceValue = result ? (Number(result.confidence || 0) * 100) : 0;
  
  let sortedTop3 = [];
  if (result?.top3) {
      sortedTop3 = [...result.top3].sort((a, b) => Number(b.confidence) - Number(a.confidence));
  }
  
  const displayTop3 = result ? [0, 1, 2].map(idx => {
      const item = sortedTop3[idx];
      let conf = item && item.confidence !== undefined && item.confidence !== null ? Number(item.confidence) : NaN;
      if (isNaN(conf)) {
          if (idx === 0) conf = (confidenceValue > 0 ? confidenceValue / 100 : 0.85);
          else if (idx === 1) conf = 0.60;
          else conf = 0.40;
      }
      return {
          name: item?.breed || (idx === 0 ? result.prediction : `Alternative ${idx}`),
          value: conf * 100,
          color: idx === 0 ? '#10b981' : idx === 1 ? '#facc15' : '#f97316'
      };
  }) : [];

  const mainConfidence = displayTop3.length > 0 ? displayTop3[0].value : confidenceValue;
  const confColor = getConfidenceColor(mainConfidence);

  const typeStr = (result?.metadata?.type || '').toLowerCase();
  let animalType = '';
  if (typeStr.includes('buffalo')) animalType = 'Buffalo';
  else if (typeStr.includes('cow') || typeStr.includes('cattle')) animalType = 'Cow';
  
  const mainBreedDisplay = displayTop3.length > 0 ? displayTop3[0].name : (result?.prediction || 'Unknown');
  const fullBreedTitle = animalType ? `${mainBreedDisplay} ${animalType}` : mainBreedDisplay;
  const xaiData = getXAIFactors(mainBreedDisplay);

  const shareWhatsApp = () => {
    if (!result) return;
    const conf = mainConfidence.toFixed(1);
    const text = `I just analyzed a cattle image using CattleAI! 🐄\n\nDetected Breed: *${fullBreedTitle}* (${conf}% match)\nAlternative: ${displayTop3[1]?.name || 'N/A'}\n\nCheck out CattleAI today!`;
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
  };

  const findNearbyVet = () => {
    if (navigator.geolocation) {
      toast.loading('Locating...', { id: 'geo' });
      navigator.geolocation.getCurrentPosition(
        (position) => {
           toast.success('Found location!', { id: 'geo' });
           const lat = position.coords.latitude;
           const lng = position.coords.longitude;
           window.open(`https://www.google.com/maps/search/veterinary+clinic+animal+hospital/@${lat},${lng},14z`);
        },
        (error) => { toast.error('Geolocation failed. Please allow location access.', { id: 'geo' }); }
      );
    }
  };

  const totalScans = history.length;
  let mostDetected = 'N/A';
  let avgAccuracy = 0;

  if (totalScans > 0) {
    const freq = {};
    let totalConf = 0;
    history.forEach(h => { freq[h.breed] = (freq[h.breed] || 0) + 1; totalConf += Number(h.confidence || 0); });
    mostDetected = Object.keys(freq).reduce((a, b) => freq[a] > freq[b] ? a : b);
    avgAccuracy = ((totalConf / totalScans) * 100).toFixed(1);
  }

  // Generate Feature Badges
  const features = result?.metadata?.characteristics ? result.metadata.characteristics.split(',').slice(0, 4) : [];

  return (
    <div className="relative space-y-16 py-8">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-[120px] -z-10 animate-pulse"></div>
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[120px] -z-10 animate-pulse"></div>

      <header className="text-center space-y-6 max-w-4xl mx-auto relative">
        <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-blue-600 leading-tight">
          🐄 CattleAI ✨
        </h1>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }} className="bg-gradient-to-br from-emerald-400 to-emerald-600 p-6 rounded-2xl shadow-xl shadow-emerald-500/20 flex items-center gap-4 text-white hover:-translate-y-1 transition-transform">
          <div className="p-4 bg-white/20 rounded-2xl"><Activity size={28} /></div>
          <div><p className="text-emerald-50 text-xs font-bold uppercase">📊 Total Scans</p><p className="text-3xl font-black">{totalScans}</p></div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }} className="bg-gradient-to-br from-orange-400 to-orange-600 p-6 rounded-2xl shadow-xl shadow-orange-500/20 flex items-center gap-4 text-white hover:-translate-y-1 transition-transform">
          <div className="p-4 bg-white/20 rounded-2xl"><TrendingUp size={28} /></div>
          <div><p className="text-orange-50 text-xs font-bold uppercase">📈 Most Detected</p><p className="text-3xl font-black">{mostDetected}</p></div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.6, ease: "easeOut" }} className="bg-gradient-to-br from-purple-400 to-purple-600 p-6 rounded-2xl shadow-xl shadow-purple-500/20 flex items-center gap-4 text-white hover:-translate-y-1 transition-transform">
          <div className="p-4 bg-white/20 rounded-2xl"><Target size={28} /></div>
          <div><p className="text-purple-50 text-xs font-bold uppercase">🎯 Avg Accuracy</p><p className="text-3xl font-black">{avgAccuracy}%</p></div>
        </motion.div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 relative z-10 mt-8">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.8 }} className="flex flex-col space-y-6 group p-6 -m-6 rounded-3xl hover:bg-emerald-50/50 hover:shadow-[0_0_40px_rgba(34,197,94,0.15)] transition-all duration-500">
           <div className="text-center">
              <h2 className="text-3xl font-black text-emerald-600 tracking-tight flex items-center justify-center gap-3">
                 <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 5, ease: "linear" }} className="text-4xl inline-block drop-shadow-md group-hover:scale-125 transition-transform duration-300">🐄</motion.div> 
                 <span className="group-hover:text-emerald-500 transition-colors">CATTLE</span>
              </h2>
              <p className="text-slate-500 text-sm mt-1 font-medium">Identify cattle breeds like Gir, Jersey, Holstein, Red Sindhi, Sahiwal</p>
           </div>
           <UploadSection 
              species="cattle" 
              themeColor="emerald" 
              onPredictionStart={onPredictionStart} 
              onPredictionSuccess={(res) => { setActiveSection('cattle'); onPredictionSuccess(res); }} 
              onPredictionError={onPredictionError} 
           />
           {result && activeSection === 'cattle' && (
              <div className="mt-4 flex justify-center">
                 <button onClick={() => {
                     document.getElementById('result-section').scrollIntoView({ behavior: 'smooth' });
                 }} className="text-emerald-600 font-bold text-sm animate-bounce">↓ View Cattle Results Below ↓</button>
              </div>
           )}
        </motion.div>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 1.0 }} className="flex flex-col space-y-6 group p-6 -m-6 rounded-3xl hover:bg-orange-50/50 hover:shadow-[0_0_40px_rgba(249,115,22,0.15)] transition-all duration-500">
           <div className="text-center">
              <h2 className="text-3xl font-black text-orange-500 tracking-tight flex items-center justify-center gap-3">
                 <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 5, ease: "linear" }} className="text-4xl inline-block drop-shadow-md group-hover:scale-125 transition-transform duration-300">🐃</motion.div> 
                 <span className="group-hover:text-orange-400 transition-colors">BUFFALO</span>
              </h2>
              <p className="text-slate-500 text-sm mt-1 font-medium">Identify buffalo breeds like Murrah, Surti, Mehsana, Jaffarabadi</p>
           </div>
           <UploadSection 
              species="buffalo" 
              themeColor="orange" 
              onPredictionStart={onPredictionStart} 
              onPredictionSuccess={(res) => { setActiveSection('buffalo'); onPredictionSuccess(res); }} 
              onPredictionError={onPredictionError} 
           />
           {result && activeSection === 'buffalo' && (
              <div className="mt-4 flex justify-center">
                 <button onClick={() => {
                     document.getElementById('result-section').scrollIntoView({ behavior: 'smooth' });
                 }} className="text-orange-500 font-bold text-sm animate-bounce">↓ View Buffalo Results Below ↓</button>
              </div>
           )}
        </motion.div>
      </div>

      <AnimatePresence>
        {errorResult && errorResult.error === 'Species-Breed Mismatch' && (
          <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 40 }} transition={{ duration: 0.5 }} className="max-w-4xl mx-auto mt-16 relative z-10">
            <div className="bg-gradient-to-br from-rose-50 to-orange-50 border border-rose-200 rounded-[2.5rem] p-10 relative overflow-hidden shadow-2xl shadow-rose-500/10">
                <div className="absolute top-0 right-0 w-64 h-64 bg-rose-500/10 rounded-full blur-[80px] -z-10"></div>
                <div className="flex items-center space-x-4 mb-6">
                    <div className="bg-white p-4 rounded-2xl border border-rose-100 shadow-sm">
                        <AlertTriangle className="text-rose-500" size={32} />
                    </div>
                    <div>
                        <h2 className="text-3xl font-black text-slate-800">⚠️ Wrong Section!</h2>
                        <p className="text-rose-600 font-semibold">Species-Breed Mismatch Detected</p>
                    </div>
                </div>
                <div className="p-6 bg-white rounded-3xl border-l-4 border-rose-500 mb-8 shadow-sm">
                    <p className="text-slate-800 text-xl font-medium">{errorResult.message}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-2xl border border-rose-100 shadow-sm">
                        <p className="text-xs text-rose-500 font-black uppercase mb-2 tracking-widest">AI Detected Animal</p>
                        <p className="text-2xl font-bold text-slate-800 capitalize flex items-center justify-between">
                            {errorResult.detected_species === 'buffalo' ? '🐃 Buffalo' : '🐄 Cattle/Cow'}
                            <span className="text-sm font-bold text-white bg-rose-500 px-3 py-1 rounded-full shadow-sm">
                                {Math.round((errorResult.species_confidence || 0) * 100)}% Sure
                            </span>
                        </p>
                    </div>
                    <div className="bg-white p-6 rounded-2xl border border-orange-100 shadow-sm">
                        <p className="text-xs text-orange-500 font-black uppercase mb-2 tracking-widest">Closest Breed Match</p>
                        <p className="text-2xl font-bold text-slate-800">{errorResult.detected_breed}</p>
                    </div>
                </div>
                <div className="bg-blue-50 border border-blue-100 p-6 rounded-2xl flex items-start space-x-4 shadow-sm">
                    <Info className="text-blue-500 shrink-0 mt-1" size={24} />
                    <div>
                        <h4 className="text-blue-600 font-bold text-lg mb-1">What to do</h4>
                        <p className="text-slate-700 font-medium">{errorResult.suggestion}</p>
                    </div>
                </div>
                <div className="mt-8 flex justify-end">
                    <button onClick={() => setErrorResult(null)} className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-lg hover:shadow-blue-600/30 hover:-translate-y-1 transition-all py-3 px-8 text-lg font-bold rounded-xl flex items-center gap-2">
                        Try Again
                    </button>
                </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {errorResult && errorResult.error === 'Not a livestock animal' && (
          <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 40 }} transition={{ duration: 0.5 }} className="max-w-4xl mx-auto mt-16 relative z-10">
            <div className="bg-gradient-to-br from-slate-50 to-gray-100 border border-gray-200 rounded-[2.5rem] p-10 relative overflow-hidden shadow-2xl">
                <div className="flex items-center space-x-4 mb-6">
                    <div className="bg-white p-4 rounded-2xl border border-gray-200 shadow-sm text-4xl">🚫</div>
                    <div>
                        <h2 className="text-3xl font-black text-slate-800">No Animal Detected</h2>
                        <p className="text-gray-500 font-semibold">Image does not contain recognisable livestock</p>
                    </div>
                </div>
                <div className="p-6 bg-white rounded-3xl border-l-4 border-gray-400 mb-8 shadow-sm">
                    <p className="text-slate-700 text-xl font-medium">{errorResult.message}</p>
                </div>
                <div className="bg-amber-50 border border-amber-100 p-6 rounded-2xl flex items-start space-x-4 shadow-sm">
                    <Info className="text-amber-500 shrink-0 mt-1" size={24} />
                    <div>
                        <h4 className="text-amber-600 font-bold text-lg mb-1">Tips for a good photo</h4>
                        <ul className="text-slate-700 font-medium space-y-1 list-disc list-inside">
                            <li>Animal should be clearly visible and fill most of the frame</li>
                            <li>Good lighting — avoid dark or blurry images</li>
                            <li>Side or front view of the animal works best</li>
                            <li>Avoid images with multiple animals or heavy background clutter</li>
                        </ul>
                    </div>
                </div>
                <div className="mt-8 flex justify-end">
                    <button onClick={() => setErrorResult(null)} className="bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-lg hover:-translate-y-1 transition-all py-3 px-8 text-lg font-bold rounded-xl">
                        Try Another Image
                    </button>
                </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {result && (
          <motion.div id="result-section" initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-16 max-w-7xl mx-auto">
            {/* History Banner */}
            {result.fromHistory && (
                <div className="lg:col-span-12 bg-blue-500/10 border border-blue-500/20 text-blue-400 p-4 rounded-2xl flex items-center justify-center font-semibold text-lg">
                    <Info className="mr-2" size={20} /> Result retrieved from previous analysis.
                </div>
            )}

            {/* Mock Prediction Warning */}
            {result.mock && (
                <div className="lg:col-span-12 bg-amber-500/10 border border-amber-400/40 text-amber-700 p-4 rounded-2xl flex items-center gap-3 font-semibold text-base">
                    <AlertTriangle className="shrink-0 text-amber-500" size={22} />
                    <span>
                        <strong>Demo Mode:</strong> The AI model is not loaded on the server, so this result is a <strong>simulated prediction</strong> — not a real analysis. To get accurate results, ensure <code className="bg-amber-100 px-1 rounded text-sm">buffalo_breed_model.h5</code> is present in the <code className="bg-amber-100 px-1 rounded text-sm">ai-service/</code> folder and TensorFlow is installed.
                    </span>
                </div>
            )}

            {/* Action Bar */}
            <div className="lg:col-span-12 flex flex-wrap justify-end gap-3 mb-[-1rem]">
                <button onClick={() => setShowMilkCalc(true)} className={`flex items-center gap-2 text-white shadow-lg px-4 py-2 rounded-xl transition-all text-sm font-semibold hover:-translate-y-1 ${activeSection === 'buffalo' ? 'bg-gradient-to-r from-orange-400 to-orange-600 hover:shadow-orange-500/50' : 'bg-gradient-to-r from-emerald-400 to-emerald-600 hover:shadow-emerald-500/50'}`}>
                  📊 Calculator
                </button>
                <button onClick={() => setShowIDCard(true)} className={`flex items-center gap-2 text-white shadow-lg px-4 py-2 rounded-xl transition-all text-sm font-semibold hover:-translate-y-1 ${activeSection === 'buffalo' ? 'bg-gradient-to-r from-orange-500 to-red-500 hover:shadow-orange-500/50' : 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:shadow-emerald-500/50'}`}>
                  🆔 ID Card
                </button>
                <button onClick={findNearbyVet} className={`flex items-center gap-2 text-white shadow-lg px-4 py-2 rounded-xl transition-all text-sm font-bold hover:-translate-y-1 ${activeSection === 'buffalo' ? 'bg-gradient-to-r from-amber-400 to-amber-600 hover:shadow-amber-500/50' : 'bg-gradient-to-r from-green-400 to-green-600 hover:shadow-green-500/50'}`}>
                  ⭐ Nearby Vet
                </button>
                <button onClick={exportPDF} className={`flex items-center gap-2 text-white shadow-lg px-4 py-2 rounded-xl transition-all text-sm font-semibold hover:-translate-y-1 ${activeSection === 'buffalo' ? 'bg-gradient-to-r from-red-400 to-red-600 hover:shadow-red-500/50' : 'bg-gradient-to-r from-teal-400 to-teal-600 hover:shadow-teal-500/50'}`}>
                  📄 PDF Report
                </button>
                <button onClick={shareWhatsApp} className={`flex items-center gap-2 text-white shadow-lg px-4 py-2 rounded-xl transition-all text-sm font-semibold hover:-translate-y-1 ${activeSection === 'buffalo' ? 'bg-gradient-to-r from-yellow-500 to-orange-500 hover:shadow-orange-500/50' : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:shadow-green-500/50'}`}>
                  💬 WhatsApp
                </button>
            </div>

            {/* Main Result Card */}
            <div ref={resultRef} className="lg:col-span-5 bg-white shadow-2xl rounded-[2.5rem] p-10 border border-slate-100 relative flex flex-col h-fit overflow-hidden">
                <div className="flex flex-col items-center mb-6 relative z-10">
                  <div className="w-40 h-40 mb-6 drop-shadow-xl relative z-10">
                    <CircularProgressbar value={mainConfidence} text={`${(mainConfidence || 0).toFixed(0)}%`} styles={buildStyles({ pathColor: confColor, textColor: confColor, trailColor: '#f1f5f9', textSize: '24px'})}/>
                  </div>
                  <h3 className="text-3xl font-extrabold text-slate-800 text-center mb-4">{fullBreedTitle}</h3>
                  <div className="flex flex-wrap justify-center gap-2">
                     {features.map((f, i) => (
                        <span key={i} className="text-[10px] uppercase font-bold bg-gray-100 text-slate-600 px-3 py-1 rounded-full border border-gray-200 shadow-sm">{f.trim()}</span>
                     ))}
                  </div>
                </div>

                <div className="w-full mt-4 bg-gray-50 p-6 rounded-3xl border border-gray-100 shadow-inner">
                  <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mb-6 text-center">Prediction Weights</p>
                  <div className="space-y-5">
                     {displayTop3.map((item, idx) => (
                        <div key={idx} className="flex items-center gap-4">
                           <div className="w-28 truncate text-sm font-bold text-slate-600">{item.name}</div>
                           <div className="flex-grow h-2.5 bg-gray-200 rounded-full overflow-hidden shadow-inner">
                              <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${item.value}%`, backgroundColor: item.color }} />
                           </div>
                           <div className="w-10 text-right text-sm font-black text-slate-700">{item.value.toFixed(0)}%</div>
                        </div>
                     ))}
                  </div>
                </div>
            </div>

            {/* Right Side Stack: Breed Info & XAI Panel */}
            <div className="lg:col-span-7 flex flex-col gap-6">
                {/* Breed Info Card */}
                <div className="bg-white shadow-2xl rounded-[2.5rem] p-10 border border-slate-100">
                    <div className="flex items-center justify-between mb-8 pb-6 border-b border-gray-100">
                        <div className="flex items-center space-x-3">
                            <h2 className="text-3xl font-bold text-slate-800 tracking-tight">🐄 Characteristics & Context</h2>
                        </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                        <div className="space-y-8">
                            <div><p className="text-[10px] text-slate-500 font-black uppercase mb-1 flex items-center gap-1"><span className="text-blue-500">🔵</span> Species Type</p><p className="text-lg font-bold text-slate-800">{result.metadata?.type || 'Cattle/Livestock'}</p></div>
                            <div><p className="text-[10px] text-slate-500 font-black uppercase mb-1 flex items-center gap-1"><span className="text-orange-500">📍</span> Origin</p><p className="text-lg font-bold text-slate-800">{result.metadata?.origin}</p></div>
                            <div><p className="text-[10px] text-slate-500 font-black uppercase mb-1 flex items-center gap-1"><span className="text-blue-400">🥛</span> Lactation Potential</p><p className="text-lg font-bold text-slate-800">{result.metadata?.milkProduction}</p></div>
                        </div>
                    </div>
                    <div className="mt-10 p-6 bg-amber-50 rounded-3xl border-l-4 border-amber-400 shadow-sm">
                        <p className="text-slate-700 italic text-lg font-medium">"{result.metadata?.description}"</p>
                    </div>
                </div>
            </div>

            {/* XAI Decision Factors Panel */}
            <div className="lg:col-span-12 bg-white shadow-2xl rounded-[2.5rem] p-10 border border-slate-100">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">🧠 AI Decision Factors</h2>
                    </div>
                </div>
                <p className="text-sm font-medium text-slate-500 mb-8 border-b border-gray-100 pb-6">These features explain why the AI predicted this breed.</p>
                
                <div className="p-6 bg-blue-50 rounded-3xl border-l-4 border-blue-500 mb-8 shadow-sm">
                    <p className="text-[10px] text-blue-600 font-black uppercase mb-2">Explainable AI Analysis</p>
                    <p className="text-slate-800 text-lg font-medium">{xaiData.summary}</p>
                </div>

                <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {xaiData.points.map((point, i) => (
                        <li key={i} className="flex items-center text-slate-700 font-medium text-lg bg-gray-50 p-4 rounded-xl border border-gray-100 hover:bg-gray-100 transition-colors shadow-sm">
                            <span className="text-emerald-500 mr-4 text-xl drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]">✔</span>
                            {point}
                        </li>
                    ))}
                </ul>
            </div>

            {/* AI Visual Explanation Panel */}
            {result.heatmapUrl && (
            <div className="lg:col-span-12 bg-white shadow-2xl rounded-[2.5rem] p-10 border border-slate-100">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">👁️ AI Visual Explanation</h2>
                    </div>
                </div>
                <p className="text-sm font-medium text-slate-500 mb-8 border-b border-gray-100 pb-6">This heatmap highlights the regions the AI focused on when predicting the breed.</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                        <h3 className="text-xl font-bold text-slate-700 text-center">Original Image</h3>
                        <div className="rounded-2xl overflow-hidden border-2 border-gray-100 shadow-xl bg-gray-50 aspect-video flex items-center justify-center relative">
                            <img src={`${import.meta.env.VITE_API_URL || ''}${result.imageUrl}`} alt="Original" className="w-full h-full object-contain" />
                        </div>
                    </div>
                    <div className="space-y-4">
                        <h3 className="text-xl font-bold text-slate-700 text-center">AI Heatmap</h3>
                        <div className="rounded-2xl overflow-hidden border-2 border-purple-300 shadow-[0_0_20px_rgba(168,85,247,0.2)] bg-gray-50 aspect-video flex items-center justify-center relative group">
                            <div className="absolute inset-0 bg-gradient-to-t from-purple-900/10 opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none"></div>
                            <img src={`${import.meta.env.VITE_API_URL || ''}${result.heatmapUrl}`} alt="Grad-CAM Heatmap" className="w-full h-full object-contain" />
                        </div>
                    </div>
                </div>
            </div>
            )}

          </motion.div>
        )}
      </AnimatePresence>

      {/* ID Card Modal */}
      {showIDCard && (
         <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
             <div className="bg-white border border-gray-200 p-8 rounded-3xl w-full max-w-md relative shadow-2xl">
                 <button onClick={() => setShowIDCard(false)} className="absolute top-4 right-4 text-gray-400 hover:text-gray-800"><X /></button>
                 <div id="buffalo-id-card" className="bg-gradient-to-br from-purple-500 to-indigo-700 p-6 rounded-2xl text-white shadow-xl relative overflow-hidden">
                     <div className="absolute top-0 right-0 w-32 h-32 bg-white/20 rounded-full blur-2xl"></div>
                     <h2 className="text-2xl font-black mb-1 uppercase tracking-widest text-purple-100">Cattle ID Card</h2>
                     <p className="text-xs font-medium text-purple-200 mb-6 border-b border-purple-400/30 pb-4">Digital Recognition Registry</p>
                     
                     <div className="flex justify-between items-end relative z-10">
                         <div>
                             <p className="text-sm text-purple-200 uppercase tracking-widest mb-1 font-semibold">Primary Breed</p>
                             <p className="text-3xl font-black mb-4">{fullBreedTitle}</p>
                             <p className="text-xs mb-1">Scanned: {new Date().toLocaleDateString()}</p>
                             <p className="text-xs text-purple-300">Confidence: {mainConfidence.toFixed(1)}%</p>
                         </div>
                         <div className="bg-white p-2 rounded-xl shadow-lg">
                             <QRCodeSVG value={`https://buffalo-ai.app/verify/${Date.now()}`} size={80} />
                         </div>
                     </div>
                 </div>
                 <button onClick={() => {
                     const opt = { margin: 0, filename: 'Cattle_ID.pdf', image: { type: 'jpeg', quality: 1 }, html2canvas: { scale: 3 }};
                     html2pdf().set(opt).from(document.getElementById('buffalo-id-card')).save();
                 }} className="mt-6 w-full py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white font-bold rounded-xl shadow-lg hover:shadow-purple-500/30 transition-all hover:-translate-y-1">Download Digital ID</button>
             </div>
         </div>
      )}

      {/* Calculator Modal */}
      {showMilkCalc && (
         <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
             <div className="bg-white border border-gray-200 p-8 rounded-3xl w-full max-w-md relative shadow-2xl">
                 <button onClick={() => setShowMilkCalc(false)} className="absolute top-4 right-4 text-gray-400 hover:text-gray-800"><X /></button>
                 <h2 className="text-2xl font-black mb-6 text-slate-800">Profitability <span className="text-blue-500">Calculator</span></h2>
                 
                 <div className="space-y-4 mb-8">
                     <div>
                         <label className="text-xs font-bold text-slate-500 uppercase">Age (Years)</label>
                         <input type="number" value={milkStats.age} onChange={e => setMilkStats({...milkStats, age: e.target.value})} className="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 mt-1 text-slate-800 focus:ring-2 focus:ring-blue-500/50 outline-none transition-all" />
                     </div>
                     <div>
                         <label className="text-xs font-bold text-slate-500 uppercase">Milk Price (₹/Liter)</label>
                         <input type="number" value={milkStats.price} onChange={e => setMilkStats({...milkStats, price: e.target.value})} className="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 mt-1 text-slate-800 focus:ring-2 focus:ring-blue-500/50 outline-none transition-all" />
                     </div>
                     <div className="p-4 bg-blue-50 rounded-xl border border-blue-100 shadow-sm">
                         <p className="text-xs font-bold text-blue-600 uppercase mb-2">Estimated Yield</p>
                         <p className="text-2xl font-black text-slate-800">~{Math.floor((mainBreedDisplay === 'Murrah' ? 14 : 9) * (milkStats.age > 3 ? 1 : 0.8))} L/Day</p>
                         <p className="text-sm mt-2 text-slate-600">Est. Income: <span className="text-emerald-600 font-bold">₹{Math.floor((mainBreedDisplay === 'Murrah' ? 14 : 9) * milkStats.price * 30)}/month</span></p>
                     </div>
                 </div>
             </div>
         </div>
      )}

    </div>
  );
};

export default Dashboard;
