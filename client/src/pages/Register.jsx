import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, Loader2, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

const Register = ({ login }) => {
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const onChange = e => setFormData({ ...formData, [e.target.name]: e.target.value });

  const onSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      let data;
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") !== -1) {
        data = await response.json();
      } else {
        const text = await response.text();
        data = { msg: text || 'An unexpected error occurred' };
      }

      if (response.ok) {
        login(data.user, data.token);
        navigate('/');
      } else {
        setError(data.msg || 'Registration failed');
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError('Connection failed. Please ensure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Left Panel: Gradient Branding & Animated Logo */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col items-center justify-center p-12 overflow-hidden bg-gradient-to-br from-emerald-500 to-sky-500">
        {/* Animated Background Elements */}
        <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] bg-white/10 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-white/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }}></div>
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="relative z-10 flex flex-col items-center text-center space-y-8"
        >
          <div className="relative group floating">
            <div className="absolute -inset-4 bg-white/30 rounded-full blur-lg opacity-50 group-hover:opacity-80 transition duration-1000"></div>
            <div className="relative bg-white/20 p-8 rounded-full border border-white/30 backdrop-blur-xl w-48 h-48 flex items-center justify-center">
               <motion.div 
                 animate={{ rotate: 360 }} 
                 transition={{ repeat: Infinity, duration: 5, ease: "linear" }} 
                 className="text-7xl drop-shadow-lg"
               >
                 🐄
               </motion.div>
            </div>
          </div>

          <div className="space-y-4">
            <h1 className="text-5xl font-black tracking-tight text-white drop-shadow-md">
              Cattle<span className="text-emerald-200">AI</span>
            </h1>
            <p className="text-xl text-white/90 font-medium max-w-md leading-relaxed drop-shadow-sm">
              Join our global network of researchers and livestock management professionals.
            </p>
          </div>

          <div className="flex items-center space-x-6 pt-4">
            <div className="flex flex-col items-center bg-white/10 px-6 py-3 rounded-2xl backdrop-blur-md border border-white/20 shadow-sm">
              <span className="text-3xl font-black text-white">Global</span>
              <span className="text-xs uppercase tracking-widest text-emerald-100 font-bold mt-1">Network</span>
            </div>
            <div className="flex flex-col items-center bg-white/10 px-6 py-3 rounded-2xl backdrop-blur-md border border-white/20 shadow-sm">
              <span className="text-3xl font-black text-white">Advanced</span>
              <span className="text-xs uppercase tracking-widest text-emerald-100 font-bold mt-1">Tools</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Right Panel: White Register Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative">
        {/* Mobile Header (Hidden on Desktop) */}
        <div className="lg:hidden absolute top-0 left-0 w-full p-8 bg-gradient-to-br from-emerald-500 to-sky-500 rounded-b-[3rem] shadow-lg flex flex-col items-center justify-center text-white z-0 h-64">
           <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 5, ease: "linear" }} className="text-5xl drop-shadow-md mb-2">🐄</motion.div>
           <h1 className="text-3xl font-black tracking-tight drop-shadow-md">CattleAI</h1>
        </div>

        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="w-full max-w-md relative z-10 mt-32 lg:mt-0"
        >
          <div className="bg-white rounded-3xl p-10 border border-gray-100 shadow-2xl relative overflow-hidden">
            <div className="mb-8 text-center lg:text-left">
              <h2 className="text-4xl font-extrabold tracking-tight text-slate-800 mb-2">
                Create <span className="text-emerald-500">Account</span>
              </h2>
              <p className="text-slate-500 font-medium">Join the CattleAI researcher community</p>
            </div>
    
            {error && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-2xl text-sm mb-6 text-center shadow-sm"
                >
                    {error}
                </motion.div>
            )}
    
            <form onSubmit={onSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-500 ml-1">Full Name</label>
                <div className="relative group">
                    <User className="absolute left-4 top-4 text-slate-400 group-focus-within:text-emerald-500 transition-colors" size={18} />
                    <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={onChange}
                        placeholder="John Doe"
                        className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-12 pr-4 py-3.5 text-slate-800 focus:ring-2 focus:ring-emerald-500 focus:bg-white outline-none transition-all shadow-sm"
                        required
                    />
                </div>
              </div>
    
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-500 ml-1">Email Address</label>
                <div className="relative group">
                    <Mail className="absolute left-4 top-4 text-slate-400 group-focus-within:text-emerald-500 transition-colors" size={18} />
                    <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={onChange}
                        placeholder="name@example.com"
                        className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-12 pr-4 py-3.5 text-slate-800 focus:ring-2 focus:ring-emerald-500 focus:bg-white outline-none transition-all shadow-sm"
                        required
                    />
                </div>
              </div>
    
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-500 ml-1">Password</label>
                <div className="relative group">
                    <Lock className="absolute left-4 top-4 text-slate-400 group-focus-within:text-emerald-500 transition-colors" size={18} />
                    <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={onChange}
                        placeholder="••••••••"
                        className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-12 pr-4 py-3.5 text-slate-800 focus:ring-2 focus:ring-emerald-500 focus:bg-white outline-none transition-all shadow-sm"
                        required
                        minLength="6"
                    />
                </div>
              </div>
    
              <button 
                type="submit" 
                disabled={loading}
                className="w-full py-4 flex items-center justify-center space-x-2 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-bold rounded-xl shadow-xl hover:shadow-emerald-500/40 hover:-translate-y-1 transition-all duration-300 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:hover:translate-y-0 text-lg group mt-6"
              >
                {loading ? <Loader2 className="animate-spin" size={20} /> : (
                  <>
                    <span className="font-bold tracking-wide">Create Account</span>
                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </form>
    
            <div className="mt-8 text-center lg:text-left">
              <p className="text-slate-600 text-sm font-medium">
                Already have an account? {' '}
                <Link to="/login" className="text-emerald-500 font-bold hover:text-emerald-600 transition-colors inline-flex items-center space-x-1 group">
                  <span>Sign In</span>
                  <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Register;
