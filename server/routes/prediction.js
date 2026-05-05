const express = require('express');
const router = express.Router();
const multer = require('multer');
const axios = require('axios');
const path = require('path');
const fs = require('fs');
const FormData = require('form-data');
const Prediction = require('../models/Prediction');
const auth = require('../middleware/auth');
const crypto = require('crypto');

// Multer Config
const storage = multer.diskStorage({
    destination: './uploads/',
    filename: (req, file, cb) => {
        cb(null, `${Date.now()}-${file.originalname}`);
    }
});

const upload = multer({
    storage: storage,
    limits: { fileSize: 5000000 }, // 5MB limit
    fileFilter: (req, file, cb) => {
        const filetypes = /jpeg|jpg|png/;
        const extname = filetypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = filetypes.test(file.mimetype);
        if (mimetype && extname) {
            return cb(null, true);
        } else {
            cb('Error: Images Only!');
        }
    }
});

// @route   POST api/prediction/predict/:species
// @desc    Upload image and get prediction
router.post('/predict/:species', [auth, upload.single('image')], async (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ msg: 'No image uploaded' });
        
        const species = req.params.species;
        if (species !== 'cattle' && species !== 'buffalo') {
            return res.status(400).json({ msg: 'Invalid species' });
        }

        const imagePath = req.file.path;
        const fileBuffer = fs.readFileSync(imagePath);
        const imageHash = crypto.createHash('md5').update(fileBuffer).digest('hex');

        // Check if image Hash exists
        const existingPrediction = await Prediction.findOne({ imageHash: imageHash });

        if (existingPrediction) {
            console.log("Image found in cache, but bypassing to force new AI prediction.");
            // Delete the old wrong prediction from the database so it can be replaced
            await Prediction.deleteOne({ _id: existingPrediction._id });
        }
        
        // Prepare data for Python AI service
        const formData = new FormData();
        formData.append('image', fs.createReadStream(imagePath));

        // Call Python Flask API
        const AI_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';
        const response = await axios.post(`${AI_URL}/predict/${species}`, formData, {
            headers: {
                ...formData.getHeaders()
            },
            timeout: 120000 // 2 minute timeout for cold starts on free tier
        });

        const { prediction, confidence, top3, info, heatmap, quality } = response.data;

        let heatmapUrl = '';
        if (heatmap) {
            const base64Data = heatmap.replace(/^data:image\/\w+;base64,/, "");
            const heatmapName = `heatmap_${Date.now()}.jpg`;
            require('fs').writeFileSync(`./uploads/${heatmapName}`, base64Data, 'base64');
            heatmapUrl = `/uploads/${heatmapName}`;
        }

        const newPrediction = new Prediction({
            userId: req.user.id,
            imageName: req.file.filename,
            imageUrl: `/uploads/${req.file.filename}`,
            breed: prediction,
            confidence: confidence,
            top3: top3,
            metadata: info,
            heatmapUrl: heatmapUrl,
            imageHash: imageHash,
            imageQuality: quality
        });

        await newPrediction.save();

        res.json(newPrediction);
    } catch (err) {
        if (err.response) {
            console.error('Python API Error Data:', err.response.data);
            console.error('Python API Status:', err.response.status);
        } else {
            console.error('Prediction Route Error:', err.message);
        }
        res.status(500).json({ 
            msg: 'Prediction Service Error. Make sure AI service is running.', 
            error: err.response?.data?.error || err.message,
            trace: err.response?.data?.trace
        });
    }
});

// @route   GET api/prediction/history
// @desc    Get user's prediction history
router.get('/history', auth, async (req, res) => {
    try {
        const history = await Prediction.find({ userId: req.user.id }).sort({ createdAt: -1 });
        res.json(history);
    } catch (err) {
        console.error(err.message);
        res.status(500).json({ msg: 'Server Error' });
    }
});

// @route   GET api/prediction/stats
// @desc    Get system stats for admin
router.get('/stats', auth, async (req, res) => {
    try {
        // Simple admin check (this should be more robust)
        if (req.user.role !== 'admin') return res.status(401).json({ msg: 'Not authorized' });

        const totalPredictions = await Prediction.countDocuments();
        const breedStats = await Prediction.aggregate([
            { $group: { _id: "$breed", count: { $sum: 1 } } }
        ]);

        res.json({ totalPredictions, breedStats });
    } catch (err) {
        console.error(err.message);
        res.status(500).json({ msg: 'Server Error' });
    }
});

module.exports = router;
