import React from 'react';
import { useNavigate } from 'react-router-dom';

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
    <div className="w-full py-6 bg-base-100 shadow-sm">
      <ul className="steps w-full">
        {steps.map((step, index) => (
          <li 
            key={index} 
            className={`step ${index <= currentStep ? 'step-primary' : ''} cursor-pointer hover:text-primary transition-colors`}
            onClick={() => {
                // Allow navigation to completed or current steps
                if (index <= currentStep + 1) navigate(step.path); 
            }}
          >
            {step.label}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PhaseStepper;
