document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const promptInput = document.getElementById('prompt-input');
    const processButton = document.getElementById('process-button');

    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'ai-message');

        const avatarImg = document.createElement('img');
        avatarImg.classList.add('avatar');
        avatarImg.src = isUser ? '/static/user-avatar.png' : '/static/ai-avatar.png';
        avatarImg.alt = isUser ? 'User Avatar' : 'AI Avatar';

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');

        if (isUser) {
            messageContent.textContent = content;
        } else {
            messageContent.innerHTML = marked.parse(content);
        }

        messageDiv.appendChild(avatarImg);
        messageDiv.appendChild(messageContent);

        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    async function processPrompt() {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        addMessage(prompt, true);
        promptInput.value = '';

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            addMessage(data.response);
        } catch (error) {
            console.error('Error:', error);
            addMessage('An error occurred while processing your request.');
        }
    }

    processButton.addEventListener('click', processPrompt);
    promptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            processPrompt();
        }
    });

    function createStar() {
        const star = document.createElement('div');
        star.classList.add('star');
        star.style.left = `${Math.random() * 100}vw`;
        star.style.animationDuration = `${Math.random() * 3 + 2}s`;
        document.querySelector('.background-animation').appendChild(star);

        star.addEventListener('animationend', () => {
            star.remove();
        });
    }

    setInterval(createStar, 100);
});