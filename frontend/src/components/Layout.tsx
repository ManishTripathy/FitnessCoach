import React, { ReactNode } from 'react';
import PhaseStepper from './PhaseStepper';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
  currentStep: number;
}

const Layout: React.FC<LayoutProps> = ({ children, currentStep }) => {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Navbar */}
      <Header variant="default" />

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
