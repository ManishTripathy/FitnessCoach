import React from 'react';
import PhaseStepper from './PhaseStepper';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';

const Layout = ({ children, currentStep }) => {
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
    <div className="min-h-screen bg-base-200 flex flex-col">
      {/* Navbar */}
      <div className="navbar bg-base-100 shadow-md px-4">
        <div className="flex-1">
          <a className="btn btn-ghost normal-case text-xl text-primary font-bold">Fitness Coach AI</a>
        </div>
        <div className="flex-none">
          <button className="btn btn-ghost" onClick={handleLogout}>Logout</button>
        </div>
      </div>

      {/* Stepper */}
      <PhaseStepper currentStep={currentStep} />

      {/* Main Content */}
      <main className="flex-grow container mx-auto p-4 animate-fade-in">
        {children}
      </main>
    </div>
  );
};

export default Layout;
