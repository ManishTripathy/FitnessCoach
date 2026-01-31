import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-base-200 flex flex-col items-center justify-center p-4">
      <div className="card w-96 bg-base-100 shadow-xl">
        <figure className="px-10 pt-10">
          <div className="avatar placeholder">
            <div className="bg-neutral text-neutral-content rounded-full w-24">
              <span className="text-3xl">FC</span>
            </div>
          </div>
        </figure>
        <div className="card-body items-center text-center">
          <h2 className="card-title">Fitness Coach</h2>
          <p>Welcome to your AI-powered fitness journey!</p>
          <div className="card-actions">
            <button className="btn btn-primary">Get Started</button>
            <button className="btn btn-ghost">Log In</button>
          </div>
        </div>
      </div>
      
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="stats shadow">
          <div className="stat">
            <div className="stat-title">Backend Status</div>
            <div className="stat-value text-primary text-2xl">Checking...</div>
            <div className="stat-desc">Connecting to Python API</div>
          </div>
        </div>
        
        <div className="stats shadow">
          <div className="stat">
            <div className="stat-title">AI Status</div>
            <div className="stat-value text-secondary text-2xl">Checking...</div>
            <div className="stat-desc">Gemini Integration</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
