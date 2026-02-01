import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { API_BASE } from '../config';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Loader2, Sparkles, Check, AlertCircle, ArrowRight } from 'lucide-react';
import { cn } from '../lib/utils';

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
      // alert("Path updated! You have completed the Decision phase.");
      // Navigate to Act phase
      navigate('/act');
    } catch (err: any) {
        console.error(err);
        setError("Failed to commit selection: " + err.message);
    }
  };

  if (loading) {
      return (
          <Layout currentStep={committed ? 2 : 1}>
              <div className="flex items-center justify-center min-h-[50vh]">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
          </Layout>
      );
  }

  return (
    <Layout currentStep={committed ? 2 : 1}>
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Phase 2: Decide</h1>
        <p className="text-muted-foreground">Review your potential futures and commit to a goal path.</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-destructive text-sm w-full p-4 bg-destructive/10 rounded-lg border border-destructive/20">
            <AlertCircle className="w-4 h-4" />
            {error}
        </div>
      )}

      {/* AI Suggestion Section */}
      <div className="flex justify-center w-full">
        {!recommendation ? (
            <Button 
                size="lg"
                onClick={handleAskAI}
                disabled={aiLoading}
                className="gap-2"
            >
                {aiLoading ? (
                    <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analyzing Options...
                    </>
                ) : (
                    <>
                        <Sparkles className="h-4 w-4" />
                        Ask AI for Recommendation
                    </>
                )}
            </Button>
        ) : (
            <Card className="w-full max-w-2xl animate-fade-in border-primary/20 bg-primary/5">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-primary">
                        <Sparkles className="h-5 w-5" />
                        AI Recommendation: <span className="uppercase">{recommendation.suggested_path}</span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p className="leading-relaxed text-foreground/90">{recommendation.reasoning}</p>
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-muted-foreground">Confidence Score:</span>
                        <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-primary text-primary-foreground hover:bg-primary/80">
                            {Math.round(recommendation.confidence_score * 100)}%
                        </div>
                    </div>
                </CardContent>
            </Card>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {images.map((img, idx) => {
            const isSelected = selectedPath === img.goal;
            const isRecommended = recommendation?.suggested_path === img.goal;
            
            return (
                <Card 
                    key={idx} 
                    className={cn(
                        "overflow-hidden transition-all duration-300 border-2",
                        isSelected ? "border-primary shadow-lg scale-[1.02]" : 
                        isRecommended ? "border-primary/50 shadow-md" : "border-transparent hover:border-muted-foreground/20"
                    )}
                >
                    <div className="relative aspect-[3/4] w-full overflow-hidden bg-muted">
                        <img 
                            src={img.url} 
                            alt={img.goal} 
                            className="h-full w-full object-cover transition-transform duration-300 hover:scale-105" 
                        />
                        {isSelected && (
                            <div className="absolute top-2 right-2">
                                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-primary text-primary-foreground shadow">
                                    SELECTED
                                </div>
                            </div>
                        )}
                        {isRecommended && !isSelected && (
                            <div className="absolute top-2 right-2">
                                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground shadow">
                                    RECOMMENDED
                                </div>
                            </div>
                        )}
                    </div>
                    <CardHeader>
                        <CardTitle className="uppercase text-center">{img.goal}</CardTitle>
                        <CardDescription className="text-center">
                            Path to a {img.goal} physique
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pb-6">
                        <Button 
                            className={cn("w-full gap-2", isSelected && "pointer-events-none opacity-90")}
                            variant={isSelected ? "default" : isRecommended ? "secondary" : "outline"}
                            onClick={() => handleSelectPath(img.goal)}
                        >
                            {isSelected ? (
                                <>
                                    <Check className="h-4 w-4" />
                                    Selected
                                </>
                            ) : (
                                "Select This Path"
                            )}
                        </Button>
                    </CardContent>
                </Card>
            );
        })}
      </div>

      {committed && (
        <div className="flex justify-center pt-8">
            <Button 
                size="lg" 
                onClick={() => navigate('/act')}
                className="w-full sm:w-auto px-8 gap-2 text-lg h-12 animate-in fade-in slide-in-from-bottom-4"
            >
                Proceed to Phase 3: Act
                <ArrowRight className="w-5 h-5" />
            </Button>
        </div>
      )}
    </div>
    </Layout>
  );
};

export default Decide;
