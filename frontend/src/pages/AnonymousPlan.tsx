import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { WorkoutPlan } from '../components/WorkoutPlan';

export default function AnonymousPlan() {
  const { goal } = useParams<{ goal: string }>();
  const navigate = useNavigate();

  // If no goal is provided, redirect to analyze
  React.useEffect(() => {
    if (!goal) {
      navigate('/analyze');
    }
  }, [goal, navigate]);

  if (!goal) return null;

  return (
    <WorkoutPlan 
      onBack={() => navigate('/analyze')}
      goalType={goal.charAt(0).toUpperCase() + goal.slice(1)} // Capitalize first letter
    />
  );
}
