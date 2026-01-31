import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Observe from './pages/Observe';
import { useAuth } from './auth/AuthContext';

const PrivateRoute = ({ children }) => {
  const { currentUser, loading } = useAuth();
  
  if (loading) return <div className="flex justify-center items-center h-screen"><span className="loading loading-spinner loading-lg"></span></div>;
  
  return currentUser ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <Router>
      <Routes>
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
        <Route path="/" element={<Navigate to="/observe" />} />
      </Routes>
    </Router>
  );
}

export default App;
