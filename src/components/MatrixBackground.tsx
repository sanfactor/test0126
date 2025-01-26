import { useEffect } from 'react';

export function MatrixBackground() {
  useEffect(() => {
    const container = document.getElementById('matrixBg');
    if (!container) return;

    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    const columns = Math.floor(window.innerWidth / 15); // Increased density
    
    const createRainDrop = () => {
      const element = document.createElement('div');
      element.className = 'matrix-character';
      element.style.left = `${Math.random() * 100}%`;
      element.style.animationDelay = `${Math.random() * 3}s`; // More varied delays
      element.innerText = characters[Math.floor(Math.random() * characters.length)];
      
      container.appendChild(element);
      
      setTimeout(() => {
        element.remove();
      }, 4000); // Match the CSS animation duration
    };

    const interval = setInterval(() => {
      for (let i = 0; i < columns / 4; i++) { // Create more characters per interval
        createRainDrop();
      }
    }, 120); // Slightly slower interval for better performance

    return () => {
      clearInterval(interval);
      container.innerHTML = '';
    };
  }, []);

  return null;
}
