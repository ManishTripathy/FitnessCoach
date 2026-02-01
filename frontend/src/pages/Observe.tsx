import React, { useState, useEffect, ChangeEvent } from 'react';
import { useAuth } from '../auth/AuthContext';
import { storage } from '../firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import Layout from '../components/Layout';
import { useNavigate } from 'react-router-dom';
import { API_BASE } from '../config';

interface AnalysisData {
    category: string;
    reasoning: string;
}

interface GeneratedImage {
    url: string;
    goal: string;
    path: string;
    prompt?: string;
}

const Observe: React.FC = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [futureImages, setFutureImages] = useState<GeneratedImage[]>([]);
  const [error, setError] = useState<string | null>(null);
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
                    setFutureImages(data.generatedImages || []);
                    
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

  const handleImageChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
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
      
    } catch (err: any) {
      console.error(err);
      setError(err.message || "An error occurred");
      setLoading(false);
    }
  };

  const generateImages = async (storagePath: string, token: string) => {
      setGenLoading(true);
      const goals = ['lean', 'athletic', 'muscle'];
      try {
          const promises = goals.map(async (goal) => {
              const res = await fetch(`${API_BASE}/observe/generate`, {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${token}`
                  },
                  body: JSON.stringify({ storage_path: storagePath, goal })
              });
              
              if (!res.ok) throw new Error(`Failed to generate ${goal}`);
              
              const data = await res.json();
              // data is { url, path }
              return {
                  goal,
                  url: data.url,
                  path: data.path,
                  prompt: `Future ${goal} self`
              } as GeneratedImage;
          });

          const results = await Promise.all(promises);
          setFutureImages(results);
          
      } catch (err: any) {
          console.error("Generation error:", err);
          setError("Analysis complete, but failed to generate some future visualizations.");
      } finally {
          setGenLoading(false);
      }
  };

  const handleProceed = async () => {
      if (!currentUser || !analysis) return;
      setSaving(true);
      try {
          const token = await currentUser.getIdToken();
          const storagePath = `users/${currentUser.uid}/observe/original.jpg`;
          
          const body = {
              original_image_path: storagePath,
              analysis: analysis,
              generated_images: futureImages
          };

          const res = await fetch(`${API_BASE}/decide/save`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify(body)
          });

          if (!res.ok) throw new Error("Failed to save progress");

          navigate('/decide');
      } catch (err: any) {
          console.error(err);
          setError("Failed to save progress: " + err.message);
      } finally {
          setSaving(false);
      }
  };

  return (
    <Layout currentStep={0}>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">Phase 1: Observe</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Upload Section */}
            <div className="card bg-base-100 shadow-xl">
                <div className="card-body">
                    <h2 className="card-title">Upload Your Photo</h2>
                    <p className="text-sm text-gray-500 mb-4">Upload a full-body photo for AI analysis.</p>
                    
                    <input 
                        type="file" 
                        className="file-input file-input-bordered file-input-primary w-full max-w-xs" 
                        onChange={handleImageChange}
                        accept="image/*"
                    />
                    
                    {preview && (
                        <div className="mt-4 relative">
                            <img src={preview} alt="Preview" className="rounded-lg shadow-md max-h-96 object-cover mx-auto" />
                        </div>
                    )}
                    
                    <div className="card-actions justify-end mt-4">
                        <button 
                            className={`btn btn-primary ${loading ? 'loading' : ''}`}
                            onClick={handleUploadAndAnalyze}
                            disabled={!image || loading || genLoading}
                        >
                            {loading ? 'Analyzing...' : 'Analyze & Visualize'}
                        </button>
                    </div>
                    {error && <p className="text-error mt-2 text-sm">{error}</p>}
                </div>
            </div>

            {/* Results Section */}
            <div className="flex flex-col gap-6">
                {/* Analysis Result */}
                {analysis && (
                    <div className="card bg-base-100 shadow-xl animate-fade-in">
                        <div className="card-body">
                            <h2 className="card-title text-secondary">AI Analysis</h2>
                            <div className="divider my-0"></div>
                            <div className="prose">
                                <p><strong>Body Category:</strong> {analysis.category}</p>
                                <p><strong>Analysis:</strong> {analysis.reasoning}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Generated Futures */}
                {genLoading && (
                    <div className="alert alert-info shadow-lg">
                        <div>
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current flex-shrink-0 w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            <span>Generating your potential future selves... (This takes ~10-20s)</span>
                        </div>
                    </div>
                )}

                {futureImages.length > 0 && (
                    <div className="card bg-base-100 shadow-xl animate-fade-in">
                        <div className="card-body">
                            <h2 className="card-title text-accent">Potential Futures</h2>
                            <div className="carousel rounded-box w-full space-x-4 p-4 bg-neutral-focus">
                                {futureImages.map((img, idx) => (
                                    <div key={idx} className="carousel-item flex flex-col items-center">
                                        <img src={img.url} alt={img.goal} className="rounded-box h-64 object-cover" />
                                        <span className="badge badge-outline mt-2">{img.goal}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>

        {/* Navigation */}
        {(analysis || isCompleted) && (
            <div className="mt-8 flex justify-center">
                <button 
                    className="btn btn-secondary btn-lg btn-wide gap-2"
                    onClick={handleProceed}
                    disabled={saving || genLoading}
                >
                    Proceed to Phase 2: Decide
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
                </button>
            </div>
        )}
      </div>
    </Layout>
  );
};

export default Observe;
