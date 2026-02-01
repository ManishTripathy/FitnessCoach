import React from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { Check } from 'lucide-react';

interface PhaseStepperProps {
  currentStep: number;
}

const PhaseStepper: React.FC<PhaseStepperProps> = ({ currentStep }) => {
  const navigate = useNavigate();
  
  const steps = [
    { label: 'Observe', path: '/observe' },
    { label: 'Decide', path: '/decide' },
    { label: 'Act', path: '/act' }
  ];

  return (
    <div className="w-full py-4 px-6 flex justify-center items-center">
      <div className="flex items-center w-full max-w-3xl">
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          const isLast = index === steps.length - 1;

          return (
            <React.Fragment key={index}>
              <div 
                className={cn(
                  "flex items-center gap-2 cursor-pointer",
                  (isActive || isCompleted) ? "text-primary" : "text-muted-foreground"
                )}
                onClick={() => {
                  if (index <= currentStep + 1) navigate(step.path);
                }}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center border-2 text-sm font-medium transition-colors",
                  isActive ? "border-primary bg-primary text-primary-foreground" : 
                  isCompleted ? "border-primary bg-primary text-primary-foreground" : "border-muted-foreground bg-background"
                )}>
                  {isCompleted ? <Check className="w-4 h-4" /> : index + 1}
                </div>
                <span className="font-medium hidden sm:inline">{step.label}</span>
              </div>
              
              {!isLast && (
                <div className="flex-1 mx-4 h-[2px] bg-muted relative">
                  <div 
                    className="absolute top-0 left-0 h-full bg-primary transition-all duration-300"
                    style={{ width: isCompleted ? '100%' : '0%' }}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default PhaseStepper;
