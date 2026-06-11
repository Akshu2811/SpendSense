import React from 'react';
import { Link } from 'react-router-dom';

export default function Privacy() {
  return (
    <div className="state-calm min-h-screen px-5 py-10 max-w-lg mx-auto fade-in">
      <Link to="/" style={{ color: 'var(--accent)', fontSize: 13 }}>← back</Link>
      <h1 className="text-2xl font-medium mt-6 mb-4">Privacy Policy</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.7 }}>
        SpendSense stores only the data you provide. No data is sold to third parties.
        Transaction data is processed through Fivetran and stored in BigQuery.
        Personal data and purchase history are stored in MongoDB Atlas (GCP asia-south1).
        You can delete all your data at any time from Settings.
      </p>
    </div>
  );
}
