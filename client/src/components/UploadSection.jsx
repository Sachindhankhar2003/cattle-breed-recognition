import React, { useState, useCallback } from 'react';
import { Upload, X, ImageIcon, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

const UploadSection = ({ onPredictionStart, onPredictionSuccess, onPredictionError, species = 'cattle', themeColor = 'emerald' }) => {
  const [dragActive, setDragActive] = useState(false);
  const [previews, setPreviews] = useState([]);
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Dynamic colors based on theme
  const getThemeClasses = () => {
    if (themeColor === 'orange') {
      return {
        borderActive: 'border-orange-500 bg-orange-50',
        borderHover: 'hover:border-orange-400 hover:bg-orange-50',
        textMain: 'text-orange-600',
        bgLight: 'bg-orange-100',
        btnGradient: 'bg-gradient-to-r from-orange-500 to-orange-600 hover:shadow-orange-500/40',
        focusRing: 'focus:ring-orange-500'
      };
    }
    return {
      borderActive: 'border-emerald-500 bg-emerald-50',
      borderHover: 'hover:border-emerald-400 hover:bg-emerald-50',
      textMain: 'text-emerald-600',
      bgLight: 'bg-emerald-100',
      btnGradient: 'bg-gradient-to-r from-emerald-500 to-emerald-600 hover:shadow-emerald-500/40',
      focusRing: 'focus:ring-emerald-500'
    };
  };

  const theme = getThemeClasses();

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const processFiles = async (selectedFiles) => {
    const fileArray = Array.from(selectedFiles);
    if (fileArray.length > 0) {
      setIsUploading(true);
      toast.loading('Enhancing images...', { id: 'enhance' });
      
      const enhancedFiles = await Promise.all(fileArray.map(async (file) => {
        return new Promise((resolve) => {
           const reader = new FileReader();
           reader.onload = (e) => {
              const img = new Image();
              img.onload = () => {
                 const canvas = document.createElement('canvas');
                 canvas.width = img.width;
                 canvas.height = img.height;
                 const ctx = canvas.getContext('2d');
                 // Auto enhance: contrast, saturation, brightness
                 ctx.filter = 'contrast(1.2) saturate(1.1) brightness(1.05)';
                 ctx.drawImage(img, 0, 0);
                 canvas.toBlob((blob) => {
                    const safeName = file.name || `capture_${Date.now()}.jpg`;
                    const enhancedFile = new File([blob], safeName, { type: 'image/jpeg' });
                    resolve(enhancedFile);
                 }, 'image/jpeg', 0.95);
              };
              img.src = e.target.result;
           };
           reader.readAsDataURL(file);
        });
      }));

      setFiles(enhancedFiles);
      setPreviews(enhancedFiles.map(f => URL.createObjectURL(f)));
      toast.success('Images enhanced!', { id: 'enhance' });
      setIsUploading(false);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files) {
      processFiles(e.dataTransfer.files);
    }
  }, []);

  const handleChange = (e) => {
    if (e.target.files) {
      processFiles(e.target.files);
    }
  };

  const removeImage = (indexToRemove) => {
    setFiles(files.filter((_, i) => i !== indexToRemove));
    setPreviews(previews.filter((_, i) => i !== indexToRemove));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    onPredictionStart();
    const token = localStorage.getItem('token');
    
    try {
      let lastData = null;
      let lastError = null;
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        const filename = file.name && file.name.includes('.') ? file.name : `capture_${Date.now()}.jpg`;
        formData.append('image', file, filename);

        const API_BASE = import.meta.env.VITE_API_URL || '';
        const response = await fetch(`${API_BASE}/api/prediction/predict/${species}`, {
          method: 'POST',
          headers: { 'x-auth-token': token },
          body: formData
        });

        if (response.ok) {
          lastData = await response.json();
          setUploadProgress(i + 1);
        } else {
          const errText = await response.text();
          let errObj = {};
          try { errObj = JSON.parse(errText); } catch(e) {}

          lastError = errObj;

          // 422 = structured error (mismatch / not-animal) — pass to onPredictionError, don't toast
          if (response.status === 422) {
            break;
          }

          const msg = errObj.trace ? `Python crash: ${errObj.error}` : errObj.error || errObj.msg || errText.substring(0, 50);
          console.error('Failed to upload file', errText);
          toast.error(`Upload failed: ${msg}`);
          break;
        }
      }

      if (lastError) {
        if (onPredictionError) onPredictionError(lastError);
      } else if (lastData) {
        onPredictionSuccess(lastData);
      } else {
        toast.error('Prediction failed, no valid response.');
      }
    } catch (err) {
      console.error('Upload error:', err);
      toast.error('Error connecting to server. Please check your connection.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="w-full mx-auto">
      <div 
        className={`relative p-8 bg-white border-2 border-dashed rounded-2xl transition-all duration-300 shadow-sm ${
          dragActive ? theme.borderActive : `border-gray-300 ${theme.borderHover}`
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {previews.length === 0 ? (
          <div className="flex flex-col md:flex-row gap-4 w-full h-full justify-center">
            <label className={`relative flex-grow p-8 text-center border border-gray-200 rounded-2xl cursor-pointer transition-colors group ${theme.borderHover}`}>
              <input 
                type="file" 
                multiple
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
                onChange={handleChange}
                accept="image/*"
              />
              <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 6, ease: "linear" }} className={`${theme.bgLight} w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform shadow-sm`}>
                <Upload className={theme.textMain} size={24} />
              </motion.div>
              <h3 className="text-xl font-semibold mb-2 text-slate-800">Upload {species === 'buffalo' ? 'Buffalo' : 'Cattle'} Images</h3>
              <p className="text-xs text-slate-500">Drag & drop or select multiple</p>
            </label>
            
            <label className={`relative flex-grow p-8 text-center border border-gray-200 rounded-2xl cursor-pointer transition-colors group ${theme.borderHover}`}>
               <input 
                type="file" 
                capture="environment"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
                onChange={handleChange}
                accept="image/*"
              />
              <motion.div animate={{ rotate: -360 }} transition={{ repeat: Infinity, duration: 6, ease: "linear" }} className={`${theme.bgLight} w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform shadow-sm`}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={theme.textMain}><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>
              </motion.div>
              <h3 className="text-lg font-semibold mb-1 text-slate-800">Take Photo</h3>
              <p className="text-xs text-slate-500">Use device camera</p>
            </label>
          </div>
        ) : (
          <div className="relative z-20">
            <h3 className={`text-lg font-medium ${theme.textMain} mb-4`}>{previews.length} File{previews.length > 1 ? 's' : ''} Selected</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {previews.map((preview, idx) => (
                <motion.div 
                  key={idx}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="relative rounded-xl overflow-hidden shadow-md border border-gray-200 group"
                >
                  <button 
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); removeImage(idx); }}
                    className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 shadow-md z-10 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X size={14} />
                  </button>
                  <img src={preview} alt={`Preview ${idx}`} className="w-full h-24 object-cover" />
                </motion.div>
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-4 text-center">Batch mode: Only the last scan result will appear in details below, but all are saved in History.</p>
          </div>
        )}
      </div>

      <AnimatePresence>
        {previews.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mt-8 text-center"
          >
            <button 
              onClick={handleUpload}
              disabled={isUploading}
              className={`w-full py-4 flex items-center justify-center space-x-2 text-white font-bold rounded-xl shadow-xl hover:-translate-y-1 transition-all duration-300 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:hover:translate-y-0 text-lg ${theme.btnGradient}`}
            >
              {isUploading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span>Processing... {uploadProgress}/{files.length}</span>
                </>
              ) : (
                <>
                  <span>🔍 {files.length > 1 ? 'Batch Analyze' : `Identify ${species === 'buffalo' ? 'Buffalo' : 'Cattle'} Breed`}</span>
                </>
              )}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default UploadSection;
