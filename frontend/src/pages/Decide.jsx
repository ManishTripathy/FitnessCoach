import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';

const API_BASE = 'http://localhost:8000/api/v1';

const Decide = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [images, setImages] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [recommendation, setRecommendation] = useState(null);
  const [error, setError] = useState(null);
  const [committed, setCommitted] = useState(false);
  const [selectedPath, setSelectedPath] = useState(null);

  useEffect(() => {
    if (!currentUser) return;
    fetchState();
  }, [currentUser]);

  const fetchState = async () => {
    try {
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
      const token = await currentUser.getIdToken();
      const res = await fetch(`${API_BASE}/decide/suggest`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) {
          throw new Error(await res.text());
      }
      
      const data = await res.json();
      setRecommendation(data);
      
    } catch (err) {
      console.error(err);
      setError("Failed to get AI suggestion: " + err.message);
    } finally {
      setAiLoading(false);
    }
  };

  const handleSelectPath = async (pathKey) => {
    if (committed && selectedPath === pathKey) return; // Already selected this one
    
    if (!window.confirm(`Are you sure you want to ${committed ? 'switch' : 'commit'} to the ${pathKey} path?`)) return;
    
    try {
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
      
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div className="p-8 text-center"><span className="loading loading-spinner loading-lg"></span></div>;

  return (
    <Layout currentStep={1}>
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-2 text-center">Decide Your Path</h1>
      <p className="text-center text-gray-500 mb-8">Choose the physique you want to work towards.</p>

      {committed && (
          <div className="alert alert-success mb-6 shadow-lg">
              <div>
                  <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <div>
                    <h3 className="font-bold">Path Selected: {selectedPath.toUpperCase()}</h3>
                    <div className="text-xs">You can still change your mind by selecting a different path below.</div>
                  </div>
              </div>
          </div>
      )}

      {error && <div className="alert alert-error mb-6"><span>{error}</span></div>}

      {/* AI Suggestion Section */}
      <div className="mb-8 flex justify-center">
        {!recommendation ? (
            <button 
                className="btn btn-secondary btn-lg gap-2"
                onClick={handleAskAI}
                disabled={aiLoading}
            >
                {aiLoading ? <span className="loading loading-spinner"></span> : "✨ Ask AI to Suggest a Path"}
            </button>
        ) : (
            <div className="card w-full max-w-4xl bg-base-100 shadow-xl border border-secondary">
                <div className="card-body">
                    <h2 className="card-title text-secondary mb-4">AI Recommendation</h2>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        {['lean', 'athletic', 'muscle'].map(key => (
                            <div key={key} className="bg-base-200 p-4 rounded-lg">
                                <h3 className="font-bold capitalize mb-2">{key}</h3>
                                <p className="text-sm mb-1"><strong>Time:</strong> {recommendation[key]?.time_estimate}</p>
                                <p className="text-sm mb-1"><strong>Effort:</strong> {recommendation[key]?.effort_level}</p>
                                <p className="text-xs text-gray-600">{recommendation[key]?.description}</p>
                            </div>
                        ))}
                    </div>
                    
                    <div className="alert alert-info bg-opacity-20 border-info">
                        <div>
                            <h3 className="font-bold">Recommendation: {recommendation.recommendation.suggested_path.toUpperCase()}</h3>
                            <p>{recommendation.recommendation.reasoning}</p>
                        </div>
                    </div>
                </div>
            </div>
        )}
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {images.map((img, idx) => {
            // If AI recommended this, highlight it
            const isRecommended = recommendation?.recommendation?.suggested_path === img.goal;
            const isSelected = selectedPath === img.goal;
            
            return (
                <div key={idx} className={`card bg-base-100 shadow-xl transition-all hover:scale-105 ${isSelected ? 'ring-4 ring-success ring-offset-2 scale-105' : isRecommended ? 'ring-4 ring-secondary ring-offset-2' : ''}`}>
                    <figure className="px-4 pt-4">
                        <img src={img.url} alt={img.goal} className="rounded-xl w-full h-64 object-cover" />
                    </figure>
                    <div className="card-body items-center text-center">
                        <h2 className="card-title capitalize">
                            {img.goal}
                            {isRecommended && <div className="badge badge-secondary">AI Pick</div>}
                            {isSelected && <div className="badge badge-success">Selected</div>}
                        </h2>
                        <div className="card-actions mt-4">
                            <button 
                                className={`btn ${isSelected ? 'btn-success' : isRecommended ? 'btn-secondary' : 'btn-primary'} w-full`}
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
    </div>
    </Layout>
  );
};

export default Decide;
