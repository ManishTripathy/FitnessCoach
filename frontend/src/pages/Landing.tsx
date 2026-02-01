import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';

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
          <div className="text-white text-xl font-bold">
            <span className="text-orange-500">Fitness</span> Coach AI
          </div>
          <div className="flex items-center gap-6">
            <Button 
                variant="ghost" 
                className="text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                onClick={() => {}} // Help
            >
              Help
            </Button>
            <Button 
                variant="ghost" 
                className="text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                onClick={() => navigate('/login')}
            >
              Log in
            </Button>
            <Button 
                className="bg-orange-500 text-white hover:bg-orange-600 border-none rounded-full px-6"
                onClick={() => navigate('/register')}
            >
              Sign up
            </Button>
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
              <h1 className="text-7xl lg:text-8xl font-black text-white drop-shadow-2xl tracking-tight leading-none">
                Meet <span className="text-orange-500">Your AI</span> Coach
              </h1>
              
              {/* Sub-headline */}
              <p className="text-2xl lg:text-3xl text-white/95 max-w-xl leading-relaxed drop-shadow-lg font-light">
                Your personal fitness coach that plans for you — so you don't quit halfway.
              </p>
              
              {/* Supporting text */}
              <p className="text-base text-orange-300/90 tracking-widest uppercase font-medium">
                Powered by Gemini 1.5 Pro
              </p>
            </div>

            {/* CTA Button */}
            <div className="pt-4">
              <Button 
                size="lg"
                className="bg-orange-500 hover:bg-orange-600 text-white text-lg px-8 py-6 h-auto rounded-full shadow-[0_0_40px_-10px_rgba(249,115,22,0.5)] hover:shadow-[0_0_60px_-10px_rgba(249,115,22,0.7)] transition-all duration-300 border-none"
                onClick={() => navigate('/register')}
              >
                Start Your Journey
              </Button>
            </div>

            {/* Feature Pills */}
            <div className="flex flex-wrap gap-4 pt-8">
              {['Analyze Physique', 'Personalized Plan', 'Track Progress'].map((feature) => (
                <div key={feature} className="px-6 py-3 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-white/90 text-sm font-medium">
                  {feature}
                </div>
              ))}
            </div>
          </div>

          {/* Right Column - Hero Visual */}
          <div className="hidden lg:block relative">
             {/* Abstract visual or dashboard preview could go here. 
                 For now, keeping it empty or simple to match reference if it had an image. 
                 Reference code stopped at text-orange-300/90. 
                 I'll add a placeholder or simple graphic. */}
             <div className="relative w-full aspect-square bg-gradient-to-tr from-orange-500/20 to-purple-600/20 rounded-full blur-3xl animate-pulse"></div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Landing;
