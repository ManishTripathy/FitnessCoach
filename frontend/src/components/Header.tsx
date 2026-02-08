import React, { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { AuthModal } from './AuthModal';
import { Menu, X, ArrowLeft, LogOut, User as UserIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';

interface HeaderProps {
  variant?: 'transparent' | 'default';
  showBack?: boolean;
  onBack?: () => void;
  className?: string;
}

export const Header: React.FC<HeaderProps> = ({ 
  variant = 'default', 
  showBack = false, 
  onBack,
  className 
}) => {
  const { currentUser, logout } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      setIsMobileMenuOpen(false);
      window.location.reload();
    } catch (error) {
      console.error("Logout failed", error);
    }
  };

  const isTransparent = variant === 'transparent';

  return (
    <>
      <header 
        className={cn(
          "relative w-full z-50 transition-colors duration-200",
          isTransparent 
            ? "bg-black/50 backdrop-blur-md border-b border-white/10 text-white" 
            : "bg-background/80 backdrop-blur-md border-b border-border text-foreground",
          className
        )}
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {showBack && (
              <button 
                onClick={onBack}
                className={cn(
                  "p-2 rounded-full transition-colors",
                  isTransparent 
                    ? "hover:bg-white/10 text-white/80 hover:text-white" 
                    : "hover:bg-accent text-muted-foreground hover:text-foreground"
                )}
                aria-label="Go back"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}
            
            <div 
              className="text-xl font-bold cursor-pointer flex items-center gap-2"
              onClick={() => navigate('/')}
            >
              <span className="text-orange-500">Ryan</span> 
              <span>Coach</span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            <button 
                className={cn(
                    "transition-colors text-sm font-medium",
                    isTransparent ? "text-white/80 hover:text-white" : "text-muted-foreground hover:text-foreground"
                )}
                onClick={() => window.open('mailto:support@ryancoach.ai')}
            >
              Help
            </button>
            
            {currentUser ? (
              <div className="flex items-center gap-4">
                 <span className={cn(
                    "text-sm", 
                    isTransparent ? "text-white/80" : "text-muted-foreground"
                 )}>
                    {currentUser.email}
                 </span>
                 <button 
                    className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-full transition-colors text-sm font-medium",
                        isTransparent 
                            ? "bg-white/10 hover:bg-white/20 text-white" 
                            : "bg-secondary hover:bg-secondary/80 text-secondary-foreground"
                    )}
                    onClick={handleLogout}
                >
                  <LogOut className="w-4 h-4" />
                  Log out
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-4">
                <button 
                    className={cn(
                        "transition-colors text-sm font-medium",
                        isTransparent ? "text-white/80 hover:text-white" : "text-muted-foreground hover:text-foreground"
                    )}
                    onClick={() => setIsAuthModalOpen(true)}
                >
                  Log in
                </button>
                <button 
                    className="bg-orange-500 text-white px-5 py-2 rounded-full hover:bg-orange-600 transition-colors text-sm font-medium shadow-lg hover:shadow-orange-500/20"
                    onClick={() => setIsAuthModalOpen(true)}
                >
                  Sign up
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            className="md:hidden p-2"
            onClick={() => setIsMobileMenuOpen(true)}
          >
            <Menu className={cn("w-6 h-6", isTransparent ? "text-white" : "text-foreground")} />
          </button>
        </div>
      </header>

      {/* Mobile Menu Drawer */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-[60] md:hidden">
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsMobileMenuOpen(false)}
          />
          <div className="absolute right-0 top-0 h-full w-[280px] bg-slate-900 border-l border-white/10 p-6 shadow-2xl animate-in slide-in-from-right duration-200">
            <div className="flex justify-between items-center mb-8">
              <span className="text-xl font-bold text-white">Menu</span>
              <button 
                onClick={() => setIsMobileMenuOpen(false)}
                className="p-2 text-white/60 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="flex flex-col gap-6">
              {currentUser ? (
                <>
                    <div className="flex items-center gap-3 text-white/80 p-3 bg-white/5 rounded-lg">
                        <UserIcon className="w-5 h-5" />
                        <span className="text-sm truncate">{currentUser.email}</span>
                    </div>
                    <button 
                        className="flex items-center gap-3 text-white/80 hover:text-white transition-colors p-2"
                        onClick={handleLogout}
                    >
                        <LogOut className="w-5 h-5" />
                        Log out
                    </button>
                </>
              ) : (
                <>
                    <button 
                        className="w-full bg-orange-500 text-white px-5 py-3 rounded-xl hover:bg-orange-600 transition-colors font-medium"
                        onClick={() => {
                            setIsMobileMenuOpen(false);
                            setIsAuthModalOpen(true);
                        }}
                    >
                        Sign up / Log in
                    </button>
                </>
              )}
              
              <div className="h-px bg-white/10 my-2" />
              
              <button 
                className="text-left text-white/60 hover:text-white transition-colors p-2"
                onClick={() => window.open('mailto:support@ryancoach.ai')}
              >
                Help & Support
              </button>
            </div>
          </div>
        </div>
      )}

      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)} 
        // Note: sessionId is not passed here as this header is for global auth.
        // Page-specific save flows should use their own AuthModal trigger if needed,
        // or we could potentially accept sessionId as a prop if we really want to support saving from header login.
      />
    </>
  );
};
