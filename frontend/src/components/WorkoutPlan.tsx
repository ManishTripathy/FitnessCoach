import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, GripVertical, Play, MessageCircle, X, AlertCircle } from 'lucide-react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { anonymousApi } from '../services/api';

interface WorkoutPlanProps {
  onBack: () => void;
  goalType: string;
}

interface WorkoutDay {
  id: string;
  day: number;
  title: string;
  exercises: string;
  duration: string;
  thumbnail?: string;
  isRestDay: boolean;
}

interface DragItem {
  index: number;
  id: string;
  type: string;
}

interface FeedbackModalProps {
  day: WorkoutDay;
  onClose: () => void;
}

function FeedbackModal({ day, onClose }: FeedbackModalProps) {
  const [effort, setEffort] = useState<string | null>(null);
  const [completion, setCompletion] = useState<string | null>(null);
  const [bodyFeel, setBodyFeel] = useState<string | null>(null);

  const effortOptions = ['Easy', 'Manageable', 'Hard', 'Too Hard'];
  const completionOptions = ['Completed', 'Skipped', 'Left Midway'];
  const bodyFeelOptions = ['Fresh', 'Neutral', 'Sore', 'Pain'];

  const quickPrompts = [
    '💬 "Can you suggest a shorter version?"',
    '💬 "This was too intense for me"',
    '💬 "Give me something similar but easier"',
  ];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4 animate-fadeIn">
      <div className="bg-slate-900 rounded-3xl w-full max-w-lg max-h-[85vh] overflow-y-auto border border-white/10 shadow-2xl">
        {/* Header with Coach Avatar */}
        <div className="sticky top-0 bg-slate-900 border-b border-white/10 p-6 flex items-center gap-4 z-10">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-xl shadow-lg">
            R
          </div>
          <div className="flex-1">
            <h3 className="text-white font-bold font-sans">Ryan</h3>
            <p className="text-white/60 text-sm font-sans">Your AI Coach</p>
          </div>
          <button 
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4 text-white" />
          </button>
        </div>

        {/* Chat Content */}
        <div className="p-6 space-y-6">
          {/* Coach Message */}
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              R
            </div>
            <div className="bg-slate-800 rounded-2xl rounded-tl-sm p-4 flex-1">
              <p className="text-white font-sans">
                Hey! How did <span className="font-bold text-orange-400">{day.title}</span> go for you today? 💪
              </p>
            </div>
          </div>

          {/* Effort Question */}
          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                R
              </div>
              <div className="bg-slate-800 rounded-2xl rounded-tl-sm p-4 flex-1">
                <p className="text-white/90 font-sans text-sm">How was the effort level?</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 ml-11">
              {effortOptions.map((option) => (
                <button
                  key={option}
                  onClick={() => setEffort(option)}
                  className={`py-3 px-4 rounded-xl font-sans text-sm font-medium transition-all ${
                    effort === option
                      ? 'bg-orange-500 text-white shadow-lg'
                      : 'bg-slate-800 text-white/80 hover:bg-slate-700'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          {/* Completion Question */}
          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                R
              </div>
              <div className="bg-slate-800 rounded-2xl rounded-tl-sm p-4 flex-1">
                <p className="text-white/90 font-sans text-sm">Did you complete it?</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 ml-11">
              {completionOptions.map((option) => (
                <button
                  key={option}
                  onClick={() => setCompletion(option)}
                  className={`py-3 px-4 rounded-xl font-sans text-sm font-medium transition-all ${
                    completion === option
                      ? 'bg-orange-500 text-white shadow-lg'
                      : 'bg-slate-800 text-white/80 hover:bg-slate-700'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          {/* Body Feel Question */}
          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                R
              </div>
              <div className="bg-slate-800 rounded-2xl rounded-tl-sm p-4 flex-1">
                <p className="text-white/90 font-sans text-sm">How does your body feel?</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 ml-11">
              {bodyFeelOptions.map((option) => (
                <button
                  key={option}
                  onClick={() => setBodyFeel(option)}
                  className={`py-3 px-4 rounded-xl font-sans text-sm font-medium transition-all ${
                    bodyFeel === option
                      ? 'bg-orange-500 text-white shadow-lg'
                      : 'bg-slate-800 text-white/80 hover:bg-slate-700'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          {/* Quick Prompts */}
          <div className="space-y-2 pt-4 border-t border-white/10">
            <p className="text-white/60 text-xs font-sans ml-11">Or tell me what you need:</p>
            <div className="space-y-2 ml-11">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  className="w-full text-left py-3 px-4 rounded-xl bg-slate-800/50 text-white/70 hover:bg-slate-800 hover:text-white transition-all font-sans text-sm"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          {(effort || completion || bodyFeel) && (
            <div className="pt-2">
              <button 
                onClick={onClose}
                className="w-full bg-orange-500 text-white py-4 rounded-full font-bold font-sans hover:bg-orange-600 transition-colors"
              >
                Submit Feedback
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function WorkoutCard({ day, index, moveCard }: { day: WorkoutDay; index: number; moveCard: (dragIndex: number, hoverIndex: number) => void }) {
  const [showFeedback, setShowFeedback] = useState(false);
  
  const [{ isDragging }, drag] = useDrag({
    type: 'workout-card',
    item: { index, id: day.id },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop<DragItem>({
    accept: 'workout-card',
    hover: (item: DragItem) => {
      if (item.index !== index) {
        moveCard(item.index, index);
        item.index = index;
      }
    },
  });

  return (
    <>
      <div
        ref={(node) => { drag(drop(node)); }}
        className={`bg-black/40 backdrop-blur-xl rounded-2xl p-6 border border-white/10 hover:border-orange-500/50 transition-all cursor-move group relative ${
          isDragging ? 'opacity-50' : ''
        }`}
      >
        {/* Ryan Chat Head - Only for non-rest days */}
        {!day.isRestDay && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowFeedback(true);
            }}
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white font-bold shadow-lg hover:scale-110 transition-transform z-10 cursor-pointer"
            style={{ cursor: 'pointer' }}
          >
            <MessageCircle className="w-5 h-5" />
          </button>
        )}

        <div className="flex items-start gap-4">
          {/* Drag Handle */}
          <div className="pt-2 opacity-40 group-hover:opacity-100 transition-opacity">
            <GripVertical className="w-5 h-5 text-white" />
          </div>

          {/* Thumbnail */}
          {!day.isRestDay && day.thumbnail && (
            <div className="relative flex-shrink-0 w-32 h-20 rounded-lg overflow-hidden bg-slate-800">
              <img
                src={day.thumbnail}
                alt={day.title}
                className="w-full h-full object-cover"
              />
              {/* Play button overlay */}
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center">
                  <Play className="w-5 h-5 text-white ml-0.5" fill="white" />
                </div>
              </div>
            </div>
          )}

          {/* Rest Day Icon */}
          {day.isRestDay && (
            <div className="flex-shrink-0 w-32 h-20 rounded-lg bg-slate-800/50 flex items-center justify-center border-2 border-dashed border-slate-700">
              <span className="text-3xl">😴</span>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <span className="bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold font-sans">
                Day {day.day}
              </span>
              {day.isRestDay && (
                <span className="bg-slate-700 text-white px-3 py-1 rounded-full text-xs font-semibold font-sans">
                  Rest
                </span>
              )}
            </div>
            <h3 className="text-xl font-bold text-white mb-1 font-sans">{day.title}</h3>
            {!day.isRestDay && (
              <>
                <p className="text-white/70 text-sm mb-2 font-sans">{day.exercises}</p>
                <div className="flex items-center gap-2 text-orange-400 text-sm font-sans">
                  <span>⏱️</span>
                  <span>{day.duration}</span>
                </div>
              </>
            )}
            {day.isRestDay && (
              <p className="text-white/60 text-sm font-sans">Recovery and muscle repair</p>
            )}
          </div>
        </div>
      </div>

      {/* Feedback Modal */}
      {showFeedback && (
        <FeedbackModal 
          day={day} 
          onClose={() => setShowFeedback(false)} 
        />
      )}
    </>
  );
}

function WorkoutPlanContent({ onBack, goalType }: WorkoutPlanProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workoutDays, setWorkoutDays] = useState<WorkoutDay[]>([]);
  const fetchedGoal = useRef<string | null>(null);

  useEffect(() => {
    if (fetchedGoal.current === goalType) return;
    fetchedGoal.current = goalType;

    const getYoutubeThumbnail = (url: string) => {
      try {
        // Handle standard youtube URLs
        const videoIdMatch = url.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/);
        if (videoIdMatch && videoIdMatch[1]) {
          return `https://img.youtube.com/vi/${videoIdMatch[1]}/hqdefault.jpg`;
        }
        return null;
      } catch (e) {
        return null;
      }
    };

    const fetchPlan = async () => {
      try {
        setIsLoading(true);
        const data = await anonymousApi.generatePlan(goalType);
        
        if (data && data.schedule) {
          const mappedDays: WorkoutDay[] = data.schedule.map((day: any) => {
            const details = day.workout_details || {};
            // Use provided thumbnail, or extract from YouTube URL, or use a default fallback
            const thumbnail = details.thumbnail_url || 
                            (details.url ? getYoutubeThumbnail(details.url) : null) || 
                            'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&q=80&w=1080';

            return {
              id: `day-${day.day}`,
              day: day.day,
              title: day.focus || details.title || `Day ${day.day}`,
              exercises: Array.isArray(details.exercises) 
                ? details.exercises.join(', ') 
                : (details.exercises || ''),
              duration: details.duration || '',
              thumbnail: thumbnail,
              isRestDay: day.is_rest || false,
            };
          });
          setWorkoutDays(mappedDays);
        }
      } catch (err) {
        console.error('Error fetching plan:', err);
        setError('Failed to generate your workout plan. Please try again.');
        // Reset the ref so we can try again if the component doesn't unmount
        fetchedGoal.current = null;
      } finally {
        setIsLoading(false);
      }
    };

    fetchPlan();
  }, [goalType]);

  const moveCard = (dragIndex: number, hoverIndex: number) => {
    const dragCard = workoutDays[dragIndex];
    const newCards = [...workoutDays];
    newCards.splice(dragIndex, 1);
    newCards.splice(hoverIndex, 0, dragCard);
    
    // Update day numbers
    const updatedCards = newCards.map((card, index) => ({
      ...card,
      day: index + 1,
    }));
    
    setWorkoutDays(updatedCards);
  };

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
      <main className="relative max-w-4xl mx-auto px-6 py-12">
        <div className="space-y-8">
          {/* Title */}
          <div className="text-center space-y-3">
            <h1 className="text-5xl lg:text-6xl font-black text-white drop-shadow-2xl font-sans">
              Your <span className="text-orange-500">{goalType}</span> Plan
            </h1>
            <p className="text-xl text-white/80 font-light font-sans">
              7-day personalized workout schedule • Drag to reorder
            </p>
          </div>

          {/* Error State */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-2xl p-6 text-center space-y-4">
              <div className="flex justify-center">
                <AlertCircle className="w-12 h-12 text-red-500" />
              </div>
              <h3 className="text-xl font-bold text-white">Oops! Something went wrong</h3>
              <p className="text-white/70">{error}</p>
              <button 
                onClick={() => window.location.reload()}
                className="bg-red-500 text-white px-6 py-2 rounded-full font-bold hover:bg-red-600 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                <div
                  key={i}
                  className="bg-black/40 backdrop-blur-xl rounded-2xl p-6 border border-white/10 animate-pulse"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-32 h-20 bg-slate-700 rounded-lg"></div>
                    <div className="flex-1 space-y-3">
                      <div className="h-6 bg-slate-700 rounded w-24"></div>
                      <div className="h-6 bg-slate-700 rounded w-3/4"></div>
                      <div className="h-4 bg-slate-700 rounded w-1/2"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Workout Cards */}
          {!isLoading && !error && (
            <div className="space-y-4">
              {workoutDays.map((day, index) => (
                <WorkoutCard
                  key={day.id}
                  day={day}
                  index={index}
                  moveCard={moveCard}
                />
              ))}
            </div>
          )}

          {/* Start Program Button */}
          {!isLoading && !error && (
            <div className="text-center pt-4">
              <button className="bg-orange-600 text-white px-12 py-4 rounded-full hover:bg-orange-700 transition-all shadow-lg font-bold text-lg font-sans">
                Start My Program 🔥
              </button>
            </div>
          )}
        </div>
      </main>

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

export function WorkoutPlan(props: WorkoutPlanProps) {
  return (
    <DndProvider backend={HTML5Backend}>
      <WorkoutPlanContent {...props} />
    </DndProvider>
  );
}
