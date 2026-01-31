import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { storage } from '../firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import Layout from '../components/Layout';
import { useNavigate } from 'react-router-dom';

const API_BASE = 'http://localhost:8000/api/v1';

const Observe = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [futureImages, setFutureImages] = useState([]);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  // Load saved state on mount
  useEffect(() => {
    if (!currentUser) return;
    
    const fetchState = async () => {
        try {
            const token = await currentUser.getIdToken();
            const res = await fetch(`${API_BASE}/decide/state`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.observeCompleted) {
                    setIsCompleted(true);
                    setAnalysis(data.analysis);
                    setFutureImages(data.generatedImages);
                    
                    // Load original image preview
                    if (data.originalImage) {
                        try {
                            const url = await getDownloadURL(ref(storage, data.originalImage));
                            setPreview(url);
                        } catch (e) {
                            console.error("Failed to load original image:", e);
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Failed to load state:", err);
        }
    };
    
    fetchState();
  }, [currentUser]);

  const handleImageChange = (e) => {
    if (e.target.files[0]) {
      setImage(e.target.files[0]);
      setPreview(URL.createObjectURL(e.target.files[0]));
      setAnalysis(null);
      setFutureImages([]);
      setError(null);
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!image || !currentUser) return;
    setLoading(true);
    setError(null);

    try {
      // 1. Upload Image
      const storagePath = `users/${currentUser.uid}/observe/original.jpg`;
      const storageRef = ref(storage, storagePath);
      await uploadBytes(storageRef, image);
      
      // 2. Call Backend Analysis
      const token = await currentUser.getIdToken();
      const res = await fetch(`${API_BASE}/observe/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ storage_path: storagePath })
      });
      
      if (!res.ok) {
          const errText = await res.text();
          throw new Error(`Analysis Failed: ${errText}`);
      }
      const data = await res.json();
      setAnalysis(data);
      setLoading(false);
      
      // 3. Trigger Generation (Parallel)
      generateImages(storagePath, token);
      
    } catch (error) {
      console.error("Error:", error);
      setError(error.message);
      setLoading(false);
    }
  };

  const generateImages = async (storagePath, token) => {
    setGenLoading(true);
    const goals = ['lean', 'athletic', 'muscle'];
    
    try {
        const promises = goals.map(goal => 
            fetch(`${API_BASE}/observe/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ storage_path: storagePath, goal })
            }).then(async r => {
                if (!r.ok) throw new Error(await r.text());
                return r.json();
            })
        );
        
        const results = await Promise.all(promises);
        // results = [{url: ..., path: ...}, ...]
        setFutureImages(results.map((r, i) => ({ ...r, goal: goals[i] })));
        
    } catch (e) {
        console.error("Generation error:", e);
        setError("Failed to generate physique images. " + e.message);
    } finally {
        setGenLoading(false);
    }
  };

  const handleContinue = async () => {
    if (!currentUser || !analysis || futureImages.length === 0) return;
    setSaving(true);
    try {
        const token = await currentUser.getIdToken();
        const storagePath = `users/${currentUser.uid}/observe/original.jpg`;
        
        const res = await fetch(`${API_BASE}/decide/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                original_image_path: storagePath,
                analysis: analysis,
                generated_images: futureImages
            })
        });
        
        if (!res.ok) throw new Error("Failed to save progress");
        
        setIsCompleted(true);
        // Navigate to Decide phase
        navigate('/decide');
    } catch (e) {
        setError(e.message);
    } finally {
        setSaving(false);
    }
  };

  return (
    <Layout currentStep={0}>
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Observe Phase: Body Analysis</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">1. Upload Your Photo</h2>
            {isCompleted && (
                <div className="alert alert-success mb-4">
                    <span>Progress Saved! Upload a new photo to start over.</span>
                </div>
            )}
            
            <p className="text-sm text-gray-500">Upload a full-body front-facing photo.</p>
            <input 
                type="file" 
                className="file-input file-input-bordered file-input-primary w-full max-w-xs" 
                accept="image/*"
                onChange={handleImageChange}
                disabled={loading || genLoading}
            />
            
            {preview && (
              <div className="mt-4 flex justify-center bg-base-200 p-4 rounded-xl">
                <img src={preview} alt="Preview" className="rounded-lg max-h-80 object-contain" />
              </div>
            )}
            {error && <div className="alert alert-error mt-4"><span>{error}</span></div>}
            
            {!isCompleted && (
                <div className="card-actions justify-end mt-4">
                  <button 
                    className="btn btn-primary w-full" 
                    onClick={handleUploadAndAnalyze}
                    disabled={!image || loading || genLoading}
                  >
                    {loading ? <span className="loading loading-spinner"></span> : "Analyze & Generate"}
                  </button>
                </div>
            )}
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-8">
            {/* Analysis Text */}
            {analysis && (
            <div className="card bg-base-100 shadow-xl border border-secondary">
                <div className="card-body">
                <h2 className="card-title text-secondary">2. AI Analysis</h2>
                <div className="badge badge-lg badge-secondary mb-2">{analysis.category}</div>
                <p className="text-lg">{analysis.reasoning}</p>
                </div>
            </div>
            )}

            {/* Generated Images */}
            {(genLoading || futureImages.length > 0) && (
                <div className="card bg-base-100 shadow-xl">
                    <div className="card-body">
                        <h2 className="card-title">3. Future Potentials</h2>
                        {genLoading && <div className="flex justify-center p-8"><span className="loading loading-spinner loading-lg text-primary"></span><span className="ml-2 mt-2">Generating future you...</span></div>}
                        
                        <div className="grid grid-cols-1 gap-4">
                            {futureImages.map((img, idx) => (
                                <div key={idx} className="card bg-base-200">
                                    <figure className="px-4 pt-4">
                                        <img src={img.url} alt={img.goal} className="rounded-xl w-full" />
                                    </figure>
                                    <div className="card-body items-center text-center p-4">
                                        <h2 className="card-title capitalize">{img.goal}</h2>
                                    </div>
                                </div>
                            ))}
                        </div>
                        
                        {/* Continue Button */}
                        {!isCompleted && !genLoading && futureImages.length > 0 && (
                            <div className="card-actions justify-end mt-6">
                                <button 
                                    className="btn btn-accent btn-lg w-full"
                                    onClick={handleContinue}
                                    disabled={saving}
                                >
                                    {saving ? <span className="loading loading-spinner"></span> : "Continue & Save Progress"}
                                </button>
                            </div>
                        )}
                        
                        {isCompleted && (
                            <div className="card-actions justify-end mt-6">
                                <button className="btn btn-primary w-full" onClick={() => navigate('/decide')}>
                                    Go to Decision Phase →
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
      </div>
    </div>
    </Layout>
  );
};

export default Observe;
