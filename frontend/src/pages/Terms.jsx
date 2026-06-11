import React from 'react';
import { Link } from 'react-router-dom';

export default function Terms() {
  return (
    <div className="state-calm min-h-screen px-5 py-10 max-w-lg mx-auto fade-in">
      <Link to="/" style={{ color: 'var(--accent)', fontSize: 13 }}>← back</Link>
      <h1 className="text-2xl font-medium mt-6 mb-4">Terms of Service</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.7 }}>
        SpendSense is provided as-is for personal financial awareness.
        It is not a licensed financial advisor. Budget suggestions are informational only.
        By using SpendSense you agree to our data practices described in the Privacy Policy.
        This service is free and open-source under the MIT License.
      </p>
    </div>
  );
}
