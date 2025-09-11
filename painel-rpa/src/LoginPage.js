import React, { useState } from 'react';
import './LoginPage.css';
import logo from './assets/logo-onesid.png';
import { login } from './api'; // Importa a função de login da nossa API

function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      // A resposta da API agora inclui 'access_token' e 'role'
      const data = await login(username, password);
      
      if (data.access_token && data.role) {
        // Passa o token e a role para o componente App
        onLoginSuccess(data.access_token, data.role);
      } else {
        setError('Resposta de login inválida do servidor.');
      }
    } catch (err) {
      setError(err.message || 'Falha no login. Verifique suas credenciais.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <img src={logo} alt="Logo OneSid" className="login-logo" />
        <form onSubmit={handleLogin}>
          <div className="input-group">
            <input
              type="text"
              placeholder="Usuário"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="input-group">
            <input
              type="password"
              placeholder="Senha"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="login-button">Entrar</button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;