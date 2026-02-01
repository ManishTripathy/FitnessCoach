import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { API_BASE } from '../config';

interface GeneratedImage {
    url: string;
    goal: string;
    prompt?: string;
}

interface Recommendation {
    suggested_path: string;
    reasoning: string;
    confidence_score: number;
}

const Decide: React.FC = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [images, setImages] = useState<GeneratedImage[]>([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [committed, setCommitted] = useState(false);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  useEffect(() => {
    if (!currentUser) return;
    fetchState();
  }, [currentUser]);

  const fetchState = async () => {
    try {
      if (!currentUser) return;
      const token = await currentUser.getIdToken();
      const res = await fetch(`${API_BASE}/decide/state`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.decideCompleted && data.selectedPath) {
             setCommitted(true);
             setSelectedPath(data.selectedPath);
        }
        if (data.generatedImages) {
             setImages(data.generatedImages);
        } else {
             setError("No generated images found. Please complete the Observe phase.");
        }
      }
    } catch (err) {
      console.error(err);
      setError("Failed to load images.");
    } finally {
      setLoading(false);
    }
  };

  const handleAskAI = async () => {
    setAiLoading(true);
    setError(null);
    try {
      if (!currentUser) return;
      const token = await currentUser.getIdToken();
      const res = await fetch(`${API_BASE}/decide/suggest`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) {
          throw new Error(await res.text());
      }
      
      const data = await res.json();
      setRecommendation(data.recommendation);
      
    } catch (err: any) {
      console.error(err);
      setError("Failed to get AI suggestion: " + err.message);
    } finally {
      setAiLoading(false);
    }
  };

  const handleSelectPath = async (pathKey: string) => {
    if (committed && selectedPath === pathKey) return; // Already selected this one
    
    if (!window.confirm(`Are you sure you want to ${committed ? 'switch' : 'commit'} to the ${pathKey} path?`)) return;
    
    try {
      if (!currentUser) return;
      const token = await currentUser.getIdToken();
      const res = await fetch(`${API_BASE}/decide/commit`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({
            selected_path: pathKey,
            source: recommendation ? 'ai_suggested' : 'user_selected',
            ai_recommendation: recommendation
        })
      });
      
      if (!res.ok) throw new Error("Failed to commit path");
      
      setCommitted(true);
      setSelectedPath(pathKey);
      alert("Path updated! You have completed the Decision phase.");
      // Navigate to Act phase
      navigate('/act');
    } catch (err: any) {
        console.error(err);
        setError("Failed to commit selection: " + err.message);
    }
  };

  if (loading) return <div className="p-8 text-center"><span className="loading loading-spinner loading-lg"></span></div>;

  return (
    <Layout currentStep={committed ? 2 : 1}>
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-2 text-center">Decide Your Path</h1>
      <p className="text-center text-gray-500 mb-8">Review your potential futures and commit to a goal.</p>

      {error && <div className="alert alert-error mb-4">{error}</div>}

      {/* AI Suggestion Section */}
      <div className="flex justify-center mb-8">
        {!recommendation ? (
            <button 
                className={`btn btn-accent btn-lg gap-2 ${aiLoading ? 'loading' : ''}`}
                onClick={handleAskAI}
                disabled={aiLoading}
            >
                ✨ Ask AI for Recommendation
            </button>
        ) : (
            <div className="card bg-accent text-accent-content shadow-lg w-full max-w-2xl animate-fade-in">
                <div className="card-body">
                    <h2 className="card-title">AI Recommendation: {recommendation.suggested_path}</h2>
                    <p>{recommendation.reasoning}</p>
                    <div className="badge badge-outline">Confidence: {Math.round(recommendation.confidence_score * 100)}%</div>
                </div>
            </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {images.map((img, idx) => {
            const isSelected = selectedPath === img.goal;
            const isRecommended = recommendation?.suggested_path === img.goal;
            
            return (
                <div key={idx} className={`card bg-base-100 shadow-xl border-4 transition-all ${isSelected ? 'border-primary scale-105' : isRecommended ? 'border-accent' : 'border-transparent'}`}>
                    <figure><img src={img.url} alt={img.goal} className="h-64 w-full object-cover" /></figure>
                    <div className="card-body">
                        <h2 className="card-title">
                            {img.goal}
                            {isSelected && <div className="badge badge-primary">SELECTED</div>}
                            {isRecommended && <div className="badge badge-accent">RECOMMENDED</div>}
                        </h2>
                        <div className="card-actions justify-end mt-4">
                            <button 
                                className={`btn ${isSelected ? 'btn-disabled' : 'btn-primary'}`}
                                onClick={() => handleSelectPath(img.goal)}
                                disabled={isSelected}
                            >
                                {isSelected ? "Selected" : "Select This Path"}
                            </button>
                        </div>
                    </div>
                </div>
            );
        })}
      </div>

      {committed && (
        <div className="mt-12 flex justify-center">
            <button 
                className="btn btn-primary btn-lg gap-2 shadow-lg animate-bounce"
                onClick={() => navigate('/act')}
            >
                Proceed to Act Phase 
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
            </button>
        </div>
      )}
    </div>
    </Layout>
  );
};

export default Decide;
