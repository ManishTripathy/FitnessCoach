import React, { ReactNode } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Observe from './pages/Observe';
import Decide from './pages/Decide';
import Act from './pages/Act';
import Landing from './pages/Landing';
import { useAuth } from './auth/AuthContext';


interface PrivateRouteProps {
  children: ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { currentUser, loading } = useAuth();
  
  if (loading) return <div className="flex justify-center items-center h-screen"><span className="loading loading-spinner loading-lg"></span></div>;
  
  return currentUser ? <>{children}</> : <Navigate to="/login" />;
};

import { PhotoUpload } from './components/PhotoUpload';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/analyze" element={<PhotoUpload onBack={() => window.location.href = '/'} />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route 
          path="/observe" 
          element={
            <PrivateRoute>
              <Observe />
            </PrivateRoute>
          } 
        />
        <Route 
          path="/decide" 
          element={
            <PrivateRoute>
              <Decide />
            </PrivateRoute>
          } 
        />
        <Route 
          path="/act" 
          element={
            <PrivateRoute>
              <Act />
            </PrivateRoute>
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;
