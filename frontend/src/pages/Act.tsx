import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import Layout from '../components/Layout';
import { API_BASE } from '../config';

interface WorkoutDetails {
    title?: string;
    url?: string;
    description?: string;
}

interface PlanDay {
    day: number;
    day_name: string;
    is_rest: boolean;
    workout_id?: string;
    workout_details?: WorkoutDetails;
}

interface WeeklyPlan {
    goal: string;
    schedule: PlanDay[];
}

const Act: React.FC = () => {
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
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
    if (!currentUser) return;
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
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGenerating(false);
      setLoading(false);
    }
  };

  const renderDayCard = (day: PlanDay) => {
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
                <span className="badge badge-primary">Workout</span>
            )}
          </div>
          
          {isRest ? (
            <div className="py-4 text-center text-gray-500 italic">
                Active recovery: Light walking or stretching recommended.
            </div>
          ) : (
            <>
                <h4 className="font-bold mt-2">{workout.title || "Workout Session"}</h4>
                <p className="text-sm text-gray-600 line-clamp-3">{workout.description}</p>
                <div className="card-actions justify-end mt-4">
                    <a href={workout.url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-outline">
                        Watch Video
                    </a>
                </div>
            </>
          )}
        </div>
      </div>
    );
  };

  if (loading) return <div className="flex justify-center p-10"><span className="loading loading-spinner loading-lg"></span></div>;

  return (
    <Layout currentStep={2}>
      <div className="container mx-auto">
        <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">Your Weekly Plan</h1>
            <button 
                className={`btn btn-sm btn-ghost ${generating ? 'loading' : ''}`}
                onClick={() => generatePlan(true)}
                disabled={generating}
            >
                Regenerate Plan
            </button>
        </div>

        {error && <div className="alert alert-error mb-4">{error}</div>}

        {generating && (
            <div className="alert alert-info mb-6">
                <span>Creating your personalized schedule based on your goal...</span>
            </div>
        )}

        {plan && (
            <div className="space-y-6">
                <div className="alert alert-success shadow-lg">
                    <div>
                        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        <span>Current Goal: <strong>{plan.goal}</strong></span>
                    </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {plan.schedule.map(day => renderDayCard(day))}
                </div>
            </div>
        )}
      </div>
    </Layout>
  );
};

export default Act;
