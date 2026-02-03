import { useState, useRef, useEffect } from 'react';
import { Upload, Camera, ArrowLeft } from 'lucide-react';
import { anonymousApi, observeApi } from '../services/api';
import { AuthModal } from './AuthModal';
import { WorkoutPlan } from './WorkoutPlan';
import { getAuth, onAuthStateChanged } from 'firebase/auth';

interface PhotoUploadProps {
  onBack: () => void;
}

export function PhotoUpload({ onBack }: PhotoUploadProps) {
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<Record<string, string>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [showWorkoutPlan, setShowWorkoutPlan] = useState(false);
  const [selectedBodyType, setSelectedBodyType] = useState<number | null>(null);
  const [isAISuggested, setIsAISuggested] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const potentialBodies = [
    {
      type: 'Skinny',
      goalKey: 'lean',
      image: 'https://images.unsplash.com/photo-1544655709-85ac776c2f61?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxza2lubnklMjBhdGhsZXRpYyUyMGJvZHklMjB0eXBlfGVufDF8fHx8MTc2OTk1MTUyN3ww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
      description: 'Lean & toned'
    },
    {
      type: 'Shredded',
      goalKey: 'athletic',
      image: 'https://images.unsplash.com/photo-1738725602689-f260e7f528cd?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzaHJlZGRlZCUyMG11c2N1bGFyJTIwcGh5c2lxdWV8ZW58MXx8fHwxNzY5OTUxNTI3fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
      description: 'Defined & athletic'
    },
    {
      type: 'Muscular',
      goalKey: 'muscle',
      image: 'https://images.unsplash.com/photo-1754475172820-6053bbed3b25?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtdXNjdWxhciUyMGJvZHlidWlsZGVyJTIwcGh5c2lxdWV8ZW58MXx8fHwxNzY5OTUxNTI4fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
      description: 'Powerful & built'
    }
  ];

  const fitnessVideos = [
    {
      id: 1,
      url: "https://images.unsplash.com/photo-1741156229623-da94e6d7977d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiaWNlcHMlMjB3b3Jrb3V0JTIwZ3ltfGVufDF8fHx8MTc2OTkyMDk1M3ww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      alt: "Biceps workout"
    },
    {
      id: 2,
      url: "https://images.unsplash.com/photo-1499290572571-a48c08140a19?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzcXVhdCUyMGV4ZXJjaXNlJTIwZml0bmVzc3xlbnwxfHx8fDE3Njk4NjQ4MTZ8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      alt: "Squat exercise"
    },
    {
      id: 3,
      url: "https://images.unsplash.com/photo-1729778783875-103c8545dc65?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhdGhsZXRlJTIwc3dlYXRpbmclMjBpbnRlbnNlfGVufDF8fHx8MTc2OTkyMDk1NHww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      alt: "Athlete sweating"
    },
    {
      id: 4,
      url: "https://images.unsplash.com/photo-1737736193172-f3b87a760ad5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxydW5uaW5nJTIwY2FyZGlvJTIwZml0bmVzc3xlbnwxfHx8fDE3Njk5MjA5NTV8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      alt: "Running cardio"
    },
    {
      id: 5,
      url: "https://images.unsplash.com/photo-1607909599990-e2c4778e546b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx5b2dhJTIwc3RyZXRjaCUyMGZsZXhpYmlsaXR5fGVufDF8fHx8MTc2OTkyMDk1NXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      alt: "Yoga stretch"
    },
    {
      id: 6,
      url: "https://images.unsplash.com/photo-1744551472900-d23f4997e1cd?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkZWFkbGlmdCUyMHN0cmVuZ3RoJTIwdHJhaW5pbmd8ZW58MXx8fHwxNzY5ODcyNjI2fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      alt: "Deadlift training"
    }
  ];

  useEffect(() => {
    // Load session from local storage if exists
    const storedSession = localStorage.getItem('anonymous_session_id');
    const auth = getAuth();
    
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setIsLoggedIn(!!user);
      
      if (storedSession) {
        setSessionId(storedSession);
        setIsUploading(true);

        const fetchAnonymous = (sid: string) => {
          anonymousApi.getResults(sid)
              .then(data => {
              if (data.uploaded_photo_url) {
                  setUploadedImage(data.uploaded_photo_url);
              }
              if (data.analysis_results) {
                  setAnalysisResults(data.analysis_results);
                  setShowAnalysis(true);
              }
              if (data.generated_images && Array.isArray(data.generated_images)) {
                  const images: Record<string, string> = {};
                  data.generated_images.forEach((img: any) => {
                      images[img.goal] = img.url;
                  });
                  setGeneratedImages(images);
              }
              })
              .catch(err => {
              console.error("Failed to restore session", err);
              if (err.response && err.response.status === 404) {
                  localStorage.removeItem('anonymous_session_id');
              }
              })
              .finally(() => {
              setIsUploading(false);
              });
        };

        if (user) {
            // User is logged in, try fetching from user's scans first
            try {
                const data = await observeApi.getScan(storedSession);
                if (data.uploaded_photo_url) {
                  setUploadedImage(data.uploaded_photo_url);
                }
                if (data.analysis_results) {
                  setAnalysisResults(data.analysis_results);
                  setShowAnalysis(true);
                }
                // Check if user scan has generated images (might be stored differently or same structure)
                // Assuming same structure for now or adapting
                if (data.generated_images && Array.isArray(data.generated_images)) {
                    const images: Record<string, string> = {};
                    data.generated_images.forEach((img: any) => {
                        images[img.goal] = img.url;
                    });
                    setGeneratedImages(images);
                }
                setIsUploading(false);
            } catch (err) {
                console.error("Failed to fetch from user scans, trying anonymous", err);
                fetchAnonymous(storedSession);
            }
        } else {
            // Not logged in, fetch from anonymous
            fetchAnonymous(storedSession);
        }
      }
    });
    
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (showAnalysis && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [showAnalysis]);

  const handleAISuggest = () => {
    setSelectedBodyType(1); // Select the 2nd option (Shredded)
    setIsAISuggested(true);
  };

  const handleBodyTypeSelect = (index: number) => {
    setSelectedBodyType(index);
    setIsAISuggested(false);
  };

  const handleContinue = () => {
    setShowWorkoutPlan(true);
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setError(null);
    if (file) {
      setIsUploading(true);
      // Show preview immediately
      const reader = new FileReader();
      reader.onloadend = () => {
        setUploadedImage(reader.result as string);
        setShowAnalysis(false);
      };
      reader.readAsDataURL(file);

      // Upload in background
      try {
        const response = await anonymousApi.uploadPhoto(file, sessionId);
        setSessionId(response.session_id);
        localStorage.setItem('anonymous_session_id', response.session_id);
      } catch (err) {
        console.error("Upload failed", err);
        setError("Failed to upload photo. Please try again.");
      } finally {
        setIsUploading(false);
      }
    }
  };

  const handleAnalyze = async () => {
    if (!sessionId) {
      console.error("No session ID found");
      setError("Session invalid. Please upload photo again.");
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    try {
      const results = await anonymousApi.analyzePhoto(sessionId);
      setAnalysisResults(results);
      setShowAnalysis(true);

      // Trigger generation of potential transformations
      setIsGenerating(true);
      const goals = ['lean', 'athletic', 'muscle'];
      
      // We don't await this block to block the UI, but we want to show loading states
      // Actually, we should probably await to ensure we catch errors, or handle promises individually
      goals.forEach(async (goal) => {
          try {
              const res = await anonymousApi.generateTransformations(sessionId, goal);
              setGeneratedImages(prev => ({
                  ...prev,
                  [goal]: res.url
              }));
          } catch (e) {
              console.error(`Failed to generate ${goal}`, e);
          }
      });

      // If user is logged in, automatically migrate the new analysis to their profile
      const auth = getAuth();
      if (auth.currentUser) {
          try {
              const token = await auth.currentUser.getIdToken();
              await anonymousApi.migrateData(sessionId, token);
              // Note: Session is deleted from anonymous store, but we keep the ID 
              // because observeApi.getScan can now retrieve it from user profile
          } catch (migrateErr) {
              console.error("Auto-migration failed", migrateErr);
              // Don't fail the analysis display, just log it
          }
      }

    } catch (err: any) {
      console.error("Analysis failed", err);
      if (err.response?.status === 404) {
        setError("Session expired. Please upload your photo again.");
        localStorage.removeItem('anonymous_session_id');
        setSessionId(null);
        setUploadedImage(null);
      } else {
        setError("Analysis failed. Please try again.");
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (showWorkoutPlan && selectedBodyType !== null) {
    return (
      <WorkoutPlan 
        onBack={() => setShowWorkoutPlan(false)}
        goalType={potentialBodies[selectedBodyType].type}
      />
    );
  }

  return (
    <div className="min-h-screen w-full bg-black relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 flex gap-4 opacity-20">
        {fitnessVideos.map((video) => (
          <div key={video.id} className="flex-1 min-w-0 animate-scroll">
            <img
              src={video.url}
              alt={video.alt}
              className="w-full h-full object-cover"
            />
          </div>
        ))}
      </div>

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-orange-500/30 via-red-500/20 to-purple-600/30 pointer-events-none"></div>

      {/* Header */}
      <header className="relative w-full bg-black/50 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <button 
            onClick={onBack}
            className="flex items-center gap-2 text-white/80 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back
          </button>
          <div className="text-white">
            <span className="text-orange-500">Ryan</span> Coach
          </div>
          <div className="w-20"></div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-6xl mx-auto px-6 py-12">
        <div className="space-y-8">
          {/* Title */}
          <div className="text-center space-y-3">
            <h1 className="text-5xl lg:text-6xl font-black text-white drop-shadow-2xl font-sans">
              Let's Analyze Your Body
            </h1>
            <p className="text-xl text-white/80 font-light font-sans">
              Upload a front-facing photo to get started
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-200 px-6 py-4 rounded-xl max-w-2xl mx-auto text-center backdrop-blur-md">
              <p>{error}</p>
            </div>
          )}

          {/* Upload Section */}
          <div className="bg-black/40 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              {/* Left Side: Upload Area */}
              <div className="w-full">
                {!uploadedImage ? (
                  <label className="flex flex-col items-center justify-center aspect-[3/4] border-2 border-dashed border-orange-500/50 rounded-2xl cursor-pointer hover:border-orange-500 transition-colors group">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                    />
                    <div className="text-center space-y-4 p-6">
                      <div className="w-20 h-20 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                        <Upload className="w-10 h-10 text-orange-500" />
                      </div>
                      <div className="space-y-2">
                        <p className="text-2xl font-semibold text-white font-sans">
                          Upload Your Photo
                        </p>
                        <p className="text-white/60 font-sans">
                          Click to browse or drag and drop
                        </p>
                      </div>
                      <div className="flex items-center gap-2 text-orange-400 justify-center">
                        <Camera className="w-5 h-5" />
                        <span className="text-sm font-sans">Front-facing photo works best</span>
                      </div>
                    </div>
                  </label>
                ) : (
                  <div className="space-y-6">
                    <div className="relative rounded-2xl overflow-hidden bg-slate-900 aspect-[3/4] flex items-center justify-center border border-white/10">
                      <img
                        src={uploadedImage}
                        alt="Uploaded"
                        className="w-full h-full object-cover"
                      />
                    </div>

                    <div className="flex gap-4 justify-center">
                      <label className="bg-slate-700 text-white px-6 py-3 rounded-full hover:bg-slate-600 transition-colors cursor-pointer font-sans text-sm">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageUpload}
                          className="hidden"
                        />
                        Change Photo
                      </label>
                      
                      {!showAnalysis && (
                        <button
                          onClick={handleAnalyze}
                          disabled={isAnalyzing || isUploading}
                          className="bg-orange-600 text-white px-8 py-3 rounded-full hover:bg-orange-700 disabled:bg-orange-600/50 transition-colors font-semibold font-sans flex items-center gap-2 text-sm"
                        >
                          {isAnalyzing ? (
                            <>
                              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                              Analyzing...
                            </>
                          ) : isUploading ? (
                            <>
                              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                              Uploading...
                            </>
                          ) : (
                            'Analyze Photo'
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Side: Information Write-up */}
              <div className="space-y-8">
                <div className="space-y-4">
                  <h2 className="text-3xl font-bold text-white font-sans leading-tight">
                    Instant Physique Analysis
                  </h2>
                  <p className="text-lg text-white/70 font-sans leading-relaxed">
                    Our AI evaluates your current form to provide a comprehensive baseline for your transformation.
                  </p>
                </div>

                <div className="space-y-6">
                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0">
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold font-sans">Current Body Analysis</h3>
                      <p className="text-white/60 text-sm font-sans mt-1">
                        A detailed 1-liner assessment of your current physique and posture.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0">
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold font-sans">Key Metrics</h3>
                      <p className="text-white/60 text-sm font-sans mt-1">
                        Get indicative Body Fat and Muscle Mass percentages calculated by our vision model.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0">
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold font-sans">Transformation Path</h3>
                      <p className="text-white/60 text-sm font-sans mt-1">
                        Identify your body type and visualize your potential progress.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
                  <p className="text-orange-400 text-sm italic font-sans">
                    "The first step to a better you is knowing exactly where you stand today."
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Analysis Results */}
          {showAnalysis && (
            <div ref={resultsRef} className="space-y-8 animate-fadeIn">
              {/* Current Analysis */}
              <div className="bg-black/40 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-3xl font-bold text-white font-sans">
                    Current Body Analysis
                    </h2>
                    {!isLoggedIn && (
                        <button 
                            onClick={() => setIsAuthModalOpen(true)}
                            className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-full font-semibold transition-colors"
                        >
                            Save Analysis & Continue
                        </button>
                    )}
                </div>
                
                <p className="text-white/80 mb-6 font-sans text-lg italic">
                    "{analysisResults?.reasoning || 'Analyzing...'}"
                </p>

                <div className="grid md:grid-cols-3 gap-6">
                  <div className="bg-orange-500/10 rounded-xl p-6 border border-orange-500/20">
                    <div className="text-orange-400 text-sm font-semibold mb-2 font-sans">Category</div>
                    <div className="text-4xl font-black text-white font-sans">{analysisResults?.category || 'N/A'}</div>
                    <div className="text-white/60 text-sm mt-1 font-sans">{analysisResults?.body_type_description || 'Analysis'}</div>
                  </div>
                  <div className="bg-orange-500/10 rounded-xl p-6 border border-orange-500/20">
                    <div className="text-orange-400 text-sm font-semibold mb-2 font-sans">Body Fat (Est.)</div>
                    <div className="text-4xl font-black text-white font-sans">{analysisResults?.estimated_body_fat || '18'}%</div>
                    <div className="text-white/60 text-sm mt-1 font-sans">Approximate</div>
                  </div>
                  <div className="bg-orange-500/10 rounded-xl p-6 border border-orange-500/20">
                    <div className="text-orange-400 text-sm font-semibold mb-2 font-sans">Muscle Mass (Est.)</div>
                    <div className="text-4xl font-black text-white font-sans">{analysisResults?.estimated_muscle_mass || '42'}%</div>
                    <div className="text-white/60 text-sm mt-1 font-sans">Approximate</div>
                  </div>
                </div>
              </div>

              {/* Potential Bodies */}
              <div className="bg-black/40 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
                <h2 className="text-4xl lg:text-5xl font-black text-white mb-4 font-sans">
                  Choose Your <span className="text-orange-500">Transformation Goal</span>
                </h2>
                <p className="text-xl text-white/90 mb-6 font-sans">
                  Select your dream physique and Ryan will build a custom workout & nutrition plan to get you there 🔥
                </p>
                
                {/* Suggest Me Button */}
                <div className="mb-8">
                  <button 
                    onClick={handleAISuggest}
                    className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-8 py-4 rounded-full hover:from-orange-600 hover:to-red-600 transition-all shadow-lg hover:shadow-orange-500/50 font-bold text-lg font-sans flex items-center gap-2 mx-auto"
                  >
                    <span>✨</span>
                    Not Sure? Let AI Suggest for Me
                    <span>→</span>
                  </button>
                </div>

                <div className="grid md:grid-cols-3 gap-6">
                  {potentialBodies.map((body, index) => (
                    <button
                      key={body.type}
                      onClick={() => handleBodyTypeSelect(index)}
                      className={`group relative bg-slate-900 rounded-2xl overflow-hidden transition-all hover:scale-[1.02] ${
                        selectedBodyType === index 
                          ? 'ring-4 ring-orange-500 scale-[1.02]' 
                          : 'hover:ring-4 hover:ring-orange-500'
                      }`}
                    >
                      {/* AI Suggested Badge */}
                      {selectedBodyType === index && isAISuggested && (
                        <div className="absolute top-4 right-4 bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold z-10 shadow-lg font-sans flex items-center gap-1">
                          <span>✨</span>
                          AI Suggested
                        </div>
                      )}
                      
                      <div className="aspect-[3/4] overflow-hidden">
                        <img
                          src={generatedImages[body.goalKey] || body.image}
                          alt={body.type}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      </div>
                      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent"></div>
                      <div className="absolute bottom-0 left-0 right-0 p-6 text-left">
                        <h3 className="text-2xl font-bold text-white mb-1 font-sans">{body.type}</h3>
                        <p className="text-white/80 text-sm font-sans">{body.description}</p>
                        <div className={`mt-3 transition-opacity ${
                          selectedBodyType === index 
                            ? 'opacity-100' 
                            : 'opacity-0 group-hover:opacity-100'
                        }`}>
                          <span className="text-orange-500 text-sm font-semibold font-sans">
                            {selectedBodyType === index ? '✓ Selected' : 'Click to select →'}
                          </span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                {/* Continue Button */}
                {selectedBodyType !== null && (
                  <div className="mt-8 text-center animate-fadeIn">
                    <button 
                      onClick={handleContinue}
                      className="bg-orange-600 text-white px-12 py-4 rounded-full hover:bg-orange-700 transition-all shadow-lg font-bold text-lg font-sans"
                    >
                      Continue with {potentialBodies[selectedBodyType].type} Goal →
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
      
      {/* Auth Modal */}
      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)}
        sessionId={sessionId || ''}
      />

      <style>{`
        @keyframes scroll {
          0% {
            transform: translateY(0);
          }
          100% {
            transform: translateY(-50%);
          }
        }
        
        .animate-scroll {
          animation: scroll 20s linear infinite;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.6s ease-out;
        }
      `}</style>
    </div>
  );
}
