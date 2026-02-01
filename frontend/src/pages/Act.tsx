import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import Layout from '../components/Layout';
import { API_BASE } from '../config';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Loader2, Play, ExternalLink, RefreshCw, Calendar, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';

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
      <Card key={day.day} className={cn("overflow-hidden flex flex-col h-full", isRest && "opacity-80 bg-muted/50")}>
        {!isRest && thumbnailUrl && (
          <div className="relative aspect-video w-full overflow-hidden bg-black group">
            <img 
                src={thumbnailUrl} 
                alt={workout.title} 
                className="w-full h-full object-cover transition-opacity group-hover:opacity-75" 
            />
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <a 
                    href={workout.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center justify-center w-12 h-12 rounded-full bg-primary text-primary-foreground shadow-lg hover:scale-110 transition-transform"
                >
                    <Play className="h-6 w-6 fill-current" />
                </a>
            </div>
          </div>
        )}
        <CardHeader className="p-4 pb-2">
          <div className="flex justify-between items-start">
            <CardTitle className="text-lg flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                {day.day_name}
            </CardTitle>
            {isRest ? (
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80">
                    Rest Day
                </div>
            ) : (
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-primary text-primary-foreground hover:bg-primary/80">
                    Workout
                </div>
            )}
          </div>
        </CardHeader>
        
        <CardContent className="p-4 pt-2 flex-grow">
            {isRest ? (
                <div className="py-4 text-center text-muted-foreground italic text-sm">
                    Active recovery: Light walking or stretching recommended.
                </div>
            ) : (
                <>
                    <h4 className="font-semibold leading-none tracking-tight mb-2 line-clamp-1">{workout.title || "Workout Session"}</h4>
                    <p className="text-sm text-muted-foreground line-clamp-3">{workout.description}</p>
                </>
            )}
        </CardContent>

        {!isRest && (
            <CardFooter className="p-4 pt-0">
                <Button variant="outline" size="sm" className="w-full gap-2" asChild>
                    <a href={workout.url} target="_blank" rel="noopener noreferrer">
                        Watch Video
                        <ExternalLink className="h-3 w-3" />
                    </a>
                </Button>
            </CardFooter>
        )}
      </Card>
    );
  };

  if (loading) {
      return (
          <Layout currentStep={2}>
              <div className="flex items-center justify-center min-h-[50vh]">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
          </Layout>
      );
  }

  return (
    <Layout currentStep={2}>
      <div className="container mx-auto space-y-8 pb-12">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Your Weekly Plan</h1>
                <p className="text-muted-foreground">A personalized schedule to help you achieve your goals.</p>
            </div>
            <Button 
                variant="ghost" 
                size="sm"
                className="gap-2"
                onClick={() => generatePlan(true)}
                disabled={generating}
            >
                {generating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                    <RefreshCw className="h-4 w-4" />
                )}
                Regenerate Plan
            </Button>
        </div>

        {error && (
            <div className="flex items-center gap-2 text-destructive text-sm w-full p-4 bg-destructive/10 rounded-lg border border-destructive/20">
                <AlertCircle className="w-4 h-4" />
                {error}
            </div>
        )}

        {generating && (
            <div className="flex items-center justify-center p-12 border rounded-lg bg-muted/20">
                <div className="text-center space-y-4">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                    <p className="text-muted-foreground">Creating your personalized schedule based on your goal...</p>
                </div>
            </div>
        )}

        {plan && !generating && (
            <div className="space-y-6 animate-fade-in">
                <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 text-green-700 dark:text-green-400 border border-green-500/20">
                    <CheckCircle2 className="h-5 w-5" />
                    <span>Current Goal: <strong>{plan.goal}</strong></span>
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
