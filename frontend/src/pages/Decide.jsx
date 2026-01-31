import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';

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
             // Could redirect to next phase if it existed
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
    if (!window.confirm(`Are you sure you want to commit to the ${pathKey} path?`)) return;
    
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
      alert("Path confirmed! You have completed the Decision phase.");
      
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div className="p-8 text-center"><span className="loading loading-spinner loading-lg"></span></div>;

  if (committed) {
      return (
          <div className="hero min-h-screen bg-base-200">
              <div className="hero-content text-center">
                  <div className="max-w-md">
                      <h1 className="text-5xl font-bold text-success">Path Chosen!</h1>
                      <p className="py-6">You have successfully committed to your transformation path. The next phase (Planning) is coming soon.</p>
                      <button className="btn btn-primary" onClick={() => navigate('/observe')}>Back to Observe</button>
                  </div>
              </div>
          </div>
      );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-2 text-center">Decide Your Path</h1>
      <p className="text-center text-gray-500 mb-8">Choose the physique you want to work towards.</p>

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
            
            return (
                <div key={idx} className={`card bg-base-100 shadow-xl transition-all hover:scale-105 ${isRecommended ? 'ring-4 ring-secondary ring-offset-2' : ''}`}>
                    <figure className="px-4 pt-4">
                        <img src={img.url} alt={img.goal} className="rounded-xl w-full h-64 object-cover" />
                    </figure>
                    <div className="card-body items-center text-center">
                        <h2 className="card-title capitalize">
                            {img.goal}
                            {isRecommended && <div className="badge badge-secondary">Recommended</div>}
                        </h2>
                        <div className="card-actions mt-4">
                            <button 
                                className={`btn ${isRecommended ? 'btn-secondary' : 'btn-primary'} w-full`}
                                onClick={() => handleSelectPath(img.goal)}
                            >
                                Select This Path
                            </button>
                        </div>
                    </div>
                </div>
            );
        })}
      </div>
    </div>
  );
};

export default Decide;
