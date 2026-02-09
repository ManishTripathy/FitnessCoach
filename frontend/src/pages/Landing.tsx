import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Menu, MessageCircle, AlertCircle, Check, FastForward, Pause } from 'lucide-react';
import { Header } from '../components/Header';

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
      <Header variant="transparent" />

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
                onClick={() => navigate('/analyze')}
                className="bg-orange-600 text-white text-xl px-12 py-5 rounded-full shadow-lg hover:bg-orange-700 hover:scale-[1.03] active:scale-[0.97] transition-all duration-200 font-semibold font-sans"
              >
                Try now
              </button>
            </div>

            {/* Energy stats */}
            <div className="flex gap-12 pt-6">
              <div className="space-y-2">
                <div className="text-5xl font-black text-orange-500 font-sans">100%</div>
                <div className="text-base text-white/70 font-medium font-sans">Personalized Plans</div>
              </div>
              <div className="space-y-2">
                <div className="text-5xl font-black text-orange-500 font-sans">24/7</div>
                <div className="text-base text-white/70 font-medium font-sans">AI Coach Access</div>
              </div>
            </div>
          </div>

          {/* Right Column - Mobile Phone Frame */}
          <div className="flex items-center justify-center lg:justify-end">
            <div className="relative w-full max-w-[375px] h-[812px] bg-gradient-to-br from-slate-900 to-black rounded-[3rem] shadow-2xl shadow-orange-500/20 overflow-hidden border-8 border-slate-800">
              {/* Phone Notch */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-7 bg-black rounded-b-3xl z-10"></div>
              
              {/* App Content - Mock Interface */}
              <div className="relative h-full w-full bg-[#1c1c1e] overflow-y-auto text-white font-sans no-scrollbar">
                {/* Status Bar Mock */}
                <div className="flex justify-between items-center px-6 pt-12 pb-4 bg-gradient-to-b from-black/50 to-transparent">
                  <ArrowLeft className="w-6 h-6 text-white cursor-pointer" />
                  <div className="text-xl font-bold tracking-tight"><span className="text-orange-500">Ryan</span> Coach</div>
                  <Menu className="w-6 h-6 text-white cursor-pointer" />
                </div>

                {/* Header Text */}
                <div className="px-6 py-4">
                  <h2 className="text-4xl font-black leading-[0.95] tracking-tight">
                    Your <br />
                    <span className="text-orange-500">Shredded</span> Plan
                  </h2>
                  <p className="text-gray-400 mt-3 text-sm font-medium">
                    7-day personalized workout schedule • <br/>Drag to reorder
                  </p>
                </div>

                {/* Card */}
                <div className="px-4 pb-8">
                  <div className="bg-[#2c2c2e] rounded-[2rem] overflow-hidden p-4 shadow-2xl border border-white/5">
                    {/* Image Area */}
                    <div className="relative h-48 rounded-2xl overflow-hidden mb-4 group">
                      <img 
                        src="https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80" 
                        alt="Workout" 
                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                      
                      {/* Chat Bubble */}
                      <div className="absolute top-3 right-3 bg-orange-500 p-2 rounded-full shadow-lg">
                         <MessageCircle className="w-5 h-5 text-white" />
                      </div>
                      
                      {/* Overlay Text */}
                      <div className="absolute bottom-3 left-3">
                         {/* <div className="text-white/90 font-bold text-3xl italic tracking-tighter drop-shadow-lg" style={{ fontFamily: 'cursive' }}>DAY 1</div> */}
                         <div className="text-white font-black text-3xl leading-none uppercase drop-shadow-lg tracking-wide">FULL BODY</div>
                      </div>
                    </div>

                    {/* Badges */}
                    <div className="flex gap-2 mb-4">
                      <span className="bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-md shadow-orange-500/20">Day 1</span>
                      <span className="bg-yellow-900/40 text-yellow-500 px-3 py-1 rounded-full text-xs font-bold border border-yellow-600/30">Intermediate</span>
                    </div>

                    {/* Title */}
                    <h3 className="text-xl font-bold text-white mb-1 leading-tight">30 Minute Full Body Workout</h3>
                    <div className="flex items-center gap-2 mb-5 text-sm font-medium">
                      <span className="text-gray-400">Full Body</span>
                      <span className="text-orange-500">35 min</span>
                    </div>

                    {/* Note Box */}
                    <div className="bg-[#3a3a3c] rounded-2xl p-4 mb-6 flex gap-3 border border-white/5">
                      <AlertCircle className="w-5 h-5 text-orange-500 shrink-0 mt-0.5" />
                      <p className="text-xs text-gray-300 italic leading-relaxed">
                        Kicking off the week with a full body workout to engage all major muscle groups and build a solid foundation for the week's activities.
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="space-y-5">
                      <div>
                        <p className="text-gray-500 text-xs font-semibold uppercase tracking-wider mb-3">Completed?</p>
                        <div className="flex gap-3">
                           <button className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center border border-green-500/30 hover:bg-green-500/30 transition-colors">
                             <Check className="w-6 h-6 text-green-500" />
                           </button>
                           <button className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center border border-blue-500/30 hover:bg-blue-500/30 transition-colors">
                             <FastForward className="w-6 h-6 text-blue-500" />
                           </button>
                           <button className="w-12 h-12 bg-gray-700/50 rounded-xl flex items-center justify-center border border-gray-600/30 hover:bg-gray-700 transition-colors">
                             <Pause className="w-6 h-6 text-gray-400" />
                           </button>
                        </div>
                      </div>

                      <div>
                         <p className="text-gray-500 text-xs font-semibold uppercase tracking-wider mb-3">Effort</p>
                         <div className="flex gap-3">
                            {['😋', '💪', '😅', '🥵'].map((emoji, i) => (
                              <button key={i} className="w-12 h-12 bg-[#3a3a3c] rounded-xl flex items-center justify-center text-2xl hover:bg-[#4a4a4c] hover:scale-110 transition-all border border-white/5 shadow-lg">
                                {emoji}
                              </button>
                            ))}
                         </div>
                      </div>
                    </div>

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
