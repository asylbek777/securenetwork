// Фильтр заданий
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.btn-filter');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.dataset.category;
            window.location.href = `/?category=${category}`;
        });
    });

    // Уведомления для чата
    const chatSocket = new WebSocket('ws://' + window.location.host + '/ws/chat/');
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const chat = document.getElementById('chat-messages');
        chat.innerHTML += `<p><strong>${data.username}</strong> (${data.timestamp}): ${data.message}</p>`;
        chat.scrollTop = chat.scrollHeight;

        // Показ уведомления
        const notification = document.getElementById('chat-notification');
        notification.textContent = `Новое сообщение от ${data.username}`;
        notification.style.display = 'block';
        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    };

    document.getElementById('chat-form').onsubmit = function(e) {
        e.preventDefault();
        const messageInput = document.getElementById('message-input');
        chatSocket.send(JSON.stringify({'message': messageInput.value}));
        messageInput.value = '';
    };
});