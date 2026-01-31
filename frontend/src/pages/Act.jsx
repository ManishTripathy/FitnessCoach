import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import Layout from '../components/Layout';
import { API_BASE } from '../config';

const Act = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPlan();
  }, [currentUser]);

  const fetchPlan = async () => {
    if (!currentUser) return;
    try {
      const token = await currentUser.getIdToken();
      const response = await fetch(`${API_BASE}/act/plan`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.plan) {
          setPlan(data.plan);
        } else {
            // No plan exists yet, auto-generate
            generatePlan();
            return; // Exit here, generatePlan will handle loading state
        }
      }
    } catch (err) {
      console.error("Error fetching plan:", err);
    } finally {
      setLoading(false);
    }
  };

  const generatePlan = async (force = false) => {
    setGenerating(true);
    setError('');
    try {
      const token = await currentUser.getIdToken();
      const response = await fetch(`${API_BASE}/act/generate-plan`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ force_refresh: force })
      });
      
      if (!response.ok) throw new Error("Failed to generate plan");
      
      const data = await response.json();
      setPlan(data.plan);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
      setLoading(false);
    }
  };

  const renderDayCard = (day) => {
    const isRest = day.is_rest || !day.workout_id;
    const workout = day.workout_details || {};
    
    // Extract YouTube ID from URL if not provided directly (fallback)
    // Note: workout_library uses full URL usually, but we stored ID in 'id' field
    const youtubeId = workout.url ? workout.url.split('v=')[1] : null;
    const thumbnailUrl = youtubeId ? `https://img.youtube.com/vi/${youtubeId}/mqdefault.jpg` : null;

    return (
      <div key={day.day} className={`card bg-base-100 shadow-xl ${isRest ? 'opacity-80' : ''}`}>
        {!isRest && thumbnailUrl && (
          <figure className="relative">
            <img src={thumbnailUrl} alt={workout.title} className="w-full h-48 object-cover" />
            <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                <a 
                    href={workout.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn btn-circle btn-lg btn-error text-white"
                >
                    ▶
                </a>
            </div>
          </figure>
        )}
        <div className="card-body p-5">
          <div className="flex justify-between items-start">
            <h3 className="card-title text-lg">{day.day_name}</h3>
            {isRest ? (
                <span className="badge badge-ghost">Rest Day</span>
            ) : (
                <span className="badge badge-secondary">{workout.duration_mins} min</span>
            )}
          </div>
          
          {isRest ? (
            <div className="mt-2">
                <p className="italic text-gray-500">{day.notes || "Rest and recover."}</p>
            </div>
          ) : (
            <div className="mt-2 space-y-2">
                <p className="font-semibold text-primary">{workout.title}</p>
                <p className="text-sm text-gray-600">{day.notes}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                    {workout.focus && workout.focus.map((tag, idx) => (
                        <span key={idx} className="badge badge-xs badge-outline">{tag}</span>
                    ))}
                </div>
            </div>
          )}
          
          {!isRest && (
             <div className="card-actions justify-end mt-4">
                 <a href={workout.url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-primary w-full">
                     Start Workout
                 </a>
             </div>
          )}
        </div>
      </div>
    );
  };

  if (loading || generating) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <h2 className="text-2xl font-bold animate-pulse">Building your perfect week...</h2>
          <p className="text-gray-500 max-w-md text-center">
            Our AI is analyzing your goal and selecting the best Caroline Girvan workouts for you.
          </p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
            <div>
                <h1 className="text-4xl font-bold mb-2">Your Weekly Plan</h1>
                <p className="text-gray-600">
                    Focus: <span className="font-semibold text-secondary">{plan?.weekly_focus || "General Fitness"}</span>
                </p>
            </div>
            <button 
                onClick={() => generatePlan(true)} 
                className="btn btn-outline btn-sm"
                disabled={generating}
            >
                ↻ Regenerate Plan
            </button>
        </div>

        {error && (
            <div className="alert alert-error mb-6">
                <span>{error}</span>
            </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {plan?.schedule?.map(renderDayCard)}
        </div>
        
        <div className="mt-12 p-6 bg-base-200 rounded-xl text-center">
            <h3 className="text-xl font-bold mb-2">Ready for next week?</h3>
            <p className="mb-4 text-gray-600">Complete this week's workouts to unlock new challenges.</p>
        </div>
      </div>
    </Layout>
  );
};

export default Act;
