import React, { useState, useEffect, ChangeEvent } from 'react';
import { useAuth } from '../auth/AuthContext';
import { storage } from '../firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import Layout from '../components/Layout';
import { useNavigate } from 'react-router-dom';
import { API_BASE } from '../config';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { ArrowRight, Upload, Loader2, Sparkles, AlertCircle } from 'lucide-react';

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
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">Phase 1: Observe</h1>
            <p className="text-muted-foreground">Upload a photo to let AI analyze your physique and project your potential.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Upload Section */}
            <Card>
                <CardHeader>
                    <CardTitle>Upload Your Photo</CardTitle>
                    <CardDescription>Full-body photo works best for accurate analysis.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <Label htmlFor="picture">Picture</Label>
                        <Input 
                            id="picture" 
                            type="file" 
                            accept="image/*"
                            onChange={handleImageChange}
                        />
                    </div>
                    
                    {preview && (
                        <div className="mt-4 relative aspect-[3/4] w-full overflow-hidden rounded-lg border bg-muted">
                            <img 
                                src={preview} 
                                alt="Preview" 
                                className="h-full w-full object-cover" 
                            />
                        </div>
                    )}
                </CardContent>
                <CardFooter className="flex flex-col gap-2">
                    {error && (
                        <div className="flex items-center gap-2 text-destructive text-sm w-full p-2 bg-destructive/10 rounded">
                            <AlertCircle className="w-4 h-4" />
                            {error}
                        </div>
                    )}
                    <Button 
                        className="w-full" 
                        onClick={handleUploadAndAnalyze}
                        disabled={!image || loading || genLoading}
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Analyzing...
                            </>
                        ) : (
                            <>
                                <Upload className="mr-2 h-4 w-4" />
                                Analyze & Visualize
                            </>
                        )}
                    </Button>
                </CardFooter>
            </Card>

            {/* Results Section */}
            <div className="flex flex-col gap-6">
                {/* Analysis Result */}
                {analysis && (
                    <Card className="animate-fade-in border-primary/20">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-primary">
                                <Sparkles className="w-5 h-5" />
                                AI Analysis
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <h4 className="font-semibold text-sm text-muted-foreground">Body Category</h4>
                                <p className="text-lg font-medium">{analysis.category}</p>
                            </div>
                            <div>
                                <h4 className="font-semibold text-sm text-muted-foreground">Detailed Assessment</h4>
                                <p className="leading-relaxed">{analysis.reasoning}</p>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Generated Futures */}
                {genLoading && (
                     <Card className="animate-pulse bg-muted/50 border-none">
                        <CardContent className="flex flex-col items-center justify-center p-8 text-center space-y-4">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            <p className="text-muted-foreground">Generating your potential future selves...<br/>This takes about 10-20 seconds.</p>
                        </CardContent>
                     </Card>
                )}

                {futureImages.length > 0 && (
                    <Card className="animate-fade-in">
                        <CardHeader>
                            <CardTitle>Potential Futures</CardTitle>
                            <CardDescription>AI-generated visualizations of your goal physiques.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                {futureImages.map((img, idx) => (
                                    <div key={idx} className="group relative overflow-hidden rounded-md border bg-muted aspect-[3/4]">
                                        <img 
                                            src={img.url} 
                                            alt={img.goal} 
                                            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105" 
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-3">
                                            <span className="text-white text-xs font-medium uppercase tracking-wider bg-black/50 px-2 py-1 rounded backdrop-blur-sm">
                                                {img.goal}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>

        {/* Navigation */}
        {(analysis || isCompleted) && (
            <div className="flex justify-center pt-8 pb-12">
                <Button 
                    size="lg" 
                    onClick={handleProceed}
                    disabled={saving || genLoading}
                    className="w-full sm:w-auto px-8 gap-2 text-lg h-12"
                >
                    {saving ? 'Saving...' : 'Proceed to Phase 2: Decide'}
                    {!saving && <ArrowRight className="w-5 h-5" />}
                </Button>
            </div>
        )}
      </div>
    </Layout>
  );
};

export default Observe;
