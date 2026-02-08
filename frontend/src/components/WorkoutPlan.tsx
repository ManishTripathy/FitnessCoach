import { useState, useEffect, useRef } from 'react';
import { GripVertical, Play, MessageCircle, X, AlertCircle, Maximize2, Send } from 'lucide-react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { getAuth } from 'firebase/auth';
import { anonymousApi, actApi } from '../services/api';
import { Header } from './Header';

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
  videoUrl?: string;
  isRestDay: boolean;
}

// Helper to extract thumbnail
const getYoutubeThumbnail = (url: string) => {
  try {
    const videoIdMatch = url.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/);
    if (videoIdMatch && videoIdMatch[1]) {
      return `https://img.youtube.com/vi/${videoIdMatch[1]}/hqdefault.jpg`;
    }
    return null;
  } catch (e) {
    return null;
  }
};

// Helper to map backend day to frontend WorkoutDay
const mapToWorkoutDay = (day: any): WorkoutDay => {
  const details = day.workout_details || {};
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
    videoUrl: details.url || null,
    isRestDay: day.is_rest || false,
  };
};

interface DragItem {
  index: number;
  id: string;
  type: string;
}

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'ryan';
}

interface ChatStickyProps {
  day: WorkoutDay;
  onClose: () => void;
  onExpand: () => void;
  cardRef: HTMLDivElement | null;
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
}

