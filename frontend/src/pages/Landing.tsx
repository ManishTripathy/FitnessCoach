import React from 'react';
import { useNavigate } from 'react-router-dom';

const Landing: React.FC = () => {
  const navigate = useNavigate();

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
    <div className="min-h-screen w-full bg-black relative overflow-hidden font-sans">
      {/* Animated Video Background */}
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

      {/* Vibrant gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-orange-500/30 via-red-500/20 to-purple-600/30 pointer-events-none"></div>

      {/* Header */}
      <header className="relative w-full bg-black/50 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-white">
            <span className="text-orange-500">Ryan</span> Coach
          </div>
          <div className="flex items-center gap-6">
            <button className="text-white/80 hover:text-white transition-colors">
              Help
            </button>
            <button 
                className="text-white/80 hover:text-white transition-colors"
                onClick={() => navigate('/login')}
            >
              Log in
            </button>
            <button 
                className="bg-orange-500 text-white px-5 py-2 rounded-full hover:bg-orange-600 transition-colors"
                onClick={() => navigate('/register')}
            >
              Sign up
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-6 py-12 lg:py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          
          {/* Left Column - Text Content */}
          <div className="space-y-10">
            <div className="space-y-8">
              {/* Headline */}
              <h1 className="text-7xl lg:text-8xl font-black text-white drop-shadow-2xl tracking-tight leading-none font-sans">
                Meet <span className="text-orange-500">Ryan</span>
              </h1>
              
              {/* Sub-headline */}
              <p className="text-2xl lg:text-3xl text-white/95 max-w-xl leading-relaxed drop-shadow-lg font-light font-sans">
                Your personal fitness coach that plans for you — so you don't quit halfway.
              </p>
              
              {/* Supporting text */}
              <p className="text-base text-orange-300/90 tracking-widest uppercase font-medium font-sans">
                Powered by AI
              </p>
            </div>

            {/* Primary CTA */}
            <div>
              <button 
                onClick={() => navigate('/register')}
                className="bg-orange-600 text-white text-xl px-12 py-5 rounded-full shadow-lg hover:bg-orange-700 hover:scale-[1.03] active:scale-[0.97] transition-all duration-200 font-semibold font-sans"
              >
                Try now
              </button>
            </div>

            {/* Energy stats */}
            <div className="flex gap-12 pt-6">
              <div className="space-y-2">
                <div className="text-5xl font-black text-orange-500 font-sans">50K+</div>
                <div className="text-base text-white/70 font-medium font-sans">Active Users</div>
              </div>
              <div className="space-y-2">
                <div className="text-5xl font-black text-orange-500 font-sans">1M+</div>
                <div className="text-base text-white/70 font-medium font-sans">Workouts Completed</div>
              </div>
            </div>
          </div>

          {/* Right Column - Mobile Phone Frame */}
          <div className="flex items-center justify-center lg:justify-end">
            <div className="relative w-full max-w-[375px] h-[812px] bg-gradient-to-br from-slate-900 to-black rounded-[3rem] shadow-2xl shadow-orange-500/20 overflow-hidden border-8 border-slate-800">
              {/* Phone Notch */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-7 bg-black rounded-b-3xl z-10"></div>
              
              {/* App Content - Placeholder */}
              <div className="relative h-full w-full bg-gradient-to-b from-slate-900 via-black to-slate-900 overflow-y-auto">
                <div className="flex flex-col items-center justify-center min-h-full px-8 py-16">
                  
                  {/* Visual Element */}
                  <div className="relative mb-8">
                    <div className="w-48 h-48 rounded-full bg-gradient-to-br from-orange-500/30 to-red-500/30 flex items-center justify-center overflow-hidden shadow-lg shadow-orange-500/30 backdrop-blur-sm border border-orange-500/20">
                      <div className="text-6xl">💪</div>
                    </div>
                    <div className="absolute -bottom-2 -right-2 w-20 h-20 rounded-full bg-gradient-to-br from-orange-400 to-red-500 opacity-40 blur-xl"></div>
                  </div>

                  {/* Placeholder text in phone */}
                  <div className="text-center space-y-3">
                    <p className="text-sm text-white/50">
                      App preview coming soon...
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
};

export default Landing;
