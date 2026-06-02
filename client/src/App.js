import React, { useState } from 'react';
import { useGoogleLogin, googleLogout } from '@react-oauth/google';
import axios from 'axios';

function App() {
  const [user, setUser] = useState(null);
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState({});
  const [filter, setFilter] = useState('all');

  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true);
      try {
        // Fetch Real User Profile from Google
        const userInfo = await axios.get(
          'https://www.googleapis.com/oauth2/v1/userinfo?alt=json',
          { headers: { Authorization: `Bearer ${tokenResponse.access_token}` } }
        );
        setUser(userInfo.data); 

        // Send token to LIVE backend to scan Live Inbox
        const res = await axios.post('https://ai-spam-shield-r5xm.onrender.com/fetch-emails', {
          access_token: tokenResponse.access_token
        });
        setEmails(res.data);
      } catch (error) {
        console.error("Backend Error:", error);
        alert("Failed to connect to backend. Please ensure the Render server is running.");
      }
      setLoading(false);
    },
    scope: 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.profile',
    onError: () => console.log('Login Failed'),
  });

  const handleLogout = () => {
    googleLogout();
    setUser(null);
    setEmails([]);
    setFeedbackGiven({});
    setFilter('all');
  };

  const submitFeedback = async (id, type) => {
    try {
      // Send feedback to LIVE backend
      await axios.post('https://ai-spam-shield-r5xm.onrender.com/feedback', { id: id, feedback: type });
      setFeedbackGiven(prev => ({ ...prev, [id]: true }));
    } catch (err) {
      console.error("Feedback error", err);
    }
  };

  const spamCount = emails.filter(e => e.result === 'spam').length;
  const hamCount = emails.length - spamCount;
  
  const displayedEmails = emails.filter(e => filter === 'all' || e.result === filter);

  return (
    <div style={styles.container}>
      <style>{`
        body { margin: 0; background-color: #09090b; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .email-card { animation: slideUp 0.4s ease forwards; opacity: 0; transition: 0.2s; }
        .email-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.4); border-color: #3f3f46; }
        .filter-btn { transition: 0.2s; }
        .filter-btn:hover { background: #27272a; }
      `}</style>

      <div style={styles.mainCard}>
        <div style={styles.headerFlex}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={styles.logoIcon}>🛡️</div>
            <h1 style={styles.header}>AI Spam Shield</h1>
          </div>
          {user && <button onClick={handleLogout} style={styles.logoutBtn}>Disconnect</button>}
        </div>

        {!user ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <h2 style={{ color: '#fafafa', marginBottom: '10px', fontSize: '24px' }}>Secure Your Inbox</h2>
            <p style={{ color: '#a1a1aa', marginBottom: '40px', fontSize: '15px' }}>Connect your Gmail to deploy real-time AI spam detection.</p>
            <button onClick={() => login()} style={styles.loginBtn}>
              <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" alt="G" style={{ width: '18px', marginRight: '10px' }} />
              Continue with Google
            </button>
          </div>
        ) : (
          <div style={{ marginTop: '20px' }}>
            
            <div style={styles.profileSection}>
              <img src={user.picture} alt="Profile" style={styles.profilePic} onError={(e) => { e.target.src = 'https://ui-avatars.com/api/?name=' + user.name; }} />
              <div style={{ textAlign: 'left' }}>
                <h2 style={{ margin: '0 0 5px 0', fontSize: '18px', color: '#fafafa' }}>{user.name}</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={styles.activeDot}></div><span style={{ color: '#10b981', fontSize: '12px', fontWeight: '600' }}>SYSTEM ACTIVE</span></div>
              </div>
            </div>
            
            {loading && (
              <div style={{ padding: '20px', textAlign: 'center', marginTop: '20px' }}>
                <span style={{ fontSize: '14px', color: '#38bdf8', fontWeight: '500' }}>Scanning latest 15 emails... ⏳</span>
              </div>
            )}

            {!loading && emails.length > 0 && (
              <div style={{ marginTop: '30px' }}>
                
                <div style={styles.statsContainer}>
                  <div style={styles.statBox}><p style={styles.statLabel}>Total Scanned</p><h3 style={styles.statNumber}>{emails.length}</h3></div>
                  <div style={styles.statBox}><p style={styles.statLabel}>Spam Detected</p><h3 style={{...styles.statNumber, color: '#f43f5e'}}>{spamCount}</h3></div>
                  <div style={styles.statBox}><p style={styles.statLabel}>Safe Emails</p><h3 style={{...styles.statNumber, color: '#10b981'}}>{hamCount}</h3></div>
                </div>

                <div style={styles.filterContainer}>
                  <h3 style={styles.sectionTitle}>Recent Inbox Activity</h3>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="filter-btn" onClick={() => setFilter('all')} style={styles.filterTab(filter === 'all')}>All</button>
                    <button className="filter-btn" onClick={() => setFilter('spam')} style={styles.filterTab(filter === 'spam')}>Spam</button>
                    <button className="filter-btn" onClick={() => setFilter('ham')} style={styles.filterTab(filter === 'ham')}>Safe</button>
                  </div>
                </div>
                
                {displayedEmails.map((email, index) => (
                  <div key={index} className="email-card" style={{ ...styles.emailCard, borderLeft: email.result === 'spam' ? '4px solid #f43f5e' : '4px solid #10b981', animationDelay: `${index * 0.05}s` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1, paddingRight: '20px' }}>
                        <h4 style={styles.emailSubject}>{email.subject}</h4>
                        <p style={styles.emailSnippet}>{email.snippet.substring(0, 100)}...</p>
                      </div>
                      
                      <div style={{ textAlign: 'right' }}>
                        <div style={styles.badge(email.result)}>{email.result.toUpperCase()}</div>
                        {email.confidence && (
                          <div style={{ marginTop: '6px', fontSize: '11px', color: '#71717a', fontWeight: '600' }}>
                            {email.confidence}% sure
                          </div>
                        )}
                      </div>
                    </div>

                    <div style={styles.feedbackSection}>
                      <span style={{ color: '#71717a', fontSize: '12px' }}>AI Prediction Accurate?</span>
                      {!feedbackGiven[email.id] ? (
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button onClick={() => submitFeedback(email.id, 'correct')} style={styles.fbBtn}>Yes</button>
                          <button onClick={() => submitFeedback(email.id, 'incorrect')} style={styles.fbBtn}>No</button>
                        </div>
                      ) : <span style={{ color: '#38bdf8', fontSize: '12px', fontWeight: '600' }}>Feedback logged ✓</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Pro-level UI Styling
const styles = {
  container: { fontFamily: "system-ui, -apple-system, sans-serif", backgroundColor: '#09090b', minHeight: '100vh', padding: '40px 20px', display: 'flex', justifyContent: 'center', boxSizing: 'border-box' },
  mainCard: { background: '#18181b', border: '1px solid #27272a', borderRadius: '16px', padding: '30px', width: '100%', maxWidth: '750px', height: 'fit-content', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' },
  headerFlex: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #27272a', paddingBottom: '20px', marginBottom: '20px' },
  logoIcon: { background: '#27272a', padding: '8px', borderRadius: '8px', fontSize: '18px' },
  header: { margin: '0', fontSize: '20px', fontWeight: '700', color: '#fafafa' },
  logoutBtn: { background: 'transparent', color: '#a1a1aa', border: '1px solid #3f3f46', padding: '6px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: '600' },
  loginBtn: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: '#fafafa', color: '#09090b', padding: '12px 24px', fontSize: '14px', fontWeight: '600', border: 'none', borderRadius: '8px', cursor: 'pointer' },
  profileSection: { display: 'flex', alignItems: 'center', gap: '15px', background: '#09090b', padding: '15px 20px', borderRadius: '12px', border: '1px solid #27272a' },
  profilePic: { width: '48px', height: '48px', borderRadius: '50%', border: '2px solid #3f3f46', objectFit: 'cover' },
  activeDot: { width: '8px', height: '8px', backgroundColor: '#10b981', borderRadius: '50%', boxShadow: '0 0 8px #10b981' },
  statsContainer: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px', marginBottom: '30px' },
  statBox: { background: '#09090b', border: '1px solid #27272a', padding: '15px', borderRadius: '10px' },
  statLabel: { margin: '0 0 8px 0', fontSize: '11px', color: '#71717a', textTransform: 'uppercase', fontWeight: '600' },
  statNumber: { margin: '0', fontSize: '24px', fontWeight: '700', color: '#fafafa' },
  filterContainer: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', paddingBottom: '10px', borderBottom: '1px solid #27272a' },
  sectionTitle: { color: '#fafafa', fontSize: '15px', fontWeight: '600', margin: '0' },
  filterTab: (isActive) => ({ background: isActive ? '#27272a' : 'transparent', color: isActive ? '#fafafa' : '#a1a1aa', border: '1px solid #3f3f46', padding: '4px 12px', borderRadius: '20px', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }),
  emailCard: { background: '#09090b', border: '1px solid #27272a', borderRight: 'none', borderTop: 'none', borderBottom: 'none', padding: '20px', borderRadius: '10px', marginBottom: '15px' },
  emailSubject: { margin: '0 0 6px 0', color: '#fafafa', fontSize: '15px', fontWeight: '600' },
  emailSnippet: { margin: '0', color: '#a1a1aa', fontSize: '13px', lineHeight: '1.6' },
  badge: (type) => ({ background: type === 'spam' ? 'rgba(244, 63, 94, 0.1)' : 'rgba(16, 185, 129, 0.1)', color: type === 'spam' ? '#f43f5e' : '#10b981', border: `1px solid ${type === 'spam' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)'}`, padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', display: 'inline-block' }),
  feedbackSection: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '15px', paddingTop: '15px', borderTop: '1px dashed #27272a' },
  fbBtn: { background: '#18181b', color: '#a1a1aa', border: '1px solid #3f3f46', padding: '4px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: '600' }
};

export default App;