function ChatSticky({ day, onClose, onExpand, cardRef, messages, onSendMessage }: ChatStickyProps) {
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (cardRef) {
      const updatePosition = () => {
        const rect = cardRef.getBoundingClientRect();
        setPosition({
          top: rect.top,
          left: rect.right + 16
        });
      };

      updatePosition();
      window.addEventListener('scroll', updatePosition, true);
      window.addEventListener('resize', updatePosition);

      return () => {
        window.removeEventListener('scroll', updatePosition, true);
        window.removeEventListener('resize', updatePosition);
      };
    }
  }, [cardRef]);

  const handleSend = () => {
    if (inputText.trim()) {
      onSendMessage(inputText);
      setInputText('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasUserMessage = messages.some(m => m.sender === 'user');

  const quickPrompts = [
    'Suggest shorter version',
    'Too intense',
    'Something easier',
  ];

  return (
    <div 
      className="fixed z-40 animate-slideInRight hidden lg:block"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        maxHeight: '80vh'
      }}
    >
      <div className="w-80 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl border border-orange-500/30 overflow-hidden flex flex-col h-[500px]">
        {/* Sticky Note Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 p-4 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white font-bold shadow-lg">
              R
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-bold text-sm font-sans truncate">Day {day.day} Chat</p>
              <p className="text-white/80 text-xs font-sans truncate">{day.title}</p>
            </div>
            <button
              onClick={onExpand}
              className="w-8 h-8 rounded-lg bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
            >
              <Maximize2 className="w-4 h-4 text-white" />
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

        {/* Chat Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-2 items-start ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white font-bold text-xs flex-shrink-0 ${
                msg.sender === 'ryan' ? 'bg-gradient-to-br from-orange-500 to-red-500' : 'bg-slate-600'
              }`}>
                {msg.sender === 'ryan' ? 'R' : 'U'}
              </div>
              <div className={`rounded-lg p-3 max-w-[80%] ${
                msg.sender === 'ryan' 
                  ? 'bg-slate-700/50 rounded-tl-sm text-white' 
                  : 'bg-orange-500/20 text-white rounded-tr-sm'
              }`}>
                <p className="text-sm font-sans">{msg.text}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Prompts */}
        {!hasUserMessage && (
          <div className="px-3 pb-2 space-y-2 flex-shrink-0">
            <p className="text-white/40 text-xs font-sans">Ask Ryan:</p>
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => onSendMessage(prompt)}
                className="w-full text-left px-3 py-2 rounded-lg bg-slate-700/30 text-white/70 hover:bg-slate-700 hover:text-white transition-all font-sans text-xs flex items-center gap-2 border border-white/5 hover:border-white/10"
              >
                <Send className="w-3 h-3" />
                {prompt}
              </button>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="p-3 border-t border-white/10 bg-slate-900/50 flex-shrink-0">
          <div className="relative">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Message Ryan..."
              className="w-full bg-slate-800 text-white pl-4 pr-10 py-3 rounded-xl border border-white/10 focus:outline-none focus:border-orange-500/50 text-sm font-sans placeholder:text-white/20"
            />
            <button
              onClick={handleSend}
              disabled={!inputText.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg bg-orange-500 text-white disabled:opacity-50 disabled:bg-slate-700 transition-all hover:bg-orange-600"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

interface FeedbackModalProps {
  day: WorkoutDay;
  onClose: () => void;
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
}

function FeedbackModal({ day, onClose, messages, onSendMessage }: FeedbackModalProps) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (inputText.trim()) {
      onSendMessage(inputText);
      setInputText('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasUserMessage = messages.some(m => m.sender === 'user');

  const quickPrompts = [
    'Suggest shorter version',
    'Too intense',
    'Something easier',
  ];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4 animate-fadeIn">
      <div className="bg-slate-900 rounded-3xl w-full max-w-lg h-[85vh] border border-white/10 shadow-2xl flex flex-col overflow-hidden">
        {/* Header with Coach Avatar */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 p-6 flex items-center gap-4 z-10 flex-shrink-0">
          <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white font-bold text-xl shadow-lg">
            R
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-white font-bold font-sans text-lg">Day {day.day} Chat</h3>
            <p className="text-white/90 text-sm font-sans truncate">{day.title}</p>
          </div>
          <button 
            onClick={onClose}
            className="w-10 h-10 rounded-lg bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Chat Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0 ${
                msg.sender === 'ryan' ? 'bg-gradient-to-br from-orange-500 to-red-500' : 'bg-slate-600'
              }`}>
                {msg.sender === 'ryan' ? 'R' : 'U'}
              </div>
              <div className={`rounded-2xl p-4 max-w-[80%] ${
                msg.sender === 'ryan' 
                  ? 'bg-slate-800 rounded-tl-sm text-white' 
                  : 'bg-orange-500/20 text-white rounded-tr-sm'
              }`}>
                <p className="font-sans text-sm sm:text-base leading-relaxed">{msg.text}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Prompts */}
        {!hasUserMessage && (
          <div className="px-6 pb-2 space-y-2 flex-shrink-0">
            <p className="text-white/40 text-xs font-sans">Ask Ryan:</p>
            <div className="space-y-2">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => onSendMessage(prompt)}
                  className="w-full text-left px-4 py-3 rounded-xl bg-slate-800/50 text-white/70 hover:bg-slate-800 hover:text-white transition-all font-sans text-sm flex items-center gap-3 border border-white/5 hover:border-white/10"
                >
                  <Send className="w-4 h-4" />
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-white/10 bg-slate-900 flex-shrink-0">
          <div className="relative flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Message Ryan..."
              className="flex-1 bg-slate-800 text-white pl-4 pr-12 py-4 rounded-xl border border-white/10 focus:outline-none focus:border-orange-500/50 text-base font-sans placeholder:text-white/20"
            />
            <button
              onClick={handleSend}
              disabled={!inputText.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center rounded-lg bg-orange-500 text-white disabled:opacity-50 disabled:bg-slate-700 transition-all hover:bg-orange-600 shadow-lg"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function WorkoutCard({ 
  day, 
  index, 
  moveCard,
  isActiveChatDay,
  onChatToggle,
  onUpdateDay
}: { 
  day: WorkoutDay; 
  index: number; 
  moveCard: (dragIndex: number, hoverIndex: number) => void;
  isActiveChatDay: boolean;
  onChatToggle: (dayId: string) => void;
  onUpdateDay: (dayId: string, updatedDay: WorkoutDay) => void;
}) {
  const [showExpandedModal, setShowExpandedModal] = useState(false);
  const [cardRef, setCardRef] = useState<HTMLDivElement | null>(null);
  const [effort, setEffort] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: '1', text: 'Need any adjustments? 💪', sender: 'ryan' }
  ]);
  
  const handleSendMessage = async (text: string) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      text,
      sender: 'user'
    };
    setMessages(prev => [...prev, newMessage]);
    
    try {
      const result = await actApi.chatWithAgent(text, day.id);
      
      if (result.status === 'success') {
        const agentMsg: ChatMessage = {
          id: Date.now().toString() + '_ryan',
          text: result.response_text,
          sender: 'ryan'
        };
        setMessages(prev => [...prev, agentMsg]);
        
        if (result.action === 'ADJUST_WORKOUT' && result.updated_day) {
          const newDay = mapToWorkoutDay(result.updated_day);
          onUpdateDay(day.id, newDay);
        }
      } else {
        setMessages(prev => [...prev, { 
          id: Date.now().toString(), 
          text: result.response_text || "I'm having trouble understanding that.", 
          sender: 'ryan' 
        }]);
      }
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        text: "Sorry, I lost connection. Please try again.", 
        sender: 'ryan' 
      }]);
    }
  };
  
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

  const effortIcons = {
    'Easy': '😊',
    'Manageable': '💪',
    'Hard': '😅',
    'Too Hard': '🥵',
  };

  const statusIcons = {
    'Completed': '✅',
    'Skipped': '⏭️',
    'Left Midway': '⏸️',
  };
 
  const handleStatusClick = (option: 'Completed' | 'Skipped' | 'Left Midway') => {
    setStatus(prev => (prev === option ? null : option));
  };

  return (
    <>
      <div
        ref={(node) => {
          drag(drop(node));
          setCardRef(node);
        }}
        className={`bg-black/40 backdrop-blur-xl rounded-2xl p-4 sm:p-6 border transition-all cursor-move group relative ${
          isDragging ? 'opacity-50' : ''
        } ${
          isActiveChatDay 
            ? 'border-orange-500 ring-2 ring-orange-500/30' 
            : 'border-white/10 hover:border-orange-500/50'
        } ${
          status === 'Completed' ? 'bg-gradient-to-br from-green-500/10 via-black/40 to-black/40' : ''
        }`}
      >
        {/* Completion Streak Badge */}
        {status === 'Completed' && (
          <div className="absolute -top-3 -right-3 bg-gradient-to-r from-green-400 to-green-600 text-white px-3 py-1 rounded-full text-xs font-bold font-sans shadow-lg z-10 flex items-center gap-1 animate-slideInTop">
            <span>🔥</span>
            <span>Done!</span>
          </div>
        )}

        {/* Ryan Chat Head - Only for non-rest days */}
        {!day.isRestDay && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onChatToggle(day.id);
            }}
            className={`absolute top-4 right-4 w-10 h-10 rounded-full flex items-center justify-center text-white font-bold shadow-lg transition-all z-10 ${
              isActiveChatDay
                ? 'bg-gradient-to-br from-orange-600 to-red-600 scale-110 ring-4 ring-orange-500/50'
                : 'bg-gradient-to-br from-orange-500 to-red-500 hover:scale-110'
            }`}
            style={{ cursor: 'pointer' }}
          >
            {isActiveChatDay ? (
              <div className="relative">
                <MessageCircle className="w-5 h-5" fill="white" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white animate-pulse"></div>
              </div>
            ) : (
              <MessageCircle className="w-5 h-5" />
            )}
          </button>
        )}

        <div className="flex flex-col sm:flex-row items-start gap-4">
          {/* Drag Handle - Hidden on mobile */}
          <div className="hidden sm:block pt-2 opacity-40 group-hover:opacity-100 transition-opacity">
            <GripVertical className="w-5 h-5 text-white" />
          </div>

          {/* Thumbnail */}
          {!day.isRestDay && day.thumbnail && (
            <a 
              href={day.videoUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className={`relative flex-shrink-0 w-full sm:w-32 h-32 sm:h-20 rounded-lg overflow-hidden bg-slate-800 block ${
                !day.videoUrl ? 'pointer-events-none' : 'cursor-pointer'
              }`}
            >
              <img
                src={day.thumbnail}
                alt={day.title}
                className="w-full h-full object-cover"
              />
              {/* Play button overlay */}
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center">
                  <Play className="w-6 h-6 text-white ml-0.5" fill="white" />
                </div>
              </div>
            </a>
          )}

          {/* Rest Day Icon */}
          {day.isRestDay && (
            <div className="flex-shrink-0 w-full sm:w-32 h-32 sm:h-20 rounded-lg bg-slate-800/50 flex items-center justify-center border-2 border-dashed border-slate-700">
              <span className="text-4xl sm:text-3xl">😴</span>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 min-w-0 w-full">
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <span className="bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold font-sans">
                Day {day.day}
              </span>
              {day.isRestDay && (
                <span className="bg-slate-700 text-white px-3 py-1 rounded-full text-xs font-semibold font-sans">
                  Rest
                </span>
              )}
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-1 font-sans">{day.title}</h3>
            {!day.isRestDay && (
              <>
                <p className="text-white/70 text-sm mb-3 font-sans">{day.exercises}</p>
                <div className="flex items-center gap-2 text-orange-400 text-sm font-sans mb-3">
                  <span>⏱️</span>
                  <span>{day.duration}</span>
                </div>

                {/* Quick Feedback Section - Mobile Responsive */}
                <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 mt-3 pt-3 border-t border-white/5">
                  <div className="flex items-center gap-2">
                    <span className="text-white/60 text-xs font-sans">Completed?</span>
                  </div>           
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* Status Buttons */}
                    {(['Completed', 'Skipped', 'Left Midway'] as const).map((option) => (
                      <button
                        key={option}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStatusClick(option);
                        }}
                        className={`w-9 h-9 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center transition-all ${
                          status === option
                            ? option === 'Completed' 
                              ? 'bg-green-500 scale-110 shadow-lg ring-2 ring-green-400/50' 
                              : 'bg-orange-500 scale-110 shadow-lg'
                            : 'bg-slate-700/50 hover:bg-slate-700'
                        }`}
                        title={option}
                      >
                        <span className="text-lg sm:text-base">{statusIcons[option]}</span>
                      </button>
                    ))}
                  </div>

                  <div className="hidden sm:block h-4 w-px bg-white/10"></div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-white/60 text-xs font-sans">Effort</span>
                    {/* Effort Buttons */}
                    {(['Easy', 'Manageable', 'Hard', 'Too Hard'] as const).map((option) => (
                      <button
                        key={option}
                        onClick={(e) => {
                          e.stopPropagation();
                          setEffort(option);
                        }}
                        className={`w-9 h-9 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center transition-all ${
                          effort === option
                            ? 'bg-orange-500 scale-110 shadow-lg'
                            : 'bg-slate-700/50 hover:bg-slate-700'
                        }`}
                        title={option}
                      >
                        <span className="text-lg sm:text-base">{effortIcons[option]}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Encouraging Message for Completion */}
              </>
            )}
            {day.isRestDay && (
              <p className="text-white/60 text-sm font-sans">Recovery and muscle repair</p>
            )}
          </div>
        </div>
      </div>

      {/* Sticky Chat Panel - Hidden on mobile, use modal instead */}
      {isActiveChatDay && !showExpandedModal && (
        <div className="hidden lg:block">
          <ChatSticky 
            day={day} 
            onClose={() => onChatToggle(day.id)}
            onExpand={() => setShowExpandedModal(true)}
            cardRef={cardRef}
            messages={messages}
            onSendMessage={handleSendMessage}
          />
        </div>
      )}

      {/* Auto-open modal on mobile when chat is active */}
      {isActiveChatDay && !showExpandedModal && (
        <div className="lg:hidden">
          <FeedbackModal 
            day={day} 
            onClose={() => onChatToggle(day.id)} 
            messages={messages}
            onSendMessage={handleSendMessage}
          />
        </div>
      )}

      {/* Expanded Modal */}
      {showExpandedModal && (
        <FeedbackModal 
          day={day} 
          onClose={() => {
            setShowExpandedModal(false);
            onChatToggle(day.id);
          }} 
          messages={messages}
          onSendMessage={handleSendMessage}
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
  const [activeChatDay, setActiveChatDay] = useState<string | null>(null);

  const toggleChatDay = (dayId: string) => {
    setActiveChatDay(prev => prev === dayId ? null : dayId);
  };

  useEffect(() => {
    if (fetchedGoal.current === goalType) return;
    fetchedGoal.current = goalType;

    const fetchPlan = async () => {
      try {
        setIsLoading(true);
        const auth = getAuth();
        const user = auth.currentUser;
        
        let scheduleData: any[] = [];

        if (user) {
           try {
               const response = await actApi.generatePlan();
               if (response.plan && response.plan.schedule) {
                   scheduleData = response.plan.schedule;
               } else if (response.schedule) {
                   scheduleData = response.schedule;
               }
           } catch (e) {
               console.error("Failed to fetch user plan, falling back to anonymous", e);
               // Fallback or re-throw? Ideally show error.
               // But if token is invalid, maybe fallback.
               throw e;
           }
        } else {
           const data = await anonymousApi.generatePlan(goalType);
           if (data && data.schedule) {
               scheduleData = data.schedule;
           }
        }
        
        if (scheduleData.length > 0) {
          const mappedDays: WorkoutDay[] = scheduleData.map(mapToWorkoutDay);
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

  const handleUpdateDay = (dayId: string, updatedDay: WorkoutDay) => {
    setWorkoutDays(prev => prev.map(d => d.id === dayId ? updatedDay : d));
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
      <Header variant="transparent" showBack={true} onBack={onBack} />

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
                  isActiveChatDay={activeChatDay === day.id}
                  onChatToggle={toggleChatDay}
                  onUpdateDay={handleUpdateDay}
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
