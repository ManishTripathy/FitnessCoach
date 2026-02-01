import React, { ReactNode } from 'react';
import PhaseStepper from './PhaseStepper';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';

interface LayoutProps {
  children: ReactNode;
  currentStep: number;
}

const Layout: React.FC<LayoutProps> = ({ children, currentStep }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error("Failed to log out", error);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Navbar */}
      <header className="relative w-full bg-background/50 backdrop-blur-md border-b border-border z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-xl font-bold">
            <span className="text-primary">Fitness</span> Coach AI
          </div>
          <div className="flex items-center gap-6">
             <Button variant="ghost" onClick={handleLogout}>Logout</Button>
          </div>
        </div>
      </header>

      {/* Stepper */}
      <div className="w-full bg-muted/20 border-b border-border">
          <PhaseStepper currentStep={currentStep} />
      </div>

      {/* Main Content */}
      <main className="flex-grow container mx-auto p-6 animate-fade-in">
        {children}
      </main>
    </div>
  );
};

export default Layout;
