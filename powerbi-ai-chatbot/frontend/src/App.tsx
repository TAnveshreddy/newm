import { useAuth } from './auth/useAuth';
import { ChatWindow } from './components/ChatWindow';

/**
 * Root component. Gates the chat surface behind authentication. In mock-auth
 * mode the user is always "signed in" so the UI runs against a MOCK_MODE
 * backend with no Entra tenant.
 */
export default function App() {
  const { isAuthenticated, login } = useAuth();

  if (!isAuthenticated) {
    return (
      <div className="signin">
        <div className="signin-card">
          <h1>Power BI AI Chatbot</h1>
          <p>Sign in with your company account to continue.</p>
          <button onClick={() => void login()}>Sign in with Microsoft</button>
        </div>
      </div>
    );
  }

  return <ChatWindow />;
}
